### Update system and install build tools
Ensure your system is up to date and has all the necessary tools for the installation:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl tar wget clang pkg-config libssl-dev jq build-essential \
  bsdmainutils git make ncdu gcc chrony liblz4-tool
```


## Install Go (if needed)
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


### Install node

```
cd "$HOME"
REPO_DIR=$(basename {{codebase.git_repo}} .git)
rm -rf "$REPO_DIR"
git clone {{codebase.git_repo}}
cd "$REPO_DIR"
VERSION="{{codebase.recommended_version}}"
git checkout "tags/$VERSION"
make build
make install
{{daemon_name}} version
```

### Initialize Node

Replace `<node_name>` with your moniker.

```
{{daemon_name}} init <node_name> --chain-id "{{chain_id}}"
```

### Download genesis.json

```
curl -Ls {{codebase.genesis.genesis_url}} > "$HOME/.{{chain_name}}/config/genesis.json"
```

### Download addrbook.json

```
curl -Ls {{addrbookUrl}} > "$HOME/.{{chain_name}}/config/addrbook.json"
```

### Create systemd service

```
NODE_USER=$(whoami)
sudo tee /etc/systemd/system/{{daemon_name}}.service > /dev/null <<EOF
[Unit]
Description={{daemon_name}} daemon
After=network-online.target

[Service]
User=${NODE_USER}
ExecStart=$(which {{daemon_name}}) start
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

```
sudo systemctl daemon-reload
sudo systemctl enable {{daemon_name}}.service
sudo systemctl start {{daemon_name}}.service
```

### Sync node:

After that you sould sync node. You have 2 ways. State-sync or download snapsot. See this guides in next tabs.

### Start service

```
sudo systemctl enable {{daemon_name}}.service && sudo systemctl start {{daemon_name}}.service && journalctl -u {{daemon_name}}.service -f
```
