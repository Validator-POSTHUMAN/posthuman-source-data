### Update system and install build tools

```
sudo apt update
sudo apt-get install git curl build-essential make jq gcc snapd chrony lz4 tmux unzip bc -y
```

### Install Go

```
rm -rf $HOME/go
sudo rm -rf /usr/local/go
cd $HOME
curl https://go.dev/dl/go1.25.7.linux-amd64.tar.gz | sudo tar -C/usr/local -zxvf -
cat <<'EOF' >>$HOME/.profile
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export GO111MODULE=on
export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin
EOF
source $HOME/.profile
go version
```

### Install Node

```
cd $HOME
rm -rf gaia
git clone https://github.com/cosmos/gaia.git
cd gaia
git checkout v27.6.0
make install
gaiad version
```

### Initialize Node
Replace NodeName with your own moniker.
```
gaiad init NodeName --chain-id=cosmoshub-4
```

### Download Genesis
```
curl -fsSLo $HOME/.gaia/config/genesis.json \
  https://rpc.cosmos.posthuman.digital/files/cosmoshub/genesis.json
```

### Download addrbook

```
curl -fsSLo $HOME/.gaia/config/addrbook.json \
  https://rpc.cosmos.posthuman.digital/files/cosmoshub/addrbook.json
```

### Create Service

```
sudo tee /etc/systemd/system/gaiad.service > /dev/null <<EOF
[Unit]
Description=gaiad Daemon
After=network-online.target
[Service]
User=$USER
ExecStart=$(which gaiad) start
Restart=always
RestartSec=3
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable gaiad
```

### Bootstrap artifact metadata

Check the POSTHUMAN manifest for file hashes, generation time, and source
provenance before replacing configuration files:

```
curl -fsSL https://rpc.cosmos.posthuman.digital/files/cosmoshub/manifest.json | jq
```

Use a verified snapshot or state-sync source separately; no POSTHUMAN Cosmos
Hub snapshot is advertised by this guide.

### Launch Node

```
sudo systemctl restart gaiad
journalctl -u gaiad -f
```
