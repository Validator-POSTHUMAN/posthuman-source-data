# Arc Network mainnet — node installation

Arc Network is an open, EVM-compatible Layer-1 built by Circle for stablecoin
settlement. USDC is the native gas token, finality is sub-second and
deterministic, and anyone may run a node — no permission and no stake required.

**An Arc node is a follower, not a validator.** It verifies every block against
the validator set's signatures and re-executes every transaction locally, but
it proposes nothing, holds no consensus stake and cannot be slashed. Nothing on
these pages carries double-sign risk.

| Fact | Arc mainnet | Verified |
|---|---|---|
| Chain ID | `5042` / `0x13b2` | `eth_chainId` against `rpc.mainnet.arc.io` |
| Node release | `v0.8.0` | `arc_getVersion` on the official mainnet RPC returns `v0.8.0`, commit `5abb64c1` |
| Public RPC | `https://rpc.mainnet.arc.io` | live |
| Explorer | <https://explorer.arc.io> | live |
| Gas token | USDC — 18 decimals natively, 6 as ERC-20 | Arc docs |
| Block gas limit | `10,000,000`–`200,000,000`, default `30,000,000` | `chainspec.rs` at tag `v0.8.0` |
| Base-fee cap | `20,000` gwei | `chainspec.rs` at tag `v0.8.0` |

All values verified 2026-09-18.

## Read this before installing: what Circle has and has not published

Arc mainnet went live on 2026-09-16. Circle's node documentation has not fully
caught up with it, and pretending otherwise would be the wrong kind of helpful.

**What is confirmed:**

- `arc-mainnet` is a first-class bundled chain spec in `arc-node` at tag
  `v0.8.0` — `ARC_SUPPORTED` lists it, and `MAINNET_CHAIN_ID = 5042` in
  `crates/shared/src/chain_ids.rs`.
- `arc-snapshots` at the same tag accepts `--chain arc-mainnet`.
- Circle's own run-a-node page states that **mainnet operators must upgrade to
  `v0.8.0` before timestamp `1789052400` (2026-09-10 15:00 UTC)**, when Zero7
  and Zero8 activate. That deadline has passed; `v0.8.0` is mandatory, not
  recommended.
- The live mainnet fleet is on it: `arc_getVersion` against
  `rpc.mainnet.arc.io` returns `v0.8.0`.

**What Circle has not published yet:**

- the **Versions** table in `node-requirements` still lists only Arc Testnet;
- the **relay endpoints** table for the consensus layer likewise lists only Arc
  Testnet.

The mainnet endpoints below come from Circle's *Connect to Arc* developer
reference, mirror the testnet pattern exactly, and all three answer `0x13b2`.
That makes them verified-reachable, not Circle-designated operator relays.
Re-check `node-requirements` before a production deployment, and treat the
relay list as the one thing here that may change.

## System requirements

| Resource | Recommendation |
|---|---|
| CPU | higher clock speed over core count |
| Storage | 1 TB+ NVMe SSD, TLC |
| OS | Linux with glibc **2.39 or newer** — Ubuntu 24.04 is known to work |

Debian 12 and other older distributions fail with `GLIBC_2.38 not found` or
`GLIBC_2.39 not found` against the pre-built binaries. Use a newer
distribution, the Docker images, or build from source.

Syncing from genesis is **not supported**. A snapshot is the only bootstrap.

## 1. Paths

```sh
cat << "EOF" > ~/.arc_env
ARC_HOME="${ARC_HOME:-$HOME/.arc}"
ARC_BIN_DIR="${ARC_BIN_DIR:-$ARC_HOME/bin}"
ARC_RUN="/run/arc"
ARC_EXECUTION=$ARC_HOME/execution
ARC_CONSENSUS=$ARC_HOME/consensus
export ARC_HOME ARC_BIN_DIR ARC_RUN ARC_EXECUTION ARC_CONSENSUS
export PATH="$ARC_BIN_DIR:$PATH"
EOF

. ~/.arc_env
mkdir -p "$ARC_EXECUTION" "$ARC_CONSENSUS" "$ARC_BIN_DIR"
sudo install -d -o "$USER" "$ARC_RUN"
```

`$ARC_RUN` must resolve to the same directory in both the EL and the CL shell.
A mismatch here is one of the most common reasons a new node never leaves
`0x0`. Under systemd, `RuntimeDirectory=arc` creates `/run/arc` and the
`install -d` line is unnecessary.

## 2. Install the binaries

```sh
curl -L https://raw.githubusercontent.com/circlefin/arc-node/main/arcup/install | bash
export ARC_HOME="${ARC_HOME:-$HOME/.arc}"
. "$ARC_HOME/env"

arcup --install v0.8.0

arc-snapshots --version
arc-node-execution --version
arc-node-consensus --version
```

Read the installer before piping it into a shell. It is a Circle-published
script, and it is also a script that configures a node you will be responsible
for later.

`arcup` verifies each archive against its `.sha256`. **GPG signature
verification is disabled until Circle publishes the release signing key** —
that is stated in Circle's own documentation, and it means the checksum is the
only integrity control in this path.

### From source

