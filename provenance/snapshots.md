# Restore a Provenance Node from a POSTHUMAN Snapshot

> Snapshot publication is temporarily paused while the backend is resynchronized and the archive is revalidated. Do not use this procedure until `info.json` contains a recent, non-empty height and the snapshot URL returns HTTP 200.

This procedure preserves the existing node data until the replacement archive has been downloaded and inspected.

## 1. Verify the snapshot

```bash
curl -fsSL https://snapshots.provenance.posthuman.digital/info.json
curl -fIL https://snapshots.provenance.posthuman.digital/data_latest.zst
```

Confirm that the reported height and timestamp are recent and that the host has enough free space for both the compressed archive and extracted data.

## 2. Stop the node and back up signing state

```bash
sudo systemctl stop provenanced
backup_dir="$HOME/provenance-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
cp -a "$HOME/.provenanced/config" "$backup_dir/"
cp -a "$HOME/.provenanced/data/priv_validator_state.json" "$backup_dir/"
```

Never restore a validator on a second machine with the same consensus key. Ensure the old signer remains stopped throughout the operation.

## 3. Download and test the archive

```bash
snapshot="$HOME/data_latest.zst"
curl -fL --retry 5 -o "$snapshot" https://snapshots.provenance.posthuman.digital/data_latest.zst
zstd -t "$snapshot"
```

Do not remove the current data directory if either command fails.

## 4. Move the old data aside and extract

```bash
mv "$HOME/.provenanced/data" "$HOME/.provenanced/data.pre-snapshot-$(date +%Y%m%d-%H%M%S)"
zstd -dc "$snapshot" | tar -xf - -C "$HOME/.provenanced"
cp -a "$backup_dir/priv_validator_state.json" "$HOME/.provenanced/data/priv_validator_state.json"
```

Keep the previous data directory until the restored node has been verified.

## 5. Start and verify

```bash
sudo systemctl start provenanced
sudo journalctl -u provenanced -n 100 --no-pager
curl -fsS http://127.0.0.1:26657/status | jq '.result.sync_info'
```

Verify that the height increases, `catching_up` eventually becomes `false`, peers are connected, and no consensus or application errors appear. Remove the old data and downloaded archive only after successful verification.
