# Espresso Network — Validator Setup Guide

> Espresso is an EVM-compatible decentralized sequencing network. Validators stake ESP tokens on Ethereum (mainnet) and participate in sequencing via BLS + Schnorr consensus keys.

---

## Requirements

| Component | Minimum |
|-----------|---------|
| OS | Ubuntu 22.04 |
| CPU | 4 cores |
| RAM | 16 GB |
| Disk | 200 GB SSD |
| Network | 100 Mbps |

---

## 1. Install Dependencies

```bash
apt -y update && apt -y upgrade
apt install -y curl git wget build-essential docker.io docker-compose
```

---

## 2. Install Espresso Staking CLI

### Option A: Docker (recommended)
```bash
alias staking-cli='docker run -it ghcr.io/espressosystems/espresso-sequencer/staking-cli:main staking-cli'
```

### Option B: Build from source (requires Rust)
```bash
git clone https://github.com/EspressoSystems/espresso-network.git
cd espresso-network
cargo build --bin staking-cli -p staking-cli --release
cp target/release/staking-cli /usr/local/bin/
```

---

## 3. Configure Wallet

Choose one signing method:

### Mnemonic (env var recommended)
```bash
export MNEMONIC="your twelve word mnemonic phrase here ..."
staking-cli --mnemonic "$MNEMONIC" --account-index 0 account
```

### Private Key
```bash
export PRIVATE_KEY="0xYourPrivateKeyHex"
staking-cli account
```

### Ledger (most secure for mainnet)
```bash
staking-cli --ledger --account-index 0 account
```

---

## 4. Initialize Config

```bash
# Mainnet
staking-cli init --network mainnet --mnemonic "$MNEMONIC" --account-index 0

# Decaf Testnet (Sepolia)
staking-cli init --network decaf --mnemonic "$MNEMONIC" --account-index 0
```

Config is saved to `~/.config/espresso/espresso-staking-cli/config.toml`.

Check config:
```bash
staking-cli config
```

---

## 5. Generate Consensus Keys (BLS + Schnorr)

Export node signatures (generates BLS and Schnorr keys, signs your Ethereum address):

```bash
staking-cli export-node-signatures \
  --address 0xYourEthereumAddress \
  --consensus-private-key BLS_SIGNING_KEY~... \
  --state-private-key SCHNORR_SIGNING_KEY~... \
  --output signatures.json
```

> Use `CONSENSUS_PRIVATE_KEY` and `STATE_PRIVATE_KEY` env vars to avoid keys in shell history.

---

## 6. Register as Validator

### Prepare metadata (optional but recommended)
Host a JSON file or use your node's `/status/metrics` endpoint.

Custom JSON schema:
```json
{
  "pub_key": "BLS_VER_KEY~...",
  "name": "POSTHUMAN Validator",
  "description": "Your validator description",
  "company_name": "POSTHUMAN",
  "company_website": "https://posthuman.digital/",
  "client_version": "v1.0.0",
  "icon": {
    "14x14": { "@1x": "https://example.com/icon-14.png" },
    "24x24": { "@1x": "https://example.com/icon-24.png" }
  }
}
```

Preview metadata before registering:
```bash
staking-cli preview-metadata --metadata-uri https://your-node.com/status/metrics
```

### Register
```bash
staking-cli register-validator \
  --node-signatures signatures.json \
  --commission 5.00 \
  --metadata-uri https://your-node.com/status/metrics
```

> - Requires ~300k gas on Ethereum
> - Each BLS key can only be registered once
> - Each Ethereum address can only register one validator

---

## 7. Approve & Stake ESP Tokens

```bash
# Approve stake table contract to spend your ESP tokens
staking-cli approve --amount 1000

# Delegate to yourself (or another validator)
staking-cli delegate \
  --validator-address 0xYourValidatorAddress \
  --amount 1000
```

---

## 8. Check Stake Table

```bash
staking-cli stake-table
```

---

## 9. Manage Validator

### Update commission (max +5% per week)
```bash
staking-cli update-commission --new-commission 7.5
```

### Update metadata URL
```bash
staking-cli update-metadata-uri \
  --metadata-uri https://your-node.com/status/metrics \
  --consensus-public-key BLS_VER_KEY~...
```

### Rotate consensus keys
```bash
export CONSENSUS_PRIVATE_KEY="BLS_SIGNING_KEY~..."
export STATE_PRIVATE_KEY="SCHNORR_SIGNING_KEY~..."
staking-cli update-consensus-keys
```
> New keys activate in the 3rd epoch after the command.

### Deregister (⚠️ removes validator and undelegates all funds)
```bash
staking-cli deregister-validator
```

---

## 10. Staking Rewards

```bash
# Check unclaimed rewards
staking-cli unclaimed-rewards

# Claim rewards
staking-cli claim-rewards
```

> Requires `espresso_url` in config or `--espresso-url` flag.

---

## Contracts

| Network | Contract | Address |
|---------|----------|---------|
| Mainnet (ETH) | Stake Table | `0xCeF474D372B5b09dEfe2aF187bf17338Dc704451` |
| Decaf Testnet (Sepolia) | Stake Table | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037` |

---

## Useful Links

- 🌐 Website: https://espresso.network/
- 📖 GitHub: https://github.com/EspressoSystems/espresso-network
- 🎰 Testnet Staking UI: https://staking.decaf.testnet.espresso.network/
- 💬 Discord: https://discord.gg/espresso
- 🐦 Twitter: https://x.com/EspressoNetwork
