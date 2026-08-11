# Gnoland Sapphire Snapshot

POSTHUMAN publishes a verified LZ4 snapshot from a dedicated non-signing
Sapphire RPC node.

- Latest archive:
  https://snapshots-gnoland.posthuman.digital/gnoland_sapphire-1-latest.tar.lz4
- SHA-256:
  https://snapshots-gnoland.posthuman.digital/SHA256SUMS
- Metadata:
  https://snapshots-gnoland.posthuman.digital/snapshot.json

The archive contains only `db/` and `wal/`. It never contains `secrets/`,
configuration, genesis, or validator signer state.

## Restore

Set the data directory used by your service:

```bash
GNO_HOME="$HOME/gnoland-sapphire"
DATA_DIR="$GNO_HOME/data"
SNAPSHOT_URL=https://snapshots-gnoland.posthuman.digital
TMP_DIR=$(mktemp -d)
BACKUP_DIR="$HOME/gnoland-backup-$(date -u +%Y%m%dT%H%M%SZ)"
```

Stop the service and back up identity, configuration, and genesis:

```bash
sudo systemctl stop gnoland.service
install -d -m 0700 "$BACKUP_DIR"
cp -a "$DATA_DIR/secrets" "$DATA_DIR/config" "$DATA_DIR/genesis.json" \
  "$BACKUP_DIR/"
```

Download and verify the archive before replacing data:

```bash
curl -fL --retry 3 \
  -o "$TMP_DIR/gnoland_sapphire-1-latest.tar.lz4" \
  "$SNAPSHOT_URL/gnoland_sapphire-1-latest.tar.lz4"
curl -fL --retry 3 \
  -o "$TMP_DIR/SHA256SUMS" \
  "$SNAPSHOT_URL/SHA256SUMS"

cd "$TMP_DIR"
sha256sum -c SHA256SUMS
lz4 -t gnoland_sapphire-1-latest.tar.lz4
if lz4 -dc gnoland_sapphire-1-latest.tar.lz4 \
  | tar -tf - \
  | grep -Evq '^(db|wal)(/|$)'; then
  echo "Unexpected snapshot path"
  exit 1
fi
```

After successful verification, preserve the old database and restore the new
one:

```bash
mv "$DATA_DIR/db" "$BACKUP_DIR/db.old"
mv "$DATA_DIR/wal" "$BACKUP_DIR/wal.old"
lz4 -dc "$TMP_DIR/gnoland_sapphire-1-latest.tar.lz4" \
  | tar -xf - -C "$DATA_DIR"
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

Keep the old `db/` and `wal/` until the restored node is synced and stable.
For a validator, independently verify recent signatures before deleting the
rollback copy.

## AppHash mismatch recovery

If the node crashes with an AppHash mismatch, preserve logs and the current
`db/` + `wal/` for forensics. Restore only those directories from a known
healthy backup or this verified snapshot. Never overwrite validator keys,
node identity, configuration, genesis, or signer state.
