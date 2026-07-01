# Celestia — One-Liner Manager

POSTHUMAN maintains a helper script for installing and managing Celestia
consensus and Data Availability nodes.

## Repository

```text
https://github.com/Validator-POSTHUMAN/celestia-oneliner
```

Run:

```bash
bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

For a persistent terminal:

```bash
screen -S celestia-manager
bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

## Current Version Matrix

- Mainnet chain ID: `celestia`
- Recommended consensus wrapper: `v9.0.4`
- Current protocol app before activation: `v8`
- Signaled app v9 height: `11771698`
- POSTHUMAN consensus snapshot DB: PebbleDB
- Celestia DA node version: `v0.31.3`
- Go: `1.24.1+`

Before installing, check whether mainnet has already passed the app v9 upgrade
height:

```bash
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.sync_info.latest_block_height'
```

If the one-liner default version lags behind this page, override versions
explicitly:

```bash
export NETWORK_TYPE=mainnet
export APP_VERSION=v9.0.4
export BRIDGE_VERSION=v0.31.3

bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

## What the Manager Covers

- Consensus node install and update.
- Pruned or archive node profile.
- Snapshot restore.
- RPC/API/gRPC exposure controls.
- Firewall helper.
- Validator wallet and validator transaction helpers.
- Data Availability nodes:
  - bridge node
  - full storage node
  - light node

## POSTHUMAN Mainnet Services

- Explorer: https://explorer.posthuman.digital/celestia
- RPC: https://rpc-celestia-mainnet.posthuman.digital
- REST: https://rest-celestia-mainnet.posthuman.digital
- gRPC: https://grpc-celestia-mainnet.posthuman.digital
- Snapshots: https://snapshots.posthuman.digital/celestia-mainnet/
- Peer: `955c18c98d5012ee510a0485bf1a6c23b18caae4@5.61.208.27:41656`
- Addrbook: `https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json`

## Manual Snapshot Restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "$SERVICE_NAME"
cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup" 2>/dev/null || true
rm -rf "$CELESTIA_HOME/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$CELESTIA_HOME"

if [ -f "$CELESTIA_HOME/priv_validator_state.json.backup" ]; then
  mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
     "$CELESTIA_HOME/data/priv_validator_state.json"
fi

sudo systemctl restart "$SERVICE_NAME"
```

Validate `snapshot.json` against a trusted live RPC before restore. Do not use
the consensus snapshot for bridge/full/light node stores. The current
POSTHUMAN consensus snapshot uses PebbleDB, so the restored node must have
`db_backend = "pebbledb"` and `app-db-backend = "pebbledb"` configured.

## Safety Notes

- Back up validator keys and `priv_validator_state.json` before deleting data.
- Do not broadcast validator, governance, staking, unjail, or PayForBlob
  transactions without reviewing signer, account, sequence, gas, fees, and
  messages.
- Do not expose bridge JSON-RPC publicly unless auth, firewall, proxy, and rate
  limits are intentionally configured.
- Verify service health after every install or update.
