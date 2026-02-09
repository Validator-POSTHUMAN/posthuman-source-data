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

Note the `version` and `migration_id` from the output — you will need them below.

#### 3. Download Canton Node

```bash
# Use the version from step 2
VERSION="0.5.8"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator
```

#### 4. Start Validator

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator

export IMAGE_TAG=${VERSION}

./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "YOUR_ONBOARDING_SECRET_FROM_SV" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w
```

> ⚠️ **If sv-2 is unavailable**, try other SVs or specify scan separately with `-c`:
> ```bash
> ./start.sh \
>   -s "https://sv.sv-1.global.canton.network.digitalasset.com" \
>   -c "https://scan.sv-2.global.canton.network.digitalasset.com" \
>   -o "YOUR_ONBOARDING_SECRET_FROM_SV" \
>   -p "YOUR_VALIDATOR_NAME" \
>   -m "4" \
>   -w
> ```

Parameters:
- `-s` - Sponsor SV URL (try sv-2 first; sv-1 can be unstable)
- `-c` - Scan address (optional, use if SV scan is down but another SV's scan works)
- `-o` - Onboarding secret from SV sponsor (use `""` after first start)
- `-p` - Party hint (validator name)
- `-m` - Migration ID (4 for MainNet)
- `-w` - Enable wallet

> ⚠️ **SV Fallback:** If sv-2 is unavailable, try other SVs:
> - `https://sv.sv-1.global.canton.network.digitalasset.com`
> - `https://sv.sv-2.global.canton.network.digitalasset.com`
> - `https://sv.sv-1.global.canton.network.sync.global`
>
> You can also specify the scan address separately with `-c` flag if the SV endpoint works but its scan is down:
> ```bash
> ./start.sh \
>   -s "https://sv.sv-1.global.canton.network.digitalasset.com" \
>   -c "https://scan.sv-2.global.canton.network.digitalasset.com" \
>   -o "" -p "YOUR_VALIDATOR_NAME" -m "4" -w
> ```
>
> Check SV health before starting:
> ```bash
> curl -s --max-time 5 "https://scan.sv-2.global.canton.network.digitalasset.com/api/scan/v0/splice-instance-names"
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

### Unsafe Auth Mode (Disable Authentication)

If you need to disable authentication for local access (e.g. scripts, monitoring):

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator
```

**1. Add compose override to `.env`:**
```bash
echo "COMPOSE_FILE=compose.yaml:compose-disable-auth.yaml" >> .env
```

**2. Set required environment variables in `.env`:**

Even with auth disabled, the Wallet UI **requires valid URLs** in its config — otherwise you get a Zod validation error (`Invalid url` for `auth.authority` / `networkFaviconUrl`).

Add these to `.env`:
```bash
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
```

**3. Restart:**
```bash
./stop.sh && ./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "" -p "YOUR_VALIDATOR_NAME" -m "4" -w
```

> ⚠️ Without valid `AUTH_URL` and `SPLICE_APP_UI_NETWORK_FAVICON_URL`, the Wallet UI will crash with:
> ```
> Error when parsing config: ZodError — Invalid url for auth.authority / networkFaviconUrl
> ```

## Accessing Wallet UI

The nginx proxy binds to `127.0.0.1:8888` (localhost only, not exposed externally).

Nginx uses **virtual hosts** and **basic auth** (`.htpasswd`). You cannot access it by IP — you need the correct `Host` header.

### 1. Set up SSH tunnel (from your local machine)

```bash
ssh -L 8888:127.0.0.1:8888 user@YOUR_SERVER_IP -N
```

### 2. Add to `/etc/hosts` on your local machine

```
127.0.0.1 wallet.localhost ans.localhost
```

### 3. Open in browser

- Wallet: `http://wallet.localhost:8888`
- ANS: `http://ans.localhost:8888`

The browser will prompt for basic auth credentials (login/password from `.htpasswd`).

### Setting up `.htpasswd`

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator/nginx

# Install htpasswd utility
apt install -y apache2-utils

# Create credentials
htpasswd -c .htpasswd YOUR_USERNAME
```

## Management

### Stop

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator
./stop.sh
```

### Restart

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator
export IMAGE_TAG=${VERSION}

./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w
```

### View Logs

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator

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
curl -s https://docs.global.canton.network.sync.global/info | jq '.'

# 2. Stop current node
cd ~/.canton/${CURRENT_VERSION}/splice-node/docker-compose/validator
./stop.sh

# 3. Backup database
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator | gzip > ~/mainnet_backup_$(date +%Y%m%d).sql.gz

# 4. Download new version
NEW_VERSION="X.Y.Z"  # from step 1
mkdir -p ~/.canton/${NEW_VERSION}
cd ~/.canton/${NEW_VERSION}
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${NEW_VERSION}/${NEW_VERSION}_splice-node.tar.gz
tar xzf ${NEW_VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator

# 5. Copy your .env (adjust if needed)
cp ~/.canton/${CURRENT_VERSION}/splice-node/docker-compose/validator/.env .env

# 6. Start with new version
export IMAGE_TAG=${NEW_VERSION}
./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "4" \
  -w

# 7. Check logs
docker compose logs -f validator
```

