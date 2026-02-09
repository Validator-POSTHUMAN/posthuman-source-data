# Canton Network MainNet Validator Installation Guide

## About Canton Network

Canton Network is the first public permissionless blockchain platform designed for institutional finance, combining privacy, interoperability, and scalability.

**Key Features:**
- Privacy-preserving architecture
- Atomic cross-domain transactions
- BFT consensus
- Institutional-grade security

**Network Details:**
- Network: MainNet
- Version: 0.5.8
- Migration ID: 4
- Purpose: Production network

**Participants:**
Goldman Sachs, Deutsche Börse, BNP Paribas, Microsoft, Moody's, S&P Global, Digital Asset, and other institutional players.

## Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16 cores |
| RAM | 16 GB | 32 GB |
| Storage | 250 GB NVMe | 500 GB NVMe |
| Network | 1 Gbps | 10 Gbps |

### Software

- Docker 20.10+
- Docker Compose 2.0+
- curl, jq

⚠️ **Important:** 
- Unique dedicated IP required (cannot be shared with DevNet or TestNet)
- Corporate email required for validator application
- ~2 weeks approval process by Tokenomics Committee

## Onboarding Process

### 1. Submit Validator Form

Fill out the validator request form:
https://sync.global/validator-request/

Requirements:
- Corporate email (not Gmail/Yahoo/etc.)
- Company information
- Dedicated IP address for MainNet

Expected approval time: ~2 weeks

### 2. IP Whitelist

1. After approval, contact SV sponsor in Slack
2. Provide your dedicated IP address for MainNet
3. Wait 2-7 days for whitelisting (2/3 Super Validators must approve)

### 3. Verify IP Whitelist

```bash
bash -c 'CURL="curl -fsS -m 5 --connect-timeout 5"
for url in $($CURL https://scan.sv-1.global.canton.network.sync.global/api/scan/v0/scans | jq -r ".scans[].scans[].publicUrl"); do
  echo -n "$url: "
  $CURL "$url"/api/scan/version | jq -r ".version" 2>&1 || echo "TIMEOUT"
done'
```

All SVs should respond with version (not TIMEOUT) = IP is whitelisted ✅

### 4. Get Onboarding Secret

Request from your SV sponsor in Slack (valid for 48 hours).

## Installation

### Step-by-Step Installation

#### 1. System Preparation

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y curl iptables build-essential git wget jq make gcc \
  nano tmux htop pkg-config libssl-dev tar clang ncdu unzip

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt update && apt install -y docker-ce
docker --version

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

#### 2. Check Network Status

```bash
# Get current version and migration ID
curl -s https://docs.global.canton.network.sync.global/info | jq '.'
```

#### 3. Download Canton Node

```bash
VERSION="0.5.8"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator
```

#### 4. Start Validator

```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator

# Enable unsafe auth (if needed for scripts/monitoring)
# echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env

export IMAGE_TAG=0.5.8

./start.sh \
  -s "https://sv.sv-1.global.canton.network.sync.global" \
  -o "YOUR_ONBOARDING_SECRET_FROM_SV" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w
```

Parameters:
- `-s` - Sponsor SV URL
- `-o` - Onboarding secret from SV sponsor (use `""` after first start)
- `-p` - Party hint (validator name)
- `-m` - Migration ID (3 for MainNet)
- `-w` - Enable wallet

#### 5. Check Status

```bash
# Container status
docker ps --filter "name=splice-validator"

# Logs
docker logs splice-validator-validator-1 -f --tail 100

# Health check
docker ps --filter "name=splice-validator-validator" --format "{{.Names}}: {{.Status}}"
# Should show: Up X minutes (healthy)
```

### Unsafe Auth Mode (Optional)

If you need to disable authentication for local scripts or monitoring (NOT recommended for production exposed ports):

```bash
# Add override file to .env
echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env

# Restart validator
./stop.sh && ./start.sh ...
```

## Management

### Stop

```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator
./stop.sh
```

### Restart

```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator
export IMAGE_TAG=0.5.8

./start.sh \
  -s "https://sv.sv-1.global.canton.network.sync.global" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w
```

### View Logs

```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator

# All containers
docker compose logs -f

# Validator only
docker compose logs -f validator

# Last 100 lines
docker logs splice-validator-validator-1 --tail 100
```

## Upgrade

⚠️ **Important:** Always backup before upgrading!

### Process

```bash
# 1. Check new version
curl -s https://docs.global.canton.network.sync.global/info | jq '.sv.version'

# 2. Stop current node
cd ~/.canton/0.5.8/splice-node/docker-compose/validator
./stop.sh

# 3. Backup database
docker run --rm -v splice-validator_postgres-splice:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mainnet_backup_$(date +%Y%m%d).tar.gz /data

# 4. Download new version
NEW_VERSION="0.5.7"  # example
mkdir -p ~/.canton/${NEW_VERSION}
cd ~/.canton/${NEW_VERSION}
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${NEW_VERSION}/${NEW_VERSION}_splice-node.tar.gz
tar xzf ${NEW_VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator

# 5. Start with new version
export IMAGE_TAG=${NEW_VERSION}
./start.sh \
  -s "https://sv.sv-1.global.canton.network.sync.global" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w

# 6. Check logs
docker compose logs -f validator
```

