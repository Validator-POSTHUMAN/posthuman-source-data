# Celestia Testnet Snapshot

**Network:** Mocha-4 pruned consensus node  
**DB backend:** PebbleDB  
**Cadence:** every 4 hours via POSTHUMAN snapshot automation  
**Download:** `https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4`

> Up-to-date height, build time, size, and snapshot file name are published at
> `snapshot.json` alongside the snapshot file.

## Quick restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "${SERVICE_NAME}"
if [ -f "${CELESTIA_HOME}/data/priv_validator_state.json" ]; then
  cp "${CELESTIA_HOME}/data/priv_validator_state.json" "${CELESTIA_HOME}/priv_validator_state.json.backup"
fi
rm -rf "${CELESTIA_HOME}/data"

curl -fL https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "${CELESTIA_HOME}"

sed -i -e 's|^db_backend *=.*|db_backend = "pebbledb"|' \
  "${CELESTIA_HOME}/config/config.toml"

if grep -q '^app-db-backend' "${CELESTIA_HOME}/config/app.toml"; then
  sed -i 's|^app-db-backend *=.*|app-db-backend = "pebbledb"|' \
    "${CELESTIA_HOME}/config/app.toml"
else
  printf '\napp-db-backend = "pebbledb"\n' >> "${CELESTIA_HOME}/config/app.toml"
fi

if [ -f "${CELESTIA_HOME}/priv_validator_state.json.backup" ]; then
  mv "${CELESTIA_HOME}/priv_validator_state.json.backup" "${CELESTIA_HOME}/data/priv_validator_state.json"
fi
sudo systemctl restart "${SERVICE_NAME}" && sudo journalctl -u "${SERVICE_NAME}" -f
```

For validator recovery, preserving and restoring `priv_validator_state.json` is
mandatory. Never replace it with an older value from a snapshot.

The pipeline keeps the PebbleDB snapshot pruned and ready for rapid validator or full-node recovery. Browse the current build at [https://snapshots.posthuman.digital/celestia-testnet/](https://snapshots.posthuman.digital/celestia-testnet/).

Each bundle is generated on POSTHUMAN bare-metal infrastructure, pruned via `cosmprund`, and delivered worldwide through Cloudflare R2 + Workers.
