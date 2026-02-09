# Canton Network TestNet Validator Installation Guide

## About Canton Network

Canton Network is the first public permissionless blockchain platform designed for institutional finance, combining privacy, interoperability, and scalability.

**Key Features:**
- Privacy-preserving architecture
- Atomic cross-domain transactions
- BFT consensus
- Institutional-grade security

**Network Details:**
- Network: TestNet
- Version: 0.5.9
- Migration ID: 1
- Purpose: Pre-production testing

## Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 250 GB NVMe |
| Network | 100 Mbps | 1 Gbps |

### Software

- Docker 20.10+
- Docker Compose 2.0+
- curl, jq

⚠️ **Important:** Unique IP required (cannot be shared with DevNet or MainNet)

## Onboarding Process

### 1. Submit Validator Form

Fill out the validator request form with corporate email (not Gmail/free email):
https://sync.global/validator-request/

### 2. IP Whitelist

1. Contact SV sponsor in Slack
2. Provide your dedicated IP address for TestNet
3. Wait 2-7 days for approval (2/3 Super Validators must approve)

### 3. Verify IP Whitelist

```bash
bash -c 'CURL="curl -fsS -m 5 --connect-timeout 5"
for url in $($CURL https://scan.sv-1.test.global.canton.network.sync.global/api/scan/v0/scans | jq -r ".scans[].scans[].publicUrl"); do
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
curl -s https://docs.test.global.canton.network.sync.global/info | jq '.'
```

#### 3. Download Canton Node

```bash
VERSION="0.5.9"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator
```

#### 4. Start Validator

```bash
cd ~/.canton/0.5.9/splice-node/docker-compose/validator

# Enable unsafe auth (if needed for scripts/monitoring)
# echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env

export IMAGE_TAG=0.5.9

./start.sh \
  -s "https://sv.sv-1.test.global.canton.network.sync.global" \
  -o "YOUR_ONBOARDING_SECRET_FROM_SV" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "1" \
  -w
```

Parameters:
- `-s` - Sponsor SV URL
- `-o` - Onboarding secret from SV sponsor (use `""` after first start)
- `-p` - Party hint (validator name)
- `-m` - Migration ID (1 for TestNet)
- `-w` - Enable wallet

> ⚠️ **If sv-1 is unavailable**, use sv-2:
> ```bash
> ./start.sh \
>   -s "https://sv.sv-2.test.global.canton.network.sync.global" \
>   -c "https://scan.sv-2.test.global.canton.network.sync.global" \
>   -o "YOUR_ONBOARDING_SECRET_FROM_SV" -p "YOUR_VALIDATOR_NAME" -m "1" -w
> ```

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
cat >> .env << 'EOF'
COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
EOF

# Restart validator
./stop.sh && ./start.sh ...
```

> ⚠️ Even with `compose-disable-auth.yaml`, Wallet UI validates `AUTH_URL` and `NETWORK_FAVICON_URL` as URLs. Empty/missing values cause a Zod validation error.

## Management

### Stop

```bash
cd ~/.canton/0.5.9/splice-node/docker-compose/validator
./stop.sh
```

### Restart

```bash
cd ~/.canton/0.5.9/splice-node/docker-compose/validator
export IMAGE_TAG=0.5.9

./start.sh \
  -s "https://sv.sv-1.test.global.canton.network.sync.global" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "1" \
  -w
```

### View Logs

```bash
cd ~/.canton/0.5.9/splice-node/docker-compose/validator

# All containers
docker compose logs -f

# Validator only
docker compose logs -f validator

# Last 100 lines
docker logs splice-validator-validator-1 --tail 100
```

## Backup & Recovery

### Backup Database

```bash
# Create PostgreSQL dump
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator \
  > ~/canton_testnet_backup_$(date +%Y%m%d).sql

# Or backup entire volume
docker run --rm -v splice-validator_postgres-splice:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/testnet_postgres_$(date +%Y%m%d).tar.gz /data
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
cat > /root/canton_testnet_monitor.sh << 'SCRIPT'
#!/bin/bash
BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"

MONIKER="CANTON - POSTHUMAN-TestNet-Validator"

if ! docker ps --format '{{.Names}} {{.Status}}' | grep -q 'splice-validator-validator.*healthy'; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d text="🔴 ${MONIKER} DOWN - $(hostname)"
fi
SCRIPT

chmod +x /root/canton_testnet_monitor.sh

# Add to cron (every 5 minutes)
(crontab -l; echo "*/5 * * * * /root/canton_testnet_monitor.sh") | crontab -
```

## Security

### Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 22/tcp      # SSH
ufw allow 443/tcp     # HTTPS
# Allow Docker network internal communication
ufw insert 1 allow out to 172.19.0.0/16
ufw enable
```

### Restrict Web UI Access

By default, wallet UI is publicly accessible. Secure it:

**Step 1:** Bind to localhost only (in compose.yaml nginx ports):
```
ports:
  - "127.0.0.1:8888:80"
```

**Step 2:** Nginx uses virtual hosts + basic auth. Access via:

1. `/etc/hosts` on local machine: `127.0.0.1 wallet.localhost ans.localhost`
2. SSH tunnel: `ssh -L 8888:127.0.0.1:8888 user@validator_ip -N`
3. Open `http://wallet.localhost:8888`, enter basic auth credentials

## Useful Links

- **TestNet Explorer:** https://lighthouse.testnet.cantonloop.com/
- **Documentation:** https://docs.sync.global/
- **GitHub:** https://github.com/digital-asset/decentralized-canton-sync
- **Validator Form:** https://sync.global/validator-request/
- **Network Status:** https://sync.global/sv-network/

## Troubleshooting

### IP Whitelist Issues

```bash
# Verify your IP is whitelisted
curl -s https://scan.sv-1.test.global.canton.network.sync.global/api/scan/version

# Should return version number, not error
```

### Onboarding Secret Expired

Contact your SV sponsor in Slack to get a new secret (48h validity).

### Container Restarts

```bash
# Check logs for errors
docker logs splice-validator-validator-1 --tail 100

# Common issues:
# 1. Wrong migration_id
# 2. Expired onboarding secret
# 3. IP not whitelisted
```

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
