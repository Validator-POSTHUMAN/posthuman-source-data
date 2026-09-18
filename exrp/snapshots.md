# XRPL EVM Mainnet snapshot

POSTHUMAN publishes a daily Zstandard snapshot of XRPL EVM Mainnet, produced by
a **non-signing** source node whose consensus identity is distinct from every
signer copy and whose voting power is zero.

| | |
|---|---|
| Metadata | <https://snapshots.exrp.posthuman.digital/info.json> |
| Archive | <https://snapshots.exrp.posthuman.digital/data_latest.zst> |
| Format | `tar` + Zstandard, contains `data/` |
| Cadence | daily at `00:40 UTC`, randomized delay up to five minutes |

```bash
curl -s https://snapshots.exrp.posthuman.digital/info.json
# {"height":"7738976","time":"2026-09-17T22:43:04Z","file":"data_latest.zst"}
```

Read `info.json` before downloading. A snapshot older than the unbonding
window is not a shortcut; it is a slow sync with extra steps.

## Order of operations

**Download and extract first. Stop the node last.** The wrong order converts
the download time into downtime, and on a chain this size that is hours rather
than minutes.

## Restore

Snapshot restore is for non-signing nodes or a fully fenced replacement node.
An active validator keeps its original `priv_validator_state.json` and never
runs two signers with the same key.

```bash
NODE_HOME=/var/lib/exrpd/.exrpd

# 1. Download and verify the archive while the node keeps running
curl -fL https://snapshots.exrp.posthuman.digital/data_latest.zst \
  -o /tmp/exrp-mainnet-data.zst
zstd -t /tmp/exrp-mainnet-data.zst
tar --use-compress-program=unzstd -tf /tmp/exrp-mainnet-data.zst | head

# 2. Only now stop the node
sudo systemctl stop exrpd

# 3. Preserve signer state, keep the old data as the rollback
sudo cp "$NODE_HOME/data/priv_validator_state.json" \
  "$NODE_HOME/priv_validator_state.json.backup"
sudo mv "$NODE_HOME/data" "$NODE_HOME/data.pre-snapshot"

# 4. Extract
sudo tar --use-compress-program=unzstd -xf /tmp/exrp-mainnet-data.zst -C "$NODE_HOME"

# 5. Restore signer state and ownership
sudo cp "$NODE_HOME/priv_validator_state.json.backup" \
  "$NODE_HOME/data/priv_validator_state.json"
sudo chown -R exrpd:exrpd "$NODE_HOME/data"

sudo systemctl start exrpd
```

The `tar -tf` listing in step 1 is the step operators skip. A truncated or
wrong-chain archive is indistinguishable from a good one until `data/` has
already been moved aside.

## Verify before deleting the rollback

```bash
H=$(curl -s http://127.0.0.1:26657/status | jq -r .result.sync_info.latest_block_height)
curl -s "http://127.0.0.1:26657/block?height=$H"        | jq -r .result.block.header.app_hash
curl -s "https://cosmos-rpc.xrplevm.org/block?height=$H" | jq -r .result.block.header.app_hash
```

Height advancing, `catching_up=false`, and a matching app hash against an
independent RPC. Only then remove `data.pre-snapshot`.

## If the node diverges after a restore

Check `client.toml` first. A stale `chain-id = "xrplevm_144000-1"` — six digits
instead of seven — causes deterministic app-hash divergence during bootstrap
even with a correct genesis file and a correct binary. This has happened in
production; it does not present as a configuration error in the logs.

## Other providers

The official documentation lists further public snapshot providers, in
`.tar.lz4` as well as `.tar.zst`. Match the extraction command to the archive
format the provider actually publishes:

<https://docs.xrplevm.org/pages/operators/resources/snapshots>
