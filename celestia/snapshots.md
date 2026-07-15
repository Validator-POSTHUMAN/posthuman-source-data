# Celestia Mainnet Snapshot

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

- DB backend: PebbleDB
- Cadence: every 4 hours
- Archive format: `snapshot-latest.tar.lz4`

## Snapshot Endpoint

- Index: https://snapshots.posthuman.digital/celestia-mainnet/
- Metadata: https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json
- Snapshot file: `https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots.posthuman.digital/celestia-mainnet/genesis.json`
- Addrbook: `https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`. Configure both CometBFT and app DB backends as
PebbleDB before starting from this snapshot.

## Preflight

Always compare snapshot metadata with a trusted live RPC before restore:

```bash
curl -fsS https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json | jq .

curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
```

Stop if:

- `chain_id` is not `celestia`;
- metadata height is far ahead of or inconsistent with trusted RPC height;
- snapshot file size is unexpectedly small;
- you cannot preserve keys and validator state.

## Quick Restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"
export SNAP_DIR="$HOME/celestia-mainnet-snapshot-restore"

# Download and validate before stopping the node.
rm -rf "$SNAP_DIR"
mkdir -p "$SNAP_DIR"
curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$SNAP_DIR"
test -d "$SNAP_DIR/data/application.db"

cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup" 2>/dev/null || true

sudo systemctl stop "$SERVICE_NAME"
BACKUP_DIR="$CELESTIA_HOME/data.before-snapshot-$(date +%Y%m%d-%H%M%S)"
if [ -d "$CELESTIA_HOME/data" ]; then
  mv "$CELESTIA_HOME/data" "$BACKUP_DIR"
fi
mv "$SNAP_DIR/data" "$CELESTIA_HOME/data"

sed -i -e 's|^db_backend *=.*|db_backend = "pebbledb"|' \
  "$CELESTIA_HOME/config/config.toml"

if grep -q '^app-db-backend' "$CELESTIA_HOME/config/app.toml"; then
  sed -i 's|^app-db-backend *=.*|app-db-backend = "pebbledb"|' \
    "$CELESTIA_HOME/config/app.toml"
else
  printf '\napp-db-backend = "pebbledb"\n' >> "$CELESTIA_HOME/config/app.toml"
fi

if [ -f "$CELESTIA_HOME/priv_validator_state.json.backup" ]; then
  mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
     "$CELESTIA_HOME/data/priv_validator_state.json"
fi

sudo systemctl start "$SERVICE_NAME"
journalctl -u "$SERVICE_NAME" -f
```

## Verify

```bash
curl -fsS http://127.0.0.1:26657/status | jq -r '
  .result.node_info.network,
  .result.sync_info.latest_block_height,
  .result.sync_info.latest_block_time,
  .result.sync_info.catching_up'
```

The node is recovered when chain ID is `celestia`, block time is fresh, height
advances, and `catching_up=false`.

## Important Boundary

This is a consensus-node snapshot for `celestia-appd`. It is not a
`celestia-node` bridge/full/light node-store snapshot. Do not extract it into
`~/.celestia-bridge`, `~/.celestia-full`, or `~/.celestia-light`.
