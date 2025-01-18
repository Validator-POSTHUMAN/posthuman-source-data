
# Agoric Node Setup Guide with Posthuman State-Sync

This guide outlines how to set up an Agoric node on the `agoric-3` chain using `agoric-upgrade-18`. It incorporates the use of the Posthuman state-sync server for efficient setup.

---

## 1. Set Validator Name
Replace `YOUR_MONIKER_GOES_HERE` with your validator name:
```bash
MONIKER="YOUR_MONIKER_GOES_HERE"
```

---

## 2. Install Dependencies

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

### Clone Project Repository
```bash
cd $HOME
rm -rf agoric-upgrade-18
git clone https://github.com/Agoric/agoric-sdk.git agoric-upgrade-18
cd agoric-upgrade-18
git checkout agoric-upgrade-18
```

### Build JavaScript Packages
```bash
yarn install && yarn build
```

### Build Cosmos SDK Support
```bash
(cd packages/cosmic-swingset && make)
```

---

## 5. Prepare Binaries for Cosmovisor

### Setup Genesis and Upgrade Binaries
```bash
mkdir -p $HOME/.agoric/cosmovisor/genesis/bin
mkdir -p $HOME/.agoric/cosmovisor/upgrades/agoric-upgrade-18-mainnet/bin

ln -sf $HOME/agoric-upgrade-18/bin/agd $HOME/.agoric/cosmovisor/genesis/bin/agd
ln -sf $HOME/agoric-upgrade-18/bin/agd $HOME/.agoric/cosmovisor/upgrades/agoric-upgrade-18-mainnet/bin/agd

ln -sf $HOME/.agoric/cosmovisor/genesis $HOME/.agoric/cosmovisor/current
```

### Create Global Symlink
```bash
sudo rm -f /usr/local/bin/agd
sudo tee /usr/local/bin/agd > /dev/null << EOF
#!/bin/bash
exec $HOME/.agoric/cosmovisor/current/bin/agd "\$@"
EOF
sudo chmod 777 /usr/local/bin/agd
```

---

## 6. Install and Configure Cosmovisor

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

## 7. Initialize the Node

### Configure Node
```bash
agd config chain-id agoric-3
agd config keyring-backend file
agd config node tcp://localhost:12757
```

### Initialize Node
```bash
agd init $MONIKER --chain-id agoric-3
```

---

## 8. Enable State-Sync Using Posthuman

### Configure State-Sync
Create a script called `state_sync.sh`:
```bash
#!/bin/bash

SNAP_RPC="https://rpc.agoric.posthuman.digital"

LATEST_HEIGHT=$(curl -s $SNAP_RPC/block | jq -r .result.block.header.height); BLOCK_HEIGHT=$((LATEST_HEIGHT - 2000)); TRUST_HASH=$(curl -s "$SNAP_RPC/block?height=$BLOCK_HEIGHT" | jq -r .result.block_id.hash)

sed -i.bak -E "s|^(enable[[:space:]]+=[[:space:]]+).*$|\1true| ; s|^(rpc_servers[[:space:]]+=[[:space:]]+).*$|\1\"$SNAP_RPC,$SNAP_RPC\"| ; s|^(trust_height[[:space:]]+=[[:space:]]+).*$|\1$BLOCK_HEIGHT| ; s|^(trust_hash[[:space:]]+=[[:space:]]+).*$|\1\"$TRUST_HASH\"|" $HOME/.agoric/config/config.toml
```

Grant execute permissions and run:
```bash
chmod 700 state_sync.sh
./state_sync.sh
```

---

## 9. Reset and Restart the Node

### Stop the Node
```bash
sudo systemctl stop agd.service
```

### Reset the Node
```bash
agd tendermint unsafe-reset-all --home $HOME/.agoric --keep-addr-book
```

### Restart the Node
```bash
sudo systemctl start agd.service
```

---

## 10. Verify Syncing
If configured correctly, your node should start syncing within 10 minutes. Use the following command to monitor logs:
```bash
sudo journalctl -u agd.service -f --no-hostname -o cat
```
