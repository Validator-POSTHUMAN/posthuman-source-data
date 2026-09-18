# Arc Network mainnet — snapshots

**Syncing an Arc node from genesis is not supported.** A snapshot is the only
bootstrap, which makes `arc-snapshots` part of the install rather than an
optimisation.

```sh
. ~/.arc_env

arc-snapshots download \
  --chain=arc-mainnet \
  --el-profile=full \
  --execution-path "$ARC_EXECUTION" \
  --consensus-path "$ARC_CONSENSUS"
```

`arc-snapshots` at tag `v0.8.0` accepts `arc-testnet`, `arc-devnet` and
`arc-mainnet` — confirmed in `crates/snapshots/README.md` at that tag. It
queries `https://snapshots.arc.network` for the newest snapshot that has both
layers published, whatever its retention.

## Two different formats in one command

| Layer | Format | Restored by |
|---|---|---|
| Execution | a **reth manifest** listing each database component separately | `arc-node-execution`, invoked by `arc-snapshots` |
| Consensus | a single `.tar.lz4` archive | `arc-snapshots` itself |

The manifest is what lets `--el-profile` fetch part of a snapshot instead of
all of it. `arc-node-execution` must be on `PATH`, or named by
`ARC_EXECUTION_BINARY`, or the execution restore cannot run at all.

## `--el-profile` is not optional in practice

| Value | Keeps | Use with |
|---|---|---|
| `minimal` | least history — **the default** | a node that only needs the tip |
| `full` | pruned history | `arc-node-execution --full` |
| `archive` | everything | an archive node |

It defaults to `minimal` **including when you pass an explicit manifest URL**.
An archive node started from a default restore is a minimal node with archive
flags, and you find out weeks later when a historical query fails.

An explicit `.tar.lz4` execution URL selects the native archive restore and
ignores this flag entirely.

## Never hand it a presigned URL

Automatically resolved manifest URLs carry no query string, and they must not.
Reth derives each component's URL by dropping the manifest's filename and
appending the component's, as plain string concatenation. A signed URL keeps
its query through that step, so the component filename lands on the end of the
query string instead of the path, and every component is fetched from an
address that does not exist.

Use `--chain`, or the API's query-free `{base}/download/{manifestKey}` form.

## Re-running it

| Situation | What happens |
|---|---|
| Layer already holds the requested snapshot | left alone |
| A **newer** snapshot resolves | the layer is replaced, not merged — a full download, and the node moves back to the snapshot's block |
| Layer holds data no restore recorded | **stops and asks for `--force`** |

The third case is the important one. A layer is marked as restored only after
its download *and* extraction have finished, so an interrupted run leaves data
behind with no mark on it. The tool cannot distinguish that from a directory
you filled yourself — by syncing from genesis, or by running a validator — so
it refuses rather than delete someone else's data.

`--force` replaces both layers regardless of what they hold. Use it
deliberately, once.

Each layer records what it holds in a `.snapshot-url` marker file.

## Sizes

Circle publishes **testnet** figures: about 68 GB compressed EL and 16 GB
compressed CL, extracting to roughly 103 GB and 36 GB. On a stable 100 Mbps
link, 10–15 minutes; on a metered link, hours.

Mainnet is a different chain and Circle has not published its sizes. Plan from
the 1 TB baseline and measure what you actually get rather than assuming
testnet numbers transfer.

## Storage v2

From `v0.8.0` Circle publishes snapshots in Reth **V2** storage format. A fresh
install from these does not need the V1→V2 migration. A node restored from an
older V1 snapshot does — read `BREAKING_CHANGES.md#v080` before upgrading such
a node rather than after.

## If automatic resolution fails

Automatic resolution requires the API to publish a **storage v2 listing** for
that chain. If it does not, `arc-snapshots` fails, and there is **no fallback
to any other listing the API serves**. That failure is informative: it means
the chain has no published v2 snapshot pair, not that your command is wrong.

Test it before planning a deployment around it:

```sh
arc-snapshots download --chain=arc-mainnet \
  --el-profile=minimal \
  --execution-path /tmp/arc-probe-el \
  --consensus-path /tmp/arc-probe-cl
```

If it resolves, mainnet snapshots are published. If it does not, the fallback
is an explicit URL pair from Circle, because genesis sync is not an option.

## Restoring onto a running node

There is no signer state to preserve and no double-sign risk — an Arc node is a
follower. The only irreplaceable file in the tree is the **consensus-layer
private key** in `$ARC_CONSENSUS`, written once by `arc-node-consensus init`.
Clearing that directory destroys your node's network identity permanently.

Otherwise: stop both processes, restore, start the EL, then the CL.

```sh
sudo systemctl stop arc-consensus arc-execution
# restore
sudo systemctl start arc-execution
sudo systemctl start arc-consensus
```

Verify against the network, by hash and not only by height:

```sh
cast block-number --rpc-url http://127.0.0.1:8545
cast block-number --rpc-url https://rpc.mainnet.arc.io
```

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
