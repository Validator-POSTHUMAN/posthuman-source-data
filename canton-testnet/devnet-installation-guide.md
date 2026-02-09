# Canton Network DevNet Validator Installation Guide

## About Canton Network

Canton Network is the first public permissionless blockchain platform designed for institutional finance, combining privacy, interoperability, and scalability.

**Key Features:**
- Privacy-preserving architecture
- Atomic cross-domain transactions
- BFT consensus
- Institutional-grade security

**Network Details:**
- Network: DevNet
- Version: 0.5.10
- Migration ID: 1
- Purpose: Testing and development

## Requirements

### Hardware

| Component | Minimum      | Recommended  |
|-----------|--------------|--------------|
| CPU       | 4 cores      | 8 cores      |
| RAM       | 8 GB         | 16 GB        |
| Storage   | 100 GB SSD   | 250 GB NVMe  |
| Network   | 100 Mbps     | 1 Gbps       |

### Software

- Docker 20.10+
- Docker Compose 2.0+
- curl, jq

## Installation

### One-liner Installation

```bash
# Install dependencies
sudo apt update && sudo apt install -y curl jq docker.io docker-compose

# Check current network version
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.'

# Create directory
VERSION="0.5.10"
MIGRATION_ID="1"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

# Download release
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator

# Get onboarding secret (valid for 1 hour)
SECRET=$(curl -X POST https://sv.sv-1.dev.global.canton.network.sync.global/api/sv/v0/devnet/onboard/validator/prepare)

# Start validator
# Enable unsafe auth (if needed for scripts/monitoring)
# echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env

export IMAGE_TAG=${VERSION}
./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "${SECRET}" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "${MIGRATION_ID}" \
  -w
```

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

#### 2. Check Network Status & IP

```bash
# Get current version and migration ID
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.'

# Verify IP connectivity (whitelist check)
curl -s -m 5 https://scan.sv-1.dev.global.canton.network.sync.global/api/scan/version
# Should return version (e.g. {"version":"0.5.10"...}), NOT timeout
```

#### 3. Download Canton Node

```bash
VERSION="0.5.10"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator
```

#### 4. Get Onboarding Secret

DevNet onboarding secret (auto-generated, valid for 1 hour):
```bash
curl -X POST https://sv.sv-1.dev.global.canton.network.sync.global/api/sv/v0/devnet/onboard/validator/prepare
```

#### 5. Start Validator

```bash
cd ~/.canton/0.5.10/splice-node/docker-compose/validator

# Enable unsafe auth (if needed for scripts/monitoring)
# echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env

export IMAGE_TAG=0.5.10

./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "YOUR_ONBOARDING_SECRET" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "1" \
  -w
```

Parameters:
- `-s` - Sponsor SV URL
- `-o` - Onboarding secret (use `""` after first start)
- `-p` - Party hint (validator name)
- `-m` - Migration ID
- `-w` - Enable wallet

> ⚠️ **If sv-1 is unavailable**, use sv-2:
> ```bash
> ./start.sh \
>   -s "https://sv.sv-2.dev.global.canton.network.sync.global" \
>   -c "https://scan.sv-2.dev.global.canton.network.sync.global" \
>   -o "${SECRET}" -p "YOUR_VALIDATOR_NAME" -m "1" -w
> ```

#### 6. Check Status

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

```bash
cat >> .env << 'EOF'
COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
EOF
```

> ⚠️ Even with `compose-disable-auth.yaml`, Wallet UI validates `AUTH_URL` and `NETWORK_FAVICON_URL` as URLs. Empty/missing values cause a Zod validation error.

### Wallet UI Access

Nginx uses virtual hosts + basic auth:

1. `/etc/hosts` on local machine: `127.0.0.1 wallet.localhost ans.localhost`
2. SSH tunnel: `ssh -L 8888:127.0.0.1:8888 user@validator_ip -N`
3. Open `http://wallet.localhost:8888`, enter basic auth credentials

## Management

### Stop

```bash
cd ~/.canton/0.5.10/splice-node/docker-compose/validator
./stop.sh
```

### Restart

```bash
cd ~/.canton/0.5.10/splice-node/docker-compose/validator
export IMAGE_TAG=0.5.10

./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "1" \
  -w
```

### View Logs

```bash
cd ~/.canton/0.5.10/splice-node/docker-compose/validator

# All containers
docker compose logs -f

# Validator only
docker compose logs -f validator

# Last 100 lines
docker logs splice-validator-validator-1 --tail 100
```

## Monitoring

### Prometheus Metrics

Canton exports metrics on port **10013** (Prometheus format):

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
cat > /root/canton_devnet_monitor.sh << 'SCRIPT'
#!/bin/bash
BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"

MONIKER="CANTON - POSTHUMAN-DevNet-Validator"

if ! docker ps --format '{{.Names}} {{.Status}}' | grep -q 'splice-validator-validator.*healthy'; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d text="🔴 ${MONIKER} DOWN - $(hostname)"
fi
SCRIPT

chmod +x /root/canton_devnet_monitor.sh

# Add to cron (every 5 minutes)
(crontab -l; echo "*/5 * * * * /root/canton_devnet_monitor.sh") | crontab -
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

**Option 1:** Change to localhost-only

```bash
cd ~/.canton/0.5.10/splice-node/docker-compose/validator
nano compose.yaml

# Find and change (use port 8888 to avoid conflicts):
ports:
  - "127.0.0.1:8888:80"  # instead of "80:80"
```

**Option 2:** SSH tunnel access

```bash
# From local machine
ssh -L 8888:127.0.0.1:8888 user@validator_ip -N

# Then open in browser
http://localhost:8888
```

## Useful Links

- **DevNet Explorer:** https://lighthouse.devnet.cantonloop.com/
- **Documentation:** https://docs.dev.sync.global/
- **GitHub:** https://github.com/digital-asset/decentralized-canton-sync
- **Validator Form:** https://sync.global/validator-request/

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
