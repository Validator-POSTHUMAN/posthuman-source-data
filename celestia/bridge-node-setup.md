# **PostHuman Celestia Bridge Node Setup Guide**

This guide will help you set up a Celestia bridge node using PostHuman infrastructure.

---

## **Hardware Requirements (data availability)**

### Non-archival
| Node type   | Memory | CPU      | Disk       | Bandwidth |
|-------------|--------|----------|------------|-----------|
| Light       | 500 MB | 1 core   | 20 GB SSD  | 56 Kbps   |
| Bridge      | 64 GB  | 8 cores  | 8 TiB NVME | 1 Gbps    |
| Full store  | 64 GB  | 8 cores  | 8 TiB NVME | 1 Gbps    |

### Archival
| Node type   | Memory | CPU      | Disk         | Bandwidth |
|-------------|--------|----------|--------------|-----------|
| Light (unpruned headers) | 500 MB | 1 core | ~111 KB per block | 56 Kbps |
| Bridge      | 64 GB  | 8 cores  | 160 TiB NVME | 1 Gbps    |
| Full store  | 64 GB  | 8 cores  | 160 TiB NVME | 1 Gbps    |

---

## **1. Update Packages and Install Dependencies**
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make gcc tar clang pkg-config libssl-dev ncdu -y
```

---

## **2. Install Go**
```sh
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

## **3. Install Celestia Node**
```sh
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

## **4. Configure and Initialize the Bridge Node**
```sh
celestia bridge init --core.ip https://rpc-celestia-mainnet.posthuman.digital --p2p.network celestia
```

After starting the Bridge Node, a wallet key will be generated. You need to fund this address with Mainnet tokens for PayForBlob transactions. Retrieve your wallet address using:

```sh
cd $HOME/celestia-node
./cel-key list --node.type bridge --keyring-backend test
```

---

## **5. Create a Service File for Celestia Bridge**
```sh
sudo tee /etc/systemd/system/celestia-bridge.service > /dev/null <<EOF
[Unit]
Description=celestia Bridge
After=network-online.target

[Service]
User=$USER
ExecStart=$(which celestia) bridge start --archival \
--p2p.network celestia \
--metrics.tls=true --metrics --metrics.endpoint otel.celestia.observer
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:
```sh
sudo systemctl daemon-reload
sudo systemctl enable celestia-bridge
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
```

---

## **6. Retrieve Node Information**
After initializing and starting your node, generate an auth token:
```sh
NODE_TYPE=bridge
AUTH_TOKEN=$(celestia $NODE_TYPE auth admin)
```

Then, get the peer ID:
```sh
curl -X POST      -H "Authorization: Bearer $AUTH_TOKEN"      -H 'Content-Type: application/json'      -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}'      http://localhost:26658
```

---

## **7. Download and Restore Bridge Node Snapshot**
Installing dependencies:
```sh
sudo apt install aria2 jq lz4 unzip -y
```

Downloading and unpacking the snapshot:
```sh
cd $HOME
aria2c -x 16 -s 16 -o celestia-bridge-snap.tar.lz4 https://server-9.itrocket.net/mainnet/celestia/bridge/null
sudo systemctl stop celestia-bridge
rm -rf ~/.celestia-bridge/{blocks,data,index,inverted_index,transients,.lock}
tar -I lz4 -xvf ~/celestia-bridge-snap.tar.lz4 -C ~/.celestia-bridge/
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
```

Removing the snapshot file:
```sh
rm ~/celestia-bridge-snap.tar.lz4
```

---

## **8. Useful Commands (Cheat Sheet)**

### **Check Wallet Balance**
```sh
celestia state balance --node.store ~/.celestia-bridge/
```

### **Get Wallet Address**
```sh
cd $HOME/celestia-node
./cel-key list --node.type bridge --keyring-backend test
```

### **Restore an Existing Key**
```sh
KEY_NAME="my_celes_key"
cd ~/celestia-node
./cel-key add $KEY_NAME --keyring-backend test --node.type bridge --recover
```

### **Check Node Sync Status**
```sh
celestia header sync-state --node.store ~/.celestia-bridge/
```

### **Get Node ID**
```sh
celestia p2p info --node.store ~/.celestia-bridge/
```

### **Add Permissions for Key Transfers**
```sh
chmod -R 700 ~/.celestia-bridge
```

### **Reset Node**
```sh
celestia bridge unsafe-reset-store
```

---

## **9. Upgrade Instructions**
### **Stop Bridge Node**
```sh
sudo systemctl stop celestia-bridge
```

### **Download Latest Version**
```sh
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

### **Update Configuration**
```sh
celestia bridge config-update
```

### **Restart Bridge Node**
```sh
sudo systemctl restart celestia-bridge && sudo journalctl -u celestia-bridge -fo cat
```

---

## **10. Delete Bridge Node**
```sh
sudo systemctl stop celestia-bridge
sudo systemctl disable celestia-bridge
sudo rm /etc/systemd/system/celestia-bridge*
rm -rf $HOME/celestia-node $HOME/.celestia-bridge
```

---

🚀 **Your Celestia Bridge Node is now set up and running.**
