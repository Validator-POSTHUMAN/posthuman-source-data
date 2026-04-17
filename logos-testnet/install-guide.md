# Logos Blockchain Testnet Node Setup Guide

This guide installs a **Logos Blockchain testnet node** on a Linux x86_64 server.

Logos Blockchain uses **Cryptarchia** — a Private Proof of Stake (PPoS) consensus protocol where block proposer identity and stake are kept private using zero-knowledge proofs.

---

## 1. Requirements

- **OS:** Linux x86_64 (Ubuntu 24.04+ recommended) or Raspberry Pi 5
- **glibc:** version 2.39 or later
- **Storage:** minimum 64 GB
- **Network:** UDP port 3000 open for P2P

### Check glibc version

```bash
ldd --version | head -1
```

---

## 2. Download Node Binary and ZK Circuits

Download the latest release from the [Logos Blockchain releases page](https://github.com/logos-blockchain/logos-blockchain/releases).

```bash
cd /tmp

# Download ZK circuits
wget https://github.com/logos-blockchain/logos-blockchain/releases/download/0.1.2/logos-blockchain-circuits-v0.4.2-linux-x86_64.tar.gz

# Download node binary
wget https://github.com/logos-blockchain/logos-blockchain/releases/download/0.1.2/logos-blockchain-node-linux-x86_64-0.1.2.tar.gz
```

> **Tip:** Check the [releases page](https://github.com/logos-blockchain/logos-blockchain/releases) for a newer version before downloading.

---

## 3. Install

```bash
cd /tmp

# Extract
tar -xf logos-blockchain-circuits-v0.4.2-linux-x86_64.tar.gz
tar -xf logos-blockchain-node-linux-x86_64-0.1.2.tar.gz

# Install circuits
mv logos-blockchain-circuits-v0.4.2-linux-x86_64 ~/.logos-blockchain-circuits

# Install binary
mkdir -p ~/logos-blockchain
mv logos-blockchain-node ~/logos-blockchain/

# Verify
~/logos-blockchain/logos-blockchain-node --version
```

Expected output:
```
logos-blockchain-node 0.1.2
```

---

## 4. Initialize Configuration

Generate a unique node configuration with bootstrap peers:

```bash
cd ~/logos-blockchain

./logos-blockchain-node init \
  -p /ip4/65.109.51.37/udp/3000/quic-v1/p2p/12D3KooWFrouXfmrR4nsLMtE7wu15DoMJ6VtoUtHinREZCvbWHar \
  -p /ip4/65.109.51.37/udp/3001/quic-v1/p2p/12D3KooWJRGau8M1rjT7R5e4YYsgdFhsMX35nRDtMwCDjxQkXAHz \
  -p /ip4/65.109.51.37/udp/3002/quic-v1/p2p/12D3KooWQXJavMDTRscjauFSgVAB1VLB6Rzpy2uY5SU9Tk7927tb \
  -p /ip4/65.109.51.37/udp/3003/quic-v1/p2p/12D3KooWSQc7CcGtvWDPF1yCbBthFnQjprfCVHmfmNDUrSmqQsU1
```

This creates a `user_config.yaml` file with fresh cryptographic keys and auto-detected public IP.

> **Note:** If your node is behind NAT, add `--no-public-ip-check` to the init command.

---

## 5. Create Systemd Service

```bash
sudo tee /etc/systemd/system/logos.service > /dev/null << EOF
[Unit]
Description=Logos Blockchain Node
After=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/logos-blockchain
ExecStart=/home/ubuntu/logos-blockchain/logos-blockchain-node user_config.yaml
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable logos.service
sudo systemctl start logos.service
```

---

## 6. Verify Node Status

### Check sync status

```bash
curl -s http://localhost:8080/cryptarchia/info | jq .
```

Example response:
```json
{
  mode: Bootstrapping,
  height: 120,
  slot: 70899
}
```

- **mode:** starts as `Bootstrapping`, transitions to `Online` when synced
- **height:** confirmed blocks (increases ~1 block every 10 seconds)
- **slot:** elapsed time intervals

### Check peer connectivity

```bash
curl -s http://localhost:8080/network/info | jq .
```

Verify `n_peers` is greater than 0.

---

## 7. Get Testnet Tokens

### Find your wallet keys

```bash
grep -A3 known_keys ~/logos-blockchain/user_config.yaml
```

### Request funds from faucet

Visit the [Logos Testnet Faucet](https://testnet.blockchain.logos.co/web/faucet/) and enter your wallet key.

Or via CLI:

```bash
curl -s -X POST https://testnet.blockchain.logos.co/web/faucet-backend/YOUR_PUBLIC_KEY
```

> **Note:** Only one faucet transaction per block. Wait 1–2 minutes between requests.

### Check balance

```bash
curl -s http://localhost:8080/wallet/YOUR_PUBLIC_KEY/balance | jq .
```

---

## 8. Block Proposal

After UTXO aging (~3.5 hours / 2 epochs), the node automatically enters the consensus lottery and begins proposing blocks. No further action required.

Block proposal is **probabilistic** — participation depends on your stake relative to total active stake.

Compare your node against the fleet at the [Logos Testnet Dashboard](https://testnet.blockchain.logos.co/web/).

---

## 9. Upgrade Procedure

1. Stop the service: `sudo systemctl stop logos.service`
2. Download new binary and circuits from [releases](https://github.com/logos-blockchain/logos-blockchain/releases)
3. Replace binary in `~/logos-blockchain/`
4. Replace circuits in `~/.logos-blockchain-circuits/`
5. If breaking release: delete old state, config, and circuits (see release notes)
6. Re-initialize if needed: `./logos-blockchain-node init -p <peers>`
7. Start service: `sudo systemctl start logos.service`
8. Verify: `curl -s http://localhost:8080/cryptarchia/info | jq .`

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl status logos.service` | Check service status |
| `sudo systemctl restart logos.service` | Restart node |
| `journalctl -u logos.service -f` | Follow logs |
| `curl -s http://localhost:8080/cryptarchia/info \| jq .` | Check sync status |
| `curl -s http://localhost:8080/network/info \| jq .` | Check peer connectivity |

---

## Links

- [Logos Testnet Dashboard](https://testnet.blockchain.logos.co/web/)
- [Faucet](https://testnet.blockchain.logos.co/web/faucet/)
- [GitHub Releases](https://github.com/logos-blockchain/logos-blockchain/releases)
- [Documentation](https://docs.logos.co)
- [Discord](https://discord.com/channels/973324189794697286/1468535289604735038)
