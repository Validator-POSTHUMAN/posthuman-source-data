# Base Snapshots

Syncing Base from genesis takes days and consumes an enormous number of L1
requests. Restore a snapshot. Base publishes them weekly at
[chain.base.org/snapshots](https://chain.base.org/snapshots).

> **Order of operations.** Download and place the snapshot data **before** the
> node runs for the first time, or with the node stopped. Everything else on
> this page assumes that. Starting the node first and then restoring means
> deleting a partially synced database you just paid for.

---

## 1. Pick the node type before you download

Reth cannot convert between node types after initial sync. Archive cannot become
pruned; pruned cannot become full. Choosing wrong means resyncing from scratch,
so decide now — the trade-offs are on the **Pruning & Storage** tab.

| Preset | Flag | Contents | Use when |
|---|---|---|---|
| Minimal | `--minimal` | latest state + headers + minimum required history | fastest and smallest; you never query history |
| Full | `--full` | default full-node prune window: state, headers, and a bounded window of transactions, receipts and history | a normal RPC node |
| Archive | `--archive` | everything — all transactions, receipts, account and storage history, no pruning | archive queries, indexing, subgraphs |

The CLI lists a single `archive` snapshot because it contains every file;
`--full` and `--minimal` select progressively smaller subsets of it.

Custom pruning is possible but it starts from the archive:
`RETH_PRUNING_ARGS` in `.env.mainnet` applies your own distances, and
**you must download the archive snapshot first** for that to work. A `--full`
download only carries the last 10,064 blocks, so a custom window larger than
that has nothing to prune from.

---

## 2. Install the CLI

```bash
curl -fsSL https://raw.githubusercontent.com/base/base/main/baseup/install | bash
```

Read the script before piping it to a shell on a production host, or take the
release binary from the
[base/base releases](https://github.com/base/base/releases) page instead.

---

## 3. Download

From the cloned `base/base` directory:

```bash
mkdir -p ./reth-data

# Full node, Base Mainnet
base-reth-node download --full --datadir ./reth-data --chain base --resumable

# Minimal node, Base Sepolia
base-reth-node download --minimal --datadir ./reth-data --chain base-sepolia --resumable
```

| Network | `--chain` |
|---|---|
| Base Mainnet | `base` |
| Base Sepolia | `base-sepolia` |

V2 snapshots are many small segmented files rather than one archive, so the
download is resumable and idempotent — it fetches only what is missing.

`--download-concurrency` defaults to `8`. Roughly 2× physical cores is a safe
increase on capable hardware:

```bash
base-reth-node download --full --datadir ./reth-data --chain base --download-concurrency 32
```

### Disk

You need room for the download **and** the extracted data at the same time, and
the extracted data is significantly larger. The sizing formula from the
installation guide exists for this moment:

```
(2 × current chain size) + snapshot size + 20% buffer
```

Check free space before starting, not at 90% through.

---

## 4. Replacing the data on an existing node

```bash
docker compose down
rm -rf ./reth-data/*          # contents, not the directory
base-reth-node download --full --datadir ./reth-data --chain base --resumable
docker compose up -d
```

The chain data must end up **directly inside** `./reth-data`. If you see
`./reth-data/reth/...`, move the contents up one level; the node will not find a
nested database and will start a fresh sync without saying anything useful about
why.

Back up nothing from the old data directory. There is no key, no slashing
database and no unique state in it — a Base node's data is entirely
reconstructible. This is one of the very few places in validator operations
where "delete it and resync" is a correct first move.

---

## 5. Migrating a V1-storage node to V2

Base Mainnet moved to reth V2 storage and V1 snapshots have been decommissioned.
A node still on V1 data has two paths:

| Path | Command | Notes |
|---|---|---|
| Fresh V2 snapshot | `base-reth-node download …` | recommended, much faster |
| In-place migration | `base-reth-node db migrate-v2` | **archival nodes only**, no `--resumable`, expect it to take far longer than a download |

If your V1 pruned node used a pruning distance greater than 10,064 blocks, the
in-place path is not available to you and `--full` will not reproduce your
configuration: pull the **archive** snapshot and re-apply your pruning args.

---

## 6. Proofs snapshots

Only relevant if you run the historical-proofs ExEx
(`RETH_HISTORICAL_PROOFS=true`). Without a snapshot the ExEx backfills for
24–48 hours on mainnet at first start.

V2 proofs snapshots were still pending at the time of writing, so these are
distributed as single archives and need `aria2c` — Cloudflare interrupts the
connection periodically and a plain `wget` will not survive it.

```bash
sudo apt-get install -y aria2

# Mainnet
aria2c -c -x 16 -s 16 "https://mainnet-reth-proofs-snapshots.base.org/$(curl -s https://mainnet-reth-proofs-snapshots.base.org/latest)"

# Sepolia
aria2c -c -x 16 -s 16 "https://sepolia-reth-proofs-snapshots.base.org/$(curl -s https://sepolia-reth-proofs-snapshots.base.org/latest)"
```

Extract, then move the *contents* into the data directory:

```bash
tar -xzvf <snapshot-filename.tar.gz>
# or, for .tar.zst
tar -I zstd -xvf <snapshot-filename.tar.zst>

mv ./reth/* ./reth-data/
rmdir ./reth
```

Same rule as above: `chaindata`, `nodes`, `segments` and friends go directly
inside `./reth-data`, never in a nested `reth/` folder.

---

## 7. Verify the restore

Start the node and confirm it resumed from the snapshot's height rather than
from genesis:

```bash
docker compose up -d
docker compose logs -f execution | head -50

curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  http://127.0.0.1:8545 | jq -r .result
```

A number near the snapshot height is a successful restore. A number near zero
means the node did not find the database — check the directory nesting first,
then permissions on `./reth-data`.

Then run the four verification checks from the **installation guide**, in
order. A restored node that answers `eth_chainId` is not yet a synced node.

---

## Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `Archive extracted, but output verification failed` | a newer snapshot was published mid-download | interrupt and re-run; the download is idempotent and fetches only the diff |
| Node starts a fresh sync after restore | data nested in `./reth-data/reth/` | move the contents up one level |
| Permission errors on `./reth-data` | the directory was created by `sudo docker` | `chown` it to the operator account and stop using `sudo` for compose |
| Out of disk mid-extract | the `2 ×` term in the sizing formula was skipped | provision more, or use `--minimal` |
| Database errors after restore | the node was running while the data changed | `docker compose down`, clear, restore again |

---

## Related

- **Pruning & Storage** — the node-type decision in full
- **Installation Guide** — the verification sequence after a restore
- **Troubleshooting** — sync that starts and then stops
