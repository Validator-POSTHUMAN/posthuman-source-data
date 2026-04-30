# Sahara AI Testnet — Installation Guide

Comprehensive guide for installing and running a Sahara AI node on testnet.

---

## Prerequisites

**For Full Node** (recommended):
- **Hardware**: 8 cores, 32 GB RAM, 2 TB SSD, 100 Mbps bandwidth
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **Network**: Stable internet connection
- **Docker**: Docker and Docker Compose installed

**Note**: These are recommended requirements for testnet full nodes. Mainnet validator requirements are higher (32 cores, 128 GB RAM, 8 TB SSD).

---

## Network Information

- **Chain ID**: `sahara-test-1`
- **Current Version**: `0.3.1-testnet-beta`
- **Genesis**: Available in setup repository
- **RPC Endpoints**:
  - https://testnet-cos-rpc1.saharalabs.ai
  - https://testnet-rpc2.saharalabs.ai
- **Seed Nodes**: Configured in setup repository

---

## Installation Methods

### Method 1: Docker (Recommended)

This is the easiest and most reliable method for running a Sahara testnet node.

#### 1. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 2. Clone Setup Repository

```bash
cd $HOME
git clone https://github.com/SaharaLabsAI/setup-testnet-node sahara-testnet
cd sahara-testnet
```

#### 3. Configure Node

Edit `chain-data/config/config.toml` to set your moniker:

```bash
sed -i 's/moniker = "sahara-testnet-node1"/moniker = "YOUR_MONIKER"/g' chain-data/config/config.toml
```

Replace `YOUR_MONIKER` with your desired node name.

#### 4. Configure External Address (Optional)

If you want your node to be discoverable by other peers:

```bash
EXTERNAL_IP=$(curl -s ifconfig.me)
sed -i "s/external_address = \"\"/external_address = \"tcp:\/\/${EXTERNAL_IP}:26656\"/g" chain-data/config/config.toml
```

#### 5. Add Persistent Peers

Get current active peers and add them:

```bash
PEERS="53198df19b9c1841a008d5588e1d6ff3457284fc@144.76.98.52:26656,085a92a6d022ba99ca16574c91320a140fcb3406@109.236.90.95:26656,8e5ba302f0afceaf33a17625a09199a7c14a9ae5@5.9.116.2:26656"
sed -i "s/^persistent_peers = .*/persistent_peers = \"$PEERS\"/g" chain-data/config/config.toml
```

#### 6. Configure State Sync (Recommended)

State sync allows fast synchronization from a recent snapshot:

```bash
# Get latest block height
LATEST_HEIGHT=$(curl -s https://testnet-cos-rpc1.saharalabs.ai/status | jq -r .result.sync_info.latest_block_height)
SYNC_BLOCK_HEIGHT=$((LATEST_HEIGHT - 1000))
SYNC_BLOCK_HASH=$(curl -s "https://testnet-cos-rpc1.saharalabs.ai/commit?height=${SYNC_BLOCK_HEIGHT}" | jq -r .result.signed_header.commit.block_id.hash)

# Update config
sed -i "s/enable = false/enable = true/g" chain-data/config/config.toml
sed -i "s/trust_height = .*/trust_height = ${SYNC_BLOCK_HEIGHT}/g" chain-data/config/config.toml
sed -i "s/trust_hash = .*/trust_hash = \"${SYNC_BLOCK_HASH}\"/g" chain-data/config/config.toml

echo "State sync configured:"
echo "Height: ${SYNC_BLOCK_HEIGHT}"
echo "Hash: ${SYNC_BLOCK_HASH}"
```

**Note**: If state sync fails, you can disable it and sync from genesis (slower):

```bash
sed -i "s/enable = true/enable = false/g" chain-data/config/config.toml
```

#### 7. Start Node

```bash
docker-compose up -d
```

#### 8. Check Logs

```bash
# View logs
docker-compose logs -f

# Check sync status
curl -s http://localhost:26657/status | jq .result.sync_info
```

#### 9. Verify Node is Running

```bash
# Check container status
docker-compose ps

# Check peer connections
curl -s http://localhost:26657/net_info | jq .result.n_peers

# Check current height
curl -s http://localhost:26657/status | jq .result.sync_info.latest_block_height
```

---

