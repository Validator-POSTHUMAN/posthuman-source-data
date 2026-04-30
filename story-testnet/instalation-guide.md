
# Story Node Installation Guide

## Recommended Hardware:
- **CPU:** 4 Cores
- **Memory:** 8GB RAM
- **Storage:** 200GB NVME

---

## Install Dependencies
Ensure your system is up to date and has all the necessary tools for the installation:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl tar wget clang pkg-config libssl-dev jq build-essential bsdmainutils git make ncdu gcc git jq chrony liblz4-tool -y
```

---

## Install Go 
Replace `VERSION` with the desired Go version
```bash
VERSION="1.22.3"
cd $HOME
wget "https://golang.org/dl/go$VERSION.linux-amd64.tar.gz"
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf "go$VERSION.linux-amd64.tar.gz"
rm "go$VERSION.linux-amd64.tar.gz"

# Set Go environment variables
echo "export PATH=\$PATH:/usr/local/go/bin:\$HOME/go/bin" >> ~/.bash_profile
source ~/.bash_profile
```

---

## Set Environment Variables
Set up your node by exporting environment variables. This helps customize the node’s behavior:
```bash
echo "export MONIKER="test"" >> ~/.bash_profile
echo "export STORY_CHAIN_ID="iliad-0"" >> ~/.bash_profile
echo "export STORY_PORT="26"" >> ~/.bash_profile
source ~/.bash_profile
```

---

## Download Binaries
Get the required Story binaries:
```bash
cd $HOME
wget -O geth https://github.com/piplabs/story-geth/releases/download/v0.11.0/geth-linux-amd64
chmod +x $HOME/geth
mv $HOME/geth ~/go/bin/
mkdir -p $HOME/.story/story
mkdir -p $HOME/.story/geth
```

---

## Install Story
Clone the Story repository and build the client:
```bash
cd $HOME
rm -rf story
git clone https://github.com/piplabs/story
cd story
git checkout v0.13.0
go build -o story ./client 
mv $HOME/story/story $HOME/go/bin/
```

---

## Initialize Story App
Initialize the Story node with your custom moniker and network settings:
```bash
story init --moniker test --network odyssey
```

---

## Set Seeds and Peers
Set the seeds and peers for your node:
```bash
SEEDS="434af9dae402ab9f1c8a8fc15eae2d68b5be3387@story-testnet-seed.itrocket.net:29656,b7e9b91c9e8c7e66e46dd15720cbe4f74f005592@galactica.seed-t.stavr.tech:35106,ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@testnet-seeds.polkachu.com:29256"
PEERS="c2a6cc9b3fa468624b2683b54790eb339db45cbf@story-testnet-peer.itrocket.net:26656,a1847e8325772ada9e2ad3a41e81ca022af4f1ef@65.21.136.219:41656,36f30f03a013f33fcdcd1962cb28b86478d3b549@149.50.118.20:26156,92782932b46812fb9772ccd7a1fedad924938246@65.108.226.200:26656,1c63647905963a0c95d904cd92ed7626bf1b8183@198.178.224.104:60730,4240c286741a402f9bd3dede9144c41de6c1079a@142.132.209.236:29256,f13f0bf2b5aea85ca15677879e7f65ee02886111@49.12.122.53:27656,e8d2732e64d3dcedb3960cbed9aeb325e6ffec51@37.60.234.34:656,cae3aa25f8eceedb3ba1cc87e016cc1975d28354@37.60.252.105:656,a4f0d9f44b56dcc8f98a714e8efcd87ac71c6652@65.109.26.242:25556,ef2f9d930fa65c0e3f184e2899ac7a9053fd1e69@49.13.4.170:26656,ee1aee60f82ea8d4a9c5b27e768584d8800971e6@2.56.246.4:26656,57fd6538790be2ecad5f488eb10089f670ecb41c@188.68.38.127:26656,6fbcfda71b3afadbce92198e2fa286eda0058881@177.54.159.225:26656,65066f1c877b1b5f9858740e91bb70e067609886@94.72.99.85:656,d7bd9c076ed06cc6ddaf40cf29ed9cbd7696d50c@194.163.148.243:26656,234680bca36bf35c62318a2b2945f9122d624625@37.60.234.20:656,dbf30e16653d477358b244521d9f5cb25387461c@149.50.118.61:26156,41ade4c9cb31ebad3f65d58ea862bdc119b87287@62.169.16.182:26656"
sed -i -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*seeds *=.*/seeds = "$SEEDS"/}" -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = "$PEERS"/}" $HOME/.story/story/config/config.toml
```

---

## Download Genesis and Addrbook
Download the required genesis and address book files:
```bash
wget -O $HOME/.story/story/config/genesis.json https://snapshots.story.posthuman.digital/genesis.json
wget -O $HOME/.story/story/config/addrbook.json https://snapshots.story.posthuman.digital/addrbook.json
```

---

## Customize Ports
Set custom ports in your configuration files:
```bash
sed -i.bak -e "s%:1317%:${STORY_PORT}317%g; s%:8551%:${STORY_PORT}551%g" $HOME/.story/story/config/story.toml
sed -i.bak -e "s%:26658%:${STORY_PORT}658%g; s%:26657%:${STORY_PORT}657%g; s%:26656%:${STORY_PORT}656%g; s%^external_address = ""%external_address = "$(wget -qO- eth0.me):${STORY_PORT}656"%;" $HOME/.story/story/config/config.toml
```

---

## Enable Prometheus and Disable Indexing
Enable Prometheus for monitoring and disable indexing:
```bash
sed -i -e "s/prometheus = false/prometheus = true/" $HOME/.story/story/config/config.toml
sed -i -e "s/^indexer *=.*/indexer = "null"/" $HOME/.story/story/config/config.toml
```

---

## Create Geth Service File
Create a systemd service file for the Geth daemon:
```bash
sudo tee /etc/systemd/system/story-geth.service > /dev/null <<EOF
[Unit]
Description=Story Geth daemon
After=network-online.target

