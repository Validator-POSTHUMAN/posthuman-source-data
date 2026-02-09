# NEAR Mainnet Validator Installation Guide

## About NEAR

NEAR Protocol is a sharded, proof-of-stake Layer 1 blockchain with fast finality, low fees, and a developer-friendly environment. Validators produce blocks and chunks, securing the network via staking.

**Network Details:**

| Parameter | Value |
|-----------|-------|
| Network | NEAR Mainnet |
| Chain ID | `mainnet` |
| Currency | `NEAR` |
| Block Time | ~1s |
| Current Version | `2.10.6` |
| P2P Port | `24567` |
| RPC Port | `3030` |
| Explorer | [nearblocks.io](https://nearblocks.io) |

## Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16+ cores |
| RAM | 20 GB | 64 GB+ |
| Storage | 1 TB NVMe SSD | 2 TB+ NVMe SSD |
| Network | 1 Gbps | 1 Gbps |

### Software

- Ubuntu 22.04+
- Rust (latest stable)
- Git, curl, jq

## 1. System Preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl jq build-essential pkg-config libssl-dev \
  clang cmake protobuf-compiler llvm gcc g++ make nano htop

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

## 2. Network Tuning

```bash
sudo tee -a /etc/sysctl.conf > /dev/null << 'EOF'
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
EOF
sudo sysctl -p
```

## 3. Build nearcore

```bash
git clone https://github.com/near/nearcore.git
cd nearcore
git fetch --tags

# Check latest release
git tag -l --sort=-v:refname | head -5

# Checkout and build
git checkout 2.10.6
cargo build --release -p neard
```

Verify:

```bash
./target/release/neard --version
```

## 4. Initialize Node

```bash
~/nearcore/target/release/neard --home ~/.near init --chain-id mainnet --download-config --download-genesis
```

## 5. Firewall

```bash
sudo ufw allow 24567/tcp comment "NEAR P2P"
sudo ufw allow 3030/tcp comment "NEAR RPC"
sudo ufw enable
```

## 6. Create Systemd Service

```bash
sudo tee /etc/systemd/system/neard.service > /dev/null << 'EOF'
[Unit]
Description=NEAR Validator Node
Documentation=https://docs.near.org
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
ExecStart=/home/ubuntu/nearcore/target/release/neard --home /home/ubuntu/.near run
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable neard
sudo systemctl start neard
```

Check logs:

```bash
journalctl -u neard -f --no-pager
```

## 7. Check Sync Status

```bash
curl -s localhost:3030/status | jq '.sync_info'
```

Wait until `"syncing": false`.

## 8. Generate Wallet & Validator Key

### Install near-cli

```bash
npm install -g near-cli
export NEAR_ENV=mainnet
```

### Generate keypair

```bash
near generate-key validator_name --networkId mainnet
```

### Get implicit address

Your implicit address is the hex representation of your public key. Fund it with NEAR.

### Create validator_key.json

```json
{
  "account_id": "YOUR_POOL.poolv1.near",
  "public_key": "ed25519:YOUR_PUBLIC_KEY",
  "secret_key": "ed25519:YOUR_SECRET_KEY"
}
```

Save to `~/.near/validator_key.json` and restart neard:

```bash
sudo systemctl restart neard
```

## 9. Deploy Staking Pool

Minimum deposit: **30 NEAR**.

```bash
near call poolv1.near create_staking_pool \
  '{"staking_pool_id": "YOUR_POOL_NAME", "owner_id": "YOUR_OWNER_ACCOUNT", "stake_public_key": "ed25519:YOUR_PUBLIC_KEY", "reward_fee_fraction": {"numerator": 7, "denominator": 100}}' \
  --accountId YOUR_OWNER_ACCOUNT --amount 30 --gas 300000000000000 --networkId mainnet
```

Parameters:
- `staking_pool_id` — pool name (e.g. `posthuman`), creates `posthuman.poolv1.near`
- `owner_id` — account that controls the pool
- `stake_public_key` — from validator_key.json
- `reward_fee_fraction` — commission (7/100 = 7%)

## 10. Setup Ping Cron

Pool must be pinged **at least once per epoch** (~12 hours) to distribute rewards.

```bash
crontab -e
```

Add:

```
0 */2 * * * /usr/local/bin/near call YOUR_POOL.poolv1.near ping '{}' --accountId YOUR_OWNER_ACCOUNT --networkId mainnet --gas 300000000000000 >> /home/ubuntu/near-ping.log 2>&1
```

> ⚠️ Always specify `--networkId mainnet`, otherwise near-cli defaults to testnet.

Cost: ~0.00003 NEAR per ping (~0.01 NEAR/month).

## 11. Useful Commands

```bash
# Node status
curl -s localhost:3030/status | jq '{validator: .validator_account_id, syncing: .sync_info.syncing, block: .sync_info.latest_block_height, version: .version.version}'

# Pool total staked
near view YOUR_POOL.poolv1.near get_total_staked_balance '{}' --networkId mainnet

# Current seat price
curl -s https://rpc.mainnet.near.org \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"1","method":"validators","params":[null]}' \
  | jq -r '.result.current_validators | sort_by(.stake | tonumber) | .[0].stake' \
  | awk '{printf "Seat price: %.2f NEAR\n", $1/1e24}'

# Manual ping
near call YOUR_POOL.poolv1.near ping '{}' --accountId YOUR_OWNER_ACCOUNT --networkId mainnet --gas 300000000000000
```

## 12. Upgrade Node

```bash
cd ~/nearcore
git fetch --tags
git checkout NEW_VERSION
cargo build --release -p neard
sudo systemctl restart neard
```

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
