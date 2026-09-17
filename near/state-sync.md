# NEAR Epoch Sync and State Sync

NEAR has two bootstrap mechanisms and neither is a Cosmos-style state-sync
trust-height handshake. Pick the right one, and know what your `config.json`
actually says.

## Epoch Sync — the current default

Epoch Sync lets a node catch up from genesis without downloading a state
snapshot and without downloading the full header history. Since the free public
snapshot service was deprecated on 1 June 2025, this is the recommended
bootstrap for validators and RPC nodes.

It only needs a fresh boot-node list before the first start:

```bash
BOOT_NODES=$(curl -s -X POST https://rpc.mainnet.near.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"network_info","params":[],"id":"dontcare"}' \
  | jq -r '.result.active_peers as $active | .result.known_producers as $known |
      $active[] as $peer | $known[] | select(.peer_id == $peer.id) |
      "\(.peer_id)@\($peer.addr)"' | paste -sd "," -)

cp ~/.near/config.json ~/.near/config.json.backup
jq --arg newBootNodes "$BOOT_NODES" '.network.boot_nodes = $newBootNodes' \
  ~/.near/config.json > ~/.near/config.tmp && mv ~/.near/config.tmp ~/.near/config.json
sudo systemctl restart neard
```

Use the testnet RPC for a testnet node. A stale or empty boot-node list is the
most common reason a fresh node sits at height 0 with no peers.

## State Sync from external storage

State Sync downloads state parts for a shard from external storage rather than
from peers. It matters in two situations: initial bootstrap of an RPC node, and
**catchup** when a validator is reassigned to a different shard at an epoch
boundary.

```json
{
  "state_sync_enabled": true,
  "state_sync": {
    "sync": {
      "ExternalStorage": {
        "location": { "GCS": { "bucket": "state-parts" } },
        "num_concurrent_requests": 4,
        "num_concurrent_requests_during_catchup": 4
      }
    }
  }
}
```

The reference values ship in the downloadable config. Regenerate a reference
config rather than hand-writing these fields:

```bash
neard --home /tmp/near-ref init --download-genesis --download-config validator --chain-id mainnet
jq '{state_sync_enabled, state_sync, tracked_shards}' /tmp/near-ref/config.json
```

Replace `validator` with `rpc` or `archival` for the other roles.

## Validators track no shards explicitly

Counter-intuitive but correct: a validator should leave the tracking fields
empty.

```json
{
  "tracked_shards": [],
  "tracked_accounts": [],
  "tracked_shard_schedule": []
}
```

Once the node stakes and is accepted, consensus assigns it the shard it must
track, and it switches shards between epochs using State Sync. Hard-coding
`tracked_shards` on a validator makes it carry state it does not need.

## Troubleshooting a sync that will not finish

If State Sync has not completed after ~3 hours, check, in this order:

1. The effective config the node is actually using — not the file you think it
   is using:

   ```bash
   curl -s http://127.0.0.1:3030/debug/client_config | jq \
     '{state_sync_enabled, tracked_shards, archive, block_fetch_horizon}'
   ```

2. Disk space on **every** mount:

   ```bash
   df -h | grep -v 'tmpfs\|udev\|loop'
   ```

3. Peers and height movement:

   ```bash
   curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
     | jq '{height: .result.sync_info.latest_block_height, syncing: .result.sync_info.syncing}'
   ```

If the configuration is correct and sync still stalls, set
`"state_sync_enabled": false` and retry — falling back to peer sync is a valid
diagnostic step, not a workaround to leave in place.

## Sources

- [near-nodes.io — epoch sync](https://near-nodes.io/intro/node-epoch-sync)
- [near-nodes.io — state sync](https://near-nodes.io/rpc/state-sync)
- [nearcore — state sync from external storage](https://github.com/near/nearcore/blob/master/docs/misc/state_sync_from_external_storage.md)
