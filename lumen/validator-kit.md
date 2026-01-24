# Lumen deployment toolbox

# ⚠️ CRITICAL VALIDATOR WARNING – READ FIRST ⚠️

## 🚨 KEY BACKUP REQUIREMENT (ED25519 + PQC)

**Validators MUST backup BOTH cryptographic keys:**
- ✅ **ed25519 key** (classic Cosmos key)
- ✅ **PQC key (Dilithium)**

👉 **If you lose ONE of them, you LOSE ACCESS TO YOUR FUNDS.**

---

## ❌ DO NOT DO THIS
- ❌ Do NOT delete your node without backing up **BOTH** keys  
- ❌ Do NOT reinstall / redeploy / wipe `.lumen` blindly  
- ❌ Do NOT assume PQC keys can be regenerated  
- ❌ Do NOT assume there is an override, reset, or admin recovery  

**THERE IS NO PQC KEY OVERRIDE.  
THERE IS NO ADMIN RESET.  
THERE IS NO FUND RECOVERY.**

**Store all backups OFF the server. Losing them = losing funds.**

---

## 🚨 DOUBLE-SIGNING WARNING

**NEVER run the same validator on more than ONE node.**

The file:
- `~/.lumen/config/priv_validator_key.json`

**MUST exist on ONE running machine only.**

❌ Do NOT copy it to a sentry  
❌ Do NOT run two nodes with it  
❌ Do NOT restore a backup while another node is running  

⚠️ **Double-signing = instant slashing + permanent jail. No recovery.**

**Validator = 1 key = 1 running node.**

---

## Join the network (root workflow)

For most operators, the flow is:

```bash
git clone https://github.com/network-lumen/validator-kit.git
cd validator-kit
./join.sh <moniker> [--public-api]
```

- `./join.sh` uses the toolkit to:
  - initialize a `.lumen` home (or the one specified via `--home` / `LUMEN_HOME`),
  - copy templates from `config/`,
  - install and start a `lumend` systemd service.

By design, this join step creates a **non-validator** full node / sentry / RPC node only.
Promotion to validator and staking are handled explicitly in `ops/scripts/blockchain/`.

### Fast sync (recommended)

If you have a trusted RPC endpoint and want to avoid replaying all blocks:

1. Join the network and let `./join.sh` create the node home and systemd service:
   ```bash
   ./join.sh <moniker> [--public-api]
   ```
2. Stop the node before it starts replaying from genesis:
   ```bash
   sudo systemctl stop lumend
   ```
3. Clear local state only (keep config and keys):
   ```bash
   rm -rf ~/.lumen/data
   mkdir -p ~/.lumen/data
   printf '{ "height": "0", "round": 0, "step": 0 }\n' \
     > ~/.lumen/data/priv_validator_state.json
   ```
4. Configure state sync against a trusted RPC:
   ```bash
   ops/scripts/network/state_sync.sh \
     --home ~/.lumen \
     --rpc http://trusted-rpc:26657 \
     --last 100
   ```
5. Restart the node:
   ```bash
   sudo systemctl start lumend
   ```

The node will then fast-forward via state sync instead of replaying the full chain.

### Becoming a validator (single path)

Once your node is synced and stable:

1. **Create or import the validator wallet on the node host**  
   ```bash
   lumend keys add validator --home ~/.lumen --keyring-backend test
   # or, to import an existing mnemonic:
   lumend keys add validator --home ~/.lumen --keyring-backend test --recover
   ```
   Save the mnemonic **off-host** before proceeding.

2. **Fund the validator account**  
   Send LMN to the address:
   ```bash
   lumend keys show validator -a --home ~/.lumen --keyring-backend test
   ```

3. **Promote this node to validator**  
   From the repo root:
   ```bash
   HOME_DIR=~/.lumen FROM=validator \
     ops/scripts/blockchain/become_validator.sh --moniker "<public-validator-name>"
   ```
   This script will:
   - ensure a PQC key `validator-pqc` exists (and generate it if needed),
   - link the PQC account on-chain,
   - use the existing consensus pubkey from `lumend tendermint show-validator`,
   - broadcast `tx staking create-validator` with a minimal self-delegation,
   - optionally create a structured backup under `~/.lumen/validator-node.bak`.

4. **Stake more tokens (optional, separate step)**  
   Once the validator exists on-chain and PQC is linked:
   ```bash
   HOME_DIR=~/.lumen FROM=validator \
     ops/scripts/blockchain/stake_tokens.sh --amount <NUMulmn>
   ```
   This script refuses to run unless:
   - the address is already a validator on-chain, and  
   - the PQC account is linked.

### Important files

- `bin/` – `lumend` binary used by the scripts (see `ops/README.md` for how to download it).
- `config/` – configuration templates:
  - `validator/` – validator,
  - `fullnode/` – fullnode / sentry,
  - `genesis.json`, `seeds.txt`, `peers.txt`.
- `ops/` – operator toolbox (scripts, Headscale, monitoring, advanced docs).

For network bootstrap (`init_chain`), snapshots, Headscale, monitoring, or advanced tuning, see `ops/README.md`.
