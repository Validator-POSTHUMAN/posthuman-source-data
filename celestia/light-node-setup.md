# Celestia Light Node (Mainnet) — POSTHUMAN

Deploy a production-ready Celestia light node that connects to POSTHUMAN consensus endpoints and publishes metrics for monitoring.

## Hardware Requirements
- 4 CPU cores  
- 4 GB RAM  
- 120 GB SSD  
- 100 Mbps symmetric bandwidth

## 1. Update packages and install dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make gcc tar clang pkg-config libssl-dev ncdu -y
```

## 2. Install Go (if needed)
```bash
cd ~
if ! command -v go >/dev/null 2>&1; then
  VER="1.24.1"
  wget "https://golang.org/dl/go${VER}.linux-amd64.tar.gz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "go${VER}.linux-amd64.tar.gz"
  rm "go${VER}.linux-amd64.tar.gz"
fi

[ -d "$HOME/go/bin" ] || mkdir -p "$HOME/go/bin"
if ! grep -q "/usr/local/go/bin" "$HOME/.bash_profile" 2>/dev/null; then
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> "$HOME/.bash_profile"
fi
source "$HOME/.bash_profile" 2>/dev/null || true
go version
```

## 3. Download and build celestia-node
```bash
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.26.4"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
```

## 4. Initialize the light node
```bash
celestia light init \
  --core.ip https://rpc.celestia-mainnet.posthuman.digital \
  --p2p.network celestia
```

## 5. Create or restore a wallet
```bash
KEY_NAME="my_celes_key"
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type light
```

Restore an existing key:
```bash
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type light --recover
```

Display the wallet address:
```bash
cd "$HOME/celestia-node"
./cel-key list --node.type light --keyring-backend test
```

> Replace `my_celes_key` with the key name you actually use; reuse the same value in the systemd unit below.

## 6. Create a systemd service
```bash
sudo tee /etc/systemd/system/celestia-light.service > /dev/null <<EOF
[Unit]
Description=Celestia light node (POSTHUMAN)
After=network-online.target

[Service]
User=$USER
ExecStart=$(which celestia) light start \
  --core.ip https://rpc.celestia-mainnet.posthuman.digital \
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
```

Reload and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celestia-light
sudo systemctl restart celestia-light && sudo journalctl -u celestia-light -fo cat
```

> POSTHUMAN RPC/gRPC endpoints are served over HTTPS behind Cloudflare. If you connect to a raw Tendermint endpoint, replace the host and set the ports back to `26657` / `9090`.

## 7. Inspect node information
```bash
NODE_TYPE=light
AUTH_TOKEN=$(celestia "$NODE_TYPE" auth admin --p2p.network celestia)

curl -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
  http://localhost:26658
```

## 8. Useful commands

```bash
# Balance
celestia state balance --node.store ~/.celestia-light/

# Wallet address
cd "$HOME/celestia-node"
./cel-key list --node.type light --keyring-backend test

# Restore key
cd "$HOME/celestia-node"
./cel-key add my_celes_key --keyring-backend test --node.type light --recover

# Sync status
celestia header sync-state --node.store ~/.celestia-light/

# Peer information
celestia p2p info --node.store ~/.celestia-light/

# Harden permissions
chmod -R 700 ~/.celestia-light

# Reset
celestia light unsafe-reset-store --p2p.network celestia
```

## 9. Upgrading
```bash
sudo systemctl stop celestia-light
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.26.4"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
celestia light config-update
sudo systemctl restart celestia-light && sudo journalctl -u celestia-light -fo cat
```

## 10. Removal
```bash
sudo systemctl stop celestia-light
sudo systemctl disable celestia-light
sudo rm /etc/systemd/system/celestia-light.service
rm -rf "$HOME/celestia-node" "$HOME/.celestia-light"
```
