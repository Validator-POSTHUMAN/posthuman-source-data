# Celestia Testnet Snapshot

**Network:** Mocha-4 pruned consensus node  
**Cadence:** refreshed around every 4 h, available 24/7 via Cloudflare R2  
**Download:** `https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst`

> Up-to-date height, build time, and checksum are published at `snapshot.json` alongside the archive.

## Quick restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "${SERVICE_NAME}"
cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst | \
  tar -I zstd -xf - -C "${CELESTIA_HOME}"

mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

The pipeline keeps the archive pruned and ready for rapid validator or full-node recovery. Browse historical builds at [https://snapshots.posthuman.digital/celestia-testnet/](https://snapshots.posthuman.digital/celestia-testnet/).
