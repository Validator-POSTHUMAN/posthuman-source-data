# Celestia Light Node Setup

This guide installs a Celestia Data Availability light node on mainnet using
`celestia-node`.

## Current Version

- Celestia node: `v0.31.3`
- Network: `celestia`
- Default light-node store: `~/.celestia-light`
- Trusted core RPC: `https://rpc-celestia-mainnet.posthuman.digital`

## Requirements

- 1 CPU core or more
- 500 MB RAM or more
- 20 GB SSD or more for non-archival use
- Stable network connection

## 1. Install Packages and Go

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git wget jq tar make gcc build-essential clang \
  pkg-config libssl-dev ncdu

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
celestia light init \
  --core.ip https://rpc-celestia-mainnet.posthuman.digital \
  --p2p.network celestia
```

Create or restore a key:

```bash
KEY_NAME="my_celes_key"
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type light

# Restore existing key:
# ./cel-key add "$KEY_NAME" --keyring-backend test --node.type light --recover
```

## 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-light.service > /dev/null <<EOF
[Unit]
Description=Celestia light node
After=network-online.target

[Service]
User=$USER
ExecStart=$(command -v celestia) light start \
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
sudo systemctl enable celestia-light
sudo systemctl restart celestia-light
journalctl -u celestia-light -f -o cat
```

## 5. Verify

```bash
systemctl status celestia-light --no-pager
celestia header sync-state --node.store ~/.celestia-light
celestia p2p info --node.store ~/.celestia-light
celestia state balance --node.store ~/.celestia-light
```

## 6. Upgrade

```bash
sudo systemctl stop celestia-light

cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node

NODE_VERSION="v0.31.3"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key

celestia light config-update
sudo systemctl restart celestia-light
```

## 7. Remove

```bash
sudo systemctl stop celestia-light
sudo systemctl disable celestia-light
sudo rm -f /etc/systemd/system/celestia-light.service
sudo systemctl daemon-reload
rm -rf "$HOME/celestia-node" "$HOME/.celestia-light"
```