[Service]
User=$USER
ExecStart=$HOME/go/bin/geth --odyssey --syncmode full --http --http.api eth,net,web3,engine --http.vhosts '*' --http.addr 0.0.0.0 --http.port ${STORY_PORT}545 --authrpc.port ${STORY_PORT}551 --ws --ws.api eth,web3,net,txpool --ws.addr 0.0.0.0 --ws.port ${STORY_PORT}546
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

---

## Create Story Service File
Create a systemd service file for the Story application:
```bash
sudo tee /etc/systemd/system/story.service > /dev/null <<EOF
[Unit]
Description=Story Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$HOME/.story/story
ExecStart=$(which story) run

Restart=on-failure
RestartSec=5
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF
```

---

# Story Node Snapshot Installation Guide

## Pruned Snapshot Installation
Updated every 24 hours

### Pruned Snapshot 

```bash
# Install dependencies, if needed
sudo apt install curl jq lz4  -y

# Stop node
sudo systemctl stop story story-geth

# Backup priv_validator_state.json
cp $HOME/.story/story/data/priv_validator_state.json $HOME/.story/story/priv_validator_state.json.backup

# Remove old data and unpack Story snapshot
rm -rf $HOME/.story/story/data
curl https://snapshots-pruned.story.posthuman.digital/story_pruned.tar.lz4 | lz4 -dc - | tar -xf - -C $HOME/.story/story

# Restore priv_validator_state.json
mv $HOME/.story/story/priv_validator_state.json.backup $HOME/.story/story/data/priv_validator_state.json

# Delete Geth data and unpack Geth snapshot
rm -rf $HOME/.story/geth/iliad/geth/chaindata
curl https://snapshots-pruned.story.posthuman.digital/geth_story_pruned.tar.lz4 | lz4 -dc - | tar -xf - -C $HOME/.story/geth/iliad/geth

# Restart node and check logs
sudo systemctl restart story story-geth
sudo journalctl -u story-geth -u story -f
```

---

## Enable and Start Services
Reload systemd, enable and start the services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable story story-geth
sudo systemctl start story story-geth
```

---

## Check Logs
Monitor the logs for both the Story and Geth services:
```bash
journalctl -u story -u story-geth -f
```

---

## Firewall Configuration
Configure firewall rules to allow network traffic:
```bash
sudo ufw allow 30303/tcp comment geth_p2p_port
sudo ufw allow 26656/tcp comment story_p2p_port
```

---

## Deleting the Node
To completely remove the node and services, run the following commands:
```bash
sudo systemctl stop story story-geth
sudo systemctl disable story story-geth
rm -rf $HOME/.story
sudo rm /etc/systemd/system/story.service /etc/systemd/system/story-geth.service
sudo systemctl daemon-reload
```

---
