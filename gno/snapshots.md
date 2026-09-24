# Gnoland Mainnet Snapshot

POSTHUMAN publishes a verified LZ4 snapshot every six hours from a dedicated
non-signing `gnoland-1` archive RPC node.

- Latest archive:
  https://snapshots-gnoland.posthuman.digital/gnoland_gnoland-1-latest.tar.lz4
- SHA-256:
  https://snapshots-gnoland.posthuman.digital/SHA256SUMS
- Metadata:
  https://snapshots-gnoland.posthuman.digital/snapshot.json

The archive contains only `db/` and `wal/`. It never contains `secrets/`,
configuration, genesis, or validator signer state, so it can be restored into a
node of any role without touching identity.

`snapshot.json` states the exact height and the app hash of the snapshot, which
is what makes an archive verifiable before you trust it.

## Restore

Set the data directory used by your service:

```bash
GNO_HOME="$HOME/gnoland-mainnet"
DATA_DIR="$GNO_HOME/data"
SNAPSHOT_URL=https://snapshots-gnoland.posthuman.digital
SNAPSHOT_FILE=gnoland_gnoland-1-latest.tar.lz4
TMP_DIR=$(mktemp -d)
BACKUP_DIR="$HOME/gnoland-backup-$(date -u +%Y%m%dT%H%M%SZ)"
```

Download and verify **before** touching the running node — the download is the
long part, and a node that is still running loses no blocks meanwhile:

```bash
curl -fL --retry 3 -o "$TMP_DIR/$SNAPSHOT_FILE" "$SNAPSHOT_URL/$SNAPSHOT_FILE"
curl -fL --retry 3 -o "$TMP_DIR/SHA256SUMS" "$SNAPSHOT_URL/SHA256SUMS"

cd "$TMP_DIR"
sha256sum -c SHA256SUMS
lz4 -t "$SNAPSHOT_FILE"
if lz4 -dc "$SNAPSHOT_FILE" \
  | tar -tf - \
  | grep -Evq '^(db|wal)(/|$)'; then
  echo "Unexpected snapshot path"
  exit 1
fi
```

Only now stop the service and back up identity, configuration, and genesis:

```bash
sudo systemctl stop gnoland.service
install -d -m 0700 "$BACKUP_DIR"
cp -a "$DATA_DIR/secrets" "$DATA_DIR/config" "$DATA_DIR/genesis.json" \
  "$BACKUP_DIR/"
```

Preserve the old database and restore the new one:

```bash
mv "$DATA_DIR/db" "$BACKUP_DIR/db.old"
mv "$DATA_DIR/wal" "$BACKUP_DIR/wal.old"
lz4 -dc "$TMP_DIR/$SNAPSHOT_FILE" | tar -xf - -C "$DATA_DIR"
sudo systemctl start gnoland.service
```

Verify chain, progress, and service health:

```bash
systemctl is-active gnoland.service
curl -fsS http://127.0.0.1:26657/status | jq '.result | {
  network: .node_info.network,
  height: .sync_info.latest_block_height,
  catching_up: .sync_info.catching_up,
  voting_power: .validator_info.voting_power
}'
sudo journalctl -u gnoland.service --since '10 minutes ago' --no-pager
```

The reported network must be `gnoland-1`. Keep the old `db/` and `wal/` until
the restored node is synced and stable. For a validator, independently verify
recent signatures before deleting the rollback copy.

## AppHash mismatch recovery

If the node crashes with an AppHash mismatch, preserve logs and the current
`db/` + `wal/` for forensics. Restore only those directories from a known
healthy backup or this verified snapshot. Never overwrite validator keys, node
identity, configuration, genesis, or signer state.
