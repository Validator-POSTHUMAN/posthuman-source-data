# Celestia Testnet (Mocha-5) — Installation Guide

For a **new non-running** Mocha-5 app node. Existing nodes must follow
[App upgrade and multiplexer](multiplexer.md), not reinitialize their home.

**Reviewed 2026-09-23:** target `v10.2.0-mocha`, commit
`3b77dc2f5b00e1a646a2e9dd98b5c024a0d9ad8a`, app v10 activation **1082619**.
Before activation the multiplexer runs app v9; binary version is not protocol
version. The upgrade guide defines RPC-first order, verification and the
pre-fork/pre-migration-only rollback boundary. Mainnet and Mocha-4 are separate.

POSTHUMAN operates app nodes, not Bridge/Light. DA `v0.34.2-mocha` and its Fibre
namespace are documented in the [Bridge](bridge-node-setup.md) and
[Light](light-node-setup.md) informational guides; Fibre/escrow activation
requires a separate decision.

---

## Prerequisites

**For Validator/Consensus Node** (official requirements):
- **Hardware**: 32 cores, 32 GB RAM, 12 TiB NVMe planning envelope, 1 Gbps bandwidth; see [capacity assumptions](full-node-setup.md)
- **OS**: Ubuntu 24.04 or equivalent with glibc >= 2.38; Ubuntu 22.04 and older unsupported
- **Network**: Stable internet connection

**Note**: These are official requirements for validators. For non-validator full nodes, lower specs may work but are not recommended for production.

---

## 1. Update System and Install Build Tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl tar wget clang pkg-config libssl-dev jq build-essential bsdmainutils git make ncdu gcc chrony liblz4-tool
```

---

## 2. Select the verified multiplexer artifact or toolchain

Prefer the checksum-verified official multiplexer archive and staging commands
in [App upgrade and multiplexer](multiplexer.md). Do not select `standalone`
while Mocha-5 is still on app v9. Do not use Cosmovisor for this upgrade.

If building from source, install Go **1.26.6** through trusted distribution
channels and verify `go version`. Do not reuse the old v9 toolchain assumption.

## 3. Build from the pinned source (alternative to the official archive)

Use a new staging directory without deleting or replacing another checkout:

```bash
set -eu
VERSION="v10.2.0-mocha"
APP_COMMIT="3b77dc2f5b00e1a646a2e9dd98b5c024a0d9ad8a"
test "$(go env GOVERSION)" = "go1.26.6"
BUILD_ROOT="$(mktemp -d -p /tmp celestia-app-build.XXXXXX)"
git clone --filter=blob:none --depth 1 --branch "$VERSION" \
  https://github.com/celestiaorg/celestia-app.git "$BUILD_ROOT/src"
test "$(git -C "$BUILD_ROOT/src" rev-parse HEAD)" = "$APP_COMMIT"
make -C "$BUILD_ROOT/src" build
"$BUILD_ROOT/src/build/celestia-appd" version --long
```

Require `10.2.0-mocha`, the pinned commit and the `multiplexer` build tag.
Review the embedded historical assets as described in the upgrade guide.
Only after review, install the binary for this **new non-running** node;
existing nodes use the controlled upgrade workflow instead of this command:

```bash
make -C "$BUILD_ROOT/src" install
celestia-appd version --long
```

Verify the effective installed binary path before creating a service. Avoid
sharing an executable path with a mainnet or any running node.

---

## 4. Initialize the Node

Initialize with your node name and testnet chain ID:

```bash
# Set variables
MONIKER="<YOUR_NODE_NAME>"
CHAIN_ID="mocha-5"

# Initialize
celestia-appd init "$MONIKER" --chain-id "$CHAIN_ID" --home "$HOME/.celestia-app-mocha-5"
```

This creates: `~/.celestia-app-mocha-5/`

---

## 5. Download Genesis and Address Book

**Important**: Use the official Mocha-5 genesis and the listed community addrbook; verify chain identity before use:

```bash

