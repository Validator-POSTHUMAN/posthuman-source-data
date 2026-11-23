# FLOP Devnet: GPU miner and keyless node guide

FLOP is a verification layer for AI inference. A **miner** serves one pinned model on its own GPU:
- a vLLM backend produces TOPLOC proofs;
- a worker holds the miner account, answers calibration jobs, and later serves paid sessions over an HTTPS session endpoint.

Its stake is posted by a sponsor. The penalties documented so far come from jobs it leaves unanswered; FLOP has not published full slashing rules, so never run two workers on one miner account.

The first part follows the official **devnet public-path miner pack** and adds the checks POSTHUMAN uses. The second part, [Keyless full node](#keyless-full-node-first-step-to-a-validator-seat), covers the first steps towards a validator seat. Test FLOP has no value, and there are no earnings yet. The devnet changes often: re-verify every pinned value against the pack, <https://flop.network/releases.json> and the finalized chain before you use it.

## Host

- Ubuntu 22.04 or 24.04.
- An NVIDIA GPU with at least 16 GB VRAM.
- Docker with Compose and the NVIDIA container toolkit: `docker info | grep -i nvidia` must print something.
- `jq`, `curl`, `openssl`.
- A public DNS name for the session endpoint, served one of two ways:
  - **Caddy sidecar** from the pack: inbound TCP 80 and 443, Let's Encrypt certificate;
  - **your own tunnel or TLS proxy** to `http://127.0.0.1:8645`, for hosts behind NAT. Then leave `docker-compose.tls.yml` out.
- **Open nothing else.** The session port 8645 and the model backend stay on loopback.
- **Sharing the GPU.** On a shared GPU, lower `GPU_MEMORY_UTILIZATION` (for example `0.5` on a 24 GB card) and confirm in the backend log that the KV cache still fits.

Run everything as root from `/opt/flop-miner` (mode 0700). Verify the pack tarball's SHA256 against the value you received with it before unpacking.

## Before any start or signature

Work in a root shell (`sudo -i`, then `cd /opt/flop-miner`). `miner.env` is root-only, and `sudo` resets the environment, so running pack scripts through `sudo` from a user shell easily loses `FLOP_CLI` and `DRY_RUN`. Load and check the pinned CLI first:

```sh
export FLOP_CLI="$(sed -n 's/^FLOP_CLI=//p' /opt/flop-miner/miner.env | tail -1)"
case "$FLOP_CLI" in *@sha256:*) echo "FLOP_CLI pinned" ;; *) echo "FLOP_CLI empty or unpinned: STOP" >&2 ;; esac
```

1. **Genesis.** Read the genesis hash with the digest-pinned CLI and compare it with the value you recorded. Stop on any mismatch: a devnet reset invalidates keys, grants and policies.

   ```sh
   docker run --rm --network host "$FLOP_CLI" --network devnet --rpc wss://rpc.devnet.flop.network network status --json | jq -r .rpc.genesis_hash
   ```

2. **Images.** Pin every image in `miner.env` as `vX.Y.Z@sha256:…`, never `:stable`. `decode-policy.sh`, `sponsor.sh` and `retire.sh` fall back to `cli:stable` when `FLOP_CLI` is not in their environment, and the last two mount the miner signer into it. An empty value counts as unset, so run the scripts only from the root shell above, after the `FLOP_CLI pinned` check.
3. **Account.** Dry-run every signing script first and check the printed address. The dry run happens only when `DRY_RUN` reaches the script as exactly `1`:
   - in the root shell, use `DRY_RUN=1 ./retire.sh` (and `DRY_RUN=1 ./sponsor.sh`), without `sudo`;
   - **never** use `DRY_RUN=1 sudo ./retire.sh`: sudo drops the variable, and the deregistration is signed for real;
   - no `DRY_RUN:` line in the output means it did not dry-run, so stop.
4. **Model.** Fetch the exact model revision the pack names with `./fetch-model.sh`, check every file against a checksum list, and mount it read-only.
5. **Decode policy.** Before every start, run `./decode-policy.sh miner.env` in the root shell, after the `FLOP_CLI pinned` check. It writes the policy hash only if the chain allowlists it. Never run `sudo ./decode-policy.sh`: it drops `FLOP_CLI` and mounts `miner.env`, tokens included, into `:stable`.

## Account and sponsorship

- **Create the account and keep its files private.** Create the miner account with the pack's key commands. Back up `miner-key.json` offline. Never send it, the `signer` file or the phrase to anyone, including FLOP.
- **Approved operators** request an operator key once, through the access-request template at <https://github.com/flop-labs/network>, and grant miners with `sponsor-grant.sh`. Keep the operator key off miner hosts.
- **Sponsorship request:**
  1. Read <https://faucet.flop.network/limits>.
  2. In the root shell, dry-run with `DRY_RUN=1 ./sponsor.sh`, then run `./sponsor.sh` once. Approved operators prefix `GRANT_FILE=…`.
  3. Read the reply:
     - `200`/`201` means done;
     - `409` means already sponsored;
     - `503` means retry in a minute;
     - `429` means a limit, so retry later;
     - `403` means the wrong role or an invalid grant;
     - `422` means operator review.
- **Never retry in a loop,** and never run `miner register` by hand.

## Secrets

`miner.env` holds `INFERENCE_API_KEY` and `SESSION_AUTH_TOKEN`, and `session-keys/enclave.seed` signs sessions.
- Generate each **once**, on the host. Create the seed with `set -C` so a rerun cannot overwrite it.
- Never regenerate them after the first start, and never pass them in command arguments.
- Never run `docker compose … config` unfiltered: it prints them.
- For authenticated loopback calls, give curl the bearer header through a config on stdin (`curl --config -`).

## Start

1. **Backend.** Start it first and wait for `/health` to show:
   - `model_identity: "measured"`;
   - the expected model hash and decode-policy hash.

   Record the cold-start time.
2. **Endpoint.** Behind a tunnel, the public name must answer 502 (origin down; Cloudflare may show 530) with no redirect or bot challenge.
3. **Worker.** Start it. The log should show:
   - `Image: version …`;
   - `[gpu] declared`;
   - `published ghost key`;
   - `Endpoint ad (https://<name>): published to the mailbox`.

   From here the worker signs small on-chain actions and pays fees from the miner account.
4. **Reachability.** Through the endpoint, an unauthenticated `/session/info` must return **401**.

## Calibration and health

- **Calibration** runs automatically and can take up to a day. Watch <https://explorer.devnet.flop.network/mining> and `miner status <address> --json` until `calibration` is non-null. Until then, `is_ready: false` and three failing self-check items (`local-session`, `chain`, `info-proof`) are normal.
- **`sudo ./self-check.sh --json`** (add `--no-tls` behind your own tunnel) is read-only. Fix the first FAIL. After calibration, everything except `gateway-listing` should pass.
- **The POSTHUMAN skill's `flop-miner-healthcheck.sh`** adds:
  - the genesis comparison;
  - container restart counts;
  - GPU memory;
  - the edge 401;
  - the calibration record;
  - a free-balance reading to compare between runs.
- **Backups.** After calibration, back up the worker-data volume together with `miner.env` and `enclave.seed`, encrypted or in root-only storage.

## Downtime, restarts and upgrades

- **There is no pause.** A calibration job left unanswered is penalised. Operators in November 2026 used a 600-block deadline, which is about 10 minutes at about 1 s per block; re-check it for your release. Keep any planned outage to at most about 5 minutes (half the deadline), including the backend cold start.
- **Prefer `docker compose … restart worker`.** Allowed commands:
  - `stop`;
  - `start`;
  - `restart`;
  - `up -d`;
  - `down` **without** `-v`.
- **Never run:**
  - `down -v`;
  - `docker volume rm|prune`;
  - `docker system prune --volumes`.
- **Avoid unplanned outages.** Keep unattended upgrades from replacing the NVIDIA driver while the miner runs. Do not restart the Docker daemon casually.
- **Image upgrade:**
  1. Record the current image pins.
  2. Read the release notes: older workers cannot read newer journals.
  3. Run the genesis check and the decode policy.
  4. Run `up -d`.
  5. Keep the old pins for rollback.

## Permanent exit

1. In the root shell, load and check `FLOP_CLI`, then run the genesis check.
2. Run `DRY_RUN=1 ./retire.sh` and confirm the `DRY_RUN:` line shows your address.
3. Stop the worker.
4. Immediately run `./retire.sh`, then confirm `registered: false` in `miner status`.

An open session, a dispute or native delegated stake refuses the exit until it is resolved. Sponsored stake unbonds over 7 days and returns to the sponsor. A retired miner still counts toward the operator's quota.

## Keyless full node: first step to a validator seat

FLOP's [validator page](https://explorer.devnet.flop.network/validator) and its [Devnet RPC guide](https://gist.github.com/sv/7c8b93f3868bc15e3b6eabe0578057e3) (setup files pinned to revision `21adaa99c601003278d1682bf937696f21d31432`) describe this path:
1. one operator application per team (you may apply before the node is synced and add the evidence later);
2. a keyless full node that syncs over public P2P and survives a restart;
3. a signing handoff, by FLOP's invitation only.

This part covers the first two steps. It adds what POSTHUMAN learned while qualifying its candidate in November 2026.
- **No account, session or validator key.** The node never signs and holds no stake. Its only key is the libp2p node key on its volume, which fixes its Peer ID. Do not set `NODE_ROLE=validator` or run any `join` command on it.
- **A host of its own.** Run it on a different host from the miner: it needs inbound TCP 30333, and the miner host opens nothing beyond its session endpoint. Never copy miner or account files into it.

### Host

- **Machine.** A dedicated Linux x86-64 host or isolated VM with:
  - Docker Engine and Compose v2 (2.24.4 or later for the hardening below; we tested with 2.40);
  - `curl`, `jq` and `sha256sum`;
  - a stable public IPv4.

  No GPU is needed. FLOP's pilot reference is 4 vCPU, 16 GiB RAM and 300 GB SSD, an observed starting point rather than a requirement. The archive database keeps growing (57 GB on 2026-11-21), so watch free disk.
- **Shared hosts: check disk I/O first.** The initial sync writes heavily.
  - Our first attempt ran on a host with signing validators, and it tripped another validator's I/O-pressure guard. CPU and memory limits did not help, and I/O throttling raised the pressure further.
  - We stopped it and moved the node to a host where its data sits on a separate NVMe disk.
  - Before you place the node next to a signer: list the host's existing I/O, thermal and disk guards and sample their margins. Count the initial sync in the load budget, and have a way to stop only this node.
- **Ports.**
  - Open inbound TCP 30333 and allow outbound P2P.
  - RPC 9944, metrics 9615 and readiness 9619 stay on `127.0.0.1`. From another host, check that they are refused, for example with `curl -m 5 http://<public IPv4>:9944`, then 9615 and 9619. A refusal or a timeout are both fine; an answer is not.

### Install and sync

1. Follow step 1 of FLOP's guide:
   - download the five setup files and the raw chain spec;
   - check every SHA256 it lists;
   - create `rpc-pool.env`.

   The env template pins the node image by digest (`node-devnet@sha256:84498fd7…`) and uses archive pruning.
2. In `rpc-pool.env`:
   - set `HOST_IP` to the host's own interface and `PUBLIC_ADDR` to `/ip4/<public IPv4>/tcp/30333`. Behind NAT (AWS, for example) the two differ;
   - keep `RPC_BIND_IP=127.0.0.1` and `PROMETHEUS_BIND_IP=127.0.0.1`.
3. **Keep the project and the volume.** The node key and the database live on the volume.
   - Use the same Compose project name and volume on every start.
   - Never run `down -v`, `docker volume rm` or a volume prune on it.
   - A new volume means a new Peer ID, which breaks the restart proof and the Peer ID in your application, and then a full resync.
4. **Bootnode.** In November 2026 the pinned bootnode accepted TCP and then closed or reset the connection during the libp2p handshake (flop-labs/network#522, #571).
   - If your node finds no peers through it, put a community peer from another team's public application first in `BOOTNODES` (space-separated) and keep the official one second. We used one from flop-labs/network#429.
   - A community peer is a third party you choose to trust. The hash comparison against FLOP's reference below still decides whether you follow the right chain.
   - Never edit the chain spec or genesis to fix peering.
5. **Start and wait.** `curl http://127.0.0.1:9619/ready` returns 503 while syncing and 200 once caught up.
   - Our sync from genesis took 1 h 44 min. FLOP quotes about 3 hours.
   - FLOP also publishes a [daily archive snapshot](https://snapshots.flop.network/devnet-ts/archive/). Read the caveats in its guide first: blocks before the snapshot height are not re-executed, and it only fits an archive node.
   - A running container or a peer count alone is not success.

### Optional hardening (what POSTHUMAN runs)

This is an **excerpt, not a complete file**, used as an override on top of FLOP's file. Add it (`-f <override>.yml`) to every FLOP Compose command and to the systemd unit, or a plain `up -d` recreates the containers without the hardening. Everything else stays as in FLOP's `docker-compose.rpc.yml`, including:
- `NODE_ROLE: rpc` and `RPC_METHODS: safe`;
- `PUBLIC_ADDR`;
- `CHAIN: /chainspec/chain.raw.json`;
- the loopback bindings of 9944, 9615 and 9619.

Without `NODE_ROLE: rpc`, the entrypoint defaults to the validator role.

```yaml
services:
  rpc:
    image: local/flop-keyless:21adaa99   # see the Dockerfile below
    restart: "no"                        # a systemd unit starts and stops the project
    read_only: true
    tmpfs: ["/tmp:size=256m,mode=1777"]
    cap_drop: [ALL]
    cap_add: [SETUID, SETGID]            # the entrypoint drops to the node user with gosu
    security_opt: [no-new-privileges:true]
    mem_limit: 32g                       # size to your host
    memswap_limit: 32g
    volumes: !override [rpc-data:/data]  # entrypoint and chain spec are baked into the image
  ready:
    image: local/flop-ready:21adaa99     # FROM the pinned python digest, COPY rpc_ready.py /opt/rpc_ready.py, USER 65534
    restart: "no"
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    volumes: !reset []
```

```dockerfile
FROM ghcr.io/flop-labs/flop-core/node-devnet@sha256:84498fd73db2464eb13088ab34d369ddf7cddd22a45c810d140c9ff8ec16c91d
COPY node-entrypoint.sh /usr/local/bin/devnet-node-entrypoint.sh
COPY chain.raw.json /chainspec/chain.raw.json
ENTRYPOINT ["/bin/sh", "/usr/local/bin/devnet-node-entrypoint.sh"]
```

- **Data directory.** In our build the node runs as UID 1001 (check with `docker run --rm --entrypoint id <image> user`), so its data directory must be writable by that user.
- **systemd unit.**
  - On start, it checks free disk space, then runs `docker compose up -d --no-build`.
  - On stop, it sets this project's containers to `restart=no`, stops them, and confirms that they really stopped.
- **Disk guard.** A timer checks free space every five minutes and stops only this node below a set threshold.
- **Monitoring.** With `restart: "no"`, a crashed node stays down, so alert on readiness and on the container state.

### Prove sync and restart recovery

Run the `observe` checks from step 2 of FLOP's guide:
1. two observations at least 60 s apart;
2. one restart of this project only;
3. a third observation after readiness returns.

Keep all three receipts:
- UTC time;
- local and reference finalized heights;
- the common height and its hash;
- the Peer ID.

The heights must rise, the hashes must match, and the Peer ID must not change across the restart. If finality stalls or a hash differs, stop and report it in your application. Never delete the database to "fix" sync. If you restart through systemd, check that both containers actually stopped before you start them again.

### Apply once per team

- **Which form.** Use FLOP's [operator application](https://github.com/flop-labs/network/issues/new?template=operator-application.yml&network=devnet): one per team per network, updated as you progress, never duplicated. The fields are listed in step 3 of FLOP's guide.
- **Earlier contacts.** Link any earlier introduction, for example a comment in flop-labs/network#10. Because the rule is one application per network, we filed Testnet interest as a separate issue.
- **Approval.** The issue is a public record, not approval. Maintainers add `intake:sync-qualified` and later labels only after they verify the evidence.
- **Secrets.** Never post any of these:
  - seeds or session secret keys;
  - `account.json` or `.env` files;
  - keystores, enrollment tokens or TLS private keys.

### What comes next

- **Signing.** Self-service signing is not open. FLOP has published a [signing release and handoff](https://gist.github.com/sv/870b0fa9d63efa6c7873ded10d49d411), but the coordinated committee deployment and complete public DA reachability are still pending, and signing needs FLOP's explicit invitation. Until then, keep the node keyless and synced.
- **When invited:**
  - use the checksummed package for your invitation, on a separate validator host or isolated deployment;
  - never run two processes with the same validator keys;
  - per FLOP, copying a volume into another Compose project is not an approved migration.
- **Testnet** will have its own image, chain spec, genesis and admission steps. Start it with a fresh database.

## Sources

- FLOP devnet public-path miner pack, README and scripts (`devnet-ts-20261110`)
- [FLOP Devnet RPC guide](https://gist.github.com/sv/7c8b93f3868bc15e3b6eabe0578057e3) (setup files at revision `21adaa99…`) and the [validator page](https://explorer.devnet.flop.network/validator)
- [Operator documentation](https://docs.flop.network/)
- [Mining explorer](https://explorer.devnet.flop.network/mining)
- [POSTHUMAN FLOP miner skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/flop)
