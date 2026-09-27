# Celestia Mainnet Snapshot

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

- DB backend: PebbleDB
- Publication cadence: every four hours when the source node passes its size
  gate. Publication has been blocked since 2026-09-24 while that gate is
  reviewed, so **read `snapshot_time` from `snapshot.json` and decide whether
  that height is recent enough for you** before restoring.
- Archive format: `snapshot-latest.tar.lz4`
- Resumable: yes. The host answers byte-range requests, so an interrupted
  download continues instead of starting over.

## Snapshot Endpoint

- Index: https://snapshots-celestia-mainnet.posthuman.digital/
- Metadata: https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json
- Snapshot file: `https://snapshots-celestia-mainnet.posthuman.digital/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots-celestia-mainnet.posthuman.digital/genesis.json`
- Addrbook: `https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`. Configure both CometBFT and app DB backends as
PebbleDB before starting from this snapshot.

## Preflight

Always compare snapshot metadata with a trusted live RPC before restore:

```bash
curl -fsS https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json | jq .

curl -fsS https://celestia-rpc.publicnode.com/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
```

Stop if:

- `chain_id` is not `celestia`;
- metadata height is far ahead of or inconsistent with trusted RPC height;
- snapshot file size is unexpectedly small;
- you cannot preserve keys and validator state.

## Quick Restore

Requires `aria2`, `jq` and `lz4`:

```bash
sudo apt update && sudo apt install -y aria2 jq lz4
```

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"
export SNAP_DIR="$HOME/celestia-mainnet-snapshot-restore"

# Download and validate before stopping the node. The archive is fetched to disk
# rather than piped into tar: the host supports byte ranges, so a dropped
# connection resumes, and the published SHA-256 can be checked before anything
# touches live data.
rm -rf "$SNAP_DIR"
mkdir -p "$SNAP_DIR"
curl -fsS https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json \
  -o "$SNAP_DIR/snapshot.json"
EXPECTED_SHA256="$(jq -er '.snapshot_sha256' "$SNAP_DIR/snapshot.json")"
EXPECTED_SIZE="$(jq -er '.snapshot_size_bytes' "$SNAP_DIR/snapshot.json")"

aria2c --continue=true --max-connection-per-server=8 --split=8 \
  --min-split-size=64M --file-allocation=none \
  --dir="$SNAP_DIR" --out=snapshot-latest.tar.lz4 \
  https://snapshots-celestia-mainnet.posthuman.digital/snapshot-latest.tar.lz4

test "$(stat -c %s "$SNAP_DIR/snapshot-latest.tar.lz4")" = "$EXPECTED_SIZE"
printf '%s  %s\n' "$EXPECTED_SHA256" "$SNAP_DIR/snapshot-latest.tar.lz4" | \
  sha256sum --check --strict
lz4 -t "$SNAP_DIR/snapshot-latest.tar.lz4"

lz4 -dc "$SNAP_DIR/snapshot-latest.tar.lz4" | tar -xf - -C "$SNAP_DIR"
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
