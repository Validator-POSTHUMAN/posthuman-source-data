# XRPL EVM Testnet snapshot

Metadata: <https://snapshots.exrp-testnet.posthuman.digital/info.json>

Archive: <https://snapshots.exrp-testnet.posthuman.digital/data_latest.zst>

The archive contains `data/` and is compressed with Zstandard. Inspect the
metadata and confirm that the snapshot is recent before use.

## Restore

Snapshot restore is intended for non-signing nodes or a fully fenced
replacement node. An active validator must retain its original
`priv_validator_state.json` and must never run two signers with the same key.

```bash
NODE_HOME=/var/lib/exrpd/.exrpd
sudo systemctl stop exrpd

sudo cp "$NODE_HOME/data/priv_validator_state.json" \
  "$NODE_HOME/priv_validator_state.json.backup"
sudo mv "$NODE_HOME/data" "$NODE_HOME/data.pre-snapshot"

curl -fL https://snapshots.exrp-testnet.posthuman.digital/data_latest.zst \
  -o /tmp/exrp-testnet-data.zst
zstd -t /tmp/exrp-testnet-data.zst
sudo tar --use-compress-program=unzstd -xf /tmp/exrp-testnet-data.zst \
  -C "$NODE_HOME"

sudo cp "$NODE_HOME/priv_validator_state.json.backup" \
  "$NODE_HOME/data/priv_validator_state.json"
sudo chown -R exrpd:exrpd "$NODE_HOME/data"
sudo systemctl start exrpd
```

Verify local height and block time against
<https://cosmos-rpc.testnet.xrplevm.org/status> before removing the rollback
directory.

