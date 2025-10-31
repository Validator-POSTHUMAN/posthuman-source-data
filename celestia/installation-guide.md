# Celestia Mainnet — Installation Guide

## 1. Update system and install build tools
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl tar wget clang pkg-config libssl-dev jq build-essential \
  bsdmainutils git make ncdu gcc chrony liblz4-tool
```

## 2. Install Go (if needed)
```bash
cd "$HOME"
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

## 3. Build and install `celestia-appd`
```bash
cd "$HOME"
rm -rf celestia-app
git clone https://github.com/celestiaorg/celestia-app.git
cd celestia-app
VERSION="v5.0.11"
git checkout "tags/$VERSION"
make build
make install
celestia-appd version
```

## 4. Initialize the node
Replace `<node_name>` with your moniker.
```bash
celestia-appd init <node_name> --chain-id celestia
```

## 5. Download network data
```bash
curl -Ls <genesis_url> -o "$HOME/.celestia-appd/config/genesis.json"
curl -Ls <addrbook_url> -o "$HOME/.celestia-appd/config/addrbook.json"
```

## 6. Create a systemd service
Replace `<your_user>` with the account running the node.
```bash
sudo tee /etc/systemd/system/celestia-appd.service > /dev/null <<'EOF'
[Unit]
Description=celestia-appd daemon (mainnet)
After=network-online.target

[Service]
User=<your_user>
ExecStart=$(which celestia-appd) start
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
