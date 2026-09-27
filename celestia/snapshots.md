# Celestia Mainnet Snapshot


> **Restore-verified on 2026-09-27.** This archive was restored end to end on a
> throwaway node: it reached the chain tip, ran 371 blocks past the snapshot
> height with `catching_up=false`, and logged no app-hash divergence. That test
> exists because the previous pipeline pruned the copy offline with `cosmprund`,
> which rewrote the application state and produced an archive that stalled a
> restored node with `APP HASH MISMATCH` at height `14443346`. The publisher no
> longer rewrites anything: the archive is a copy of the node's own pruned data.

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

- DB backend: PebbleDB
- Publication cadence: every four hours. Read `snapshot_time` from
  `snapshot.json` rather than assuming freshness.
- Archive format: `snapshot-latest.tar.lz4`, roughly 3 GB
- Resumable: yes. The host answers byte-range requests, so an interrupted
  download continues instead of starting over.
- Restore-verified: **yes**, 2026-09-27, at height `14445450`. See the notice
  above for what the test actually proved.
- Node parameters behind it: `pruning = custom` / `keep-recent = 100` /
  `interval = 19`, `min-retain-blocks = 300000` (about ten days of blocks),
  `indexer = null`, PebbleDB. The archive inherits exactly those, so it is not an
  archive node and carries no transaction index.

## Snapshot Endpoint

- Index: https://snapshots-celestia-mainnet.posthuman.digital/
- Metadata: https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json
- Snapshot file: `https://snapshots-celestia-mainnet.posthuman.digital/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots-celestia-mainnet.posthuman.digital/genesis.json`
- Addrbook: `https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`. Configure both CometBFT and app DB backends as
PebbleDB before starting from this snapshot.

### An alternative source

Our archive is rebuilt every four hours, so it can be a few hours old. ITRocket
publishes a PebbleDB Celestia snapshot with the same node parameters and a
machine-readable index; measured on 2026-09-27 at height `14439541`, 3.0 GiB,
`HEAD` 200, range `206`. POSTHUMAN restored its own node from that provider twice
in September, so it is a route we have walked rather than a link we found.

It is somebody else's artifact: confirm the height against a live RPC, keep
`priv_validator_key.json` and `priv_validator_state.json` out of the extraction,
and stop the node only after the download and decompression have succeeded.

## Preflight

Always compare snapshot metadata with a trusted live RPC before restore:

```bash
# The candidate you are about to restore, from the source named above.
curl -fsS https://server-1.itrocket.net/mainnet/celestia/.current_state.json | jq .

# Two independent views of the live chain: ours and somebody else's.
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
curl -fsS https://celestia-rpc.publicnode.com/status | \
  jq -r '.result.sync_info.latest_block_height'
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

# Download and validate before stopping the node. Fetched to disk rather than
# piped into tar, so a dropped connection resumes and the archive is proven
# before anything touches live data.
rm -rf "$SNAP_DIR"
install -d -m 0700 "$SNAP_DIR"

SNAP_BASE="https://snapshots-celestia-mainnet.posthuman.digital"
curl -fsS "$SNAP_BASE/snapshot.json" -o "$SNAP_DIR/snapshot.json"
EXPECTED_SHA256="$(jq -er '.snapshot_sha256' "$SNAP_DIR/snapshot.json")"
EXPECTED_SIZE="$(jq -er '.snapshot_size_bytes' "$SNAP_DIR/snapshot.json")"
jq -er '.chain_id == "celestia"' "$SNAP_DIR/snapshot.json"

aria2c --continue=true --max-connection-per-server=8 --split=8 \
  --min-split-size=64M --file-allocation=none \
  --dir="$SNAP_DIR" --out=snapshot-latest.tar.lz4 \
  "$SNAP_BASE/snapshot-latest.tar.lz4"

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
