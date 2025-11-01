# Celestia Testnet (Mocha-4) — One-Liner Setup Script

Automated installation and management script for Celestia Mocha-4 testnet by [PostHuman Validator](https://posthuman.digital).

---

## 🚀 Quick Start

Download and run the interactive setup script:

```bash
curl -o celestia-manager.sh https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh && chmod +x celestia-manager.sh && ./celestia-manager.sh
```

**Network:** Celestia Testnet (Mocha-4)  
**Chain ID:** mocha-4  
**Current Version:** v6.2.0-mocha  
**Script Repository:** [github.com/Validator-POSTHUMAN/celestia-oneliner](https://github.com/Validator-POSTHUMAN/celestia-oneliner)

---

## 📋 Features Overview

### 🔧 Installation & Setup

#### 1️⃣ **Install Node (Full Setup)**
Complete automated testnet installation:
- ✅ System requirements check (CPU, RAM, disk space)
- ✅ Install dependencies (Go 1.24.1+, build tools)
- ✅ Download and install Celestia testnet binaries (v6.2.0-mocha)
- ✅ Initialize node with custom moniker
- ✅ Download genesis and addrbook from Posthuman snapshots
- ✅ Configure seeds, peers, pruning, gas price
- ✅ Setup systemd service (celestia-appd-testnet)
- ✅ Ready to sync on Mocha-4!

#### 2️⃣ **Install Snapshot for Faster Sync**
Skip hours of syncing with Posthuman testnet snapshots:
- 📦 **Pruned Snapshot** (~1-2 GB, smaller than mainnet)
  - Latest: `https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst`
  - Updated every 24h
  - Perfect for testnet validators
- 🔒 Automatically backs up `priv_validator_state.json`
- ⚡ Extracts and restarts service
- 🎯 Testnet node ready in minutes!

**Manual snapshot restore:**
```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"  # or celestia-appd-testnet

sudo systemctl stop "${SERVICE_NAME}"
cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst | \
  tar -I zstd -xf - -C "${CELESTIA_HOME}"

mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

---

### 🔄 Update & Maintenance

#### 3️⃣ **Update Node** ⭐ 
**Easy one-click update to latest testnet version:**
- 📥 Downloads latest testnet binary (v6.2.0-mocha or newer)
- 🛑 Gracefully stops the service
- 🔧 Installs new binary
- ✅ Restarts service automatically
- 📊 Verifies version after update

**Testnet updates are frequent** — stay up-to-date for new features and network upgrades!

**Manual update commands:**
```bash
cd ~/celestia-app
git fetch --all
git checkout tags/v6.2.0-mocha  # or latest testnet version
make install
celestia-appd version
sudo systemctl restart celestia-appd  # or celestia-appd-testnet
```

---

### 👤 Validator Management

#### 4️⃣ **Create Validator**
Initialize your testnet validator:
- 🔑 Setup testnet wallet (create new or import)
- 💰 **Get testnet tokens**: 
  - Join [Celestia Discord](https://discord.com/invite/celestiacommunity)
  - Go to #mocha-faucet channel
  - Request tokens with your address
- 📝 Set moniker, commission rates, details
- ✅ Check sync status (must be fully synced)
- 🚀 Submit create-validator transaction
- 🎯 Your testnet validator is live!

#### 5️⃣ **Validator Operations**
Complete validator management:
- 📊 **View Validator Info** — status, voting power
- 💰 **Delegate Tokens** — stake testnet TIA
- 📤 **Unstake Tokens** — unbond tokens
- 🏦 **Set Withdrawal Address** — configure rewards
- 🔓 **Unjail Validator** — restore jailed validator

---

### 🖥️ Node Operations

#### 6️⃣ **Node Management**
- 📊 **Node Info** — current status, block height
- 🌐 **Your Node Peer** — share your peer with others
- 🔥 **Firewall Configuration** — secure testnet node
- 🗑️ **Delete Node** — clean removal

#### 7️⃣ **Service Operations**
systemd service control:
- ▶️ **Start Service**
- ⏸️ **Stop Service**
- 🔄 **Restart Service**
- 📜 **Check Logs** — monitor testnet activity
- 🔧 **Enable Service** — auto-start
- ❌ **Disable Service** — manual start only

---

### 🌉 Bridge Node (Data Availability)

#### 8️⃣ **Bridge Node Setup**
Test data availability features:
- 🔧 **Install Bridge Node** — testnet DA bridge
- 💼 **Bridge Node Wallet** — manage bridge wallet
- 🔄 **Update Bridge Node** — latest testnet features
- 🔃 **Reset Bridge Node** — troubleshooting

---

### ⚙️ Advanced Operations

#### 9️⃣ **Advanced Settings**
Test and configure:
- 🌐 **Toggle RPC & gRPC** — public endpoint testing
- 📡 **Toggle API** — REST API control
- 📊 **Check Sync Status** — detailed progress
- 🔍 **Prometheus Metrics** — monitoring setup
- 🛠️ **Custom Ports** — multi-node testing

---

## 💾 Snapshot Information

**Posthuman Testnet Snapshots:**
- 📍 **URL**: https://snapshots.posthuman.digital/celestia-testnet/
- 📦 **Pruned Snapshot**: ~1-2 GB (testnet is smaller)
- ⏱️ **Update Frequency**: Every 24 hours
- 🌐 **CDN**: Cloudflare R2 (fast worldwide)
- 📄 **Metadata**: `snapshot.json` (height, timestamp, checksum)

**Benefits:**
- ⚡ Sync testnet in minutes
- 💾 Perfect for testing and development
- ✅ Maintained by PostHuman
- 🔄 Daily updates with latest blocks

---

## 🔄 Update Guide

### When to Update?
- 🚨 Testnet upgrade announced (check Discord!)
- 🐛 Bug fixes for testnet features
- ✨ New testnet features released
- 📢 Monitor [Celestia Discord #mocha-announcements](https://discord.com/invite/celestiacommunity)

### Update Process (using script):
1. Run the script: `./celestia-manager.sh`
2. Select **"3. Update Node"**
3. Confirm the update
4. Wait for completion (~1-2 minutes)
5. Verify: `celestia-appd version` (should show v6.2.0-mocha or newer)

### Update Process (manual):
```bash
# Stop service
sudo systemctl stop celestia-appd  # or celestia-appd-testnet

# Update
cd ~/celestia-app
git fetch --all
git checkout tags/v6.2.0-mocha  # or announced version
make install

# Verify
celestia-appd version

# Restart
sudo systemctl restart celestia-appd

# Check logs
sudo journalctl -u celestia-appd -f --no-hostname -o cat
```

**Note:** Testnet updates are more frequent than mainnet. Stay connected to Discord!

---

## 📊 System Requirements

### Testnet Validator / Full Node
- **CPU**: 4+ cores (6+ recommended)
- **RAM**: 8 GB minimum (16 GB recommended)
- **Disk**: 250 GB NVMe SSD (500 GB for safety)
- **Network**: 100 Mbps+ connection
- **OS**: Ubuntu 20.04+ or similar Linux

**Testnet requirements are lighter than mainnet** — great for testing on modest hardware!

---

## 🪙 Getting Testnet Tokens

### Mocha-4 Faucet
1. Create or restore wallet: `celestia-appd keys add wallet`
2. Get your address: `celestia-appd keys show wallet -a`
3. Join [Celestia Discord](https://discord.com/invite/celestiacommunity)
4. Navigate to **#mocha-faucet** channel
5. Request tokens: `!faucet celestia1your_address_here`
6. Wait for confirmation (~1-5 minutes)
7. Check balance: `celestia-appd query bank balances $(celestia-appd keys show wallet -a)`

**Faucet limits:**
- Request frequency: ~24 hours between requests
- Amount per request: Enough to create validator + transactions

---

## 🔗 Useful Resources

### PostHuman Testnet Services
- 🌐 **Website**: https://posthuman.digital
- 🔌 **RPC**: https://rpc-celestia-testnet.posthuman.digital
- 🔌 **REST**: https://rest-celestia-testnet.posthuman.digital
- 🔌 **gRPC**: https://grpc-celestia-testnet.posthuman.digital
- 💾 **Snapshots**: https://snapshots.posthuman.digital/celestia-testnet/

### Official Celestia Testnet
- 📚 **Testnet Docs**: https://docs.celestia.org/nodes/mocha-testnet
- 💬 **Discord**: https://discord.com/invite/celestiacommunity (#mocha-faucet, #mocha-announcements)
- 🐦 **Twitter**: https://twitter.com/CelestiaOrg
- 💻 **GitHub**: https://github.com/celestiaorg/celestia-app

---

## 🛡️ Security Notes (Testnet)

- 🔐 **Backup Keys**: Even on testnet, backup `~/.celestia-app/config/priv_validator_key.json`
- 🔥 **Firewall**: Configure basic firewall protection
- 🔑 **SSH**: Use key-based auth even for test servers
- 👁️ **Monitor**: Test your monitoring setup on testnet first
- 💰 **No Real Value**: Testnet tokens have no monetary value — perfect for testing!

**Testnet Benefits:**
- 🧪 Test validator operations risk-free
- 🎓 Learn without financial risk
- 🐛 Help find bugs before mainnet
- 🚀 Prepare for mainnet deployment

---

## 🐛 Troubleshooting

### Testnet-specific issues

#### Chain reset or upgrade?
```bash
# Testnet may reset or upgrade frequently
# Check Discord announcements
# May need to:
cd ~/celestia-app
git fetch --all
git checkout tags/NEW_VERSION
make install
# May need fresh genesis: check snapshots.posthuman.digital
```

#### Node not syncing?
```bash
# Check logs
sudo journalctl -u celestia-appd -f -n 100

# Verify correct chain-id
celestia-appd status 2>&1 | jq -r .NodeInfo.network
# Should show: mocha-4
```

#### Need more peers?
```bash
# Check current peers
celestia-appd status 2>&1 | jq .SyncInfo.peers

# Add PostHuman peer (check networks.json for latest)
# Edit ~/.celestia-app/config/config.toml
```

### REST API not working?
- Common issue on testnet too
- Use gRPC instead: `grpcurl -plaintext localhost:9090 list`
- See [installation guide](./installation-guide.md) for gRPC setup

---

## 📝 License

This script is provided by [PostHuman Validator](https://posthuman.digital).  
Open source and community-maintained.

**Support:** For testnet issues or questions:
- Discord: PostHuman community or #mocha-validators
- GitHub: [celestia-oneliner repository](https://github.com/Validator-POSTHUMAN/celestia-oneliner)

---

**Version:** v6.2.0-mocha | **Chain ID:** mocha-4 | **Last Updated:** 2025-01-11  
🧪 **This is a testnet** — tokens have no real value, perfect for testing!
