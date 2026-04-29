# Pharos Atlantic Testnet Node Installation Guide

## Overview

Pharos is an EVM-compatible blockchain. This guide covers installation of a full node using Docker.

## Requirements

### Minimum Hardware
- **CPU:** 32 cores, 2.8GHz+ (AMD EPYC Milan / Intel Xeon Platinum)
- **RAM:** 256 GB
- **Storage:** 5 TB SSD (350 MB/s, 30000 IOPS)
- **Network:** 0.5 Gbps
- **ulimit:** ≥ 10000000 open files

### Software
- Docker Engine 20.10+
- Docker Compose 2.0+

## Installation Steps

### 1. Create Working Directory

```bash
export WORKSPACE=pharos
mkdir -p /data/$WORKSPACE && cd /data/$WORKSPACE
```

### 2. Download Configuration Files

**For Atlantic Testnet:**

```bash
mkdir -p bin
wget -O genesis.conf https://raw.githubusercontent.com/PharosNetwork/resources/refs/heads/main/atlantic.genesis
wget -O bin/VERSION https://raw.githubusercontent.com/PharosNetwork/resources/refs/heads/main/atlantic.version
wget -O pharos.conf https://raw.githubusercontent.com/PharosNetwork/resources/refs/heads/main/conf/full.conf
```

### 3. Create docker-compose.yml

```bash
cat > docker-compose.yml <<'COMPOSE_EOF'
services:
  pharos:
    image: public.ecr.aws/k2g7b7g1/pharos:pharos_community_v0.12.2_f301031a_0422
    container_name: pharos-atlantic
    environment:
      - CONSENSUS_KEY_PWD=YOUR_SECURE_PASSWORD_HERE
      - PHAROS_CONF=/data/pharos.conf
      - GENESIS_CONF=/data/genesis.conf
      - KEYS_DIR=/data/keys
    volumes:
      - /data/pharos:/data
    ports:
      - "18100:18100"  # HTTP RPC
      - "18200:18200"  # WebSocket
      - "19000:19000"  # P2P TCP
      - "20000:20000"  # RPC
    restart: unless-stopped
    privileged: true
    healthcheck:
      test: ["CMD", "curl", "-sf", "-X", "POST", "-H", "Content-Type: application/json", "-d", "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}", "http://localhost:18100"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
COMPOSE_EOF
```

**Important:** Replace `YOUR_SECURE_PASSWORD_HERE` with a strong password.

**Note:** `privileged: true` is required for ulimit settings.

### 4. Start the Node

```bash
docker compose up -d
```

### 5. Check Node Status

**View logs:**
```bash
docker compose logs -f pharos
```

**Check sync status:**
```bash
curl -s -X POST http://localhost:18100 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | jq
```

**Check container health:**
```bash
docker compose ps
```

## Key Management

### Backup Keys (CRITICAL)

After first start, keys are generated in `/data/pharos/keys/`:
- `domain.key` — prime256v1 private key
- `domain.pub` — prime256v1 public key
- `stabilizing.key` — bls12381 private key
- `stabilizing.pub` — bls12381 public key

**Create backup immediately:**
```bash
cd /data/pharos
tar -czf ~/pharos-keys-backup-$(date +%Y%m%d).tar.gz keys/
```

**Verify backup:**
```bash
tar -tzf ~/pharos-keys-backup-*.tar.gz
```

## Becoming a Validator

Pharos Atlantic is a **permissioned testnet**. To become a validator:

1. **Run a synced full node** (this guide)
2. **Contact Pharos team:**
   - Email: janesh@dplabs.xyz
   - Telegram: @janesh_dani
3. **Provide:**
   - Your organization name
   - Server IP
   - Domain public key (`cat /data/pharos/keys/domain.pub`)
   - Stabilizing public key (`cat /data/pharos/keys/stabilizing.pub`)
4. **Wait for approval** and staking tokens from team

## Management Commands

**Stop node:**
```bash
docker compose stop
```

**Restart node:**
```bash
docker compose restart
```

**View logs:**
```bash
docker compose logs -f
```

**Update to new version:**
```bash
# Update image tag in docker-compose.yml, then:
docker compose pull
docker compose up -d
```

## Monitoring

**Check block height:**
```bash
curl -s -X POST http://localhost:18100 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  | jq -r '.result' | xargs printf '%d\n'
```

**Check peer count:**
```bash
curl -s -X POST http://localhost:18100 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}' | jq
```

## Troubleshooting

**Container won't start (ulimit error):**
- Ensure `privileged: true` is set in docker-compose.yml

**Node not syncing:**
- Check logs: `docker compose logs -f`
- Verify network connectivity
- Check P2P port 19000 is accessible

**Keys not generated:**
- Check logs for errors
- Verify CONSENSUS_KEY_PWD is set
- Ensure /data/pharos has correct permissions

## Resources

- **Official Docs:** https://docs.pharos.xyz/
- **GitHub:** https://github.com/PharosNetwork/resources
- **Website:** https://pharosnetwork.xyz/

## POSTHUMAN Services

- **RPC:** http://107.155.103.210:18100
- **WebSocket:** ws://107.155.103.210:18200
- **P2P:** 107.155.103.210:19000

---

**Installed by POSTHUMAN team on 2026-04-29**
