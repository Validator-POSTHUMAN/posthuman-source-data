# Celestia Bridge Node Setup

This guide installs a Celestia Data Availability bridge node on mainnet using
`celestia-node`.

## Current Version

- Celestia node: `v0.31.3`
- Network: `celestia`
- Default bridge store: `~/.celestia-bridge`
- Default local JSON-RPC: `http://127.0.0.1:26658`
- Trusted core RPC: `https://rpc-celestia-mainnet.posthuman.digital`
- Metrics collector: `otel.celestia.observer`

## Requirements

Bridge nodes are heavy DA nodes. Plan for:

- 8 CPU cores or more
- 64 GB RAM
- 8 TiB NVMe for non-archival operation
- 160 TiB NVMe for archival operation
- 1 Gbps network

## 1. Install Packages and Go

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git wget jq tar make gcc build-essential clang \
  pkg-config libssl-dev ncdu lz4 aria2

cd "$HOME"
GO_VERSION="1.24.1"
if ! command -v go >/dev/null 2>&1; then
  wget "https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
  rm "go${GO_VERSION}.linux-amd64.tar.gz"
fi

grep -q "/usr/local/go/bin" "$HOME/.bash_profile" 2>/dev/null || \
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> "$HOME/.bash_profile"
source "$HOME/.bash_profile" 2>/dev/null || true
go version
```

## 2. Build `celestia-node`

```bash
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node

NODE_VERSION="v0.31.3"
git checkout "tags/${NODE_VERSION}"

make build
sudo make install
make cel-key

celestia version
./cel-key version 2>/dev/null || true
```

## 3. Initialize the Bridge Node

```bash
celestia bridge init \
  --core.ip https://rpc-celestia-mainnet.posthuman.digital \
  --p2p.network celestia
```

List the generated bridge key:

```bash
cd "$HOME/celestia-node"
./cel-key list --node.type bridge --keyring-backend test
```

Fund the bridge wallet with enough TIA for PayForBlob transactions before
production use.

## 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-bridge.service > /dev/null <<EOF
[Unit]
Description=Celestia bridge node
After=network-online.target

[Service]
User=$USER
ExecStart=$(command -v celestia) bridge start \
  --core.ip https://rpc-celestia-mainnet.posthuman.digital \
  --core.rpc.port 443 \
  --core.grpc.port 443 \
  --p2p.network celestia \
  --metrics \
  --metrics.tls=true \
  --metrics.endpoint otel.celestia.observer
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable celestia-bridge
sudo systemctl restart celestia-bridge
journalctl -u celestia-bridge -f -o cat
```

Add `--archival` only when you intentionally run an archival bridge node and
have enough disk.

## 5. Verify

```bash
systemctl status celestia-bridge --no-pager

celestia header sync-state --node.store ~/.celestia-bridge
celestia p2p info --node.store ~/.celestia-bridge
celestia state balance --node.store ~/.celestia-bridge

NODE_TYPE=bridge
AUTH_TOKEN=$(celestia "$NODE_TYPE" auth admin --node.store ~/.celestia-bridge)

curl -fsS \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
  http://127.0.0.1:26658 | jq .
```

## 6. Optional Bridge Store Restore

Bridge-node stores are not consensus snapshots. Do not restore
`snapshot-latest.tar.lz4` into `~/.celestia-bridge`.

If you use a third-party bridge snapshot, verify the provider, network,
archive name, checksum or size, and freshness first. ITRocket publishes a
Celestia bridge-node guide at:

```text
https://itrocket.net/services/mainnet/celestia/bridge-node/
```

Safe restore shape:

```bash
sudo systemctl stop celestia-bridge

cp -a ~/.celestia-bridge ~/.celestia-bridge.backup-$(date +%Y%m%d-%H%M%S)

# Replace only bridge-node store data after verifying the selected snapshot.
# Do not delete keys unless the operator explicitly approves it.

sudo systemctl restart celestia-bridge
journalctl -u celestia-bridge -f -o cat
```

## 7. Upgrade

```bash
sudo systemctl stop celestia-bridge

cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node

NODE_VERSION="v0.31.3"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key

celestia bridge config-update
sudo systemctl restart celestia-bridge
```

Verify header sync, p2p info, balance, metrics, and logs after every upgrade.

## 8. Remove

```bash
sudo systemctl stop celestia-bridge
sudo systemctl disable celestia-bridge
sudo rm -f /etc/systemd/system/celestia-bridge.service
sudo systemctl daemon-reload
rm -rf "$HOME/celestia-node" "$HOME/.celestia-bridge"
```
