# Celestia Mainnet Snapshot

**Type:** pruned consensus node (goleveldb)  
**Cadence:** refreshed around every 4 h, served 24/7 from Cloudflare R2  
**Download:** `https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst`

> Latest height, build time, and checksum are published alongside the archive at `snapshot.json`.

## Quick restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "${SERVICE_NAME}"
cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst | \
  tar -I zstd -xf - -C "${CELESTIA_HOME}"

mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

The archive already contains the `data/` directory, so extraction straight into `$CELESTIA_HOME` brings the node back with the pruned state. Snapshots remain available in the public index at [https://snapshots.posthuman.digital/celestia-mainnet/](https://snapshots.posthuman.digital/celestia-mainnet/).

Automated archives are produced on POSTHUMAN bare-metal nodes, pruned with `cosmprund`, and distributed globally via Cloudflare R2 + Workers for consistent low-latency access.
