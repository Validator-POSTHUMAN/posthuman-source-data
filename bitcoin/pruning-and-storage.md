# Pruning, Storage and Fast Sync

## What the chain actually costs

v31.1 ships these as its own size assumptions for mainnet:

| | Size |
|---|---|
| Block data | **856 GB** |
| Chainstate (UTXO set) | **14 GB** |
| `txindex=1` | ~50 GB on top |
| `blockfilterindex=1` | ~10 GB on top |

Blocks grow by roughly 55–60 GB per year at full blocks. The chainstate grows
with the UTXO set, not with time, and can shrink. Size the volume for at least
two years or plan to grow it online.

Check what your node is using:

````bash
bitcoin-cli getblockchaininfo | jq '{size_on_disk, pruned, prune_height, automatic_pruning, prune_target_size}'
du -sh /var/lib/bitcoind/{blocks,chainstate,indexes} 2>/dev/null
````

## Archive or pruned — decide before the first sync

| | Archive (`txindex=1`) | Pruned (`prune=<MiB>`) |
|---|---|---|
| Disk | 900 GB+ | as low as ~10 GB |
| Serves historical blocks to peers | yes | no |
| `getrawtransaction` for any txid | yes | recent only |
| Electrum server, explorer, indexer backend | yes | **no** |
| Lightning node backend | yes | yes, with care |
| Wallet rescan from an old birthday | yes | **no** |

`prune` and `txindex` are mutually exclusive, and switching either way requires
`-reindex` — a full revalidation from genesis, hours to days. This is the one
decision to get right before you start.

`prune=550` is the minimum (550 MiB). Realistic values: `prune=50000` (50 GB)
for a Lightning backend with room for reorg depth, `prune=550000` (550 GB) for
a node that keeps most history but caps growth.

Pruning is not retroactive in the way people expect: setting `prune` on an
existing archive node deletes old blocks, but the space is only released as the
node passes the next prune checkpoint, and the indexes do not shrink. You can
also prune manually up to a height:

````bash
bitcoin-cli pruneblockchain 900000
````

### Pruned nodes and Lightning

A pruned node works as a Lightning backend, but the channel database must never
need a block older than your prune horizon. LND and Core Lightning both handle
this, and both will fail at exactly the wrong moment — during a force-close
that requires an old block — if the horizon is too tight. Keep at least
`prune=50000`, and prefer an archive node for anything holding meaningful
channel balances.

## assumeutxo — a usable node in minutes

Normal IBD validates every block from genesis before the node is usable.
`assumeutxo` loads a UTXO snapshot at a fixed height, gives you a working node
against the network tip almost immediately, and validates the historical blocks
in the background afterwards.

The snapshot is **not trusted**: Core compares its serialised hash against a
value hardcoded in the release, so a snapshot from any source — a mirror, a
torrent, a colleague — is either byte-identical to what the developers
committed or rejected. That is what makes this safe.

v31.1 accepts these mainnet snapshots:

| Height | Block hash |
|---|---|
| 840,000 | `0000000000000000000320283a032748cef8227873ff4872689bf23f1cda83a5` |
| **880,000** | `000000000000000000010b17283c3c400507969a9c2afd1dcf2082ec5cca2880` |

Use the highest one your release supports. Serialised UTXO hash for 880,000:
`dbd190983eaf433ef7c15f78a278ae42c00ef52e0fd2a54953782175fbadcea9`.

### Producing a snapshot yourself

The cleanest source is one of your own synced nodes:

````bash
# on a synced archive node, ~10–20 minutes, ~11 GB output
bitcoin-cli -rpcclienttimeout=0 dumptxoutset /srv/snapshots/utxo-880000.dat rollback=880000
sha256sum /srv/snapshots/utxo-880000.dat
````

`rollback=<height>` temporarily rewinds the chainstate to that height, dumps,
and rolls forward again. The node is unusable while it runs — do not do this on
a node something else depends on.

### Loading it

````bash
# on the new node, started and connected to peers
bitcoin-cli -rpcclienttimeout=0 loadtxoutset /srv/snapshots/utxo-880000.dat
````

Then watch both chainstates converge:

````bash
bitcoin-cli getchainstates | jq
````

You get two: the snapshot chainstate (`validated: false`), which follows the
tip and is what your wallets and services talk to, and the background
chainstate still validating from genesis. When background validation finishes,
the snapshot chainstate is marked validated and the extra one is discarded.
Disk use is roughly doubled for the chainstate until then.

Do not treat the node as fully verified until `getchainstates` shows one
chainstate with `validated: true`. Until that point you have the security of a
correctly-hashed snapshot plus everything after it — strong, but not the same
as having checked every block yourself.

## Making IBD faster

| Lever | Effect |
|---|---|
| `dbcache=8192` (or 16384) during IBD | Largest single factor. Drop back to 4096 afterwards. |
| NVMe rather than SATA SSD | Second largest. Spinning disks are no longer practical for IBD. |
| `par=<cores>` | Script verification is parallel and CPU-bound until `assumevalid`. |
| `blocksonly=1` during IBD | Saves bandwidth; remember to remove it afterwards. |
| assumeutxo | Usable node in minutes instead of hours. |

`assumevalid` is already set to a recent block in every release — v31.1 uses
block 938,343 — so signatures below that height are not re-checked by default.
Setting `assumevalid=0` forces full script validation of the entire history and
multiplies IBD time; do it when you are auditing, not routinely.

## Moving the data directory

````bash
sudo systemctl stop bitcoind
# wait for a clean exit — check the log for "Shutdown: done"
sudo rsync -aH --info=progress2 /var/lib/bitcoind/ /srv/bitcoin/
sudo rsync -aH --checksum /var/lib/bitcoind/ /srv/bitcoin/   # final pass
````

The second pass with `--checksum` is not optional for LevelDB data: size and
mtime are not sufficient to prove two copies of a chainstate match.

Then point `-datadir` at the new path and start. Verify `getblockchaininfo`
returns the same tip you stopped at before deleting anything from the old
location.

## Corruption and recovery

A `bitcoind` killed mid-flush — `SIGKILL`, power loss, a container with a
10-second stop grace period — leaves a corrupt chainstate. Symptoms:
`Error opening block database`, `Corrupted block database detected`, or a node
that refuses to start after an unclean shutdown.

````bash
bitcoind -datadir=/var/lib/bitcoind -reindex-chainstate   # rebuild UTXO set from local blocks, hours
bitcoind -datadir=/var/lib/bitcoind -reindex              # rebuild everything, much longer
````

Try `-reindex-chainstate` first: it reuses the block files you already have.
`-reindex` re-reads and re-validates them and is only needed when the block
files themselves are suspect or you changed `txindex`/`prune`.

The real fix is preventing it: `TimeoutStopSec=1200` in systemd,
`stop_grace_period: 20m` in Compose, and never `kill -9` a syncing node.

## Sources

- [bitcoin/bitcoin — `doc/design/assumeutxo.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/design/assumeutxo.md)
- [bitcoin/bitcoin — `src/kernel/chainparams.cpp` at v31.1](https://github.com/bitcoin/bitcoin/blob/v31.1/src/kernel/chainparams.cpp)
- [bitcoincore.org — v31.1 release notes](https://bitcoincore.org/en/releases/31.1/)
- [bitcoin/bitcoin — `doc/reduce-memory.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/reduce-memory.md)