## Backup & Recovery

### Backup Identity

```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator

# Get token
TOKEN=$(python3 get-token.py administrator)

# Create backup
curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_mainnet_identity_$(date +%Y%m%d).json
```

### Backup Database

```bash
# PostgreSQL dump
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator \
  > ~/canton_mainnet_db_$(date +%Y%m%d).sql

# Full volume backup
docker run --rm -v splice-validator_postgres-splice:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mainnet_postgres_$(date +%Y%m%d).tar.gz /data
```

### Automated Backups (Cron)

```bash
cat > /root/canton_mainnet_backup.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="/root/canton_mainnet_backups"
mkdir -p ${BACKUP_DIR}
DATE=$(date +%Y%m%d_%H%M%S)

# DB backup
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator \
  > ${BACKUP_DIR}/mainnet_db_${DATE}.sql

# Compress and upload to remote storage (S3/backup server)
gzip ${BACKUP_DIR}/mainnet_db_${DATE}.sql

# Remove old backups (>7 days)
find ${BACKUP_DIR} -name "mainnet_db_*.sql.gz" -mtime +7 -delete
SCRIPT

chmod +x /root/canton_mainnet_backup.sh

# Add to cron (every 6 hours)
(crontab -l; echo "0 */6 * * * /root/canton_mainnet_backup.sh") | crontab -
```

## Monitoring

### Prometheus Metrics

Canton exports metrics on port **10013**:

```bash
docker exec splice-validator-validator-1 curl -s http://localhost:10013/metrics | head -20
```

### Alerting

Set up monitoring alerts for:
- Container health status
- Database availability
- Disk space usage
- Network connectivity
- Sync status

Example Telegram alert:

```bash
cat > /root/canton_mainnet_monitor.sh << 'SCRIPT'
#!/bin/bash
BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"

MONIKER="CANTON - POSTHUMAN-MainNet-Validator"

if ! docker ps --format '{{.Names}} {{.Status}}' | grep -q 'splice-validator-validator.*healthy'; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d text="🔴 ${MONIKER} DOWN - $(hostname)"
fi
SCRIPT

chmod +x /root/canton_mainnet_monitor.sh

# Add to cron (every 5 minutes)
(crontab -l; echo "*/5 * * * * /root/canton_mainnet_monitor.sh") | crontab -
```

## Security

### Essential Security Measures

1. **Firewall Configuration**
```bash
# Allow only necessary ports
ufw allow 22/tcp      # SSH
ufw allow 443/tcp     # HTTPS
# Allow Docker network internal communication
ufw insert 1 allow out to 172.19.0.0/16
ufw enable
```

2. **Restrict Web UI Access**

Change to localhost-only:
```bash
cd ~/.canton/0.5.8/splice-node/docker-compose/validator
nano compose.yaml

# Change nginx ports (localhost only, port 8888):
ports:
  - "127.0.0.1:8888:80"
```

3. **SSH Tunnel for UI Access**
```bash
# From local machine
ssh -L 8888:127.0.0.1:8888 user@validator_ip -N

# Access via: http://localhost:8888
```

4. **Regular Updates**
- Monitor Canton Network announcements
- Apply security patches promptly
- Test upgrades on TestNet first

5. **Access Control**
- Use SSH keys (disable password auth)
- Implement fail2ban
- Regular security audits

## Rewards

Validators earn Canton Coin (CC) for:
- Node uptime and liveness
- Traffic generation
- Featured app participation

Check balance: http://localhost:8888 (wallet UI)

## Useful Links

- **MainNet Explorer:** https://lighthouse.cantonloop.com/
- **Documentation:** https://docs.sync.global/
- **GitHub:** https://github.com/digital-asset/decentralized-canton-sync
- **WhitePaper:** https://www.canton.network/whitepaper
- **Canton Foundation:** https://canton.foundation/
- **Validator Form:** https://sync.global/validator-request/
- **Network Status:** https://sync.global/sv-network/

## Troubleshooting

### IP Whitelist Verification Failed

```bash
# Check if your IP can reach SV endpoints
curl -s https://scan.sv-1.global.canton.network.sync.global/api/scan/version

# Should return version, not error/timeout
```

### Onboarding Secret Issues

- Secret expired? Request new one from SV sponsor
- Invalid secret? Double-check the string (48h validity)

### Container Health Issues

```bash
# Detailed logs
docker logs splice-validator-validator-1 --tail 200

# Check resource usage
docker stats splice-validator-validator-1

# Verify network connectivity
docker exec splice-validator-validator-1 ping -c 3 sv.sv-1.global.canton.network.sync.global
```

### Database Issues

```bash
# Check PostgreSQL status
docker exec splice-validator-postgres-splice-1 psql -U cnadmin -d validator -c "SELECT version();"

# Check disk space
df -h
```

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
