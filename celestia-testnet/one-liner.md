# Celestia — One-Liner Setup Script

Automated installation and management for Celestia nodes (Mainnet & Testnet) by [PostHuman Validator](https://posthuman.digital).

---

## 🚀 One-Liner Install & Run

**Quick run (auto-cleanup):**
```bash
bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```
**With screen (persistent session):**
```bash
 screen -S celestia-manager
```
**Current Versions:**
- 🌐 Mainnet: `v8.0.8` (chain-id: `celestia`)
- 🧪 Testnet: `v9.0.4-mocha` (chain-id: `mocha-4`)
- 🔧 Go: `1.24.1`

## 📋 Features

### 1️⃣ Install Node
**Consensus Nodes:**
- Pruned Node (Indexer On/Off) — for validators
- Archive Node (Indexer On/Off) — full history

### 2️⃣ Update Node
One-click update with version selection.

### 3️⃣ Node Operations
- Node info, snapshot installation
- Firewall configuration
- RPC/gRPC/API toggle
- Delete node

### 4️⃣ Validator Operations
- Create wallet & validator
- Check balance & validator info
- Delegate/Unbond tokens
- Unjail validator

### 5️⃣ Data Availability Nodes ⭐
**NEW: Complete DA Layer Support**

**Install & Manage:**
- 🌉 **Bridge Node** — DA layer bridge (requires Core RPC + TIA tokens)
- 💾 **Full Storage Node** — Complete data storage (requires Core RPC)
- 💡 **Light Node** — Lightweight verification (no RPC needed)

**Access:** Main Menu → Option 5 → Option 1 (Install DA Node)

---

## 💾 Snapshots

**PostHuman Snapshots:**
- 📍 Mainnet: https://snapshots.posthuman.digital/celestia-mainnet/
- 📍 Testnet: https://snapshots.posthuman.digital/celestia-testnet/
- ⏱️ Mainnet snapshots are automated; testnet snapshots are refreshed manually while retention/storage is being fixed
- 🌐 Fast worldwide via Cloudflare R2

**Manual snapshot restore:**
```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd-testnet"

sudo systemctl stop "${SERVICE_NAME}"
if [ -f "${CELESTIA_HOME}/data/priv_validator_state.json" ]; then
  cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
fi
rm -rf "${CELESTIA_HOME}/data"
curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "${CELESTIA_HOME}"
if [ -f "${CELESTIA_HOME}/priv_validator_state.json.backup" ]; then
  mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
fi
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

---

## 📊 System Requirements

| Node Type | CPU | RAM | Disk | Network |
|-----------|-----|-----|------|---------|
| **Validator** | 16 cores | 32 GB | 2 TB NVMe | 1 Gbps |
| **Archive** | 8+ cores | 24 GB | 3+ TB NVMe | 1 Gbps |
| **Bridge** | 4+ cores | 8 GB | 500+ GB SSD | 100 Mbps |
| **Full Storage** | 4+ cores | 8 GB | 500+ GB SSD | 100 Mbps |
| **Light** | 2+ cores | 2 GB | 50+ GB SSD | 25 Mbps |

---

## 🔗 PostHuman Services

### Mainnet (celestia)
- 🌐 **Website**: https://posthuman.digital
- 📊 **Explorer**: https://explorer.posthuman.digital/celestia
- 🔌 **RPC**: https://celestia-rpc.posthuman.digital
- 🔌 **API**: https://celestia-api.posthuman.digital
- 🔌 **gRPC**: celestia-grpc.posthuman.digital:443
- 💾 **Snapshots**: https://snapshots.posthuman.digital/celestia-mainnet/
- 🌐 **Peer**: `2cc7330049bc02e4276668c414222593d52eb718@celestia-peer.posthuman.digital:26656`
- 🌐 **Addrbook**: https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json

### Testnet (mocha-4)
- 📊 **Explorer**: https://explorer.posthuman.digital/celestia-testnet
- 🔌 **RPC**: https://rpc-celestia-testnet.posthuman.digital
- 💾 **Snapshots**: https://snapshots.posthuman.digital/celestia-testnet/
- 🌐 **Addrbook**: https://snapshots.posthuman.digital/celestia-testnet/addrbook.json

---

## 🛡️ Official Celestia
- 📚 **Docs**: https://docs.celestia.org
- 💬 **Discord**: https://discord.com/invite/celestiacommunity
- 🐦 **X**: https://x.com/CelestiaOrg
- 💻 **GitHub**: https://github.com/celestiaorg/celestia-app

---

## 🆕 New Features

### Network Selection
Supports both Mainnet and Testnet:
```bash
export NETWORK_TYPE=testnet  # or mainnet (default)
./celestia-manager.sh
```

### Custom Installation Directory
Install to custom location (e.g., separate disk):
```bash
export CELESTIA_HOME=/mnt/data/.celestia-app
./celestia-manager.sh
```

Script now checks disk space of selected directory, not just root filesystem.

### DA Nodes Management
Complete suite for Data Availability nodes:
- Main Menu → Option 5 (Data Availability Nodes)
- Option 1 → Install DA Node (submenu for all DA types)
- Support for Bridge, Full Storage, and Light nodes
- Unified management interface

---

## 🔄 Quick Update

```bash
./celestia-manager.sh
# Select: 2 (Update Node) → Press Enter for latest version
```

---

## 🛡️ Security Best Practices

- 🔐 Backup `~/.celestia-app/config/priv_validator_key.json`
- 🔥 Use script's firewall configuration (Option 3 → 5)
- 🔑 Enable SSH key-based authentication
- 👁️ Setup monitoring and alerts
- 💰 Never share private keys or seed phrases

---

## 🐛 Troubleshooting

**Node not syncing?**
```bash
sudo journalctl -u celestia-appd -f -n 100
celestia-appd status 2>&1 | jq .SyncInfo
```

**Service won't start?**
```bash
sudo systemctl status celestia-appd
sudo journalctl -u celestia-appd -n 50 --no-pager
```

**Check sync status:**
```bash
./celestia-manager.sh
# Select: 7 (Status & Logs) → 2 (Check Sync Status)
```

---

## 📝 License

MIT License - [PostHuman Validator](https://posthuman.digital)

**Support:**
- 🐛 GitHub: https://github.com/Validator-POSTHUMAN/celestia-oneliner
- 💬 Discord: PostHuman Community

---

**Version:** 1.1.0 | **Last Updated:** 2026-06-08

🚀 **Happy Node Running!**