# Download genesis.json
curl -Ls https://raw.githubusercontent.com/celestiaorg/networks/main/mocha-5/genesis.json \
  -o "$HOME/.celestia-app-mocha-5/config/genesis.json"

# Download addrbook.json (peer list)
curl -Ls https://server-6.itrocket.net/testnet/celestia/addrbook.json \
  -o "$HOME/.celestia-app-mocha-5/config/addrbook.json"

# Verify downloads
ls -lh "$HOME/.celestia-app-mocha-5/config/genesis.json"
ls -lh "$HOME/.celestia-app-mocha-5/config/addrbook.json"
```

---

## 6. Configure Node Settings

### 6.1 Set Minimum Gas Price

```bash
sed -i 's|minimum-gas-prices =.*|minimum-gas-prices = "0.002utia"|g' \
  "$HOME/.celestia-app-mocha-5/config/app.toml"
```

### 6.2 Configure Pruning (Recommended for testnet)

```bash
sed -i -e 's|^pruning *=.*|pruning = "custom"|' "$HOME/.celestia-app-mocha-5/config/app.toml"
sed -i -e 's|^pruning-keep-recent *=.*|pruning-keep-recent = "100"|' "$HOME/.celestia-app-mocha-5/config/app.toml"
sed -i -e 's|^pruning-interval *=.*|pruning-interval = "19"|' "$HOME/.celestia-app-mocha-5/config/app.toml"
```

### 6.3 Disable Indexer (Saves disk space)

```bash
sed -i -e 's|^indexer *=.*|indexer = "null"|' "$HOME/.celestia-app-mocha-5/config/config.toml"
```

### 6.4 Enable Prometheus

```bash
sed -i -e 's|prometheus = false|prometheus = true|' "$HOME/.celestia-app-mocha-5/config/config.toml"
```

### 6.5 Add Peers

The old POSTHUMAN endpoint ending in `:28756` belonged to the retired
Mocha-5 source and must not be used. Select a current public peer, verify its
Mocha-5 identity and reachability, and replace every placeholder before use.

```bash
# Independently verified public Mocha-5 peer
PEERS="<VERIFIED_MOCHA_5_NODE_ID>@<PUBLIC_P2P_HOST>:<P2P_PORT>"

# Update config (adjust as needed based on available peers)
sed -i -e "/^\[p2p\]/,/^\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = \"$PEERS\"/}" \
  "$HOME/.celestia-app-mocha-5/config/config.toml"
```

---

### 6.6 v10 configuration preflight

Before startup, follow [Configuration preflight](multiplexer.md#configuration-preflight):
ensure the top-level app ABCI `address` matches `proxy_app`, preserve loopback
binds and keep `priv_validator_grpc_laddr = ""` when Fibre is not operated.
Do not blindly apply `config sync` or change ports to resolve a mismatch.

## 7. Create Systemd Service

```bash
sudo tee /etc/systemd/system/celestia-appd-testnet.service > /dev/null <<EOF
[Unit]
Description=Celestia Node (Mocha-5 Testnet)
After=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/.celestia-app-mocha-5
ExecStart=$(which celestia-appd) start --home $HOME/.celestia-app-mocha-5
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

**Note**: Service name is `celestia-appd-testnet` to distinguish from mainnet if running both.

---

## 8. Download and Apply Snapshot

POSTHUMAN does not currently publish a Mocha-5 snapshot. Use the verified
ITRocket feed at `https://server-6.itrocket.net/testnet/celestia/`. Check
`.current_state.json`, verify the live RPC identifies as `mocha-5`, download
the exact listed file before stopping the node, and validate the complete
archive with `lz4 -t`.

Before replacing validator data, preserve the local consensus key and newest
`priv_validator_state.json`. Never use signer state from a snapshot. Keep the
old data directory as rollback material until the restored node is synced and
verified.

## 9. Start the Node

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable celestia-appd-testnet

# Start service
sudo systemctl start celestia-appd-testnet