## Backup & Recovery

### Backup Identity

```bash
cd ~/.canton/${VERSION}/splice-node/docker-compose/validator

# Get token
TOKEN=$(python3 get-token.py administrator)

# Create backup
curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_mainnet_identity_$(date +%Y%m%d).json
```

### Backup Database

```bash
# PostgreSQL dump (compressed)
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator | gzip > ~/canton_mainnet_db_$(date +%Y%m%d).sql.gz

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
  | gzip > ${BACKUP_DIR}/mainnet_db_${DATE}.sql.gz

# Remove old backups (>7 days)
find ${BACKUP_DIR} -name "mainnet_db_*.sql.gz" -mtime +7 -delete
SCRIPT

chmod +x /root/canton_mainnet_backup.sh

# Add to cron (every 6 hours)
(crontab -l 2>/dev/null; echo "0 */6 * * * /root/canton_mainnet_backup.sh") | crontab -
```

## Monitoring

### Prometheus Metrics

Canton exports metrics on port **10013**:

```bash
docker exec splice-validator-validator-1 curl -s http://localhost:10013/metrics | head -20
```

### Alerting

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
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/canton_mainnet_monitor.sh") | crontab -
```

## Security

### Essential Security Measures

1. **Firewall Configuration**
```bash
ufw allow 22/tcp      # SSH
ufw allow 443/tcp     # HTTPS
ufw insert 1 allow out to 172.19.0.0/16  # Docker internal
ufw enable
```

2. **Wallet UI is localhost-only by default** — nginx binds to `127.0.0.1:8888`. Access via SSH tunnel only.

3. **SSH Tunnel for UI Access**

The Wallet UI nginx uses virtual hosts. You need to access it via `wallet.localhost` (not `127.0.0.1`):

```bash
# From local machine — forward port
ssh -L 8888:127.0.0.1:8888 user@validator_ip -N
```

Add to `/etc/hosts` on your **local machine** (where the browser runs):
```
127.0.0.1 wallet.localhost ans.localhost
```

Then open in browser:
- Wallet: `http://wallet.localhost:8888` (will ask for basic auth login/password from `.htpasswd`)
- ANS: `http://ans.localhost:8888`

4. **Recommendations**
- Use SSH keys (disable password auth)
- Implement fail2ban
- Store secrets (onboarding secret, bot token, DB password) outside of plain `.env` where possible
- Rotate credentials if exposed

## Rewards

Validators earn Canton Coin (CC) for:
- Node uptime and liveness
- Traffic generation
- Featured app participation

Check balance: `http://wallet.localhost:8888` (via SSH tunnel)

## Useful Links

- **MainNet Explorer:** https://lighthouse.cantonloop.com/
- **Documentation:** https://docs.sync.global/
- **GitHub:** https://github.com/digital-asset/decentralized-canton-sync
- **WhitePaper:** https://www.canton.network/whitepaper
- **Canton Foundation:** https://canton.foundation/
- **Validator Form:** https://sync.global/validator-request/
- **Network Status:** https://sync.global/sv-network/

## Troubleshooting

### `503` / Failed to fetch `splice_instance_names`

The SV endpoint is down. Try a different SV:

```bash
# Check which SVs are alive
for i in 1 2; do
  echo -n "sv-$i digitalasset.com: "
  curl -s --max-time 5 "https://scan.sv-$i.global.canton.network.digitalasset.com/api/scan/version" 2>&1 || echo "DOWN"
done
```

Use a working SV with `-s` flag, or specify scan separately with `-c`:
```bash
./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -c "https://scan.sv-2.global.canton.network.digitalasset.com" \
  -o "" -p "YOUR_VALIDATOR_NAME" -m "4" -w
```

### Zod Validation Error (Wallet UI)

```
Error when parsing config: ZodError — Invalid url for auth.authority / networkFaviconUrl
```

**Cause:** Empty or missing `AUTH_URL` / `SPLICE_APP_UI_NETWORK_FAVICON_URL` in `.env` when using `compose-disable-auth.yaml`.

**Fix:** Add valid values to `.env`:
```bash
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
```

Then restart.

### 401 Authorization Required (Wallet UI)

**Cause:** Nginx uses virtual hosts. Accessing by IP (`127.0.0.1:8888`) without the correct `Host` header hits basic auth.

**Fix:** Add `127.0.0.1 wallet.localhost` to `/etc/hosts` on your local machine and access via `http://wallet.localhost:8888`.

### IP Whitelist Verification Failed

```bash
curl -s https://scan.sv-1.global.canton.network.sync.global/api/scan/version
# Should return version, not error/timeout
```

### Container Health Issues

```bash
docker logs splice-validator-validator-1 --tail 200
docker stats splice-validator-validator-1
```

### Database Issues

```bash
docker exec splice-validator-postgres-splice-1 psql -U cnadmin -d validator -c "SELECT version();"
df -h
```

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital