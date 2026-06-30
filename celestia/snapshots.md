# Celestia Mainnet Snapshot

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

## Snapshot Endpoint

- Index: https://snapshots.posthuman.digital/celestia-mainnet/
- Metadata: https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json
- Snapshot file: `https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots.posthuman.digital/celestia-mainnet/genesis.json`
- Addrbook: `https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`.

## Preflight

Always compare snapshot metadata with a trusted live RPC before restore:

```bash
curl -fsS https://snapshots.posthuman.digital/celestia-mainnet/snapshot.json | jq .

curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
```

Stop if:

- `chain_id` is not `celestia`;
- metadata height is far ahead of or inconsistent with trusted RPC height;
- snapshot file size is unexpectedly small;
- you cannot preserve keys and validator state.

## Quick Restore

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "$SERVICE_NAME"

cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup" 2>/dev/null || true

rm -rf "$CELESTIA_HOME/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$CELESTIA_HOME"

if [ -f "$CELESTIA_HOME/priv_validator_state.json.backup" ]; then
  mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
     "$CELESTIA_HOME/data/priv_validator_state.json"
fi

sudo systemctl restart "$SERVICE_NAME"
journalctl -u "$SERVICE_NAME" -f
```

## Verify

```bash
curl -fsS http://127.0.0.1:26657/status | jq -r '
  .result.node_info.network,
  .result.sync_info.latest_block_height,
  .result.sync_info.latest_block_time,
  .result.sync_info.catching_up'
```

The node is recovered when chain ID is `celestia`, block time is fresh, height
advances, and `catching_up=false`.

## Important Boundary

This is a consensus-node snapshot for `celestia-appd`. It is not a
`celestia-node` bridge/full/light node-store snapshot. Do not extract it into
`~/.celestia-bridge`, `~/.celestia-full`, or `~/.celestia-light`.
