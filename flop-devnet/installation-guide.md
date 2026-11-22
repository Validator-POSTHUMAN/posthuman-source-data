# FLOP Devnet: GPU inference miner guide

FLOP is a verification layer for AI inference. A **miner** serves one pinned model on its own GPU:
- a vLLM backend produces TOPLOC proofs;
- a worker holds the miner account, answers calibration jobs, and later serves paid sessions over an HTTPS session endpoint.

Its stake is posted by a sponsor. It is penalised for jobs it leaves unanswered, not for double-signing.

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

1. **Genesis.** Read the genesis hash with the digest-pinned CLI and compare it with the value you recorded. Stop on any mismatch: a devnet reset invalidates keys, grants and policies.

   ```sh
   docker run --rm --network host "$FLOP_CLI" --network devnet --rpc wss://rpc.devnet.flop.network network status --json | jq -r .rpc.genesis_hash
   ```

2. **Images.** Pin every image in `miner.env` as `vX.Y.Z@sha256:…`, never `:stable`.
3. **Account.** Run every signing script with `DRY_RUN=1` first and check the address. `retire.sh` signs a deregistration without it.
4. **Model.** Fetch the exact model revision the pack names with `./fetch-model.sh`, check every file against a checksum list, and mount it read-only.
5. **Decode policy.** Before every start:
   1. export `FLOP_CLI` from `miner.env`;
   2. run `./decode-policy.sh miner.env`.

   It writes the policy hash only if the chain allowlists it.

## Account and sponsorship

- **Create the account and keep its files private.** Create the miner account with the pack's key commands. Back up `miner-key.json` offline. Never send it, the `signer` file or the phrase to anyone, including FLOP.
- **Approved operators** request an operator key once, through the access-request template at <https://github.com/flop-labs/network>, and grant miners with `sponsor-grant.sh`. Keep the operator key off miner hosts.
- **Sponsorship request:**
  1. Read <https://faucet.flop.network/limits>.
  2. Run `./sponsor.sh` once.
  3. Read the reply:
     - `200`/`201` means done;
     - `409` means already sponsored;
     - `503` means retry in a minute;
     - `429` means a limit, so retry later;
     - `403` means the wrong role or an invalid grant.
- **Never retry in a loop,** and never run `miner register` by hand.

## Secrets

`miner.env` holds `INFERENCE_API_KEY` and `SESSION_AUTH_TOKEN`, and `session-keys/enclave.seed` signs sessions.
- Generate each **once**, on the host. Create the seed with `set -C` so a rerun cannot overwrite it.
- Never regenerate them after the first start, and never pass them in command arguments.
- Never run `docker compose … config` unfiltered: it prints them.
- For authenticated loopback calls, give curl the bearer header through a config on stdin (`curl --config -`).

## Start

1. **Backend.** Start it first and wait for `/health` to show:
   - `ok: true`;
   - `model_identity: "measured"`;
   - the expected model hash and decode-policy hash.

   Record the cold-start time.
2. **Endpoint.** Behind a tunnel, the public name must answer 502 or 530 (origin down) with no redirect or bot challenge.
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
  - the fee trend.
- **Backups.** After calibration, back up the worker-data volume together with `miner.env` and `enclave.seed`, encrypted or in root-only storage.

## Downtime, restarts and upgrades

- **There is no pause.** A job left unanswered past its deadline (600 blocks, about 10 minutes at about 1 s per block) is penalised. Keep any planned outage to about 5 minutes, including the backend cold start.
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

1. Run the genesis check, then `DRY_RUN=1 ./retire.sh`.
2. Stop the worker.
3. Run `./retire.sh` immediately, then confirm `registered: false` in `miner status`.

An open session or dispute refuses the exit until it settles. Sponsored stake unbonds over 7 days and returns to the sponsor. A retired miner still counts toward the operator's quota.

## Sources

- FLOP devnet public-path miner pack, README and scripts (`devnet-ts-20261110`)
- [Operator documentation](https://docs.flop.network/)
- [Mining explorer](https://explorer.devnet.flop.network/mining)
- [POSTHUMAN FLOP miner skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/flop)
