# Celestia Mainnet — Consensus Node Installation

This guide installs a Celestia consensus node (`celestia-appd`) for mainnet
chain ID `celestia`.

## Current Versions

- Active mainnet app version: `v8.0.8`
- Published app v9 release: `v9.0.4`
- Signaled upgrade height for app v9: `11771698`
- Go for source builds: `1.24.1+`
- POSTHUMAN snapshot format: `snapshot-latest.tar.lz4`

Use `v8.0.8` until the network reaches the app v9 upgrade height. After the
upgrade has executed, use `v9.0.4` for new installs and recoveries.

Check live network state before choosing the binary:

```bash
curl -fsS https://celestia-rpc.publicnode.com:443/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
```

## Requirements

- Ubuntu 22.04+ or similar Linux distribution.
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

Use the current active mainnet binary unless the network has already completed
the app v9 upgrade.

```bash
APP_VERSION="v8.0.8"

cd "$HOME"
rm -rf celestia-app-release
mkdir celestia-app-release
cd celestia-app-release

curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${APP_VERSION}/celestia-app_Linux_x86_64.tar.gz"
curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${APP_VERSION}/checksums.txt"

sha256sum -c --ignore-missing checksums.txt
tar -xzf celestia-app_Linux_x86_64.tar.gz

chmod +x celestia-appd
sudo mv celestia-appd /usr/local/bin/celestia-appd
celestia-appd version
```

If the network is already on app v9, set `APP_VERSION="v9.0.4"` and repeat the
same install flow.

## 3. Initialize

```bash
MONIKER="<YOUR_NODE_NAME>"
CHAIN_ID="celestia"
CELESTIA_HOME="$HOME/.celestia-app"

celestia-appd init "$MONIKER" --chain-id "$CHAIN_ID" --home "$CELESTIA_HOME"
```

## 4. Download Genesis and Addrbook

```bash
curl -fL https://snapshots.posthuman.digital/celestia-mainnet/genesis.json \
  -o "$CELESTIA_HOME/config/genesis.json"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json \
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

# Disable transaction indexer unless you need indexed queries
sed -i 's|^indexer *=.*|indexer = "null"|' \
  "$CELESTIA_HOME/config/config.toml"

# Enable Prometheus metrics
sed -i 's|prometheus = false|prometheus = true|' \
  "$CELESTIA_HOME/config/config.toml"

# POSTHUMAN persistent peer
PEERS="2cc7330049bc02e4276668c414222593d52eb718@135.181.227.236:40656"
sed -i -e "/^\\[p2p\\]/,/^\\[/{s|^[[:space:]]*persistent_peers *=.*|persistent_peers = \\"$PEERS\\"|}" \
  "$CELESTIA_HOME/config/config.toml"
```

## 6. Restore From POSTHUMAN Snapshot

Use a snapshot for faster sync. Verify `snapshot.json` against a trusted
reference RPC before using it. If metadata and network height disagree, stop
and investigate before restore.

```bash
curl -fsS https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json | jq .
curl -fsS https://celestia-rpc.publicnode.com:443/status | \
  jq -r '.result.sync_info.latest_block_height'
```

Restore:

```bash
sudo systemctl stop celestia-appd 2>/dev/null || true

cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup" 2>/dev/null || true

rm -rf "$CELESTIA_HOME/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$CELESTIA_HOME"

if [ -f "$CELESTIA_HOME/priv_validator_state.json.backup" ]; then
  mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
     "$CELESTIA_HOME/data/priv_validator_state.json"
fi
```

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
