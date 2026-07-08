# Celestia Testnet Snapshot

**Network:** Mocha-4 pruned consensus node  
**DB backend:** PebbleDB  
**Cadence:** every 4 hours via POSTHUMAN snapshot automation  
**Download:** `https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4`

> Up-to-date height, build time, size, and snapshot file name are published at
> `snapshot.json` alongside the snapshot file.

## Snapshot Endpoint

- Index: https://snapshots.posthuman.digital/celestia-testnet/
- Metadata: https://snapshots.posthuman.digital/celestia-testnet/snapshot.json
- Snapshot file: https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4
- Genesis: https://snapshots.posthuman.digital/celestia-testnet/genesis.json
- Addrbook: https://snapshots.posthuman.digital/celestia-testnet/addrbook.json

## Preflight

Always compare snapshot metadata with the live RPC before using the archive:

```bash
curl -fsS https://snapshots.posthuman.digital/celestia-testnet/snapshot.json | jq .
curl -fsS https://rpc-celestia-testnet.posthuman.digital/status | \
  jq '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
```

Stop and investigate before restoring if:

- `chain_id` is not `mocha-4`.
- RPC is catching up or the RPC height is behind snapshot metadata.
- The snapshot file is unexpectedly small or unavailable.
- You cannot preserve validator keys and `priv_validator_state.json`.

## Quick restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "${SERVICE_NAME}"
if [ -f "${CELESTIA_HOME}/data/priv_validator_state.json" ]; then
  cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
fi
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "${CELESTIA_HOME}"

sed -i -e 's|^db_backend *=.*|db_backend = "pebbledb"|' \
  "${CELESTIA_HOME}/config/config.toml"

if grep -q '^app-db-backend' "${CELESTIA_HOME}/config/app.toml"; then
  sed -i 's|^app-db-backend *=.*|app-db-backend = "pebbledb"|' \
    "${CELESTIA_HOME}/config/app.toml"
else
  printf '\napp-db-backend = "pebbledb"\n' >> "${CELESTIA_HOME}/config/app.toml"
fi

if [ -f "${CELESTIA_HOME}/priv_validator_state.json.backup" ]; then
  mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
fi
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

For validator recovery, preserving and restoring `priv_validator_state.json` is
mandatory. Never replace it with an older value from a snapshot.

The pipeline keeps the PebbleDB snapshot pruned and ready for rapid validator or full-node recovery. Browse the current build at [https://snapshots.posthuman.digital/celestia-testnet/](https://snapshots.posthuman.digital/celestia-testnet/).

Each bundle is generated on POSTHUMAN bare-metal infrastructure, pruned via `cosmprund`, and delivered worldwide through Cloudflare R2 + Workers.
