# Pruning and Storage on Base

Base produces a block every 2 seconds. That is 43,200 blocks a day and roughly
15.8 million a year, which makes storage the first constraint you hit and the
one that is hardest to fix later.

---

## The decision you cannot reverse

**Reth cannot convert between node types after initial sync.** Archive does not
become pruned. Pruned does not become full. Changing your mind means a fresh
download and a fresh sync.

Decide before the first byte lands on disk.

| Node type | Answers | Does not answer |
|---|---|---|
| Minimal | current state, recent blocks | historical state, old receipts, old transactions by hash |
| Full | current state, plus a bounded recent window of transactions, receipts and history | state or logs older than the window |
| Archive | everything, at every historical block | — |

### What "full" actually means on Base

Reth's `--full` preset retains the last **10,064 blocks**. On Ethereum that is
about 1.4 days. On Base, at 2-second blocks, it is **five to six hours**.

That surprises people who bring Ethereum intuitions across. A Base "full" node
cannot answer `eth_getLogs` for yesterday. If your consumers index events, run
backfills, or query anything older than this morning, `--full` is the wrong
choice and you will discover it in production.

---

## Sizing

```
(2 × current chain size) + snapshot size + 20% buffer
```

- **current chain size** — [base.org/stats](https://base.org/stats)
- **snapshot size** — [chain.base.org/snapshots](https://chain.base.org/snapshots)

Both move. Read them at provisioning time rather than trusting a number written
in a guide, including this one.

The `2 ×` term is not padding. Restoring a snapshot onto an existing node holds
the old database and the new data simultaneously; without it, the first restore
you ever perform fills the disk.

Add separately, if you use them:

- **historical proofs ExEx** — hundreds of GB on top, in `<datadir>/proofs`, and
  it wants higher I/O throughput than the main database
- **log volume** — JSON logs at Base's block rate are not negligible; cap them

---

## Hardware that actually keeps up

| Resource | Requirement | Why |
|---|---|---|
| Disk | locally attached NVMe SSD | reth is I/O-bound; this is the bottleneck in nearly every slow-sync report |
| RAID | RAID 0 across local NVMe | what Base runs in production |
| Filesystem | ext4 | what Base runs in production |
| RAM | 32 GB minimum, 64 GB recommended | page cache is doing real work |
| CPU | 8+ modern cores, good single-core | execution is largely serial |

Networked storage is a downgrade. If you are on AWS EBS, `io2` Block Express is
the only class that survives initial sync — and Base's own recommendation is
still local NVMe over any network volume.

Mount with `noatime`. Leave headroom: an NVMe at 95% full loses write
performance before it loses space, and a reth database that runs out of disk is
a resync.

---

## Custom pruning

`RETH_PRUNING_ARGS` in `.env.mainnet` (or `.env.sepolia`) passes prune distances
straight through to `base-reth-node`:

```bash
RETH_PRUNING_ARGS="--prune.senderrecovery.distance=50000 \
--prune.transactionlookup.distance=50000 \
--prune.receipts.distance=50000 \
--prune.accounthistory.distance=50000 \
--prune.storagehistory.distance=50000 \
--prune.bodies.distance=50000"
```

Three rules, all of them load-bearing:

1. **The distance must be greater than 10,064 blocks.** Below that you are
   asking for less than reth's own full preset retains.
2. **Start from the archive snapshot.** A custom window only works if the data
   is there to prune. Downloading `--full` and then setting a 1,339,200-block
   distance gives you 10,064 blocks and a configuration file that says
   otherwise.
3. **The choice is still permanent.** Custom pruning is a pruned node. It cannot
   become archive later.

For reference, the pruned snapshots Base publishes are built with a distance of
`1_339_200` — about 31 days at 2-second blocks.

### Picking a distance

| Consumer | Needs |
|---|---|
| Wallet / balance reads | current state only — minimal is enough |
| dApp backend reading recent events | days, not hours — set a distance, do not use `--full` |
| Indexer, subgraph, analytics | archive |
| Explorer | archive |
| `eth_getProof`, `debug_executionWitness` | archive plus the proofs ExEx |

Work out the oldest block your consumers will ever ask for, double it, and set
that as the distance. Under-provisioning here produces errors that look like
node bugs and are configuration.

---

## Growth planning

Base's chain size grows continuously and the rate is not constant — it tracks
usage. Two habits keep this from becoming an incident:

- **Alert on predicted-full, not on percent-used.** A disk at 70% that gains
  1% a day is a two-and-a-half week outage notice. A disk at 85% that has been
  flat for a month is fine. Use a linear-prediction alert
  (`predict_linear` in Prometheus) over a 14-day horizon.
- **Re-check the sizing formula at every snapshot restore.** The chain is bigger
  than the last time you did the arithmetic.

When you do run out of headroom, the options in order of disruption:

1. Grow the volume, if the storage layer allows it online.
2. Restore a `--minimal` or pruned snapshot onto a new volume, then cut over.
3. Rebuild the node on larger hardware.

There is no online "prune it now" path from archive to pruned. Plan the volume
for the node type you chose.

---

## Related

- **Snapshots** — downloading each preset, and the V1→V2 migration
- **Installation Guide** — the sizing formula in context
- **Monitoring** — disk free, disk latency and predicted-full alerts
