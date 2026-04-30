# Validator & Operator Guide

This guide covers the essentials for running a Lumen node in production or staging environments.

## Building the Binary

```bash
# Local build (produces build/lumend)
make

# Cross-platform release artifacts (dist/<version>/…)
make build-release
```

Release artifacts contain Linux amd64/arm64 and macOS arm64 binaries plus `SHA256SUMS`.

## Systemd Service

Generate or install the unit file using the helper script:

```bash
# Dry run (prints unit to stdout)
make install-service ARGS="--print-unit"

# Install under /etc/systemd/system/lumend.service (requires sudo)
sudo make install-service
sudo systemctl enable --now lumend
```

The default unit starts the node with:

- `--minimum-gas-prices 0ulmn` (gasless operation)
- REST (`:2327`), gRPC (`:9190`), and gRPC-Web enabled on localhost
- Rate-limit env vars exported to the process (see below)

## Rate-Limit Environment Variables

Set these before launching `lumend` (or edit the systemd unit environment block):

| Variable | Default | Meaning |
|----------|---------|---------|
| `LUMEN_RL_PER_BLOCK` | `5` | Max gasless transactions per block per sender |
| `LUMEN_RL_PER_WINDOW` | `20` | Max gasless transactions within the sliding window |
| `LUMEN_RL_WINDOW_SEC` | `10` | Sliding-window length in seconds |

Example overrides:

```bash
export LUMEN_RL_PER_BLOCK=10
export LUMEN_RL_PER_WINDOW=40
export LUMEN_RL_WINDOW_SEC=30
lumend start --minimum-gas-prices 0ulmn
```

## Useful REST Queries

```bash
API=http://127.0.0.1:2327

# DNS
curl -s "$API/lumen/dns/v1/params" | jq
curl -s "$API/lumen/dns/v1/domain/example.lumen" | jq

# Gateways
curl -s "$API/lumen/gateway/v1/params" | jq
curl -s "$API/lumen/gateway/v1/gateways" | jq '.gateways[] | {id, operator, active}'

# Release metadata
curl -s "$API/lumen/release/params" | jq
curl -s "$API/lumen/release/latest?channel=stable&platform=linux-amd64&kind=daemon" | jq
```

## Networking & Security

- **Ports**: CometBFT listens on `26656` (P2P), `26657` (RPC), `2327` (REST), `9190` (gRPC), `9091` (gRPC-Web). Only expose what you need; `26657` and REST can stay behind a reverse proxy if you prefer.
- **Firewalls**: allow `26656/tcp` from peers/seeds, block public access to `26657` and `2327` unless protected by HTTPS + rate limiting.
- **IPv4/IPv6**: configure `persistent_peers` with dual-stack entries and ensure every peer advertises its `external_address`. For IPv6-only peers use `[addr]:port`.
- **Soft DoS controls**: keep `--minimum-gas-prices 0ulmn` (the rate-limit decorator handles it) and front public endpoints with nginx/Caddy + TLS and fail2ban/`limit_req`.
- **SSH access**: disable root logins, enforce UFW `default deny`, prefer IPv6, and restrict admin hosts.
- **Keys**: prefer encrypted keyrings (file/os) or HSMs. The `test` backend is only acceptable for labs.

## Automated Validator Bootstrap

To chain init + Ed25519 key + PQC + gentx + systemd, run
`devtools/scripts/bootstrap_validator.sh`:

```bash
./devtools/scripts/bootstrap_validator.sh \
  --moniker mon-validator \
  --chain-id lumen-testnet \
  --home /var/lib/lumen \
  --stake 1ulmn \
  --balance 1000ulmn \
  --pqc-passphrase-file ~/.config/lumen/pqc_pass
```

The script:
- runs `lumend init`, creates the `validator` key, and credits the account in genesis;
- generates a local Dilithium key (encrypted if `--pqc-passphrase-file` is provided) and writes it into `genesis.json`;
- creates the `gentx` and runs `collect-gentxs`;
- optionally installs the systemd service (`--install-service`).

Store the Ed25519 mnemonic and PQC passphrase printed by the script securely.

### Full bootstrap on a root server

To provision a bare host (systemd unit already installed, PQC keys coming from HSM/offline), run `devtools/scripts/bootstrap_validator_node.sh` as root:

```bash
sudo MONIKER=my-node \
     CHAIN_ID=lumen \
     PQC_PUB_FILE=/root/validator.pub \
     PQC_PRIV_FILE=/root/validator.priv \
     PQC_PASSPHRASE_FILE=/root/pqc_passphrase \
     devtools/scripts/bootstrap_validator_node.sh
```

The script:
- detects the service `--home` and user automatically (or honors `LUMEN_HOME` / `LUMEN_USER`);
- stops the service, wipes `$LUMEN_HOME`, runs `lumend init`, enforces `minimum-gas-prices = "0ulmn"` in `app.toml`, and creates the `validator` key (keyring `test`);
- credits the address (`GENESIS_BALANCE`, default `1000000000000ulmn`), generates the `gentx` (`GENTX_AMOUNT`), patches `delegator_address` if needed, and re-signs offline;
- imports your Dilithium pair (`PQC_PUB_FILE`, `PQC_PRIV_FILE`, `PQC_PASSPHRASE_FILE`), links PQC to the Ed25519 address, and injects the Genesis entry;
- validates genesis, restores ownership to `LUMEN_USER`, restarts `systemctl restart lumend`, and writes `~/mnemo` (mnemonic) plus `~/wallet` (address/valoper).

Useful env vars: `MONIKER`, `CHAIN_ID`, `KEY_NAME`, `PQC_KEY_NAME`, `GENESIS_BALANCE`, `GENTX_AMOUNT`, `MNEMO_FILE`, `WALLET_FILE`, `MIN_GAS_PRICE`. PQC files must exist (hex format, mode 600). After the run, monitor `journalctl -fu lumend` to ensure the node is producing blocks with no “validator set is empty” errors.

## Backup & Restore

Keep offline (encrypted USB, safe) the following files:

- `config/priv_validator_key.json`
- `config/node_key.json`
- `config/priv_validator_state.json` (re-creatable but useful to resume without double-signing)
- `pqc_keys/keys.json` and `pqc_keys/links.json` plus the passphrase
- Wallet exports (`lumend keys export` or a secure keyring)

To restore a node:
1. Prepare a new `$HOME` (e.g. `/var/lib/lumen`), run `lumend init` to create folders.
2. Replace the files above with the backups (keep 600 permissions).
3. Verify `lumend keys show validator` returns the expected address.
4. If the PQC keystore is encrypted, re-provide the passphrase via `--pqc-passphrase-file`.
5. Restart the service (`systemctl restart lumend`) and monitor the logs to confirm no PQC errors remain.

Losing the PQC key or the Ed25519 key makes recovery impossible; maintain at least two encrypted, tested copies of these critical artifacts.

## Upgrades & Releases

- Use `make build-release` to produce reproducible artifacts.
- Tag releases (`git tag vX.Y.Z && git push origin vX.Y.Z`) after running the validation checklist in [`docs/releases.md`](releases.md).
- Update operators with parameter changes from governance proposals (see [`docs/params.md`](params.md)).
