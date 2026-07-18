# Restore MANTRA Chain from a POSTHUMAN Snapshot

This procedure restores a `mantra-1` node from the latest POSTHUMAN pruned
snapshot. Download and verify the archive before stopping the node.

## Prerequisites

```bash
sudo apt update
sudo apt install -y aria2 jq lz4

MANTRA_HOME="${MANTRA_HOME:-$HOME/.mantrachain}"
SERVICE="${SERVICE:-mantrachaind}"
SNAP_DIR="${SNAP_DIR:-$HOME/mantra-snapshot}"
META_URL="https://snapshots-mantra.posthuman.digital/snapshot.json"

mkdir -p "$SNAP_DIR" "$HOME/backups"
```

Make sure there is enough free space for both the downloaded archive and a
temporary rollback copy of the current data directory.

## Download and verify

```bash
curl -fsSL "$META_URL" -o "$SNAP_DIR/snapshot.json"

SNAP_NAME=$(jq -r '.snapshot_name' "$SNAP_DIR/snapshot.json")
SNAP_SHA256=$(jq -r '.snapshot_sha256' "$SNAP_DIR/snapshot.json")
SNAP_URL="https://snapshots-mantra.posthuman.digital/$SNAP_NAME"

aria2c --continue=true \
  --max-connection-per-server=8 \
  --split=8 \
  --min-split-size=64M \
  --file-allocation=none \
  --dir="$SNAP_DIR" \
  --out="$SNAP_NAME" \
  "$SNAP_URL"

printf '%s  %s\n' "$SNAP_SHA256" "$SNAP_DIR/$SNAP_NAME" | sha256sum -c -
lz4 -t "$SNAP_DIR/$SNAP_NAME"
```

Do not continue unless both checks pass.

## Stop, back up, and restore

```bash
sudo systemctl stop "$SERVICE"

BACKUP_TAG=$(date -u +%Y%m%dT%H%M%SZ)
tar -czf "$HOME/backups/mantra-keys-$BACKUP_TAG.tar.gz" \
  -C "$MANTRA_HOME" config/priv_validator_key.json config/node_key.json \
  keyring-file 2>/dev/null || true
chmod 600 "$HOME/backups/mantra-keys-$BACKUP_TAG.tar.gz"

cp "$MANTRA_HOME/data/priv_validator_state.json" \
  "$HOME/backups/mantra-priv-validator-state-$BACKUP_TAG.json"
chmod 600 "$HOME/backups/mantra-priv-validator-state-$BACKUP_TAG.json"

mv "$MANTRA_HOME/data" "$MANTRA_HOME/data.rollback-$BACKUP_TAG"
lz4 -dc "$SNAP_DIR/$SNAP_NAME" | tar -xf - -C "$MANTRA_HOME"

cp "$HOME/backups/mantra-priv-validator-state-$BACKUP_TAG.json" \
  "$MANTRA_HOME/data/priv_validator_state.json"
```

Retaining the original validator state is mandatory. Never start two nodes
with the same consensus key.

## Start and verify

```bash
sudo systemctl start "$SERVICE"
sudo systemctl is-active "$SERVICE"

curl -fsS http://127.0.0.1:26657/status | \
  jq '.result.sync_info | {latest_block_height, catching_up}'
```

Keep the rollback directory until the restored node is synced and stable. If
startup fails, stop the service, move the failed `data` directory aside, move
`data.rollback-$BACKUP_TAG` back to `data`, and start the service again.
