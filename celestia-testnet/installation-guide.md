# Celestia Testnet (Mocha-5) — Installation Guide

Comprehensive guide for installing and running a Celestia node on the Mocha-5 testnet.

---

## Prerequisites

**For Validator/Consensus Node** (official requirements):
- **Hardware**: 16 cores, 32 GB RAM, 2 TiB NVMe SSD, 1 Gbps bandwidth
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **Network**: Stable internet connection

**Note**: These are official requirements for validators. For non-validator full nodes, lower specs may work but are not recommended for production.

---

## 1. Update System and Install Build Tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl tar wget clang pkg-config libssl-dev jq build-essential bsdmainutils git make ncdu gcc chrony liblz4-tool
```

---

## 2. Install Go

Celestia app v9 requires Go 1.26.1+:

```bash
cd "$HOME"
if ! command -v go >/dev/null 2>&1; then
  VER="1.26.1"
  wget "https://golang.org/dl/go${VER}.linux-amd64.tar.gz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "go${VER}.linux-amd64.tar.gz"
  rm "go${VER}.linux-amd64.tar.gz"
fi

# Setup Go environment
[ -d "$HOME/go/bin" ] || mkdir -p "$HOME/go/bin"
if ! grep -q "/usr/local/go/bin" "$HOME/.bash_profile" 2>/dev/null; then
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> "$HOME/.bash_profile"
fi
source "$HOME/.bash_profile" 2>/dev/null || true

# Verify
go version
```

---

## 3. Build and Install `celestia-appd`

Clone and build the testnet version:

```bash
cd "$HOME"
rm -rf celestia-app
git clone https://github.com/celestiaorg/celestia-app.git
cd celestia-app

# Checkout current Mocha testnet version
VERSION="v9.0.6-mocha"
git checkout "tags/$VERSION"

# Build and install
make build
make install

# Verify
celestia-appd version
```

Expected output: `9.0.6-mocha`

---

## 4. Initialize the Node

Initialize with your node name and testnet chain ID:

```bash
# Set variables
MONIKER="<YOUR_NODE_NAME>"
CHAIN_ID="mocha-5"

# Initialize
celestia-appd init "$MONIKER" --chain-id "$CHAIN_ID"
```

This creates: `~/.celestia-app/`

---

## 5. Download Genesis and Address Book

**Important**: Download from Posthuman testnet infrastructure:

```bash

# Download genesis.json
curl -Ls https://raw.githubusercontent.com/celestiaorg/networks/main/mocha-5/genesis.json \
  -o "$HOME/.celestia-app/config/genesis.json"

# Download addrbook.json (peer list)
curl -Ls https://server-6.itrocket.net/testnet/celestia/addrbook.json \
  -o "$HOME/.celestia-app/config/addrbook.json"

# Verify downloads
ls -lh "$HOME/.celestia-app/config/genesis.json"
ls -lh "$HOME/.celestia-app/config/addrbook.json"
```

---

## 6. Configure Node Settings

### 6.1 Set Minimum Gas Price

```bash
sed -i 's|minimum-gas-prices =.*|minimum-gas-prices = "0.002utia"|g' \
  "$HOME/.celestia-app/config/app.toml"
```

### 6.2 Configure Pruning (Recommended for testnet)

```bash
sed -i -e 's|^pruning *=.*|pruning = "custom"|' "$HOME/.celestia-app/config/app.toml"
sed -i -e 's|^pruning-keep-recent *=.*|pruning-keep-recent = "100"|' "$HOME/.celestia-app/config/app.toml"
sed -i -e 's|^pruning-interval *=.*|pruning-interval = "19"|' "$HOME/.celestia-app/config/app.toml"
```

### 6.3 Disable Indexer (Saves disk space)

```bash
sed -i -e 's|^indexer *=.*|indexer = "null"|' "$HOME/.celestia-app/config/config.toml"
```

### 6.4 Enable Prometheus

```bash
sed -i -e 's|prometheus = false|prometheus = true|' "$HOME/.celestia-app/config/config.toml"
```

### 6.5 Add Peers

```bash
# Posthuman testnet peer
PEERS="1f01208683a8eb380adc1075a97508fb1d2bb888@135.181.232.241:28756"

# Update config (adjust as needed based on available peers)
sed -i -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = \"$PEERS\"/}" \
  "$HOME/.celestia-app/config/config.toml"
