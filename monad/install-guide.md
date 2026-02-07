# Monad Mainnet Node Installation Guide

## About Monad

Monad is a high-performance EVM-compatible Layer 1 blockchain featuring parallel execution, MonadBFT consensus, and 400ms block times. It achieves 500M gas/sec throughput while maintaining full Ethereum compatibility.

**Network Details:**

| Parameter | Value |
|-----------|-------|
| Network | Monad Mainnet |
| Chain ID | `143` |
| Currency | `MON` |
| Block Time | 400ms |
| Block Gas Limit | 200M |
| Current Version | `v0.12.8` |
| Explorer | [monadvision.com](https://monadvision.com) |

## Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 16 cores (no HyperThreading) | 16+ cores |
| RAM | 32 GB | 64 GB |
| Storage | 2x 2TB NVMe SSD | 2x 2TB NVMe SSD |
| Network | 1 Gbps | 10 Gbps |
| OS | Ubuntu 24.04+ | Ubuntu 24.04+ |
| Kernel | >= 6.8.0.60 | >= 6.8.0.60 |

> ⚠️ HyperThreading / SMT must be **disabled** in BIOS — it degrades node performance.

> ⚠️ Linux kernel `v6.8.0.56` to `v6.8.0.59` has a known bug causing Monad clients to hang. Use `v6.8.0.60+`.

### Disk Layout
- **Disk 1** — OS + ledger data (`/home/monad/monad-bft/`)
- **Disk 2** — TrieDB raw device (`/dev/triedb`) — **no filesystem**, used directly by Monad

## 1. Update System

````bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl nvme-cli aria2 jq
````

## 2. Install Monad Package

Add the Category Labs APT repository:

````bash
cat <<EOF | sudo tee /etc/apt/sources.list.d/category-labs.sources
Types: deb
URIs: https://pkg.category.xyz/
Suites: noble
Components: main
Signed-By: /etc/apt/keyrings/category-labs.gpg
EOF

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkg.category.xyz/keys/public-key.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/category-labs.gpg
````

Install and pin the package:

````bash
sudo apt update
sudo apt install -y monad=0.12.8
sudo apt-mark hold monad
````

Verify:

````bash
monad-rpc --version
````

## 3. Create Monad User

````bash
sudo useradd -m -s /bin/bash monad

sudo mkdir -p /home/monad/monad-bft/config \
              /home/monad/monad-bft/ledger \
              /home/monad/monad-bft/config/forkpoint \
              /home/monad/monad-bft/config/validators
````

## 4. Configure TrieDB Device

Identify the **second NVMe drive** (the one with **no mountpoints**):

````bash
nvme list
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL
````

> ⚠️ **Double-check which drive to use! Formatting the wrong drive will destroy your OS!**

Set up the partition:

````bash
TRIEDB_DRIVE=/dev/nvme1n1  # CHANGE THIS TO YOUR DRIVE

sudo parted -s $TRIEDB_DRIVE mklabel gpt
sudo parted -s $TRIEDB_DRIVE mkpart triedb 0% 100%
````

Create udev rule for `/dev/triedb` symlink:

````bash
PARTUUID=$(lsblk -o PARTUUID $TRIEDB_DRIVE | tail -n 1)

echo "ENV{ID_PART_ENTRY_UUID}==\"$PARTUUID\", MODE=\"0666\", SYMLINK+=\"triedb\"" \
  | sudo tee /etc/udev/rules.d/99-triedb.rules

sudo udevadm trigger && sudo udevadm control --reload && sudo udevadm settle
ls -l /dev/triedb
````

Verify 512-byte LBA:

````bash
sudo nvme id-ns -H $TRIEDB_DRIVE | grep 'LBA Format' | grep 'in use'
````

Expected: `Data Size: 512 bytes`. If not:

````bash
sudo nvme format --lbaf=0 $TRIEDB_DRIVE
````

Format TrieDB:

````bash
sudo systemctl start monad-mpt
sudo journalctl -u monad-mpt -n 14 -o cat --no-pager
````

## 5. Configure Firewall

````bash
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw allow 8001
sudo ufw --force enable

# Anti-spam rule for UDP
sudo iptables -I INPUT -p udp --dport 8000 -m length --length 0:1400 -j DROP

# Persist iptables rules
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt install -y iptables-persistent
````

## 6. Install OTEL Collector

````bash
OTEL_VERSION="0.139.0"
curl -fsSL "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTEL_VERSION}/otelcol_${OTEL_VERSION}_linux_amd64.deb" \
  -o /tmp/otelcol.deb
sudo dpkg -i /tmp/otelcol.deb

sudo cp /opt/monad/scripts/otel-config.yaml /etc/otelcol/config.yaml
sudo systemctl restart otelcol
````

## 7. Download Configuration Files

For **full nodes**:

````bash
MF_BUCKET=https://bucket.monadinfra.com
sudo curl -o /home/monad/.env $MF_BUCKET/config/mainnet/latest/.env.example
sudo curl -o /home/monad/monad-bft/config/node.toml $MF_BUCKET/config/mainnet/latest/full-node-node.toml
````

For **validators**:

````bash
MF_BUCKET=https://bucket.monadinfra.com
sudo curl -o /home/monad/.env $MF_BUCKET/config/mainnet/latest/.env.example
sudo curl -o /home/monad/monad-bft/config/node.toml $MF_BUCKET/config/mainnet/latest/node.toml
````

## 8. Set Keystore Password

````bash
sudo sed -i "s|^KEYSTORE_PASSWORD=$|KEYSTORE_PASSWORD='$(openssl rand -base64 32)'|" /home/monad/.env

sudo mkdir -p /opt/monad/backup/
sudo bash -c 'source /home/monad/.env && echo "Keystore password: ${KEYSTORE_PASSWORD}" > /opt/monad/backup/keystore-password-backup'
````

## 9. Generate Keystores

````bash
sudo bash -c 'source /home/monad/.env && \
  monad-keystore create --key-type secp \
    --keystore-path /home/monad/monad-bft/config/id-secp \
    --password "${KEYSTORE_PASSWORD}" > /opt/monad/backup/secp-backup 2>&1'

sudo bash -c 'source /home/monad/.env && \
  monad-keystore create --key-type bls \
    --keystore-path /home/monad/monad-bft/config/id-bls \
    --password "${KEYSTORE_PASSWORD}" > /opt/monad/backup/bls-backup 2>&1'

sudo grep "public key" /opt/monad/backup/secp-backup /opt/monad/backup/bls-backup \
  | sudo tee /home/monad/pubkey-secp-bls
````

> 🔐 **Back up these files externally** — they are required to restore your node identity:
> - `/opt/monad/backup/secp-backup`
> - `/opt/monad/backup/bls-backup`
> - `/opt/monad/backup/keystore-password-backup`

## 10. Configure node.toml

Edit `/home/monad/monad-bft/config/node.toml`:

````bash
sudo nano /home/monad/monad-bft/config/node.toml
````

Update the following fields:

- `beneficiary` — set to `"0x0000000000000000000000000000000000000000"` for full nodes, or your wallet for validators
- `node_name` — set to `"full_<YOUR_NAME>-1"` (must be unique)
- Ensure `enable_client = true` under `[fullnode_raptorcast]`
- Ensure `expand_to_group = true` under `[statesync]`

## 11. Sign Name Record

````bash
MY_IP=$(curl -s4 ifconfig.me)

sudo bash -c "source /home/monad/.env && \
  monad-sign-name-record \
    --address ${MY_IP}:8000 \
    --authenticated-udp-port 8001 \
    --keystore-path /home/monad/monad-bft/config/id-secp \
    --password \"\${KEYSTORE_PASSWORD}\" \
    --self-record-seq-num 1"
````

Copy the output and update `[peer_discovery]` section in `node.toml`:

- `self_address`
- `self_record_seq_num`
- `self_name_record_sig`

## 12. Configure Remote Config Fetching

Verify these lines exist in `/home/monad/.env`:

````
REMOTE_VALIDATORS_URL='https://bucket.monadinfra.com/validators/mainnet/validators.toml'
REMOTE_FORKPOINT_URL='https://bucket.monadinfra.com/forkpoint/mainnet/forkpoint.toml'
````

## 13. Hard Reset and Start

Set permissions:

````bash
sudo chown -R monad:monad /home/monad/
````

Run the hard reset script to prepare state:

````bash
sudo bash /opt/monad/scripts/reset-workspace.sh
````

Enable and start services:

````bash
sudo chown -R monad:monad /home/monad/
sudo systemctl enable monad-bft monad-execution monad-rpc
sudo systemctl start monad-bft monad-execution monad-rpc
````

## 14. Verify

Check services:

````bash
sudo systemctl status monad-bft monad-execution monad-rpc --no-pager -l
````

All three should show `Active: active (running)`.

Check version:

````bash
monad-rpc --version
````

Monitor sync progress:

````bash
sudo journalctl -u monad-bft -f --no-pager
````

## Useful Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl status monad-bft monad-execution monad-rpc` | Check all services |
| `sudo journalctl -u monad-bft -f` | Follow consensus logs |
| `sudo journalctl -u monad-execution -f` | Follow execution logs |
| `sudo journalctl -u monad-rpc -f` | Follow RPC logs |
| `sudo systemctl restart monad-bft monad-execution monad-rpc` | Restart all services |
| `cat /home/monad/pubkey-secp-bls` | Show node public keys |
