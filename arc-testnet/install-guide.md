# Arc Network Node Installation Guide

Arc is an open EVM-compatible Layer 1 blockchain built on Malachite consensus, delivering sub-second finality and USDC as native gas currency.

## Hardware Requirements

### Minimum Specifications
- **CPU:** 4 cores
- **RAM:** 16 GB
- **Disk:** 200 GB SSD (NVMe recommended)
- **Network:** 100 Mbps

### Recommended Specifications
- **CPU:** 8+ cores
- **RAM:** 32 GB
- **Disk:** 500 GB+ NVMe SSD
- **Network:** 1 Gbps

## Prerequisites

- Ubuntu 24.04 LTS (recommended)
- Rust toolchain (1.91.1+)
- Basic Linux system administration knowledge

## Installation

### Step 1: Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### Step 2: Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y libclang-dev pkg-config build-essential git curl
```

### Step 3: Clone Arc Node Repository

```bash
git clone https://github.com/circlefin/arc-node.git
cd arc-node
git checkout v0.6.0
git submodule update --init --recursive
```

### Step 4: Build Arc Node Binaries

⏱️ **Build time:** ~10-15 minutes depending on hardware.

```bash
cargo install --path crates/node
cargo install --path crates/malachite-app
cargo install --path crates/snapshots
```

Binaries will be installed to `~/.cargo/bin/`:
- `arc-node-execution` — Execution layer (Reth-based)
- `arc-node-consensus` — Consensus layer (Malachite-based)
- `arc-snapshots` — Snapshot utility

### Step 5: Create Data Directories

```bash
mkdir -p ~/.arc/execution ~/.arc/consensus
```

### Step 6: Download Blockchain Snapshots

⚠️ **Important:** Snapshots are ~84 GB download, ~150 GB extracted. Requires stable internet and sufficient disk space.

```bash
arc-snapshots download --chain=arc-testnet \
  --execution-path ~/.arc/execution \
  --consensus-path ~/.arc/consensus
```

⏱️ **Download time:** 30-60 minutes. Extraction is CPU-intensive.

### Step 7: Generate JWT Secret

```bash
openssl rand -hex 32 | tr -d "\n" > ~/.arc/jwt.hex
chmod 600 ~/.arc/jwt.hex
```

### Step 8: Initialize Consensus Layer

```bash
arc-node-consensus init --home ~/.arc/consensus
```

### Step 9: Create Systemd Services

#### Execution Layer Service

Create `/etc/systemd/system/arc-execution.service`:

```ini
[Unit]
Description=Arc Network Execution Layer
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/arc-node
ExecStart=/home/YOUR_USERNAME/.cargo/bin/arc-node-execution node \
  --chain arc-testnet \
  --datadir /home/YOUR_USERNAME/.arc/execution \
  --http --http.port 8545 --http.addr 0.0.0.0 \
  --authrpc.port 8551 \
  --authrpc.jwtsecret /home/YOUR_USERNAME/.arc/jwt.hex \
  --port 31000
Restart=on-failure
RestartSec=10
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

#### Consensus Layer Service

Create `/etc/systemd/system/arc-consensus.service`:

```ini
[Unit]
Description=Arc Network Consensus Layer
After=network.target arc-execution.service
Requires=arc-execution.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/arc-node
ExecStart=/home/YOUR_USERNAME/.cargo/bin/arc-node-consensus start \
  --home /home/YOUR_USERNAME/.arc/consensus \
  --eth-rpc-endpoint http://localhost:8545 \
  --execution-endpoint http://localhost:8551 \
  --execution-jwt /home/YOUR_USERNAME/.arc/jwt.hex \
  --rpc.addr 127.0.0.1:31000 \
  --follow \
  --follow.endpoint https://rpc.drpc.testnet.arc.network,wss=rpc.drpc.testnet.arc.network \
  --follow.endpoint https://rpc.quicknode.testnet.arc.network,wss=rpc.quicknode.testnet.arc.network \
  --follow.endpoint https://rpc.blockdaemon.testnet.arc.network,wss=rpc.blockdaemon.testnet.arc.network
Restart=on-failure
RestartSec=10
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

⚠️ **Replace `YOUR_USERNAME` with your actual username.**

### Step 10: Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable arc-execution arc-consensus
sudo systemctl start arc-execution
sleep 10
sudo systemctl start arc-consensus
```

### Step 11: Verify Operation

Check status:
```bash
sudo systemctl status arc-execution arc-consensus
```

Check current block:
```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545 | jq -r '.result' | xargs printf "%d\n"
```

View logs:
```bash
sudo journalctl -u arc-consensus -f
```

## Network Ports

| Port | Service | Access |
|------|---------|--------|
| 8545 | Execution RPC | Local only |
| 8551 | Engine API | Local (JWT protected) |
| 31000 | Execution P2P | Public |
| 27000 | Consensus P2P | Public |

## Resources

- **Official Website:** https://www.arc.network/
- **Documentation:** https://docs.arc.network/
- **GitHub:** https://github.com/circlefin/arc-node
- **Discord:** https://discord.gg/circle

---

*Arc is currently in testnet (alpha). Network may experience instability.*  
*Guide version: 1.0 | Updated: 2026-04-17 | Node version: v0.6.0*