```

---

## 7. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-appd-testnet.service > /dev/null <<EOF
[Unit]
Description=Celestia Node (Mocha-5 Testnet)
After=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/.celestia-app
ExecStart=$(which celestia-appd) start --home $HOME/.celestia-app
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

**Note**: Service name is `celestia-appd-testnet` to distinguish from mainnet if running both.

---

## 8. Download and Apply Snapshot

POSTHUMAN does not currently publish a Mocha-5 snapshot. Use the verified
ITRocket feed at `https://server-6.itrocket.net/testnet/celestia/`. Check
`.current_state.json`, verify the live RPC identifies as `mocha-5`, download
the exact listed file before stopping the node, and validate the complete
archive with `lz4 -t`.

Before replacing validator data, preserve the local consensus key and newest
`priv_validator_state.json`. Never use signer state from a snapshot. Keep the
old data directory as rollback material until the restored node is synced and
verified.

## 9. Start the Node

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable celestia-appd-testnet

# Start service
sudo systemctl start celestia-appd-testnet

# View logs
sudo journalctl -u celestia-appd-testnet -f -o cat
```

---

## 10. Verify Node Status

### Check Sync Status

```bash
celestia-appd status 2>&1 | jq .SyncInfo
```

Look for `"catching_up": false` when fully synced.

### Check Block Height

```bash
celestia-appd status 2>&1 | jq .SyncInfo.latest_block_height
```

---

## 11. Create or Restore Wallet

### Create New Wallet

```bash
WALLET="wallet-testnet"
celestia-appd keys add "$WALLET"
```

**Save the mnemonic securely!**

### Restore Existing Wallet

```bash
WALLET="wallet-testnet"
celestia-appd keys add "$WALLET" --recover
```

### Save Wallet Address

```bash
WALLET_ADDRESS=$(celestia-appd keys show "$WALLET" -a)
echo "export WALLET_ADDRESS_TESTNET=$WALLET_ADDRESS" >> "$HOME/.bash_profile"
source "$HOME/.bash_profile"
echo "Testnet wallet: $WALLET_ADDRESS"
```

---

## 12. Get Testnet Tokens

Request testnet TIA from the faucet:

- **Celestia Discord**: https://discord.com/invite/celestiacommunity
  - Go to #mocha-faucet channel
  - Request tokens with your address

### Check Balance

```bash
celestia-appd query bank balances "$WALLET_ADDRESS"
```

---

## 13. Create Validator

After sync and funding:

```bash
celestia-appd tx staking create-validator \
  --amount=1000000utia \
  --pubkey=$(celestia-appd tendermint show-validator) \
  --moniker="<YOUR_NODE_NAME>" \
  --chain-id=mocha-5 \
  --commission-rate="0.10" \
  --commission-max-rate="0.20" \
  --commission-max-change-rate="0.01" \
  --min-self-delegation="1" \
  --gas=300000 \
  --fees=2000utia \
  --from="$WALLET"
```

---

## Useful Commands

### Service Status

```bash
sudo systemctl status celestia-appd-testnet
```

### Stop Node

```bash
sudo systemctl stop celestia-appd-testnet
```

### Node Info

```bash
celestia-appd status 2>&1 | jq
```

---

## Security

1. **Firewall Configuration**
   ```bash
   sudo ufw default allow outgoing
   sudo ufw default deny incoming
   sudo ufw allow ssh/tcp
   sudo ufw allow 26656/tcp
   sudo ufw enable
   ```

2. **Backup Keys**: `~/.celestia-app/config/priv_validator_key.json`
3. **SSH Key Auth**: Disable password authentication
4. **Monitoring**: Setup Prometheus/Grafana

---

## Uninstall

```bash
# Stop and disable
sudo systemctl stop celestia-appd-testnet
sudo systemctl disable celestia-appd-testnet

# Remove service
sudo rm /etc/systemd/system/celestia-appd-testnet.service
sudo systemctl daemon-reload

# Remove binary (if not shared with mainnet)
# sudo rm $(which celestia-appd)

# Remove data
rm -rf "$HOME/.celestia-app"

# Clean environment
sed -i '/WALLET_ADDRESS_TESTNET/d' "$HOME/.bash_profile"
```

---

## Resources

- **Mocha-5 snapshots (ITRocket)**: https://server-6.itrocket.net/testnet/celestia/
- **Mocha-5 RPC (ITRocket)**: https://celestia-testnet-rpc.itrocket.net
- **Discord Faucet**: https://discord.com/invite/celestiacommunity
- **Official Testnet Docs**: https://docs.celestia.org/nodes/mocha-testnet

---

**Last Updated**: v9.0.6-mocha | Chain ID: mocha-5
