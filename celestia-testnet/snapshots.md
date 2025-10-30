# Restore Celestia Testnet (Mocha-4) from POSTHUMAN Snapshots

POSTHUMAN rebuilds Celestia testnet (mocha-4) snapshots every 24 hours on production hardware. Files are distributed through Cloudflare R2 at [`https://snapshots.posthuman.digital/celestia-testnet/`](https://snapshots.posthuman.digital/celestia-testnet/).

## Snapshot endpoints

| Purpose            | URL |
| ------------------ | --- |
| Latest archive     | `https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst` |
| Metadata (height, checksum) | `https://snapshots.posthuman.digital/celestia-testnet/snapshot.json` |
| Addrbook           | `https://snapshots.posthuman.digital/celestia-testnet/addrbook.json` |
| Genesis            | `https://snapshots.posthuman.digital/celestia-testnet/genesis.json` |

## Prerequisites

- `zstd`, `curl`, and `jq` installed
- Default home: `$HOME/.celestia-app`
- Systemd unit name assumed to be `celestia-appd`; adjust if you run a different service file.

Set some helper variables:

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"
```

## 1. Stop the node

```bash
sudo systemctl stop "${SERVICE_NAME}"
```

## 2. Back up the validator state

```bash
cp "${CELESTIA_HOME}/data/priv_validator_state.json" \
   "${CELESTIA_HOME}/priv_validator_state.json.backup"
```

## 3. Remove previous data

```bash
rm -rf "${CELESTIA_HOME}/data"
```

## 4. Download the latest snapshot and metadata

```bash
curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst \
  -o /tmp/celestia-testnet-snapshot.tar.zst

curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot.json \
  -o /tmp/celestia-testnet-snapshot.json
```

Optional: inspect the metadata before extracting.

```bash
jq '{chain_id, height, created_at, checksum}' /tmp/celestia-testnet-snapshot.json
```

## 5. Verify the checksum (recommended)

```bash
SNAP_CHECKSUM=$(jq -r '.checksum' /tmp/celestia-testnet-snapshot.json)
echo "${SNAP_CHECKSUM}  /tmp/celestia-testnet-snapshot.tar.zst" | sha256sum --check
```

Continue only when the checksum shows `OK`.

## 6. Extract the snapshot

```bash
tar -I zstd -xf /tmp/celestia-testnet-snapshot.tar.zst -C "${CELESTIA_HOME}"
```

The archive includes the `data/` folder so it lands directly under `${CELESTIA_HOME}`.

## 7. Restore validator state and sync helpers

```bash
mv "${CELESTIA_HOME}/priv_validator_state.json.backup" \
   "${CELESTIA_HOME}/data/priv_validator_state.json"

curl -fL https://snapshots.posthuman.digital/celestia-testnet/addrbook.json \
  -o "${CELESTIA_HOME}/config/addrbook.json"
```

Refresh the genesis file if required:

```bash
curl -fL https://snapshots.posthuman.digital/celestia-testnet/genesis.json \
  -o "${CELESTIA_HOME}/config/genesis.json"
```

## 8. Start the node and tail logs

```bash
sudo systemctl start "${SERVICE_NAME}"
sudo journalctl -u "${SERVICE_NAME}" -f
```

Once the node is running, you can delete the downloaded artifacts:

```bash
rm /tmp/celestia-testnet-snapshot.tar.zst /tmp/celestia-testnet-snapshot.json
```

---

Need a different height or older archive? Browse the directory listing at [https://snapshots.posthuman.digital/celestia-testnet/](https://snapshots.posthuman.digital/celestia-testnet/).
