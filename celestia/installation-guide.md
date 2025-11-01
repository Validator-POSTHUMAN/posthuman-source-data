# Celestia Mainnet — Installation Guide

Comprehensive guide for installing and running a Celestia validator/full node on mainnet.

---

## Prerequisites

- **Hardware**: 6+ CPU cores, 8GB+ RAM, 500GB+ NVMe SSD
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **Network**: Stable internet connection with sufficient bandwidth

---

## 1. Update System and Install Build Tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl tar wget clang pkg-config libssl-dev jq build-essential bsdmainutils git make ncdu gcc chrony liblz4-tool
```

---

## 2. Install Go

Celestia requires Go 1.24.1+. Install it if not already present:

```bash
cd "$HOME"
if ! command -v go >/dev/null 2>&1; then
  VER="1.24.1"
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

# Verify installation
go version
```

---

## 3. Build and Install `celestia-appd`

Clone the repository and build the binary:

```bash
cd "$HOME"
rm -rf celestia-app
git clone https://github.com/celestiaorg/celestia-app.git
cd celestia-app

# Checkout the recommended version
VERSION="v5.0.11"
git checkout "tags/$VERSION"

# Build and install
make build
make install

# Verify installation
celestia-appd version
```

Expected output: `v5.0.11`

---

## 4. Initialize the Node

Initialize your node with a moniker (replace `<YOUR_NODE_NAME>` with your validator name):

```bash
# Set variables for easier configuration
MONIKER="<YOUR_NODE_NAME>"
CHAIN_ID="celestia"

# Initialize node
celestia-appd init "$MONIKER" --chain-id "$CHAIN_ID"
```

This creates the default directory: `~/.celestia-app/`

---

## 5. Download Genesis and Address Book

**Important**: Download the official genesis and address book from Posthuman infrastructure:

```bash
# Download genesis.json (required for network participation)
curl -Ls https://snapshots.posthuman.digital/celestia-mainnet/genesis.json \
  -o "$HOME/.celestia-app/config/genesis.json"

# Download addrbook.json (peer addresses for faster sync)
curl -Ls https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json \
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

### 6.2 Configure Pruning (Optional, for disk space optimization)

```bash
# Custom pruning settings
sed -i -e 's|^pruning *=.*|pruning = "custom"|' "$HOME/.celestia-app/config/app.toml"
sed -i -e 's|^pruning-keep-recent *=.*|pruning-keep-recent = "100"|' "$HOME/.celestia-app/config/app.toml"
sed -i -e 's|^pruning-interval *=.*|pruning-interval = "19"|' "$HOME/.celestia-app/config/app.toml"
```

### 6.3 Disable Indexer (Optional, saves disk space)

```bash
sed -i -e 's|^indexer *=.*|indexer = "null"|' "$HOME/.celestia-app/config/config.toml"
```

### 6.4 Enable Prometheus Metrics (Optional, for monitoring)

```bash
sed -i -e 's|prometheus = false|prometheus = true|' "$HOME/.celestia-app/config/config.toml"
```

### 6.5 Add Seeds and Persistent Peers

```bash
# Posthuman peer
PEERS="2cc7330049bc02e4276668c414222593d52eb718@peer-celestia-mainnet.posthuman.digital:40656"

# Add to config
sed -i -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = \"$PEERS\"/}" \
  "$HOME/.celestia-app/config/config.toml"
```

---

## 7. Create Systemd Service

Create a service file to run the node as a system daemon:

```bash
sudo tee /etc/systemd/system/celestia-appd.service > /dev/null <<EOF
[Unit]
Description=Celestia Node (Mainnet)
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

---

## 8. Download and Apply Snapshot (Optional but Recommended)

Using a snapshot significantly speeds up initial sync. Posthuman provides daily snapshots:

```bash
# Stop the service if running
sudo systemctl stop celestia-appd 2>/dev/null || true

# Reset node data (WARNING: this deletes existing blockchain data)
celestia-appd tendermint unsafe-reset-all --home "$HOME/.celestia-app" --keep-addr-book

# Download and extract snapshot
cd "$HOME"
curl -L https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst \
  | zstd -d | tar -xf - -C "$HOME/.celestia-app"