## Port Configuration

Default ports used by Sahara node:

- **26656**: P2P (must be open for peer connections)
- **26657**: RPC (can be restricted to localhost)
- **16161**: ETH JSON-RPC
- **16162**: ETH WebSocket

### Firewall Configuration

```bash
# Allow P2P port
sudo ufw allow 26656/tcp

# Optional: Allow RPC (only if you want to expose RPC publicly)
# sudo ufw allow 26657/tcp
```

---

## Node Management

### Stop Node

```bash
cd ~/sahara-testnet
docker-compose stop
```

### Start Node

```bash
cd ~/sahara-testnet
docker-compose start
```

### Restart Node

```bash
cd ~/sahara-testnet
docker-compose restart
```

### View Logs

```bash
cd ~/sahara-testnet
docker-compose logs -f
```

### Check Sync Status

```bash
curl -s http://localhost:26657/status | jq '.result.sync_info | {catching_up, latest_block_height, latest_block_time}'
```

### Update Node

```bash
cd ~/sahara-testnet
docker-compose down
git pull
docker-compose pull
docker-compose up -d
```

---

## Troubleshooting

### Node Not Syncing

1. **Check peer connections**:
   ```bash
   curl -s http://localhost:26657/net_info | jq .result.n_peers
   ```
   If 0 peers, add more persistent peers.

2. **Disable state sync** if it's failing:
   ```bash
   docker-compose down
   sed -i "s/enable = true/enable = false/g" chain-data/config/config.toml
   docker-compose up -d
   ```

3. **Check logs for errors**:
   ```bash
   docker-compose logs --tail 100
   ```

### Port Already in Use

If ports 26656 or 26657 are already in use, modify `docker-compose.yaml`:

```yaml
ports:
  - 36656:26656  # Change external port
  - 36657:26657  # Change external port
  - 36161:16161
  - 36162:16162
```

Then update external_address in config:

```bash
sed -i "s/26656/36656/g" chain-data/config/config.toml
```

### Reset Node Data

**Warning**: This will delete all blockchain data and restart from genesis.

```bash
cd ~/sahara-testnet
docker-compose down
sudo rm -rf chain-data/data/*
docker-compose up -d
```

---

## Monitoring

### Check Node Health

```bash
# Node info
curl -s http://localhost:26657/status | jq .result.node_info

# Sync status
curl -s http://localhost:26657/status | jq .result.sync_info

# Validator info (if running validator)
curl -s http://localhost:26657/status | jq .result.validator_info
```

### Monitor Resource Usage

```bash
# Container stats
docker stats sahara-testnet-saharad-1

# Disk usage
du -sh ~/sahara-testnet/chain-data/data
```

---

## Becoming a Validator

**Note**: Sahara mainnet is currently in Phase 1 (Professional Node Operators Only). Testnet is open for testing.

### Requirements for Mainnet Validator

- **Hardware**: 32 cores, 128 GB RAM, 8 TB SSD
- **Experience**: Proven track record as validator
- **Approval**: Contact Sahara team for approval

### Testnet Validator Setup

1. **Ensure node is fully synced**:
   ```bash
   curl -s http://localhost:26657/status | jq .result.sync_info.catching_up
   ```
   Should return `false`.

2. **Get testnet tokens** from faucet (check Sahara Discord for faucet info)

3. **Create validator** (commands will be provided by Sahara team)

---

## Useful Links

- **Official Website**: https://saharaai.com
- **Documentation**: https://docs.saharaai.com
- **GitHub**: https://github.com/SaharaLabsAI
- **Discord**: Check official website for invite
- **Testnet RPC**: https://testnet-cos-rpc1.saharalabs.ai

---

## Security Best Practices

1. **Never expose admin ports** (9101, 9102) publicly
2. **Use firewall** to restrict access to RPC ports
3. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
4. **Monitor logs** regularly for suspicious activity
5. **Backup validator keys** if running validator (not applicable for full nodes)

---

## Support

For issues and questions:
- Check official Sahara documentation
- Join Sahara Discord community
- Review GitHub issues: https://github.com/SaharaLabsAI/setup-testnet-node/issues

---

**Last Updated**: 2026-04-22
**Network**: Testnet (sahara-test-1)
**Version**: 0.3.1-testnet-beta
