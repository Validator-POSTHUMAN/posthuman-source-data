# Monad Testnet Validator Node Installation Guide

## About Monad

Monad is a high-performance EVM-compatible Layer 1 blockchain featuring parallel execution, MonadBFT consensus, and 400ms block times. It achieves 500M gas/sec throughput while maintaining full Ethereum compatibility.

**Testnet Details:**

| Parameter | Value |
|-----------|-------|
| Network | Monad Testnet |
| Chain ID | `10143` |
| Currency | `MON` |
| Block Time | 400ms |
| Block Gas Limit | 200M |
| Explorer | See [official docs](https://docs.monad.xyz/developer-essentials/testnets) |

---

## Architecture Overview

Monad nodes run as `systemd` services:

| Service | Description |
|---------|-------------|
| `monad-bft` | Consensus client |
| `monad-execution` | Execution client |
| `monad-rpc` | RPC server |
| `monad-mpt` | One-time TrieDB disk initialization |
| `monad-cruft` | Hourly artifact cleanup service |
| `otelcol` | OTEL metrics collector |

All services run under the `monad` system user.

**Data layout:**

| Path | Description |
|------|-------------|
| `/home/monad/.env` | Environment variables for monad services |
| `/home/monad/monad-bft/config/node.toml` | Consensus configuration |
| `/home/monad/monad-bft/config/forkpoint/` | Quorum checkpoints |
| `/home/monad/monad-bft/config/validators/` | Validator set files |
| `/home/monad/monad-bft/ledger/` | Block headers and bodies |
| `/dev/triedb` | TrieDB raw device (blockchain state) |

---

## Requirements

### Hardware

> ⚠️ **Bare metal only** — Cloud / VMs (AWS, GCP, Azure) are **not supported**. Monad's consensus enforces sub-second timing windows; virtualization introduces latency that causes missed deadlines and sync failures.

| Component | Requirement |
|-----------|-------------|
| CPU | 16 cores, 4.5 GHz+ base clock (AMD Ryzen 9950x / 7950x / EPYC 4584PX recommended) |
| RAM | 32 GB minimum, 64 GB recommended |
| Storage — TrieDB | 2 TB NVMe SSD (dedicated, **no filesystem**) |
| Storage — OS / BFT | 500 GB+ NVMe SSD |
| NVMe Grade | PCIe Gen4x4 or better |
| Bandwidth | 300 Mbit/s (validators) / 100 Mbit/s (full nodes) |
| OS | Ubuntu 24.04+ |
| Kernel | >= 6.8.0.60 |

> ⚠️ **HyperThreading / SMT must be disabled in BIOS** — it degrades node performance.

> ⚠️ Linux kernel `v6.8.0.56` through `v6.8.0.59` has a known bug that causes Monad clients to hang. Use `v6.8.0.60` or higher.

**SSD Performance Tiers (from Monad internal testing):**

| Tier | Model | Notes |
|------|-------|-------|
| ✅ Top | Samsung 980 / 990 Pro | PCIe 4.0, best performance |
| ✅ Good | Samsung PM9A1 | PCIe 4.0, stable under load |
| ⚠️ OK | Micron 7450 | PCIe 4.0, random slowdowns under heavy load |
| ❌ Avoid | Nextorage SSDs | Overheat and become unresponsive, requiring reboot |

### Disk Layout

- **Disk 1** — OS + ledger data (`/home/monad/monad-bft/`)
- **Disk 2** — TrieDB raw device (`/dev/triedb`) — **no filesystem**, accessed directly by Monad

---

## Installation

> All commands below assume you are running as `root`. If not, prefix with `sudo`.

### Step 1 — Update System

````bash
apt update
apt upgrade -y
````

Reboot if the upgrade prints `Pending kernel upgrade!`.

Install dependencies:

````bash
apt install -y curl nvme-cli aria2 jq
````

### Step 2 — Install Monad Package

Configure the Category Labs APT repository:

````bash
cat <<EOF > /etc/apt/sources.list.d/category-labs.sources
Types: deb
URIs: https://pkg.category.xyz/
Suites: noble
Components: main
Signed-By: /etc/apt/keyrings/category-labs.gpg
EOF

mkdir -p /etc/apt/keyrings
curl -fsSL https://pkg.category.xyz/keys/public-key.asc \
  | gpg --dearmor --yes -o /etc/apt/keyrings/category-labs.gpg
````

Install and pin the package:

````bash
apt update
apt install -y monad
apt-mark hold monad
````

> 📌 To install a specific version: `apt install -y monad=<VERSION>`

Verify:

````bash
monad-node --version
````

### Step 3 — Create Monad User

````bash
useradd -m -s /bin/bash monad

mkdir -p /home/monad/monad-bft/config \
         /home/monad/monad-bft/ledger \
         /home/monad/monad-bft/config/forkpoint \
         /home/monad/monad-bft/config/validators
````

### Step 4 — Configure TrieDB Device

Identify the **second NVMe drive** (the one with **no mountpoints**):

````bash
nvme list
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL
````

> ⚠️ **Double-check which drive to use! Formatting the wrong drive will destroy your OS!**

Look for a drive with **no mountpoints**. Your OS drive will show `/`, `/boot`, or swap partitions.

Set up the partition:

````bash
TRIEDB_DRIVE=/dev/nvme1n1  # ← CHANGE THIS TO YOUR DRIVE

parted $TRIEDB_DRIVE mklabel gpt
parted $TRIEDB_DRIVE mkpart triedb 0% 100%
````

Create udev rule for `/dev/triedb` symlink:

````bash
PARTUUID=$(lsblk -o PARTUUID $TRIEDB_DRIVE | tail -n 1)
echo "Disk PartUUID: ${PARTUUID}"

echo "ENV{ID_PART_ENTRY_UUID}==\"$PARTUUID\", MODE=\"0666\", SYMLINK+=\"triedb\"" \
  | tee /etc/udev/rules.d/99-triedb.rules

udevadm trigger
udevadm control --reload
udevadm settle
ls -l /dev/triedb
````

#### Verify LBA Configuration

````bash
nvme id-ns -H $TRIEDB_DRIVE | grep 'LBA Format' | grep 'in use'
````

Expected output: `Data Size: 512 bytes` marked as `(in use)`.

If not 512 bytes:

````bash
nvme format --lbaf=0 $TRIEDB_DRIVE
````

#### Format the TrieDB Partition

````bash
systemctl start monad-mpt
journalctl -u monad-mpt -n 14 -o cat --no-pager
````

Expected output should show MPT database info with capacity, `Deactivated successfully`, and `Finished monad-mpt.service`.

### Step 5 — Configure Firewall

````bash
ufw allow ssh
ufw allow 8000
ufw allow 8001
ufw enable
ufw status
````

Anti-spam rule for UDP:

````bash
iptables -I INPUT -p udp --dport 8000 -m length --length 0:1400 -j DROP
````

Persist iptables rules:

````bash
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt install -y iptables-persistent
````

Verify outbound connectivity:

````bash
nc -vz 64.31.29.190 8000
# Expected: Connection to 64.31.29.190 8000 port [tcp/*] succeeded!
````

### Step 6 — Install OTEL Collector

````bash
OTEL_VERSION="0.139.0"
OTEL_PACKAGE="https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTEL_VERSION}/otelcol_${OTEL_VERSION}_linux_amd64.deb"

curl -fsSL "$OTEL_PACKAGE" -o /tmp/otelcol_linux_amd64.deb
dpkg -i /tmp/otelcol_linux_amd64.deb

cp /opt/monad/scripts/otel-config.yaml /etc/otelcol/config.yaml
systemctl restart otelcol
````

Metrics available at `http://0.0.0.0:8889/metrics`.

---

## Configuration

### Step 7 — Download Configuration Files

Choose your node role (**Full Node** or **Validator**):

#### Full Node

````bash
MF_BUCKET=https://bucket.monadinfra.com
curl -o /home/monad/.env $MF_BUCKET/config/testnet/latest/.env.example
curl -o /home/monad/monad-bft/config/node.toml $MF_BUCKET/config/testnet/latest/full-node-node.toml
````

#### Validator

````bash
MF_BUCKET=https://bucket.monadinfra.com
curl -o /home/monad/.env $MF_BUCKET/config/testnet/latest/.env.example
curl -o /home/monad/monad-bft/config/node.toml $MF_BUCKET/config/testnet/latest/node.toml
````

### Step 8 — Set Keystore Password

Generate a secure random password (if `KEYSTORE_PASSWORD` is not already set):

````bash
sed -i "s|^KEYSTORE_PASSWORD=$|KEYSTORE_PASSWORD='$(openssl rand -base64 32)'|" /home/monad/.env
source /home/monad/.env

mkdir -p /opt/monad/backup/
echo "Keystore password: ${KEYSTORE_PASSWORD}" > /opt/monad/backup/keystore-password-backup
````

### Step 9 — Generate Keystores

````bash
bash <<'EOF'
set -e

source /home/monad/.env

if [[ -z "$KEYSTORE_PASSWORD" || \
      -f /home/monad/monad-bft/config/id-secp || \
      -f /home/monad/monad-bft/config/id-bls ]]; then
  echo "Skipping: missing KEYSTORE_PASSWORD or keys already exist."
  exit 1
fi

monad-keystore create \
  --key-type secp \
  --keystore-path /home/monad/monad-bft/config/id-secp \
  --password "${KEYSTORE_PASSWORD}" > /opt/monad/backup/secp-backup

monad-keystore create \
  --key-type bls \
  --keystore-path /home/monad/monad-bft/config/id-bls \
  --password "${KEYSTORE_PASSWORD}" > /opt/monad/backup/bls-backup

grep "public key" /opt/monad/backup/secp-backup /opt/monad/backup/bls-backup \
  | tee /home/monad/pubkey-secp-bls

echo "Success: New keystores generated"

EOF
````

> 🔐 **CRITICAL — Back up these files externally** (password manager, secrets vault, offline storage):
> - `/opt/monad/backup/secp-backup`
> - `/opt/monad/backup/bls-backup`
> - `/opt/monad/backup/keystore-password-backup`
>
> These files define your node identity. For validators, losing your keys means you **cannot migrate** your validator, and re-registering requires moving all delegations manually.

### Step 10 — Configure node.toml

Edit the config:

````bash
nano /home/monad/monad-bft/config/node.toml
````

#### For Full Nodes

| Field | Value |
|-------|-------|
| `beneficiary` | `"0x0000000000000000000000000000000000000000"` (burn address) |
| `node_name` | `"full_<YOUR_NAME>-1"` (must be unique) |
| `enable_client` | `true` under `[fullnode_raptorcast]` |
| `expand_to_group` | `true` under `[statesync]` |

#### For Validators

| Field | Value |
|-------|-------|
| `beneficiary` | `"0x<YOUR_REWARDS_ADDRESS>"` (address to receive block rewards) |
| `node_name` | `"<YOUR_NAME>-1"` (must be unique, no `full_` prefix) |
| `enable_client` | `true` under `[fullnode_raptorcast]` |
| `expand_to_group` | `true` under `[statesync]` |

Leave `[blocksync_override]` peers empty for public full nodes.

### Step 11 — Sign Name Record

````bash
source /home/monad/.env
monad-sign-name-record \
  --address $(curl -s4 ifconfig.me):8000 \
  --authenticated-udp-port 8001 \
  --keystore-path /home/monad/monad-bft/config/id-secp \
  --password "${KEYSTORE_PASSWORD}" \
  --self-record-seq-num 1
````

Copy the output and update the `[peer_discovery]` section in `node.toml`:

````toml
self_address = "YOUR.IP.ADDRESS:8000"
self_record_seq_num = 1
self_name_record_sig = "<output from command above>"
````

### Step 12 — Configure Remote Config Fetching

Verify these lines exist in `/home/monad/.env`:

````bash
REMOTE_VALIDATORS_URL='https://bucket.monadinfra.com/validators/testnet/validators.toml'
REMOTE_FORKPOINT_URL='https://bucket.monadinfra.com/forkpoint/testnet/forkpoint.toml'
````

> These URLs auto-fetch fresh configs on startup. You can replace them with alternative providers.

### Step 13 — Configure Monad Cruft Service

The `monad-cruft` timer runs hourly to clear old artifacts and prevent inode exhaustion.

Optionally configure retention times in `/home/monad/.env`:

````bash
# All values in minutes
RETENTION_LEDGER=600       # Ledger files (default: 600 = 10 hours)
RETENTION_WAL=300          # WAL files (default: 300 = 5 hours)
RETENTION_FORKPOINT=300    # Forkpoint files (default: 300 = 5 hours)
RETENTION_VALIDATORS=43200 # Validators files (default: 43200 = 30 days)
````

---

## Start the Node

### Step 14 — Hard Reset and Start

Set permissions:

````bash
chown -R monad:monad /home/monad/
````

**Run the Hard Reset** to import a recent database snapshot:

````bash
bash /opt/monad/scripts/reset-workspace.sh
````

Set permissions again (reset may create files as root):

````bash
chown -R monad:monad /home/monad/
````

Enable and start services:

````bash
systemctl enable monad-bft monad-execution monad-rpc
systemctl start monad-bft monad-execution monad-rpc
````

### Step 15 — Verify

Check all services:

````bash
systemctl status monad-bft monad-execution monad-rpc --no-pager -l
````

All three should show `Active: active (running)`.

Check version:

````bash
monad-node --version
````

Monitor sync progress:

````bash
journalctl -u monad-bft -f --no-pager
````

Check block height via RPC (available after statesync completes, port `8080`):

````bash
curl http://localhost:8080/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"method":"eth_blockNumber","params":[],"id":1,"jsonrpc":"2.0"}'
````

---

## Validator-Specific Steps

> ⚠️ **Complete the full node setup first.** Your node must be fully synced to the network tip before registering as a validator.

### Step 16 — Register as Validator (Staking)

Once your full node is synced, register as a prospective validator by calling `addValidator` on the **staking precompile**. This requires meeting the minimum staking thresholds for the testnet.

| Requirement | Value |
|-------------|-------|
| Minimum self-stake | Check testnet staking parameters |
| Minimum total stake (self + delegated) | Check testnet staking parameters |
| Active validator set size | Top validators by total stake weight |

All conditions must be met for your validator to become **active in the next epoch**.

#### Using `staking-sdk-cli`

`staking-sdk-cli` is the open-source tool for interfacing with the staking precompile.

Install and follow the onboarding workflow:

````bash
# See: https://github.com/monad-crypto/staking-sdk-cli
# Follow the onboarding workflow to:
#   1. addValidator — register with the required MON self-stake
#   2. Check validator status
#   3. Manage delegations
````

### Step 17 — Update node.toml for Validator

After transitioning from full node to validator, review `node.toml`:

1. **`beneficiary`** — Set to your rewards wallet address:

````toml
beneficiary = "0x<YOUR_REWARDS_ADDRESS>"
````

2. **`node_name`** — Remove any `full_` prefix, choose a unique identifier:

````toml
node_name = "<YOUR_NAME>-1"
````

3. **(Optional) Dedicated full node connections** — To broadcast blocks to downstream full nodes:

````toml
# [[bootstrap.peers]]
# address = "<ip>:<port>"
# record_seq_num = "<record_seq_num>"
# name_record_sig = "<name_record_sig>"
# secp256k1_pubkey = "<full node pubkey>"

# [[fullnode_dedicated.identities]]
# secp256k1_pubkey = "<full node pubkey>"
````

4. **(Optional) Prioritized full node connections**:

````toml
# [[bootstrap.peers]]
# address = "<ip>:<port>"
# record_seq_num = "<record_seq_num>"
# name_record_sig = "<name_record_sig>"
# secp256k1_pubkey = "<full node pubkey>"

# [[fullnode_raptorcast.full_nodes_prioritized.identities]]
# secp256k1_pubkey = "<full node pubkey>"
````

Apply config changes without restarting `monad-bft`:

````bash
monad-debug-node --control-panel-ipc-path /home/monad/monad-bft/controlpanel.sock reload-config
````

---

## Monitoring & Operations

### Install `monlog`

`monlog` is a lightweight log analysis tool maintained by Category Labs. It scrapes BFT logs and provides status + suggestions.

**Setup (as root):**

````bash
# Grant monad user access to systemd journal
usermod -a -G systemd-journal monad
````

**Download (as monad user):**

````bash
su - monad
cd /home/monad
curl -sSL https://pub-b0d0d7272c994851b4c8af22a766f571.r2.dev/scripts/monlog -O
chmod u+x ./monlog

# Verify checksum
sha256sum ./monlog
# Expected: f8a1066d8c093bbdb5f722f5b3d89904c17a76fa01fa1dd62e950f445e88327f
````

**Usage:**

````bash
./monlog              # One-time status check
watch -d "./monlog"   # Live updates
./monlog -r           # Show last 10 lines of grabbed logs
./monlog -n           # Show secp keys mapped to validator names
./monlog --no-color   # No color coding
````

Example healthy output:

````
Installed version:
ii monad 0.12.7 amd64 Monad BFT stack (symbols stripped)

No StateSync messages.
---
No BlockSync messages.
---
Most recent round: 52268965
Most recent epoch: 1001
Most recent block: 50041845
Blocks processing and being committed ✅
````

### Install `monad-status`

````bash
curl -sSL https://bucket.monadinfra.com/scripts/monad-status.sh -o /usr/local/bin/monad-status
chmod +x /usr/local/bin/monad-status
monad-status
````

### `monad-ledger-tail` (Consensus Stream)

````bash
systemctl start monad-ledger-tail
journalctl -fu monad-ledger-tail
````

Outputs real-time consensus information (round, epoch, seq_num, author, etc.) in JSON format.

### View TrieDB Disk Usage

````bash
monad-mpt --storage /dev/triedb
````

> MonadDB auto-compacts at 80% capacity to preserve SSD performance.

---

## Key Backup & Restore

### Export Key Backups

If backup files are missing or you need to re-export:

````bash
source /home/monad/.env

[ -f /opt/monad/backup/secp-backup ] && mv /opt/monad/backup/secp-backup "/opt/monad/backup/secp-backup.$(date +%Y%m%d%H%M%S).bak"
[ -f /opt/monad/backup/bls-backup ] && mv /opt/monad/backup/bls-backup "/opt/monad/backup/bls-backup.$(date +%Y%m%d%H%M%S).bak"

monad-keystore recover \
  --password "$KEYSTORE_PASSWORD" \
  --keystore-path /home/monad/monad-bft/config/id-secp \
  --key-type secp > /opt/monad/backup/secp-backup

monad-keystore recover \
  --password "$KEYSTORE_PASSWORD" \
  --keystore-path /home/monad/monad-bft/config/id-bls \
  --key-type bls > /opt/monad/backup/bls-backup
````

### Import Keys from Backups

To restore node identity on a new machine:

````bash
source /home/monad/.env

[ -f /home/monad/monad-bft/config/id-secp ] && mv /home/monad/monad-bft/config/id-secp "/home/monad/monad-bft/config/id-secp.$(date +%Y%m%d%H%M%S).bak"
[ -f /home/monad/monad-bft/config/id-bls ] && mv /home/monad/monad-bft/config/id-bls "/home/monad/monad-bft/config/id-bls.$(date +%Y%m%d%H%M%S).bak"

SECP_IKM=$(grep -E "Keystore secret:|Keep your IKM secure:" /opt/monad/backup/secp-backup | awk '{print $NF}')
BLS_IKM=$(grep -E "Keystore secret:|Keep your IKM secure:" /opt/monad/backup/bls-backup | awk '{print $NF}')

monad-keystore import \
  --ikm "$SECP_IKM" \
  --password "$KEYSTORE_PASSWORD" \
  --keystore-path /home/monad/monad-bft/config/id-secp \
  --key-type secp

monad-keystore import \
  --ikm "$BLS_IKM" \
  --password "$KEYSTORE_PASSWORD" \
  --keystore-path /home/monad/monad-bft/config/id-bls \
  --key-type bls
````

---

## Node Recovery

### Soft Reset

Clears consensus state while preserving TrieDB. Used when node is stuck but TrieDB is healthy:

````bash
systemctl stop monad-bft monad-execution monad-rpc
# Follow: https://docs.monad.xyz/node-ops/node-recovery/soft-reset
systemctl start monad-bft monad-execution monad-rpc
````

### Hard Reset

Full state reset with snapshot re-import. Used for major issues or version upgrades requiring re-sync:

````bash
systemctl stop monad-bft monad-execution monad-rpc
bash /opt/monad/scripts/reset-workspace.sh
chown -R monad:monad /home/monad/
systemctl start monad-bft monad-execution monad-rpc
````

### Node Migration (Promoting Full Node to Validator)

See [official docs](https://docs.monad.xyz/node-ops/node-recovery/node-migration) for migrating identity from one machine to another or promoting a full node to validator.

---

## Upgrading

### General Upgrade Procedure

````bash
# 1. Check current version
monad-node --version

# 2. Remove hold, update, re-hold
apt-mark unhold monad
apt update
apt install -y monad
apt-mark hold monad

# 3. Verify new version
monad-node --version

# 4. Restart services
systemctl restart monad-bft monad-execution monad-rpc
````

> ⚠️ Some upgrades require a **hard reset**. Always check the specific [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions) before upgrading.

### Stay Updated

- Join the [Monad Developer Discord](https://discord.gg/monad) → `#testnet-fullnode-announcements` channel

---

## Useful Commands

### Service Management

| Command | Description |
|---------|-------------|
| `systemctl status monad-bft monad-execution monad-rpc` | Check all services |
| `systemctl restart monad-bft monad-execution monad-rpc` | Restart all services |
| `systemctl stop monad-bft monad-execution monad-rpc` | Stop all services |

### Logs

| Command | Description |
|---------|-------------|
| `journalctl -u monad-bft -f` | Follow consensus logs |
| `journalctl -u monad-execution -f` | Follow execution logs |
| `journalctl -u monad-rpc -f` | Follow RPC logs |

### Node Info

| Command | Description |
|---------|-------------|
| `monad-node --version` | Show version and build info |
| `cat /home/monad/pubkey-secp-bls` | Show node public keys |
| `monad-mpt --storage /dev/triedb` | TrieDB disk usage |
| `monad-status` | Full node status dashboard |

### RPC Queries

````bash
# Block number
curl http://localhost:8080/ -X POST -H "Content-Type: application/json" \
  --data '{"method":"eth_blockNumber","params":[],"id":1,"jsonrpc":"2.0"}'

# Chain ID (should return 0x279F = 10143 for testnet)
curl http://localhost:8080/ -X POST -H "Content-Type: application/json" \
  --data '{"method":"eth_chainId","params":[],"id":1,"jsonrpc":"2.0"}'

# Client version
curl http://localhost:8080/ -X POST -H "Content-Type: application/json" \
  --data '{"method":"web3_clientVersion","params":[],"id":1,"jsonrpc":"2.0"}'
````

### CLI Help

````bash
monad-rpc --help
monad --help
monad-bft --help
````

> ⚠️ CLI arguments should not be changed arbitrarily — some configurations may cause unexpected behavior or crashes.

---

## Call Traces (Optional — for Archive/RPC nodes)

For full nodes intended for archiving or RPC workflows, enable `--trace_calls` to preserve detailed error information for `debug_traceTransaction`:

````bash
systemctl edit monad-execution
````

Add:

````ini
[Service]
Type=simple
ExecStart=
ExecStart=/usr/local/bin/monad \
    ... \
    --trace_calls
````

---

## Additional Resources

| Resource | Link |
|----------|------|
| Official Docs | [docs.monad.xyz/node-ops](https://docs.monad.xyz/node-ops) |
| Hardware Recommendations | [docs.monad.xyz/node-ops/hardware-requirements](https://docs.monad.xyz/node-ops/hardware-requirements) |
| Staking Overview | [docs.monad.xyz/reference/staking/overview](https://docs.monad.xyz/reference/staking/overview) |
| Staking API | [docs.monad.xyz/reference/staking/api](https://docs.monad.xyz/reference/staking/api) |
| Upgrade Instructions | [docs.monad.xyz/node-ops/upgrade-instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/index) |
| Testnet Info | [docs.monad.xyz/developer-essentials/testnets](https://docs.monad.xyz/developer-essentials/testnets) |
| Posthuman Twitter | [x.com/POSTHUMAN_DVS](https://x.com/POSTHUMAN_DVS) |
