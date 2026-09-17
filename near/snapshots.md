# NEAR Snapshots

**There is no free public NEAR snapshot service any more.** The Pagoda
`near-protocol-public` S3 backups and the FastNEAR free snapshot downloads were
deprecated on 1 June 2025. Guides that tell you to `rclone copy` from
`near_cf://near-protocol-public/backups/...` describe a path that no longer
works as a routine bootstrap.

POSTHUMAN does not publish NEAR snapshots.

## What to use instead

| Situation | Path |
|-----------|------|
| New validator or RPC node | **Epoch Sync** — see the **State sync** guide |
| Shard reassignment / catchup | **State Sync from external storage** — same guide |
| Archival history | request access from [FastNEAR](https://fastnear.com/snapshots), or migrate from your own RPC node — see **Archive & Indexing** |
| Rebuilding a broken node | re-sync; `data/` is disposable |

## If you do copy a database between your own hosts

`neard` uses an LSM-tree store (RocksDB). A final `rsync` pass that compares
only size and mtime will silently miss changed SST files and hand you a corrupt
database:

```bash
# first pass, node still running
rsync -avh --progress /source/.near/data/ /target/.near/data/

# stop the source node, then the final pass
sudo systemctl stop neard
rsync -avh --checksum --delete /source/.near/data/ /target/.near/data/
```

`--checksum` on the final pass is not optional.

Never copy `validator_key.json` to a second host that will run at the same time
as the first. Prove the source node is stopped before starting the target —
see **Keys & custody**.

## Order of operations

If you ever restore from an archive rather than re-syncing: download and extract
**first**, stop the node **last**. The wrong order turns the download time into
downtime.

## Sources

- [docs.fastnear.com — snapshots](https://docs.fastnear.com/snapshots)
- [near-nodes.io — epoch sync](https://near-nodes.io/intro/node-epoch-sync)
- [near-nodes.io — split storage archival](https://near-nodes.io/archival/split-storage-archival)
