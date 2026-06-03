# Monad Mainnet Snapshot Service

Use the Posthuman Monad snapshot to speed up node recovery or bootstrap a new full node.

## Snapshot Details

| Parameter | Value |
|-----------|-------|
| Network | Monad Mainnet |
| Chain ID | `143` |
| Snapshot type | Pruned |
| Format | `tar.lz4` |
| Metadata | `https://snapshots.posthuman.digital/monad/mainnet/latest.json` |
| Latest height | `https://snapshots.posthuman.digital/monad/mainnet/latest-height.txt` |

> ⚠️ Snapshot restore is destructive for runtime data. Stop Monad services first and make sure validator keys/configs are backed up.

---

## 1. Stop Monad Services

```bash
systemctl stop monad-bft monad-execution monad-rpc
```

Check that services are stopped:

```bash
systemctl is-active monad-bft monad-execution monad-rpc
```

---

## 2. Backup Important Files

Do not delete validator identity/config files.

```bash
mkdir -p /root/monad-backup
cp -a /home/monad/.env /root/monad-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/node.toml /root/monad-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/id-secp /root/monad-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/id-bls /root/monad-backup/ 2>/dev/null || true
```

---

## 3. Reset Runtime Workspace

```bash
bash /opt/monad/scripts/reset-workspace.sh
```

If `/dev/triedb` is not initialized, create it:

```bash
/usr/local/bin/monad-mpt --storage /dev/triedb --create
```

---

## 4. Download Snapshot Metadata

```bash
cd /home/monad/monad-bft/snapshots
curl -fsSLO https://snapshots.posthuman.digital/monad/mainnet/latest.json
SNAPSHOT_URL=$(jq -r '.artifact.url' latest.json)
CHECKSUM_URL=$(jq -r '.artifact.checksum_url' latest.json)
SNAPSHOT_FILE=$(basename "$SNAPSHOT_URL")
SNAPSHOT_HEIGHT=$(jq -r '.height' latest.json)
```

---

## 5. Download and Verify Snapshot

```bash
aria2c -x 8 -s 8 --continue=true "$SNAPSHOT_URL"
curl -fsSL "$CHECKSUM_URL" -o "${SNAPSHOT_FILE}.sha256"
sha256sum -c "${SNAPSHOT_FILE}.sha256"
```

---

## 6. Extract and Import TrieDB Snapshot

```bash
lz4 -dc "$SNAPSHOT_FILE" | tar -xf - -C /home/monad/monad-bft/snapshots

/usr/local/bin/monad-cli \
  --db /dev/triedb \
  --load_binary_snapshot /home/monad/monad-bft/snapshots \
  --version "$SNAPSHOT_HEIGHT" \
  --sq_thread_cpu 15
```

---

## 7. Update Forkpoint and Validators

```bash
unset REMOTE_VALIDATORS_URL
unset REMOTE_FORKPOINT_URL
MF_BUCKET=https://bucket.monadinfra.com
VALIDATORS_FILE=/home/monad/monad-bft/config/validators/validators.toml

curl -fsSL $MF_BUCKET/scripts/mainnet/download-forkpoint.sh -o /tmp/download-forkpoint.sh
bash /tmp/download-forkpoint.sh
curl -fsSL $MF_BUCKET/validators/mainnet/validators.toml -o $VALIDATORS_FILE
chown monad:monad $VALIDATORS_FILE
```

---

## 8. Fix Ownership and Start Services

```bash
chown -R monad:monad /home/monad/
systemctl start monad-bft monad-execution monad-rpc
```

Watch logs:

```bash
journalctl -u monad-bft -f -o cat
```

Check RPC:

```bash
curl http://localhost:8080/ \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

Expected mainnet chain ID: `0x8f` (`143`).

---

## Safety Notes

- Do not run restore commands on an active validator without planned downtime.
- Never delete `id-secp`, `id-bls`, `.env`, or validator config backups.
- Do not run the same validator identity on two machines at the same time.
- Verify `sha256sum` before importing the snapshot.
- Use `latest.json` for the current artifact name, height and checksum.
