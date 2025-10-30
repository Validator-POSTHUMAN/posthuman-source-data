# Celestia Light Node (Mocha-4 Testnet) — POSTHUMAN

Run a Celestia mocha-4 light node backed by POSTHUMAN RPC/gRPC endpoints. The instructions mirror Celestia’s quick-start flow while exposing POSTHUMAN public services ready for production use.

## Hardware Requirements (non-archival)
| Resource  | Requirement |
|-----------|-------------|
| CPU       | 1 core |
| Memory    | 500 MB |
| Disk      | 20 GB SSD |
| Bandwidth | 56 Kbps |

> Archival (unpruned header) light nodes on mocha-4 follow the same CPU/RAM/bandwidth profile but require ~111 KB of disk per block.
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
  --core.ip https://rpc.celestia-testnet.posthuman.digital \
  --p2p.network mocha
```

## 5. Create or restore a wallet
```bash
KEY_NAME="my_celes_key"
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type light --p2p.network mocha
```

Restore an existing key:
```bash
cd "$HOME/celestia-node"
./cel-key add "$KEY_NAME" --keyring-backend test --node.type light --p2p.network mocha --recover
```

Display the wallet address:
```bash
cd "$HOME/celestia-node"
./cel-key list --node.type light --keyring-backend test --p2p.network mocha
```

> Replace `my_celes_key` with your chosen key name; use the same identifier in the systemd unit below.

## 6. Create a systemd service
```bash
sudo tee /etc/systemd/system/celestia-light.service > /dev/null <<EOF
[Unit]
Description=Celestia mocha-4 light node (POSTHUMAN)
After=network-online.target

[Service]
User=$USER
ExecStart=$(which celestia) light start \
  --core.ip https://rpc.celestia-testnet.posthuman.digital \
  --core.rpc.port 443 \
  --core.grpc.port 443 \
  --keyring.accname my_celes_key \
  --p2p.network mocha \
  --metrics \
  --metrics.tls=true \
  --metrics.endpoint otel.mocha.celestia.observer
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

> POSTHUMAN mocha endpoints are exposed over HTTPS via Cloudflare. When pointing to a raw consensus node, switch the host and restore the default `26657` / `9090` ports.

## 7. Inspect node information
```bash
NODE_TYPE=light
AUTH_TOKEN=$(celestia "$NODE_TYPE" auth admin --p2p.network mocha)

curl -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
  http://localhost:26658
```

## 8. Useful commands

```bash
# Balance
celestia state balance --node.store ~/.celestia-light-mocha/

# Wallet address
cd "$HOME/celestia-node"
./cel-key list --node.type light --keyring-backend test --p2p.network mocha

# Restore key
cd "$HOME/celestia-node"
./cel-key add my_celes_key --keyring-backend test --node.type light --p2p.network mocha --recover

# Sync status
celestia header sync-state --node.store ~/.celestia-light-mocha/

# Peer information
celestia p2p info --node.store ~/.celestia-light-mocha/

# Harden permissions
chmod -R 700 ~/.celestia-light-mocha

# Reset
celestia light unsafe-reset-store --p2p.network mocha
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
celestia light config-update --p2p.network mocha
sudo systemctl restart celestia-light && sudo journalctl -u celestia-light -fo cat
```

## 10. Removal
```bash
sudo systemctl stop celestia-light
sudo systemctl disable celestia-light
sudo rm /etc/systemd/system/celestia-light.service
rm -rf "$HOME/celestia-node" "$HOME/.celestia-light-mocha"
```
