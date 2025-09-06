
# Agoric Node Setup Guide

This guide outlines how to set up an Agoric node on the `agoric-3` chain using `agoric-upgrade-18`. It incorporates the use of the Posthuman state-sync server or snapshot service for efficient setup.

---

## Install Dependencies

### Add Node.js Repository
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
```

### Add Yarn Repository
```bash
curl -Ls https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | sudo tee /usr/share/keyrings/yarnkey.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/yarnkey.gpg] https://dl.yarnpkg.com/debian stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
```

### Update System and Install Build Tools
```bash
sudo apt -q update
sudo apt -qy install curl git jq lz4 build-essential nodejs=18.* yarn
sudo apt -qy upgrade
```

---

## 3. Install Go
```bash
sudo rm -rf /usr/local/go
curl -Ls https://go.dev/dl/go1.20.14.linux-amd64.tar.gz | sudo tar -xzf - -C /usr/local
echo 'export PATH=$PATH:/usr/local/go/bin' | sudo tee /etc/profile.d/golang.sh
echo 'export PATH=$PATH:$HOME/go/bin' >> $HOME/.profile
source $HOME/.profile
```

---

## 4. Download and Build Binaries

### Clone Project Repository but check new [version](https://github.com/Agoric/agoric-sdk/releases) 
```bash
export version=agoric-upgrade-21
cd $HOME
git clone https://github.com/Agoric/agoric-sdk.git $version
git checkout $version
cd $version
```

### Build JavaScript Packages
```bash
yarn install && yarn build
```
make sure you have:
✅ Node.js → 20.19.5
✅ Yarn → 4.9.1 with Corepack
✅ Go → 1.23.3

### Build Cosmos SDK Support
```bash
(cd packages/cosmic-swingset && make)
```

---

## Prepare Binaries for Cosmovisor

### Setup Genesis and Upgrade Binaries
```bash
mkdir -p $HOME/.agoric/cosmovisor/genesis/bin
ln -sf $HOME/agoric/bin/agd $HOME/.agoric/cosmovisor/genesis/bin/agd
ln -sf $HOME/.agoric/cosmovisor/genesis $HOME/.agoric/cosmovisor/current
```

### Create Global Symlink
```bash
sudo tee /usr/local/bin/agd > /dev/null << EOF
#!/bin/bash
exec $HOME/.agoric/cosmovisor/current/bin/agd "\$@"
EOF
sudo chmod 777 /usr/local/bin/agd
```
```bash
ln -sfn ~/.agoric/cosmovisor/upgrades/agoric-upgrade-21 ~/.agoric/cosmovisor/current
```
---

## Install and Configure Cosmovisor

### Install Cosmovisor
```bash
go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@v1.6.0
```

### Create Systemd Service
```bash
sudo tee /etc/systemd/system/agoric.service > /dev/null << EOF
[Unit]
Description=Agoric Node Service
After=network-online.target

[Service]
User=$USER
ExecStart=$(which cosmovisor) run start
Restart=on-failure
RestartSec=10
LimitNOFILE=65535
Environment="DAEMON_HOME=$HOME/.agoric"
Environment="DAEMON_NAME=agd"
Environment="UNSAFE_SKIP_BACKUP=true"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:$HOME/.agoric/cosmovisor/current/bin"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable agoric.service
```

---

### Configure Node
```bash
agd config chain-id agoric-3
agd config keyring-backend file
```


### Initialize Node
```bash
agd init $MONIKER --chain-id agoric-3
```

---
## For Agoric nodes, make sure you set in app.toml.
```bash
iavl-disable-fastnode = true 
```

## Use State-Sync or snapshot service
 - [State Sync](https://nodes.posthuman.digital/chains/agoric?tab=state-sync)
 - [Snapshot Service](https://nodes.posthuman.digital/chains/agoric?tab=snapshot-service)


### Start the Node
```bash
sudo systemctl start agoric.service
```

---

## Verify Syncing
If configured correctly, your node should start syncing. Use the following command to monitor logs:
```bash
sudo journalctl -u agoric.service -f --no-hostname -o cat
```
