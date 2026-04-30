#  Babylon Validator Setup Guide

## Recommended Hardware
- **CPU:** 4 Cores
- **RAM:** 32GB
- **Storage:** 2TB NVMe SSD

## Step 1: Install Required Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make lz4 gcc unzip -y
```

## Step 2: Install Go (if not already installed)
```bash
cd $HOME
VER="1.23.1"
wget "https://golang.org/dl/go$VER.linux-amd64.tar.gz"
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf "go$VER.linux-amd64.tar.gz"
rm "go$VER.linux-amd64.tar.gz"
echo "export PATH=$PATH:/usr/local/go/bin:~/go/bin" >> ~/.bash_profile
source $HOME/.bash_profile
mkdir -p ~/go/bin
```

## Step 3: Set Environment Variables
```bash
echo "export WALLET="wallet"" >> $HOME/.bash_profile
echo "export MONIKER="YOUR_MONIKER_HERE"" >> $HOME/.bash_profile
echo "export POSTHUMAN_CHAIN_ID="bbn-test-5"" >> $HOME/.bash_profile
echo "export POSTHUMAN_PORT="60"" >> $HOME/.bash_profile
source $HOME/.bash_profile
```

## Step 4: Download and Build the Binary
```bash
cd $HOME
rm -rf posthuman
git clone https://github.com/posthuman-labs/posthuman.git
cd posthuman
git checkout v1.0.0-rc.3
make install
```

## Step 5: Configure and Initialize the Node
```bash
babylond init $MONIKER --chain-id $POSTHUMAN_CHAIN_ID
sed -i \
-e "s/chain-id = .*/chain-id = \"$POSTHUMAN_CHAIN_ID\"/" \
-e "s/keyring-backend = .*/keyring-backend = \"os\"/" \
-e "s/node = .*/node = \"tcp:\/\/localhost:${POSTHUMAN_PORT}657\"/" $HOME/.babylond/config/client.toml
```

## Step 6: Download Genesis and Addrbook
```bash
wget -O $HOME/.babylond/config/genesis.json http://snapshots.babylon.posthuman.digital/genesis.json
wget -O $HOME/.babylond/config/addrbook.json http://snapshots.babylon.posthuman.digital/addrbook.json
```

## Step 7: Configure Peers and Seeds
```bash
SEEDS="ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@testnet-seeds.polkachu.com:20656,0c949c3bcd83b81c794af8c3ae026a97d9c4564e@posthuman-testnet-seed.itrocket.net:60656"
PEERS="70d302558183535e220a725d463597ade72e130d@95.217.229.104:60656,4fd0303f110abe7567f318be659ce3b99436e895@65.108.198.118:20656"
sed -i -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*seeds *=.*/seeds = \"$SEEDS\"/}" \
       -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = \"$PEERS\"/}" $HOME/.babylond/config/config.toml
```

## Step 8: Set Custom Ports
```bash
sed -i.bak -e "s%:1317%:${POSTHUMAN_PORT}317%g;
s%:8080%:${POSTHUMAN_PORT}080%g;
s%:9090%:${POSTHUMAN_PORT}090%g;
s%:9091%:${POSTHUMAN_PORT}091%g;
s%:8545%:${POSTHUMAN_PORT}545%g;
s%:8546%:${POSTHUMAN_PORT}546%g;
s%:6065%:${POSTHUMAN_PORT}065%g" $HOME/.babylond/config/app.toml
```

## Step 9: Configure Pruning and Indexing
```bash
sed -i -e "s/^pruning *=.*/pruning = \"custom\"/" $HOME/.babylond/config/app.toml 
sed -i -e "s/^pruning-keep-recent *=.*/pruning-keep-recent = \"100\"/" $HOME/.babylond/config/app.toml
sed -i -e "s/^pruning-interval *=.*/pruning-interval = \"19\"/" $HOME/.babylond/config/app.toml
sed -i -e "s/^indexer *=.*/indexer = \"null\"/" $HOME/.babylond/config/config.toml
```

## Step 9.1: Configure Bitcoin Network for Checkpointing

### Valid values: [mainnet, testnet, simnet, signet, regtest]

```bash
sudo nano $HOME/.babylond/config/app.toml
```

Modify the following line:

```toml
network = "signet" # The Babylon testnet connects to the signet Bitcoin network
```


## Step 10: Create and Start the Service
```bash
sudo tee /etc/systemd/system/babylon.service > /dev/null <<EOF
[Unit]
Description=Babylon Node
After=network-online.target
[Service]
User=$USER
WorkingDirectory=$HOME/.babylond
ExecStart=$(which babylond) start --home $HOME/.babylond --chain-id bbn-test-5 --x-crisis-skip-assert-invariants
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable babylon
sudo systemctl restart babylon && sudo journalctl -u babylon -f -o cat
```

## Step 11: Create a Wallet
```bash
babylond keys add $WALLET
```
*Save the mnemonic securely.*

To restore an existing wallet:
```bash
babylond keys add $WALLET --recover
```

## Step 12: Save Wallet and Validator Address
```bash
WALLET_ADDRESS=$(babylond keys show $WALLET -a)
VALOPER_ADDRESS=$(babylond keys show $WALLET --bech val -a)
echo "export WALLET_ADDRESS="$WALLET_ADDRESS"" >> $HOME/.bash_profile
echo "export VALOPER_ADDRESS="$VALOPER_ADDRESS"" >> $HOME/.bash_profile
source $HOME/.bash_profile
```

## Step 13: Check Synchronization Status
```bash
babylond status 2>&1 | jq
```

## Step 14: Create a Validator
```bash
cd $HOME
echo "{\"pubkey\":{\"@type\":\"/cosmos.crypto.ed25519.PubKey\",\"key\":\"$(babylond comet show-validator | grep -Po '\"key\":\\s*\\"\K[^\\"]*')\"},
    \"amount\": \"1000000uphm\",
    \"moniker\": \"test\",
    \"identity\": \"\",
    \"website\": \"\",
    \"security\": \"\",
    \"details\": \"I love blockchain ❤️\",
    \"commission-rate\": \"0.1\",
    \"commission-max-rate\": \"0.2\",
    \"commission-max-change-rate\": \"0.01\",
    \"min-self-delegation\": \"1\"}" > validator.json
```
Create a pair of BLS keys that are used to
send BLS signatures for checkpointing.
BLS keys are stored along with other validator keys in priv_validator_key.json,:

```
babylond create-bls-key $WALLET_ADDRESS
```
```
babylond tx checkpointing create-validator validator.json --from $WALLET --chain-id bbn-test-5 --gas auto --gas-adjustment 1.5
```

## Step 15: Security Recommendations
- **Never share your private key or mnemonic.**
- **Use SSH keys for authentication.**
- **Set up a firewall for security:**
```bash
sudo ufw default allow outgoing
sudo ufw default deny incoming
sudo ufw allow ssh/tcp
sudo ufw allow ${POSTHUMAN_PORT}656/tcp
sudo ufw enable
