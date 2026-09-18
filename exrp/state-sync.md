# XRPL EVM Mainnet state sync

State sync bootstraps a node from a recent application-state snapshot served by
peers over the CometBFT protocol, instead of replaying blocks. It is the
fastest path to a running node and it downloads nothing by hand.

What you give up: history. A state-synced node has no blocks below the
snapshot height. That is correct for a validator and wrong for an explorer
backend.

## Configure

Pick a trust height about 1000 blocks behind the head — close enough to be
inside the retained snapshot window, far enough to be settled.

```bash
NODE_HOME=/var/lib/exrpd/.exrpd
RPC1=https://rpc.exrp.posthuman.digital:443
RPC2=https://cosmos-rpc.xrplevm.org:443

LATEST=$(curl -s "$RPC1/block" | jq -r .result.block.header.height)
TRUST_HEIGHT=$((LATEST - 1000))
TRUST_HASH=$(curl -s "$RPC1/block?height=$TRUST_HEIGHT" | jq -r .result.block_id.hash)

echo "$TRUST_HEIGHT $TRUST_HASH"
```

Cross-check the hash against the second RPC before you trust it. One source
deciding your trust root defeats the point of having a trust root.

```bash
curl -s "$RPC2/block?height=$TRUST_HEIGHT" | jq -r .result.block_id.hash
```

Then in `config.toml`:

```toml
[statesync]
enable = true
rpc_servers = "https://rpc.exrp.posthuman.digital:443,https://cosmos-rpc.xrplevm.org:443"
trust_height = 7750000
trust_hash = "..."
trust_period = "168h0m0s"
```

`rpc_servers` needs at least two entries. They should be genuinely independent
operators — listing the same endpoint twice satisfies the parser and proves
nothing.

## Run

On a **fresh, non-signing** node:

```bash
sudo -u exrpd exrpd tendermint unsafe-reset-all --home "$NODE_HOME" --keep-addr-book
sudo systemctl restart exrpd
sudo journalctl -u exrpd -f
```

Never run a reset command against a home that holds a production
`priv_validator_key.json`. On a signer, bring up a separate fresh node, prove
it healthy, and only then move the key — with the anti-double-sign check done
first.

Expected log shape:

```
INF Discovered new snapshot format=1 hash="0x..." height=7750000 module=statesync
INF Fetching snapshot chunk chunk=4 format=1 height=7750000 module=statesync total=45
INF Applied snapshot chunk to ABCI app chunk=0 format=1 height=7750000 module=statesync total=45
```

## When it fails

`state sync aborted` usually means one of:

- no peer is serving a snapshot in the trust window — move `trust_height`
  closer to the head and retry;
- `rpc_servers` are unreachable, or both point at the same operator;
- `trust_hash` does not belong to `trust_height` — re-derive both from the
  same RPC, then cross-check;
- `client.toml` carries the six-digit `xrplevm_144000-1` chain ID.

Restart first, then re-check the settings. After two clean failures, restore
the published snapshot instead — it has no peer-availability dependency.

## Turn it off afterwards

Once synced, set `enable = false`. Leaving it on means a future restart can
try to state-sync again instead of continuing from local data.

## Verify

```bash
curl -s http://127.0.0.1:26657/status | jq '.result.sync_info'
```

`catching_up=false`, and the app hash at a common height matching an
independent RPC. Height alone proves nothing.
