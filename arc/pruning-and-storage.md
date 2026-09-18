# Arc Network mainnet — pruning and storage

Three decisions, and one of them is effectively permanent.

| Decision | Made by | Reversible |
|---|---|---|
| How much history the snapshot restores | `--el-profile` | only by another full restore |
| Whether the EL prunes as it runs | `--full` | yes, on restart |
| How often it prunes | `--prune.block-interval` | yes |

## The profile decides what you can answer

```sh
arc-snapshots download --chain=arc-mainnet --el-profile=<minimal|full|archive> ...
```

| Profile | Keeps | For |
|---|---|---|
| `minimal` | least history — **the default** | a node that only serves the tip |
| `full` | pruned history | the normal operator node |
| `archive` | everything | historical queries, indexers, analytics |

**`--el-profile` defaults to `minimal`, including when you pass an explicit
manifest URL.** An archive node bootstrapped without it is a minimal node
wearing archive flags, and the way you find out is a historical query failing
weeks later. There is no in-place conversion; the fix is another full restore
with the right profile.

Match the profile to the flag you will run with. `--el-profile=full` goes with
`arc-node-execution --full`.

## `--full` on the execution layer

`--full` is **required on the first start** from a pruned snapshot. It
reconciles internal database tables that would otherwise fail a consistency
check. If you do not want pruning afterwards, restart without it once the node
is up.

With `--full`, EL pruning runs on a **128-block** interval as of `v0.7.3`,
changed from `5000`. Frequent small pruning passes instead of rare large ones —
usually better for latency, worse for a disk that is already struggling. To
keep the old behaviour:

```sh
--prune.block-interval=5000
```

`--full` on the **consensus layer** is a separate flag with the same name and a
different job: it bounds CL disk growth. Recommended.

## Backpressure

```sh
--execution-persistence-backpressure
--execution-persistence-backpressure-threshold=16
```

This throttles execution to the speed of disk writes. Without it, on some
hardware, EL memory surges during startup or a long catch-up — because
execution runs ahead of persistence and the difference lives in RAM.

Threshold default is `16` and must be greater than zero. Lower it if you
observe memory pressure. This is the first thing to reach for when an Arc node
is using far more memory than the numbers suggest it should.

Note: on **separated** EL/CL hosts, backpressure additionally requires the EL
to run a WebSocket server exposing the `reth` namespace on port `8546`, because
the CL derives the WebSocket address from `--eth-rpc-endpoint` (http→ws, port
+ 1). Without it, backpressure is silently inactive — the CL starts, retries in
the background, and never says so loudly.

## Sizing

Circle's baseline: **1 TB+ NVMe SSD, TLC**, and "higher clock speed over core
count" for the CPU.

Published snapshot sizes are **testnet only**: about 68 GB compressed EL and
16 GB compressed CL, extracting to roughly 103 GB and 36 GB. Mainnet is a
different chain, live since 2026-09-16, and Circle has not published its
figures.

So size from the baseline, not from the testnet numbers, and measure what you
actually get. A practical planning rule while mainnet figures are unpublished:
leave room for a restore alongside the live data — an interrupted restore that
cannot be retried because the disk is full is a worse position than a slow one.

Reth's own guidance applies to the EL:
<https://reth.rs/run/system-requirements/>

## Watch the disk, not the percentage

```sh
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh "$ARC_EXECUTION" "$ARC_CONSENSUS"
```

Check **all** mounts. A node home on a separate volume makes a full `/` look
like a chain problem, and a full chain volume look like nothing at all until
the node stops.

Disk **write latency** matters more than free space on this network, because it
is what backpressure exists to accommodate. If the EL is falling behind and the
disk is not full, look at latency before looking at anything else.

## Archive nodes

An archive node needs `--el-profile=archive` at restore time and considerably
more than the 1 TB baseline. Run it on its own host: an archive node and a
low-latency RPC node want opposite things from the same disk.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
