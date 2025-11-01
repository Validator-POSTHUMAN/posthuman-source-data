# Celestia Mainnet — One-Liner Setup Script

Automated installation and management script for Celestia mainnet nodes by [PostHuman Validator](https://posthuman.digital).

---

## 🚀 Quick Start

Download and run the interactive setup script:

```bash
curl -o celestia-manager.sh https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh && chmod +x celestia-manager.sh && ./celestia-manager.sh
```

**Network:** Celestia Mainnet  
**Chain ID:** celestia  
**Current Version:** v5.0.11  
**Script Repository:** [github.com/Validator-POSTHUMAN/celestia-oneliner](https://github.com/Validator-POSTHUMAN/celestia-oneliner)

---

## 📋 Features Overview

### 🔧 Installation & Setup

#### 1️⃣ **Install Node (Full Setup)**
Complete automated installation:
- ✅ System requirements check (CPU, RAM, disk space)
- ✅ Install dependencies (Go 1.24.1+, build tools)
- ✅ Download and install Celestia binaries (v5.0.11)
- ✅ Initialize node with custom moniker
- ✅ Download genesis and addrbook from Posthuman snapshots
- ✅ Configure seeds, peers, pruning, gas price
- ✅ Setup systemd service with auto-restart
- ✅ Ready to sync!

#### 2️⃣ **Install Snapshot for Faster Sync**
Skip days of syncing with Posthuman snapshots:
- 📦 **Pruned Snapshot** (recommended, ~5-6 GB)
  - Latest: `https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst`
  - Updated every 24h
  - Fast sync for validators and full nodes
- 📦 **Archive Snapshot** (if available, full history)
- 🔒 Automatically backs up `priv_validator_state.json`
- ⚡ Extracts and restarts service
- 🎯 Node ready in minutes, not days!

**Manual snapshot restore:**
```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "${SERVICE_NAME}"
cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst | \
  tar -I zstd -xf - -C "${CELESTIA_HOME}"

mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

---

### 🔄 Update & Maintenance

#### 3️⃣ **Update Node** ⭐ 
**Easy one-click update to latest version:**
- 📥 Downloads latest Celestia binary (v5.0.11 or newer)
- 🛑 Gracefully stops the service
- 🔧 Installs new binary
- ✅ Restarts service automatically
- 📊 Verifies version after update

**Update is safe and quick** — typically takes 1-2 minutes with minimal downtime.

**Manual update commands:**
```bash
cd ~/celestia-app
git fetch --all
git checkout tags/v5.0.11  # or latest version
make install
celestia-appd version
sudo systemctl restart celestia-appd
```

---

### 👤 Validator Management

#### 4️⃣ **Create Validator**
Initialize your validator:
- 🔑 Setup wallet (create new or import existing)
- 📝 Set moniker, commission rates, details
- ✅ Check sync status (must be fully synced)
- 🚀 Submit create-validator transaction
- 🎯 Your validator is live!

#### 5️⃣ **Validator Operations**
Complete validator management:
- 📊 **View Validator Info** — status, voting power, commission
- 💰 **Delegate Tokens** — self-delegate or stake more TIA
- 📤 **Unstake Tokens** — unbond tokens (21-day unbonding)
- 🏦 **Set Withdrawal Address** — configure rewards address
- 🔓 **Unjail Validator** — restore jailed validator to active

---

### 🖥️ Node Operations

#### 6️⃣ **Node Management**
- 📊 **Node Info** — current status, block height, sync status
- 🌐 **Your Node Peer** — get your peer string for others
- 🔥 **Firewall Configuration** — secure your server
- 🗑️ **Delete Node** — complete removal (backup first!)

#### 7️⃣ **Service Operations**
systemd service control:
- ▶️ **Start Service** — `sudo systemctl start celestia-appd`
- ⏸️ **Stop Service** — `sudo systemctl stop celestia-appd`
- 🔄 **Restart Service** — `sudo systemctl restart celestia-appd`
- 📜 **Check Logs** — real-time log monitoring
- 🔧 **Enable Service** — auto-start on boot
- ❌ **Disable Service** — prevent auto-start

---

### 🌉 Bridge Node (Data Availability)

#### 8️⃣ **Bridge Node Setup**
For data availability sampling:
- 🔧 **Install Bridge Node** — setup DA bridge
- 💼 **Bridge Node Wallet** — manage bridge wallet
- 🔄 **Update Bridge Node** — update to latest
- 🔃 **Reset Bridge Node** — troubleshooting

---

### ⚙️ Advanced Operations

#### 9️⃣ **Advanced Settings**
Fine-tune your node:
- 🌐 **Toggle RPC & gRPC** — enable/disable public endpoints
- 📡 **Toggle API** — REST API control (note: REST may have issues, use gRPC)
- 📊 **Check Sync Status** — detailed sync progress
- 🔍 **Prometheus Metrics** — monitoring integration
- 🛠️ **Custom Port Configuration** — avoid conflicts

---

## 💾 Snapshot Information

**Posthuman Snapshots:**
- 📍 **URL**: https://snapshots.posthuman.digital/celestia-mainnet/
- 📦 **Pruned Snapshot**: ~5-6 GB (recommended)
- ⏱️ **Update Frequency**: Every 24 hours
- 🌐 **CDN**: Cloudflare R2 (fast worldwide)
- 📄 **Metadata**: `snapshot.json` (height, timestamp, checksum)

**Benefits:**
- ⚡ Sync in minutes instead of days
- 💾 Save bandwidth and time
- ✅ Verified and maintained by PostHuman
- 🔄 Always up-to-date

---

## 🔄 Update Guide

### When to Update?
- 🚨 Network upgrade announced
- 🐛 Critical bug fixes released
- ✨ New features you want to use
- 📢 Check [Celestia Discord](https://discord.com/invite/celestiacommunity) for announcements

### Update Process (using script):
1. Run the script: `./celestia-manager.sh`
2. Select **"3. Update Node"**
3. Confirm the update
4. Wait for completion (~1-2 minutes)
5. Verify: `celestia-appd version`

### Update Process (manual):
```bash
# Stop service
sudo systemctl stop celestia-appd

# Backup (optional)
cp $(which celestia-appd) $(which celestia-appd).backup

# Update
cd ~/celestia-app
git fetch --all
git checkout tags/v5.0.11  # or latest
make install

# Verify
celestia-appd version

# Restart
sudo systemctl restart celestia-appd

# Check logs
sudo journalctl -u celestia-appd -f --no-hostname -o cat
```

**Downtime:** Typically 1-3 minutes  
**Safety:** Always backup `priv_validator_key.json` before major updates

---

## 📊 System Requirements

### Validator / Full Node
- **CPU**: 6+ cores (8+ recommended)
- **RAM**: 8 GB minimum (16 GB recommended)
- **Disk**: 500 GB NVMe SSD (1 TB recommended)
- **Network**: 100 Mbps+ connection
- **OS**: Ubuntu 20.04+ or similar Linux

### Archive Node (full history)
- **CPU**: 8+ cores
- **RAM**: 24 GB+
- **Disk**: 3 TB+ NVMe SSD
- **Network**: 1 Gbps connection

---

## 🔗 Useful Resources

### PostHuman Services
- 🌐 **Website**: https://posthuman.digital
- 📊 **Explorer**: https://celestia-explorer.posthuman.digital
- 🔌 **RPC**: https://rpc-celestia-mainnet.posthuman.digital
- 🔌 **REST**: https://rest-celestia-mainnet.posthuman.digital
- 🔌 **gRPC**: https://grpc-celestia-mainnet.posthuman.digital
- 💾 **Snapshots**: https://snapshots.posthuman.digital/celestia-mainnet/

### Official Celestia
- 📚 **Docs**: https://docs.celestia.org
- 💬 **Discord**: https://discord.com/invite/celestiacommunity
- 🐦 **Twitter**: https://twitter.com/CelestiaOrg
- 💻 **GitHub**: https://github.com/celestiaorg/celestia-app

---

## 🛡️ Security Notes

- 🔐 **Backup Keys**: Always backup `~/.celestia-app/config/priv_validator_key.json`
- 🔥 **Firewall**: Use the script's firewall setup or configure manually
- 🔑 **SSH**: Use key-based authentication, disable password login
- 👁️ **Monitor**: Setup alerts for node downtime
- 💰 **Wallet**: Never share your seed phrase or private keys

---

## 🐛 Troubleshooting

### Node not syncing?
```bash
# Check logs
sudo journalctl -u celestia-appd -f -n 100

# Check peers
celestia-appd status 2>&1 | jq .SyncInfo

# Add more peers if needed
```

### REST API not working?
- Use gRPC instead (port 9090): `grpcurl -plaintext localhost:9090 list`
- See [installation guide](./installation-guide.md) for details

### Service won't start?
```bash
# Check service status
sudo systemctl status celestia-appd

# Check for port conflicts
sudo lsof -i :26656
sudo lsof -i :26657
```

---

## 📝 License

This script is provided by [PostHuman Validator](https://posthuman.digital).  
Open source and community-maintained.

**Support:** For issues or questions, reach out via:
- Discord: PostHuman community
- GitHub: [celestia-oneliner repository](https://github.com/Validator-POSTHUMAN/celestia-oneliner)

---

**Version:** v5.0.11 | **Chain ID:** celestia | **Last Updated:** 2025-01-11
