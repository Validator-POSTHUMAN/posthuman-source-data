# Disk, Sync Modes and Pruning

Disk is the constraint that ends most Ethereum nodes. It fills, or it is too
slow, and no configuration flag fixes either.

---

## 1. Sync modes, and what they cost

| Mode | What it does | Trust | Disk |
|---|---|---|---|
| **Snap sync** (Geth, Nethermind, Besu) | Downloads a recent state snapshot, then fills history backwards | Trustless — state is verified against block headers | Smallest |
| **Full / staged sync** (Reth, Erigon) | Executes every block from genesis, prunes as it goes | Trustless | Medium |
| **Archive** | Executes every block, keeps every historical state | Trustless | Enormous |
| **Checkpoint sync** (consensus layer) | Starts from a finalised state fetched from a provider | Trusts one state root, once | Smallest |

Snap sync is the default and the right answer for a validator. Checkpoint sync
is the right answer for every beacon node — see **Installation** for provider
verification.

---

## 2. Sizing

Execution layer, from ethereum.org:

| Client | Snap / pruned | Archive |
|---|---|---|
| Geth | 500 GB+ | 12 TB+ |
| Nethermind | 500 GB+ | 12 TB+ |
| Besu | 800 GB+ | 12 TB+ |
| Erigon | ~2 TB full-pruned | 2.5 TB+ |
| Reth | ~1.2 TB full-pruned | 2.2 TB+ |

Consensus layer adds roughly 100–200 GB pruned. Blob data since Deneb, and data
columns since Fusaka's PeerDAS, add a rolling window on top — it is bounded by
the retention period rather than growing forever, but the window grows every
time a BPO fork raises blob throughput.

[EIP-7870](https://eips.ethereum.org/EIPS/eip-7870) recommends **4 TB NVMe**.
2 TB works today and is expected to stop working during 2027. Buying 2 TB now
means migrating later, and migrating a validator is riskier than buying a bigger
disk.

### Disk quality is not negotiable

- NVMe, not SATA, never spinning.
- No QLC. No DRAM-less controllers.
- Yorick Downe's [SSD list](https://gist.github.com/yorickdowne/f3a3e79a573bf35767cd002cc977b038)
  is the community reference for which specific drives keep up.

A node that cannot keep up looks like a node with a peering problem: rising
`sync_distance`, late attestations, low inclusion. Check `iostat -x 5` before
blaming the network.

---

## 3. Pruning by client

### Geth

Geth with `--state.scheme=path` (the default for new nodes since v1.13) prunes
online and needs no manual intervention. Hash-scheme databases from older
installations still need offline pruning, which requires roughly 100 GB of free
space and takes hours with the node stopped.

If you are on the old scheme, the honest move in 2026 is to resync with path
scheme rather than keep pruning it:

````bash
sudo systemctl stop execution
sudo -u execution geth --datadir /var/lib/execution removedb   # confirm carefully
sudo systemctl start execution
````

`removedb` prompts separately for state and ancient data. **Keep the ancient
store** if you want to avoid re-downloading history.

### Nethermind

Full pruning runs online and is configured in the config file:

````json
"Pruning": {
  "Mode": "Hybrid",
  "FullPruningTrigger": "VolumeFreeSpace",
  "FullPruningThresholdMb": 256000
}
````

It needs free space roughly equal to the pruned state while it runs. Plan for it
before the disk is at 90%.

### Besu

Bonsai storage (`--data-storage-format=BONSAI`) keeps only the current state and
is the default for new nodes. There is no separate pruning step.

### Reth

`--full` keeps a pruned node. Finer control is per-table in `reth.toml` under
`[prune.segments]` — you can drop receipts or transaction lookups independently
if you know which RPC methods you need.

### Erigon

Erigon 3 prunes by default. `--prune.mode=archive` keeps everything;
`--prune.mode=minimal` is the smallest useful node.

---

## 4. Consensus layer

Beacon nodes prune states automatically and keep a rolling window of blobs and
data columns. The knobs that matter:

| Client | Flag | Effect |
|---|---|---|
| Lighthouse | `--prune-blobs` (default true) | Drops blobs past retention |
| Lighthouse | `--reconstruct-historic-states` | Off by default; turning it on costs a lot of disk |
| Prysm | `--blob-retention-epochs` | Retention window |
| Teku | `--data-storage-mode=PRUNE` | Default; `ARCHIVE` keeps all states |
| Nimbus | `--history=prune` | Default |

Do not enable historic-state reconstruction on a validator host. It is an
archive feature and it competes with your attestations for disk throughput.

---

## 5. Watching the disk

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh /var/lib/execution /var/lib/consensus
iostat -x 5 3
````

Alert on predicted-full, not on a fixed percentage — a node that fills in 14 days
should page you now, not at 95%:

````yaml
- alert: DiskWillFill
  expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 14*24*3600) < 0
  for: 1h
````

**A validator host that runs out of disk stops attesting and can corrupt its
database on the way down.** This is the most common self-inflicted outage in
staking.

---

## 6. Moving the data directory

Chain data is disposable — it can always be resynced. Keys and the slashing
protection database are not. When moving chain data:

1. Stop the client. Wait for a clean shutdown (`TimeoutStopSec=300`).
2. `rsync -aH --info=progress2` the data directory.
3. Run a **second `rsync --checksum` pass**. Execution and consensus clients use
   LSM-tree databases where size and mtime do not prove equality.
4. Update the unit file, start, and verify sync from the new path.
5. Keep the old copy until the node has been synced and attesting for a day.

## Sources

- [ethereum.org — Run a node, requirements](https://ethereum.org/developers/docs/nodes-and-clients/run-a-node/)
- [EIP-7870](https://eips.ethereum.org/EIPS/eip-7870)
- Client documentation for Geth, Nethermind, Besu, Reth and Erigon
