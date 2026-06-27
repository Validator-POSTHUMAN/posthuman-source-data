# Celestia Full Storage Node Setup

This guide installs a Celestia Data Availability full storage node on mainnet
using `celestia-node`.

## Current Version

- Celestia node: `v0.31.3`
- Network: `celestia`
- Default full-node store: `~/.celestia-full`
- Trusted core RPC: `https://rpc-celestia-mainnet.posthuman.digital`

## Requirements

- 8 CPU cores or more
- 64 GB RAM
- 8 TiB NVMe for non-archival operation
- 160 TiB NVMe for archival operation
- 1 Gbps network

## 1. Install Packages and Go

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git wget jq tar make gcc build-essential clang \
  pkg-config libssl-dev ncdu lz4

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
```

## 3. Initialize

```bash
celestia full init \
  --core.ip https://rpc-celestia-mainnet.posthuman.digital \
  --p2p.network celestia
```

Create or restore a key:

```bash
KEY_NAME="my_celes_key"
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type full

# Restore existing key:
# ./cel-key add "$KEY_NAME" --keyring-backend test --node.type full --recover
```

## 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-full.service > /dev/null <<EOF
[Unit]
Description=Celestia full storage node
After=network-online.target

[Service]
User=$USER
ExecStart=$(command -v celestia) full start \
  --core.ip https://rpc-celestia-mainnet.posthuman.digital \
  --core.rpc.port 443 \
  --core.grpc.port 443 \
  --keyring.accname my_celes_key \
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
sudo systemctl enable celestia-full
sudo systemctl restart celestia-full
journalctl -u celestia-full -f -o cat
```

## 5. Verify

```bash
systemctl status celestia-full --no-pager
celestia header sync-state --node.store ~/.celestia-full
celestia p2p info --node.store ~/.celestia-full
celestia state balance --node.store ~/.celestia-full
```

## 6. Upgrade

```bash
sudo systemctl stop celestia-full

cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node

NODE_VERSION="v0.31.3"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key

celestia full config-update
sudo systemctl restart celestia-full
```

## 7. Remove

```bash
sudo systemctl stop celestia-full
sudo systemctl disable celestia-full
sudo rm -f /etc/systemd/system/celestia-full.service
sudo systemctl daemon-reload
rm -rf "$HOME/celestia-node" "$HOME/.celestia-full"
```
