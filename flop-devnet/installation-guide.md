# FLOP Devnet: GPU inference miner guide

FLOP is a verification layer for AI inference. A **miner** serves one pinned model on its own GPU:
- a vLLM backend produces TOPLOC proofs;
- a worker holds the miner account, answers calibration jobs, and later serves paid sessions over an HTTPS session endpoint.

Its stake is posted by a sponsor. The penalties documented so far come from jobs it leaves unanswered; FLOP has not published full slashing rules, so never run two workers on one miner account.

This guide follows the official **devnet public-path miner pack** and adds the checks POSTHUMAN uses. Test FLOP has no value, and there are no earnings yet. The devnet changes often: re-verify every pinned value against the pack, <https://flop.network/releases.json> and the finalized chain before you use it.

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

- **There is no pause.** A calibration job left unanswered is penalised. Operators in November 2026 used a 600-block deadline, which is about 10 minutes at about 1 s per block; re-check it for your release. Keep any planned outage to about 5 minutes, including the backend cold start.
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

## Sources

- FLOP devnet public-path miner pack, README and scripts (`devnet-ts-20261110`)
- [Operator documentation](https://docs.flop.network/)
- [Mining explorer](https://explorer.devnet.flop.network/mining)
- [POSTHUMAN FLOP miner skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/flop)
