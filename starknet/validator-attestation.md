# Starknet validator attestation

From phase 2 of the staking protocol, a validator must prove every epoch that
it actually follows the chain. The protocol assigns each validator one block
per epoch; the validator must submit an `attest` transaction containing that
block's hash inside the attestation window.

```
epoch:  |-------------------------------------------------|
                 ^ assigned block N        ^ window: N+1 … N+W
```

Mainnet: epoch = 1132 blocks (~1 hour), window = 50 blocks.
Sepolia: epoch = 231 blocks (~20 minutes), window = 30 blocks.

Rewards are **all-or-nothing per epoch**. One confirmed attestation earns the
full epoch reward for you and your delegation pools; a missed window earns zero
for the entire epoch. There is no principal slashing in this phase.

The attestation service is a small daemon that watches your own node, computes
the assigned block, and signs one transaction per epoch from the **operational
account**. It never touches your stake.

## Choosing the service

| Service | Maintainer | Pairs with | Repository |
|---|---|---|---|
| `starknet-validator-attestation` | Equilibrium | Pathfinder | [eqlabs/starknet-validator-attestation](https://github.com/eqlabs/starknet-validator-attestation) |
| `starknet-staking-v2` | Nethermind | Juno | [NethermindEth/starknet-staking-v2](https://github.com/NethermindEth/starknet-staking-v2) |

Both implement [SNIP 28](https://community.starknet.io/t/snip-28-staking-v2-proposal/115250)
and both work against any compliant JSON-RPC node. Use the pairing that matches
your client unless you have a reason not to.

## Prerequisites

- A **fully synced** node. Attesting from a lagging node produces wrong block
  hashes and failed attestations. Verify `starknet_syncing` returns `false`
  first.
- A registered validator — see [Create validator](/networks/starknet/guides/create-validator).
- The operational account funded with STRK for fees. One attestation per epoch
  is cheap, but an empty operational account silently stops attesting.
- The RPC version path your service requires. This is the single most common
  setup failure: check the service's requirement against what your node serves
  (`/rpc/v0_8`, `/rpc/v0_9`, `/v0_10`, …) before wiring them together.

## Option A — Equilibrium service (Pathfinder)

### A.1 Quick run

```bash
docker run -it --rm --network host \
  -e VALIDATOR_ATTESTATION_OPERATIONAL_PRIVATE_KEY="$OPERATIONAL_PRIVATE_KEY" \
  ghcr.io/eqlabs/starknet-validator-attestation \
  --staking-contract-address 0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7 \
  --attestation-contract-address 0x10398fe631af9ab2311840432d507bf7ef4b959ae967f1507928f5afe888a99 \
  --staker-operational-address "$OPERATIONAL_ADDRESS" \
  --node-url http://127.0.0.1:9545/rpc/v0_9 \
  --local-signer
```

Every flag also exists as an environment variable; run the image with `--help`
to list them.

### A.2 Production compose (node + attestation as one unit)

```yaml
# ~/starknet/docker-compose.yml
services:
  pathfinder:
    image: eqlabs/pathfinder:v0.22.7
    container_name: pathfinder
    restart: unless-stopped
    ports:
      - "9545:9545"
      - "9000:9000"
    volumes:
      - ./data:/usr/share/pathfinder/data
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    command:
      - --network
      - mainnet
      - --ethereum.url
      - ${PATHFINDER_ETHEREUM_API_URL}
      - --monitor-address=0.0.0.0:9000
      - --rpc.websocket.enabled

  attestation:
    image: ghcr.io/eqlabs/starknet-validator-attestation:latest
    container_name: attestation
    restart: unless-stopped
    depends_on:
      - pathfinder
    ports:
      - "9091:9090"   # Prometheus metrics
    environment:
      - RUST_LOG=info
      - VALIDATOR_ATTESTATION_OPERATIONAL_PRIVATE_KEY=${STARKNET_OPERATIONAL_PRIVATE_KEY}
      - VALIDATOR_ATTESTATION_METRICS_ADDRESS=0.0.0.0:9090
    command:
      - --staker-operational-address
      - "${STARKNET_OPERATIONAL_ADDRESS}"
      - --staking-contract-address
      - "0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7"
      - --attestation-contract-address
      - "0x10398fe631af9ab2311840432d507bf7ef4b959ae967f1507928f5afe888a99"
      - --node-url
      - http://pathfinder:9545/rpc/v0_9
      - --local-signer
```

```bash
# ~/starknet/.env — chmod 600, owned by the node user, never committed
PATHFINDER_ETHEREUM_API_URL=wss://<your-ethereum-provider>/...
STARKNET_OPERATIONAL_ADDRESS=0x...
STARKNET_OPERATIONAL_PRIVATE_KEY=0x...
```

```bash
cd ~/starknet
docker compose up -d
docker compose logs -f attestation
```

Point `--node-url` at the compose service name (`http://pathfinder:9545/...`)
rather than a host IP. It removes a whole class of failure where the service
keeps attesting against a remote node you thought you had decommissioned.

### A.3 Remote signer

`--local-signer` requires the operational private key in the service's
environment. The alternative keeps the key outside the daemon:

```bash
--remote-signer-url https://<your-signer-host>/sign
```

The signer implements a small HTTP signing API. Use it when the operational key
must live in an HSM or a separate hardened host.

## Option B — Nethermind service (Juno)

Requires a node serving JSON-RPC **0.10.2 or 0.10.3**, over both HTTP and
WebSocket.

### B.1 Configuration file

```json
{
  "provider": {
    "http": "http://127.0.0.1:6060/v0_10",
    "ws": "ws://127.0.0.1:6061/v0_10"
  },
  "signer": {
    "operationalAddress": "0x...",
    "privateKey": "0x..."
  }
}
```

```bash
./build/validator --config /etc/starknet/validator.json
```

Set **either** `privateKey` (internal signing) **or** `url` (external signer).
If both are present the remote signer wins — be explicit rather than relying on
that precedence.

### B.2 Environment variables

```bash
export PROVIDER_HTTP_URL="http://127.0.0.1:6060/v0_10"
export PROVIDER_WS_URL="ws://127.0.0.1:6061/v0_10"
export SIGNER_OPERATIONAL_ADDRESS="0x..."
export SIGNER_PRIVATE_KEY="0x..."

./build/validator
```

### B.3 Useful flags

- `--staking-contract-address`, `--attest-contract-address` — override the
  network defaults. Not needed for mainnet or Sepolia.
- `--balance-threshold` — warn when the operational balance falls below this
  value. Defaults to 100 STRK. Wire this warning into your alerting.
- `--max-tries` — retry attempts for attestation info; `infinite` by default.
- `--braavos-account` — required if the operational account is a Braavos
  account, because of its different transaction version encoding.
- `--log-level` — `info` by default, `debug` when diagnosing.

## systemd unit (binary deployments)

```ini
# /etc/systemd/system/starknet-attestation.service
[Unit]
Description=Starknet validator attestation
After=network-online.target
Wants=network-online.target

[Service]
User=starknet
Group=starknet
EnvironmentFile=/etc/starknet/attestation.env
ExecStart=/usr/local/bin/validator --config /etc/starknet/validator.json
Restart=always
RestartSec=10
LimitNOFILE=65536
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/starknet

[Install]
WantedBy=multi-user.target
```

```bash
sudo chmod 600 /etc/starknet/attestation.env
sudo chown starknet:starknet /etc/starknet/attestation.env
sudo systemctl daemon-reload
sudo systemctl enable --now starknet-attestation
sudo journalctl -u starknet-attestation -f
```

## Verify it works

Healthy startup logs the current epoch and the attestation parameters:

```
Current attestation info staker_address=0x… operational_address=0x… stake=… \
  epoch_id=1201 epoch_start=712773 epoch_length=40 attestation_window=16
```

Within one epoch you must see the full cycle:

```
INFO New epoch started epoch_id=1205 …
INFO Attestation transaction sent transaction_hash=0x79f9f5…
INFO Attestation confirmed staker_address=0x… epoch_id=1205
```

**"Attestation transaction sent" is not success.** Only
`Attestation confirmed` proves the epoch was earned. Treat a sent-but-never-
confirmed transaction as an incident: it usually means fee starvation, a
lagging node, or an operational account that cannot sign.

Cross-check onchain — unclaimed rewards must grow epoch over epoch:

```bash
sncast call \
  --contract-address=0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7 \
  --function=get_staker_info_v1 \
  --arguments=$STAKING_ADDRESS \
  --network=mainnet
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `PRIVATE_KEY not set` on startup | env var missing or `.env` not loaded by the runtime | Confirm the exact variable name for your service; for compose, confirm `env_file` resolves |
| `Connection refused` to the node | node not up, wrong port, or container-to-container name not resolvable | Curl the RPC from inside the attestation container |
| Method not found / unsupported spec | RPC version path mismatch | Align the node's served version with the service requirement |
| Attestations sent, never confirmed | operational account out of gas | Fund it; alert on `--balance-threshold` |
| Attestation skipped every epoch | node lagging behind head | Check `starknet_syncing` and the L1 WebSocket dependency |
| WebSocket stream closed, repeatedly | unstable Ethereum WS endpoint | Switch provider or add a fallback endpoint |
| Signing fails on a protected account | Ready Guardian / Braavos hardware signer blocks automated signing | Use an unprotected operational account for local signing, or a remote signer |

## Operational rules

- Never run two attestation services with the **same operational key** against
  the same validator. Duplicate `attest` transactions waste fees and make
  diagnosis ambiguous. If you run a standby host, keep its service stopped.
- Restart the attestation service after any change to the node URL, RPC
  version, operational address or key — and verify one confirmed attestation
  afterwards before walking away.
- Upgrade the node and the attestation service as a pair; a node upgrade that
  changes the served RPC version breaks a working attestation setup.

## Reference

- Starknet docs — [Attesting to blocks](https://docs.starknet.io/secure/quickstart/attesting-to-blocks)
- [Equilibrium attestation service](https://github.com/eqlabs/starknet-validator-attestation)
- [Nethermind starknet-staking-v2 documentation](https://nethermindeth.github.io/starknet-staking-v2/)
- [SNIP 28 — Staking V2](https://community.starknet.io/t/snip-28-staking-v2-proposal/115250)
