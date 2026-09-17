# NEAR Archival Node and Indexing

An archival node keeps the full chain history from genesis and can answer RPC
queries for any past block. A validator must **not** be an archival node: the
`validator` config profile deliberately discards state it does not need, and
archival storage costs would make block production worse, not better. Run
archival on a separate host.

## Split storage is the supported layout

Since nearcore 1.35.0, archival nodes use **split storage**: a small *hot*
database with recent epochs, and a large *cold* database with all history.
The client only reads hot during normal operation, so cold can live on cheap
spinning disk while hot sits on NVMe.

## Hardware

Source: [near-nodes.io archival hardware](https://near-nodes.io/archival/hardware-archival).

| | Mainnet recommended | Mainnet minimum | Testnet recommended |
|---|---|---|---|
| CPU | 8-core / 16-thread, AVX | same | same |
| RAM | 32 GB | 24 GB | 24 GB |
| Hot storage | 3 TB SSD | 1.5 TB SSD | 1.5 TB SSD |
| Cold storage | 115 TB non-SSD | 105 TB non-SSD | 15 TB non-SSD |

Cold storage grows continuously. Size for growth, monitor every mount, and
check *all* of them — not just `/`:

```bash
df -h | grep -v 'tmpfs\|udev\|loop'
```

## Configuration

Initialise with the archival profile:

```bash
neard --home ~/.near init --chain-id mainnet --download-genesis --download-config archival
```

Then the split-storage fields in `config.json`:

```json
{
  "archive": true,
  "save_trie_changes": true,
  "store":       { "path": "hot-data" },
  "cold_store":  { "path": "cold-data" },
  "split_storage": { "enable_split_storage_view_client": true }
}
```

| Field | Meaning |
|-------|---------|
| `archive` | keep data for all blocks |
| `save_trie_changes` | store the `TrieChanges` column needed for garbage collection |
| `store.path` | hot database, relative to NEAR home |
| `cold_store.path` | cold database, relative to NEAR home |
| `split_storage.enable_split_storage_view_client` | query cold storage in view-client requests, so the node actually serves archival queries rather than merely storing history |

Applied with `jq` against an existing config:

```bash
NEAR_HOME=$HOME/.near
cp $NEAR_HOME/config.json $NEAR_HOME/config.json.backup
cat <<< $(jq '.save_trie_changes = true
  | .cold_store = .store
  | .cold_store.path = "cold-data"
  | .store.path = "hot-data"
  | .split_storage.enable_split_storage_view_client = true' \
  $NEAR_HOME/config.json) > $NEAR_HOME/config.json
sudo systemctl restart neard
```

## Bootstrapping the history

**The free public snapshot flow is gone.** Pagoda's `near-protocol-public` S3
snapshots were the standard path for years; free nearcore data snapshots were
deprecated on 1 June 2025, and the NEAR Infrastructure Committee now
recommends Epoch Sync plus decentralized state sync instead. Older guides that
tell you to `rclone copy near_cf://near-protocol-public/backups/...` are
describing a service that no longer serves that purpose.

Current options, in order of preference:

1. **Epoch Sync + decentralized state sync** — the supported default for
   regular RPC and validator nodes. See the **State sync** guide.
2. **Archival snapshot access from FastNEAR** — request via
   [fastnear.com/snapshots](https://fastnear.com/snapshots). Have the network,
   node role, target `NEAR_HOME`, and whether you want a single `data/` restore
   or a split hot/cold layout ready before you ask.
3. **Manual migration from your own RPC node** — trustless, little downtime,
   but needs a second RPC node with `gc_num_epochs_to_keep` raised so it stops
   garbage-collecting. The migration runs for days and the node cannot be
   restarted during it. Reference (not a drop-in):
   [`scripts/split_storage_migration.sh`](https://github.com/near/nearcore/blob/master/scripts/split_storage_migration.sh).

## Verify cold storage is advancing

The cold head is exported as a metric. It must move:

```bash
for i in $(seq 1 5); do
  curl -s http://127.0.0.1:3030/metrics | grep cold_head_height
  sleep 60
done
```

A cold head that does not increase means the hot database and the cold database
are incompatible, or the migration did not complete. Do not treat a running
process as proof of a working archival node.

Confirm the node answers historical queries — this is what
`enable_split_storage_view_client` buys you:

```bash
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"block","params":{"block_id":100000000}}' \
  | jq '.result.header.height // .error'
```

A non-archival node returns an "unavailable / garbage collected" error here.

## Indexing on top of archival

- [`near-indexer-for-explorer`](https://github.com/near/near-indexer-for-explorer)
  and the NEAR Lake framework consume the same node stream.
- [FastNEAR NEAR Data API](https://docs.fastnear.com/neardata) and
  [Pikespeak](https://pikespeak.ai/) are hosted alternatives when you need
  analytics rather than your own index.
- For read-only history in day-to-day operations,
  [nearblocks.io](https://nearblocks.io) is usually enough and costs nothing to
  run.

Decide honestly whether you need archival at all. Most validator operations —
uptime, endorsements, pool accounting, rewards — need the last few epochs, which
a regular `rpc` node serves.

## Sources

- [near-nodes.io — split storage for archival nodes](https://near-nodes.io/archival/split-storage-archival)
- [near-nodes.io — archival hardware requirements](https://near-nodes.io/archival/hardware-archival)
- [docs.fastnear.com — snapshots](https://docs.fastnear.com/snapshots)