# Verify data directory
ls -lh "$HOME/.celestia-app/data/"
```

**Note**: Snapshot is ~5-6 GB and updates daily. Download time depends on your connection.

---

## 9. Start the Node

Enable and start the Celestia service:

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable celestia-appd

# Start the service
sudo systemctl start celestia-appd

# Check logs (Ctrl+C to exit)
sudo journalctl -u celestia-appd -f -o cat
```

---

## 10. Verify Node Status

### Check Sync Status

```bash
celestia-appd status 2>&1 | jq .SyncInfo
```

- `catching_up: false` means the node is fully synced
- `catching_up: true` means still syncing

### Check Latest Block Height

```bash
celestia-appd status 2>&1 | jq .SyncInfo.latest_block_height
```

Compare with the network height from the [Posthuman Explorer](https://celestia-explorer.posthuman.digital).

---

## 11. Create or Restore Wallet

### Create a New Wallet

```bash
WALLET="wallet"
celestia-appd keys add "$WALLET"
```

**Important**: Save the mnemonic phrase securely! It's your only way to recover the wallet.

### Restore Existing Wallet

```bash
WALLET="wallet"
celestia-appd keys add "$WALLET" --recover
```

Enter your mnemonic when prompted.

### Save Wallet Address

```bash
WALLET_ADDRESS=$(celestia-appd keys show "$WALLET" -a)
echo "export WALLET_ADDRESS=$WALLET_ADDRESS" >> "$HOME/.bash_profile"
source "$HOME/.bash_profile"
echo "Wallet address: $WALLET_ADDRESS"
```

---

## 12. Check Wallet Balance

Before creating a validator, ensure your wallet has TIA tokens:

```bash
celestia-appd query bank balances "$WALLET_ADDRESS"
```

---

## 13. Create Validator (After Full Sync)

Once your node is fully synced and wallet is funded:

```bash
celestia-appd tx staking create-validator \
  --amount=1000000utia \
  --pubkey=$(celestia-appd tendermint show-validator) \
  --moniker="<YOUR_NODE_NAME>" \
  --chain-id=celestia \
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

### Check Service Status

```bash
sudo systemctl status celestia-appd
```

### Stop Node

```bash
sudo systemctl stop celestia-appd
```

### View Node Info

```bash
celestia-appd status 2>&1 | jq
```

### Query Validator Info

```bash
celestia-appd query staking validator $(celestia-appd keys show "$WALLET" --bech val -a)
```

---

## Security Recommendations

1. **Firewall**: Configure UFW to allow only necessary ports
   ```bash
   sudo ufw default allow outgoing
   sudo ufw default deny incoming
   sudo ufw allow ssh/tcp
   sudo ufw allow 26656/tcp  # P2P port
   sudo ufw enable
   ```

2. **SSH Keys**: Use key-based authentication, disable password login
3. **Monitoring**: Set up Prometheus + Grafana for node monitoring
4. **Backups**: Regularly backup `~/.celestia-app/config/priv_validator_key.json`

---

## Uninstall Node

If you need to completely remove the node:

```bash
# Stop and disable service
sudo systemctl stop celestia-appd
sudo systemctl disable celestia-appd

# Remove service file
sudo rm /etc/systemd/system/celestia-appd.service
sudo systemctl daemon-reload

# Remove binary
sudo rm $(which celestia-appd)

# Remove data directory
rm -rf "$HOME/.celestia-app"

# Remove environment variables
sed -i '/WALLET_ADDRESS/d' "$HOME/.bash_profile"
```

---

## Resources

- **Posthuman Snapshots**: https://snapshots.posthuman.digital/celestia-mainnet/
- **Posthuman Explorer**: https://celestia-explorer.posthuman.digital
- **Posthuman RPC**: https://rpc-celestia-mainnet.posthuman.digital
- **Posthuman REST**: https://rest-celestia-mainnet.posthuman.digital
- **Posthuman gRPC**: https://grpc-celestia-mainnet.posthuman.digital
- **Official Docs**: https://docs.celestia.org/
- **GitHub**: https://github.com/celestiaorg/celestia-app

---

**Last Updated**: v5.0.11 | Chain ID: celestia
