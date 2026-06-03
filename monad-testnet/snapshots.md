# Monad Testnet Snapshot Service

Use the Posthuman Monad testnet snapshot to speed up node recovery or bootstrap a new testnet full node.

## Snapshot Details

| Parameter | Value |
|-----------|-------|
| Network | Monad Testnet |
| Chain ID | `10143` |
| Snapshot type | Pruned |
| Format | `tar.lz4` |
| Metadata | `https://snapshots.posthuman.digital/monad/testnet/latest.json` |
| Latest height | `https://snapshots.posthuman.digital/monad/testnet/latest-height.txt` |

> ⚠️ Snapshot restore deletes runtime data. Stop Monad services first and keep backups of keys/configs.

---

## 0. Install Download Tools

```bash
apt update
apt install -y curl jq aria2 lz4
```

`aria2c` should use a single connection with this Worker-backed endpoint.

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

```bash
mkdir -p /root/monad-testnet-backup
cp -a /home/monad/.env /root/monad-testnet-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/node.toml /root/monad-testnet-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/id-secp /root/monad-testnet-backup/ 2>/dev/null || true
cp -a /home/monad/monad-bft/config/id-bls /root/monad-testnet-backup/ 2>/dev/null || true
```

---

## 3. Reset Runtime Workspace

```bash
bash /opt/monad/scripts/reset-workspace.sh
```

Initialize TrieDB if needed:

```bash
/usr/local/bin/monad-mpt --storage /dev/triedb --create
```

---

## 4. Download Snapshot Metadata

```bash
cd /home/monad/monad-bft/snapshots
curl -fsSLO https://snapshots.posthuman.digital/monad/testnet/latest.json
SNAPSHOT_URL=$(jq -r '.artifact.url' latest.json)
CHECKSUM_URL=$(jq -r '.artifact.checksum_url' latest.json)
SNAPSHOT_FILE=$(basename "$SNAPSHOT_URL")
SNAPSHOT_HEIGHT=$(jq -r '.height' latest.json)
```

---

## 5. Download and Verify Snapshot

```bash
aria2c -x 1 -s 1 --continue=true "$SNAPSHOT_URL"
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

## 7. Update Runtime Files

Fetch the latest forkpoint and validators runtime files according to the current Monad testnet documentation before starting services.

If your setup uses MonadInfra URLs, the flow is usually:

```bash
MF_BUCKET=https://bucket.monadinfra.com
VALIDATORS_FILE=/home/monad/monad-bft/config/validators/validators.toml

curl -fsSL $MF_BUCKET/scripts/testnet/download-forkpoint.sh -o /tmp/download-forkpoint.sh
bash /tmp/download-forkpoint.sh
curl -fsSL $MF_BUCKET/validators/testnet/validators.toml -o $VALIDATORS_FILE
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

Expected testnet chain ID: `0x279f` (`10143`).

---

## Safety Notes

- Use this guide for testnet only.
- Do not mix mainnet and testnet snapshots or forkpoints.
- Verify `sha256sum` before importing the snapshot.
- Never delete validator identity files without a tested backup.
- Use `latest.json` for the current artifact name, height and checksum.