```sh
sudo apt-get install -y libclang-dev pkg-config build-essential
git clone https://github.com/circlefin/arc-node.git
cd arc-node && git checkout v0.8.0
cargo install --path crates/node
cargo install --path crates/malachite-app
cargo install --path crates/snapshots
```

## 3. Download a snapshot

```sh
arc-snapshots download \
  --chain=arc-mainnet \
  --el-profile=full \
  --execution-path "$ARC_EXECUTION" \
  --consensus-path "$ARC_CONSENSUS"
```

`--el-profile` defaults to `minimal`. Pass `full` to match the `--full` flag
the execution layer uses below, or `archive` for an archive node — omitting it
silently gives you a minimal restore.

Circle publishes testnet sizes only: roughly 68 GB compressed EL and 16 GB
compressed CL, extracting to about 103 GB and 36 GB. Mainnet is a different
chain and its sizes are not published; size the disk from the 1 TB baseline and
measure what you actually get.

If automatic resolution fails, the API has no storage-v2 listing for that chain
yet. `arc-snapshots` does **not** fall back to another listing — it fails, and
that failure is the answer. See the Snapshots tab.

## 4. Initialize the consensus layer

```sh
arc-node-consensus init --home "$ARC_CONSENSUS"
```

One time only. This writes the CL private key, which **is your node's network
identity**. Clearing `$ARC_CONSENSUS` destroys it and it cannot be recovered;
re-run `init` if you ever do.

## 5. Start the execution layer — first

```sh
arc-node-execution node \
  --chain arc-mainnet \
  --datadir "$ARC_EXECUTION" \
  --full \
  --ipcpath "$ARC_RUN/reth.ipc" \
  --auth-ipc --auth-ipc.path "$ARC_RUN/auth.ipc" \
  --http --http.addr 127.0.0.1 --http.port 8545 \
  --http.api eth,net,web3 \
  --rpc.forwarder https://rpc.mainnet.arc.io/ \
  --metrics 127.0.0.1:9001 \
  --disable-discovery \
  --enable-arc-rpc
```

Notes that are not obvious:

- **`--full` is required on the first start** from a pruned snapshot. It
  reconciles internal database tables that would otherwise fail a consistency
  check. Restart without it afterwards if you do not want pruning.
- With `--full`, EL pruning runs on a **128-block** interval as of `v0.7.3`,
  down from 5000. Pass `--prune.block-interval=5000` to keep the old schedule.
- `--disable-discovery` is correct here. Arc follow nodes reach the network
  through relay endpoints, not through peer discovery.
- `--http.addr 127.0.0.1`. Circle's own example uses
  `--http.api eth,net,web3,txpool,trace,debug`, which is fine on loopback and
  is not fine on anything reachable. See the Security tab.

## 6. Start the consensus layer — second

```sh
arc-node-consensus start \
  --home "$ARC_CONSENSUS" \
  --full \
  --eth-socket "$ARC_RUN/reth.ipc" \
  --execution-socket "$ARC_RUN/auth.ipc" \
  --rpc.addr 127.0.0.1:31000 \
  --follow \
  --follow.endpoint https://rpc.mainnet.arc.io,wss=rpc.mainnet.arc.io \
  --follow.endpoint https://rpc.drpc.mainnet.arc.io,wss=rpc.drpc.mainnet.arc.io \
  --follow.endpoint https://rpc.blockdaemon.mainnet.arc.io,wss=rpc.blockdaemon.mainnet.arc.io/websocket \
  --execution-persistence-backpressure \
  --execution-persistence-backpressure-threshold=16 \
  --metrics 127.0.0.1:29000
```

**Start the EL first, always.** The CL connects to the EL's sockets at startup
and fails if they are not there.

`--rpc.addr` is **required** when the EL runs `--enable-arc-rpc`: the EL proxies
`arc_getCertificate` to the CL's REST API at `http://127.0.0.1:31000`.

All three relay endpoints verified reachable on 2026-09-18, each answering
chain `0x13b2`.

## 7. Verify

```sh
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Run it several times. The height should increase. Then compare it against the
network rather than against itself:

```sh
cast block-number --rpc-url http://127.0.0.1:8545
cast block-number --rpc-url https://rpc.mainnet.arc.io
```

Compare the block **hash** at a common height, not only the height. Two chains
can be at the same number.

### If it stays at `0x0`

| Cause | Check |
|---|---|
| IPC sockets missing | `ls -l $ARC_RUN` — the EL writes both within 30 s |
| CL started before the EL | restart the CL |
| Snapshot extraction interrupted | re-run `arc-snapshots download`; add `--force` if it refuses |
| `$ARC_RUN` differs between shells | re-source `~/.arc_env` |

## Running as a service

Circle documents a systemd path; `RuntimeDirectory=arc` replaces the manual
`/run/arc` setup. Keep both units on the same host and keep IPC — the RPC
transport between EL and CL is **deprecated as of `v0.8.0` and will be removed
in `v0.9.0`**.

## Official resources

- Documentation: <https://docs.arc.io>
- Node repository: <https://github.com/circlefin/arc-node>
- Node requirements: <https://docs.arc.io/arc/references/node-requirements>
- Explorer: <https://explorer.arc.io>

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