# View logs
sudo journalctl -u celestia-appd-testnet -f -o cat
```

---

## 10. Verify Node Status

### Check Sync Status

```bash
celestia-appd status --home "$HOME/.celestia-app-mocha-5" 2>&1 | jq .SyncInfo
```

Look for `"catching_up": false` when fully synced.

### Check Block Height

```bash
celestia-appd status --home "$HOME/.celestia-app-mocha-5" 2>&1 | jq .SyncInfo.latest_block_height
```

---

## 11. Create or Restore Wallet

Optional operator-controlled onboarding, not part of an app upgrade. Keep
wallet recovery material out of chat, logs and agent context. Never import or
copy a consensus key through these wallet steps.

### Create New Wallet

```bash
WALLET="wallet-testnet"
celestia-appd --home "$HOME/.celestia-app-mocha-5" keys add "$WALLET"
```

**Save the mnemonic securely!**

### Restore Existing Wallet

```bash
WALLET="wallet-testnet"
celestia-appd --home "$HOME/.celestia-app-mocha-5" keys add "$WALLET" --recover
```

### Save Wallet Address

```bash
WALLET_ADDRESS=$(celestia-appd --home "$HOME/.celestia-app-mocha-5" keys show "$WALLET" -a)
echo "export WALLET_ADDRESS_TESTNET=$WALLET_ADDRESS" >> "$HOME/.bash_profile"
source "$HOME/.bash_profile"
echo "Testnet wallet: $WALLET_ADDRESS"
```

---

## 12. Get Testnet Tokens

Request testnet TIA from the faucet:

- **Celestia Discord**: https://discord.com/invite/celestiacommunity
  - Go to #mocha-faucet channel
  - Request tokens with your address

### Check Balance

```bash
celestia-appd --home "$HOME/.celestia-app-mocha-5" query bank balances "$WALLET_ADDRESS"
```

---

## 13. Create Validator

Optional new-validator transaction, requiring a separate operator decision;
never repeat it for an existing validator upgrade. After sync and funding:

```bash
celestia-appd tx staking create-validator \
  --amount=1000000utia \
  --pubkey=$(celestia-appd --home "$HOME/.celestia-app-mocha-5" tendermint show-validator) \
  --moniker="<YOUR_NODE_NAME>" \
  --chain-id=mocha-5 --home "$HOME/.celestia-app-mocha-5" \
  --commission-rate="0.10" \
  --commission-max-rate="0.20" \
  --commission-max-change-rate="0.01" \
  --min-self-delegation="1" \
  --gas=300000 \
  --fees=2000utia \
  --from="$WALLET"
```

---

## Useful Commands

### Service Status

```bash
sudo systemctl status celestia-appd-testnet
```

### Stop Node

```bash
sudo systemctl stop celestia-appd-testnet
```

### Node Info

```bash
celestia-appd status --home "$HOME/.celestia-app-mocha-5" 2>&1 | jq
```

---

## Security

1. **Firewall Configuration**
   ```bash
   sudo ufw default allow outgoing
   sudo ufw default deny incoming
   sudo ufw allow ssh/tcp
   sudo ufw allow 26656/tcp
   sudo ufw enable
   ```

2. **Signer custody**: Follow [Keys and signer boundaries](keys.md); preserve the existing key and newest signer state without exposing or moving them.
3. **SSH Key Auth**: Disable password authentication
4. **Monitoring**: Setup Prometheus/Grafana

---

## Retirement boundary

There is no copy-paste validator uninstall procedure here. Decommissioning,
data deletion, key handling or signer migration requires a separately reviewed
plan with verified recovery evidence and duplicate-signer fencing. Never use
installation or retirement steps as a database or signer-state rollback.

---

## Resources

- **Mocha-5 snapshots (ITRocket)**: https://server-6.itrocket.net/testnet/celestia/
- **Mocha-5 RPC (ITRocket)**: https://celestia-testnet-rpc.itrocket.net
- **Discord Faucet**: https://discord.com/invite/celestiacommunity
- **Official Testnet Docs**: https://docs.celestia.org/nodes/mocha-testnet

---

**Last Updated**: 2026-09-23 | v10.2.0-mocha | App v10 height: 1082619 | Chain ID: mocha-5
