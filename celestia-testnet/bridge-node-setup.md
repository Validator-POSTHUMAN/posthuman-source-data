# Posthuman Service Bridge Node Setup for Mocha Testnet (mocha-4)

## Hardware Requirements (mocha data availability)

### Non-archival
## Setting Up a Posthuman Service Node

### Update Packages and Install Dependencies
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make gcc tar clang pkg-config libssl-dev ncdu -y
```

### Install Go
```sh
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

### Install Celestia-Node
```sh
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.28.2-mocha"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
```

### Configure and Initialize the Application
```sh
celestia bridge init --core.ip https://rpc-celestia-testnet.posthuman.digital --p2p.network mocha
```
Once started, a wallet key is generated. You need to fund this address with testnet tokens.
Find your wallet address:
```sh
cd $HOME/celestia-node
./cel-key list --node.type bridge --keyring-backend test --p2p.network mocha
```

### Create a Systemd Service File
```sh
sudo tee /etc/systemd/system/celestia-bridge.service > /dev/null <<EOF
[Unit]
Description=Celestia Bridge
After=network-online.target

[Service]
User=$USER
ExecStart=$(which celestia) bridge start \
--p2p.network mocha --archival \
--metrics.tls=true --metrics --metrics.endpoint otel.mocha.celestia.observer
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start the Service
```sh
sudo systemctl daemon-reload
sudo systemctl enable celestia-bridge
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
```

### Get Node Peer ID Information
❗ You can only generate an auth token after initializing and starting your Celestia node.
```sh
NODE_TYPE=bridge
AUTH_TOKEN=$(celestia $NODE_TYPE auth admin --p2p.network mocha)
curl -X POST \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
     http://localhost:26658
```

### Download and Restore Snapshot
```sh
sudo apt install aria2 jq lz4 unzip -y
cd $HOME
aria2c -x 16 -s 16 -o celestia-bridge-snap.tar.lz4 https://server-8.itrocket.net/testnet/celestia/bridge/celestia_2025-03-03_4981368_snap.tar.lz4
sudo systemctl stop celestia-bridge
rm -rf ~/.celestia-bridge-mocha-4/{blocks,data,index,inverted_index,transients,.lock}
tar -I lz4 -xvf ~/celestia-bridge-snap.tar.lz4 -C ~/.celestia-bridge-mocha-4/
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
rm ~/celestia-bridge-snap.tar.lz4
```

## Cheat Sheet

### Check Wallet Balance
```sh
celestia state balance --node.store ~/.celestia-bridge-mocha-4/
```

### Get Wallet Address
```sh
cd $HOME/celestia-node
./cel-key list --node.type bridge --keyring-backend test --p2p.network mocha
```

### Restore an Existing cel_key
```sh
KEY_NAME="my_celes_key"
cd ~/celestia-node
./cel-key add $KEY_NAME --keyring-backend test --node.type bridge --recover --p2p.network mocha
```

### Check Bridge Node Status
```sh
celestia header sync-state --node.store ~/.celestia-bridge-mocha-4/
```

### Get Node ID
```sh
celestia p2p info --node.store ~/.celestia-bridge-mocha-4/
```

### Set Permissions for Transferring Keys
```sh
chmod -R 700 ~/.celestia-bridge-mocha-4
```

### Reset Node
```sh
celestia bridge unsafe-reset-store --p2p.network mocha
```

## Upgrade

### Stop Bridge Node
```sh
sudo systemctl stop celestia-bridge
```

### Download and Install Latest Version
```sh
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.28.2-mocha"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
```

### Update Configuration
```sh
celestia bridge config-update --p2p.network mocha
```

### Restart Bridge Node
```sh
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
```

## Delete Bridge Node
```sh
sudo systemctl stop celestia-bridge
sudo systemctl disable celestia-bridge
sudo rm /etc/systemd/system/celestia-bridge*
rm -rf $HOME/celestia-node $HOME/.celestia-bridge-mocha-4
