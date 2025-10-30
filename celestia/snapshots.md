# Restore Celestia Mainnet from POSTHUMAN Snapshots

POSTHUMAN publishes daily pruned Celestia mainnet snapshots from bare-metal validators. Artifacts live at [`https://snapshots.posthuman.digital/celestia-mainnet/`](https://snapshots.posthuman.digital/celestia-mainnet/) and are served directly from Cloudflare R2 for fast, reliable delivery.

## Snapshot endpoints

| Purpose            | URL |
| ------------------ | --- |
| Latest archive     | `https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst` |
| Metadata (height, checksum) | `https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json` |
| Addrbook           | `https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json` |
| Genesis            | `https://snapshots.posthuman.digital/celestia-mainnet/genesis.json` |

## Prerequisites

- `zstd`, `curl`, and `jq` installed
- Default home: `$HOME/.celestia-app`
- Service name used below assumes `celestia-appd`. Adjust if your systemd unit differs.

Set a couple of helper variables to keep the commands tidy:

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

## 3. Remove the old data tree

```bash
rm -rf "${CELESTIA_HOME}/data"
```

## 4. Download the latest snapshot and metadata

```bash
curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst \
  -o /tmp/celestia-mainnet-snapshot.tar.zst

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json \
  -o /tmp/celestia-mainnet-snapshot.json
```

Optional: inspect height and timestamp before proceeding.

```bash
jq '{height, created_at, checksum}' /tmp/celestia-mainnet-snapshot.json
```

## 5. Verify the checksum (recommended)

```bash
SNAP_CHECKSUM=$(jq -r '.checksum' /tmp/celestia-mainnet-snapshot.json)
echo "${SNAP_CHECKSUM}  /tmp/celestia-mainnet-snapshot.tar.zst" | sha256sum --check
```

You should see `OK`. If the check fails, download again before continuing.

## 6. Extract the snapshot

```bash
tar -I zstd -xf /tmp/celestia-mainnet-snapshot.tar.zst -C "${CELESTIA_HOME}"
```

The archive already contains the `data/` directory, so no extra path adjustments are required.

## 7. Restore validator state and supportive files

```bash
mv "${CELESTIA_HOME}/priv_validator_state.json.backup" \
   "${CELESTIA_HOME}/data/priv_validator_state.json"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json \
  -o "${CELESTIA_HOME}/config/addrbook.json"
```

The genesis file rarely changes, but you can refresh it if needed:

```bash
curl -fL https://snapshots.posthuman.digital/celestia-mainnet/genesis.json \
  -o "${CELESTIA_HOME}/config/genesis.json"
```

## 8. Start the node and watch logs

```bash
sudo systemctl start "${SERVICE_NAME}"
sudo journalctl -u "${SERVICE_NAME}" -f
```

Once the node catches up, you can remove the downloaded archive:

```bash
rm /tmp/celestia-mainnet-snapshot.tar.zst /tmp/celestia-mainnet-snapshot.json
```

---

Snapshots refresh every 24 hours. For historical files or automation, browse the directory index at [https://snapshots.posthuman.digital/celestia-mainnet/](https://snapshots.posthuman.digital/celestia-mainnet/).
