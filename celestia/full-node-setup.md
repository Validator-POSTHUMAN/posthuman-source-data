🚀 **PostHuman Celestia Full Storage Node Setup Guide**

This guide will help you set up a **Celestia Full Storage Node** using PostHuman infrastructure.

---

## 🔧 Hardware Requirements (data availability)

### Non-archival
| Node type  | Memory | CPU     | Disk       | Bandwidth |
|------------|--------|---------|------------|-----------|
| Full store | 64 GB  | 8 cores | 8 TiB NVME | 1 Gbps    |
| Bridge     | 64 GB  | 8 cores | 8 TiB NVME | 1 Gbps    |

### Archival
| Node type  | Memory | CPU     | Disk         | Bandwidth |
|------------|--------|---------|--------------|-----------|
| Full store | 64 GB  | 8 cores | 160 TiB NVME | 1 Gbps    |
| Bridge     | 64 GB  | 8 cores | 160 TiB NVME | 1 Gbps    |

> Figures are sourced from Celestia’s official hardware guidance (v6 throughput assumptions).

---

## 📦 1. Update Packages and Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make gcc tar clang pkg-config libssl-dev ncdu -y
```

---

## 🛠 2. Install Go
```bash
cd ~
if ! command -v go >/dev/null 2>&1; then
  VER="1.24.1"
  wget "https://golang.org/dl/go${VER}.linux-amd64.tar.gz"
  sudo rm -rf /usr/local/go
  sudo tar -C /usr/local -xzf "go${VER}.linux-amd64.tar.gz"
  rm "go${VER}.linux-amd64.tar.gz"
fi

[ -d "$HOME/go/bin" ] || mkdir -p "$HOME/go/bin"
if ! grep -q "/usr/local/go/bin" "$HOME/.bash_profile" 2>/dev/null; then
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> "$HOME/.bash_profile"
fi
source "$HOME/.bash_profile" 2>/dev/null || true
go version
```

---

## 📥 3. Install Celestia Node
```bash
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.26.4"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
```

---

## 🔑 4. Create a Wallet
```bash
./cel-key add my_celes_key --keyring-backend test --node.type full
```

### (Optional) Restore an Existing Wallet
```bash
cd ~/celestia-node
./cel-key add my_celes_key --keyring-backend test --node.type full --recover
```

Retrieve your wallet address:
```bash
cd $HOME/celestia-node
./cel-key list --node.type full --keyring-backend test
```

---

## ⚙️ 5. Configure and Initialize the Full Storage Node
```bash
celestia full init --core.ip $CORE_IP
```

---

## 📡 6. Set Consensus Node RPC and gRPC Ports
```bash
CORE_IP="<PUT_CONSENSUS_NODE_IP>"
CORE_RPC_PORT="<PUT_CONSENSUS_NODE_RPC_PORT>"
CORE_GRPC_PORT="<PUT_CONSENSUS_NODE_GRPC_PORT>"
KEY_NAME="my_celes_key"
```

---

## 🔄 7. Create a Service File for Celestia Full Storage Node
```bash
sudo tee /etc/systemd/system/celestia-bridge.service > /dev/null <<EOF
[Unit]
Description=celestia Bridge
After=network-online.target

[Service]
User=$USER
ExecStart=$(which celestia) bridge start --archival \
--metrics.tls=true --metrics --metrics.endpoint otel.celestia.observer
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celestia-full
sudo systemctl restart celestia-full && sudo journalctl -u celestia-full -fo cat
```

---

## 📡 8. Retrieve Node Peer ID
Generate an auth token:
```bash
NODE_TYPE=full
AUTH_TOKEN=$(celestia $NODE_TYPE auth admin)
```

Get the peer ID:
```bash
curl -X POST \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
     http://localhost:26658
```

---

## 📖 9. Useful Commands (Cheat Sheet)

### 💰 Check Wallet Balance
```bash
celestia state balance --node.store ~/.celestia-full/
```

### 📜 Get Wallet Address
```bash
cd $HOME/celestia-node
./cel-key list --node.type full --keyring-backend test
```

### 🔄 Restore an Existing Key
```bash
KEY_NAME="my_celes_key"
cd ~/celestia-node
./cel-key add $KEY_NAME --keyring-backend test --node.type full --recover
```

### 📊 Check Node Sync Status
```bash
celestia header sync-state --node.store ~/.celestia-full/
```

### 🔍 Get Node ID
```bash
celestia p2p info --node.store ~/.celestia-full/
```

### 🔐 Add Permissions for Key Transfers
```bash
chmod -R 700 ~/.celestia-full
```

### 🔄 Reset Node
```bash
celestia full unsafe-reset-store
```

---

## 🔄 10. Upgrade Instructions

### 🛑 Stop Full Storage Node
```bash
sudo systemctl stop celestia-full
```

### 📥 Download Latest Version
```bash
cd "$HOME"
rm -rf celestia-node
git clone https://github.com/celestiaorg/celestia-node.git
cd celestia-node
NODE_VERSION="v0.26.4"
git checkout "tags/${NODE_VERSION}"
make build
sudo make install
make cel-key
```

### 🔄 Update Configuration
```bash
celestia full config-update
```

### 🚀 Restart Full Storage Node
```bash
sudo systemctl restart celestia-full && sudo journalctl -u celestia-full -fo cat
```

---

## 🗑 11. Delete Full Storage Node
```bash
sudo systemctl stop celestia-full
sudo systemctl disable celestia-full
sudo rm /etc/systemd/system/celestia-full*
rm -rf $HOME/celestia-node $HOME/.celestia-app $HOME/.celestia-full
```

---

🚀 **Your Celestia Full Storage Node is now up and running.**
