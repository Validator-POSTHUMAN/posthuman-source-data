# Celestia Mainnet — Consensus Node Installation

This guide installs a Celestia consensus node (`celestia-appd`) for mainnet
chain ID `celestia`.

## Current Versions

- Recommended consensus multiplexer: `v10.5.0`, commit
  `6013e758d5dceb75827ad191c8d739d7c43cfa04`.
- Live mainnet protocol app: `10` (checked 2026-10-28); app v10 activated at
  height `15116658`.
- Go for source builds: `1.26.6`.
- POSTHUMAN's PebbleDB snapshot was stale at the 2026-10-28 check. Verify
  `snapshot.json` against the live chain before use; see [Snapshots](snapshots.md).

Use the official `v10.5.0` multiplexer for new installs and recoveries, not a
v9-only binary. For an existing node, preserve its home and signing state.
See the [official v10.5.0 release](https://github.com/celestiaorg/celestia-app/releases/tag/v10.5.0).

Check live network state before choosing the binary:

```bash
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/abci_info | \
  jq -r '.result.response.version, .result.response.app_version'
```

## Requirements

- Ubuntu 24.04+ for the official release binary, or Ubuntu 22.04+ when building
  `celestia-appd` from source locally.
- 16 CPU cores, 32 GB RAM, 2 TB NVMe, 1 Gbps network for validator-grade use.
- Open ports:
  - P2P: `26656/tcp`
  - RPC/API/gRPC only if intentionally exposed.

## 1. Install Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget jq tar lz4 git make gcc chrony build-essential \
  clang pkg-config libssl-dev ncdu
```

## 2. Install `celestia-appd`

Stage and checksum-verify the official multiplexer archive. This example is
for a new, non-running node; do not reinitialize an existing signer.

```bash
APP_VERSION="v10.5.0"

STAGE_DIR="$(mktemp -d -p /tmp celestia-app-release.XXXXXX)"
cd "$STAGE_DIR"

curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${APP_VERSION}/celestia-app_Linux_x86_64.tar.gz"
curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${APP_VERSION}/checksums.txt"

sha256sum --ignore-missing --check checksums.txt
tar -xzf celestia-app_Linux_x86_64.tar.gz

./celestia-appd version --long
sudo install -m 0755 celestia-appd /usr/local/bin/celestia-appd
celestia-appd version --long
```

Require version `10.5.0`, commit
`6013e758d5dceb75827ad191c8d739d7c43cfa04` and the multiplexer build
tag. Published Linux x86_64 archive SHA-256:
`3a200f501a59406cb7de9134b7ce229409b4095e8dcaa492b88238cef73d4445`.
Verify the executable path before starting a service.

## 3. Initialize

```bash
MONIKER="<YOUR_NODE_NAME>"
CHAIN_ID="celestia"
CELESTIA_HOME="$HOME/.celestia-app"

celestia-appd init "$MONIKER" --chain-id "$CHAIN_ID" --home "$CELESTIA_HOME"
```

## 4. Download Genesis and Addrbook

```bash
curl -fL https://snapshots-celestia-mainnet.posthuman.digital/genesis.json \
  -o "$CELESTIA_HOME/config/genesis.json"

curl -fL https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json \
  -o "$CELESTIA_HOME/config/addrbook.json"

jq -r '.chain_id // .genesis.chain_id' "$CELESTIA_HOME/config/genesis.json"
```

Expected chain ID: `celestia`.

## 5. Configure

```bash
# Minimum gas price
sed -i 's|minimum-gas-prices =.*|minimum-gas-prices = "0.002utia"|' \
  "$CELESTIA_HOME/config/app.toml"

# Pruned node profile
sed -i -e 's|^pruning *=.*|pruning = "custom"|' \
       -e 's|^pruning-keep-recent *=.*|pruning-keep-recent = "100"|' \
       -e 's|^pruning-interval *=.*|pruning-interval = "19"|' \
  "$CELESTIA_HOME/config/app.toml"

# PebbleDB profile; required for current POSTHUMAN snapshots
sed -i -e 's|^db_backend *=.*|db_backend = "pebbledb"|' \
  "$CELESTIA_HOME/config/config.toml"

if grep -q '^app-db-backend' "$CELESTIA_HOME/config/app.toml"; then
  sed -i 's|^app-db-backend *=.*|app-db-backend = "pebbledb"|' \
    "$CELESTIA_HOME/config/app.toml"
else
  printf '\napp-db-backend = "pebbledb"\n' >> "$CELESTIA_HOME/config/app.toml"
fi

# Disable transaction indexer unless you need indexed queries
sed -i 's|^indexer *=.*|indexer = "null"|' \
  "$CELESTIA_HOME/config/config.toml"

# Enable Prometheus metrics
sed -i 's|prometheus = false|prometheus = true|' \
  "$CELESTIA_HOME/config/config.toml"

# POSTHUMAN persistent peer
PEERS="9f21a4f163710710aa7932e1832a257ef326186f@peer-celestia-mainnet.posthuman.digital:40656"
sed -i -e "/^\\[p2p\\]/,/^\\[/{s|^[[:space:]]*persistent_peers *=.*|persistent_peers = \\"$PEERS\\"|}" \
  "$CELESTIA_HOME/config/config.toml"
```

<!-- The POSTHUMAN archive is withdrawn from the restore path; see celestia/snapshots.md -->
The restore procedure lives in one place now: **[Celestia Mainnet Snapshot](snapshots.md)**.
It uses our own archive, which was restore-verified end to end on 2026-09-27, and
names a third-party alternative. Do not copy the old one-line
`curl | lz4 | tar` restore from earlier revisions of this document: it neither
resumes nor verifies a checksum.


## 7. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-appd.service > /dev/null <<EOF
[Unit]
Description=Celestia consensus node
After=network-online.target

[Service]
User=$USER
WorkingDirectory=$CELESTIA_HOME
ExecStart=$(command -v celestia-appd) start --home $CELESTIA_HOME
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable celestia-appd
sudo systemctl restart celestia-appd
```

## 8. Verify

```bash
sudo systemctl status celestia-appd --no-pager
journalctl -u celestia-appd -n 100 --no-pager

curl -fsS http://127.0.0.1:26657/status | jq -r '
  .result.node_info.network,
  .result.sync_info.latest_block_height,
  .result.sync_info.latest_block_time,
  .result.sync_info.catching_up'
```

The node is ready when `network=celestia`, height advances, recent block time
is fresh, and `catching_up=false`.

## 9. Wallet and Validator Commands

Create a wallet:

```bash
WALLET="wallet"
celestia-appd keys add "$WALLET"
```

Restore a wallet:

```bash
WALLET="wallet"
celestia-appd keys add "$WALLET" --recover
```

Create validator only after the node is synced and the operator has reviewed
the transaction:

```bash
celestia-appd tx staking create-validator <validator.json> \
  --from "$WALLET" \
  --chain-id celestia \
  --node http://127.0.0.1:26657 \
  --fees 21000utia
```

Do not broadcast validator, staking, governance, or unjail transactions until
the signer, account, sequence, gas, fees, and message are verified.
