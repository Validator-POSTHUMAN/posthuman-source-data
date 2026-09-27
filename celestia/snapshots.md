# Celestia Mainnet Snapshot


> **The POSTHUMAN Celestia archive is not a usable restore source right now.**
> On 2026-09-27 a restore from it produced `APP HASH MISMATCH DETECTED at height
> 14443346` and the node stopped advancing; the same node, on the database it ran
> before the restore, crossed that height immediately. The archive is pruned
> offline with `cosmprund`, and that rewritten state does not reproduce the
> network's app hash. Until the publishing pipeline is rebuilt and a restore is
> proven end to end, use the third-party source below. `snapshot.json`,
> `genesis.json` and `addrbook.json` on that host remain correct and useful.

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

- DB backend: PebbleDB
- Publication cadence: every four hours. Publication stalled between 2026-09-24
  and 2026-09-27 on the publisher's source-size gate and resumed once that gate
  was raised, so read `snapshot_time` from `snapshot.json` rather than assuming
  freshness.
- Archive format: `snapshot-latest.tar.lz4`
- Resumable: yes. The host answers byte-range requests, so an interrupted
  download continues instead of starting over.
- Restore-verified: **no.** See the notice above; the metadata, genesis and
  address book on this host are fine, the archive is not a restore source today.

## Snapshot Endpoint

- Index: https://snapshots-celestia-mainnet.posthuman.digital/
- Metadata: https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json
- Snapshot file: `https://snapshots-celestia-mainnet.posthuman.digital/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots-celestia-mainnet.posthuman.digital/genesis.json`
- Addrbook: `https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`. Configure both CometBFT and app DB backends as
PebbleDB before starting from this snapshot.

### Restore source while ours is withdrawn

ITRocket publishes a PebbleDB Celestia snapshot and a machine-readable index.
Measured on 2026-09-27: `celestia_2026-09-27_14439541_snap.tar.lz4`, height
`14439541`, 3.0 GiB, `HEAD` 200, and a byte-range request answers `206`, so
`aria2c --continue` works. It is the same provider POSTHUMAN used for its own
2026-09-18 Celestia rebuild, which restored cleanly. The Quick Restore below
reads the current file name from that index rather than hard-coding a height.

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

STATE_URL="https://server-1.itrocket.net/mainnet/celestia/.current_state.json"
SNAP_BASE="https://server-1.itrocket.net/mainnet/celestia"
curl -fsS "$STATE_URL" -o "$SNAP_DIR/state.json"
SNAP_NAME="$(jq -er '.snapshot_name' "$SNAP_DIR/state.json")"
SNAP_HEIGHT="$(jq -er '.snapshot_height' "$SNAP_DIR/state.json")"
echo "candidate $SNAP_NAME at height $SNAP_HEIGHT"

aria2c --continue=true --max-connection-per-server=8 --split=8 \
  --min-split-size=64M --file-allocation=none \
  --dir="$SNAP_DIR" --out="$SNAP_NAME" "$SNAP_BASE/$SNAP_NAME"
lz4 -t "$SNAP_DIR/$SNAP_NAME"

lz4 -dc "$SNAP_DIR/$SNAP_NAME" | tar -xf - -C "$SNAP_DIR"
test -d "$SNAP_DIR/data/application.db"

# This provider publishes no checksum next to the archive, so the integrity proof
# is `lz4 -t` plus the layout check above, and the height is confirmed against two
# live RPCs in the preflight. Ours will carry a SHA-256 again when it returns.

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
