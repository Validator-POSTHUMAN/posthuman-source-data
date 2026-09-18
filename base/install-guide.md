# Running a Base Node

Base is an Ethereum L2 on the OP Stack. A Base node is a **follower**: it
derives the L2 chain from data the sequencer posts to Ethereum L1 and from the
sequencer's own feed. It does not propose blocks, does not vote, holds no
consensus key and cannot be slashed.

That single fact sets the whole risk model for this page. Everything that can go
wrong with a Base node is an availability, exposure or data problem. There is no
irreversible signing mistake to make, and no stake to lose.

What you run:

| Component | Role | Image |
|---|---|---|
| `base-reth-node` | execution layer (EL) | `ghcr.io/base/node` |
| `base-consensus` | rollup node / derivation (CL) | `ghcr.io/base/node` |

Both ship from the same image and the same repository.

---

## 0. Read this before you clone anything

**`base/node` is archived.** Releases moved to
[`base/base`](https://github.com/base/base) at `v1.3.0`, and `base/node` became
read-only on 4 September 2026. It still exists and it still has a working
`docker-compose.yml`, which is exactly why operators keep landing on it. If you
clone it, you will pin yourself to a pre-`v1.3.0` tree and miss every fork.

**There is a fork deadline right now.** Cobalt activates on Base Sepolia on
**23 September 2026** and on Base Mainnet on **30 September 2026**. Release
`v1.4.0` (16 September 2026) carries Cobalt support for both
`base-reth-node` and `base-consensus`. A node below `v1.4.0` stops following the
chain at activation.

`v1.4.0` also deprecates the `--rollup.disable-tx-pool-gossip` CLI flag on
`base-reth-node`. If your entrypoint or `ADDITIONAL_ARGS` still passes it,
remove it — it is no longer accepted.

Check the current activation table at
[docs.base.org/upgrades/cobalt/overview](https://docs.base.org/upgrades/cobalt/overview)
before you rely on the dates above.

---

## 1. Prerequisites

### An Ethereum L1 endpoint you can actually afford

A Base node needs **both** an L1 execution RPC and an L1 beacon (consensus) API.
This is not optional and it is not a nicety: derivation reads L1 blocks and
blobs continuously, and initial sync reads a great deal of them.

- Running your own Ethereum full node is the cheapest option at steady state and
  the only one with no rate limit. An **archive** L1 node is not required.
- A third-party provider works, and the Base docs warn plainly that syncing
  "will consume a vast amount of your requests quota." Size the plan before you
  start, not after the sync stalls at 60%.
- The beacon endpoint must serve blob sidecars for the retention window. A
  pruned or blob-less beacon endpoint produces a sync that runs and then simply
  stops making progress.

If the L1 node is your own, it must be **fully synced before** Base can finish
syncing.

### Hardware

| Resource | Minimum | Notes |
|---|---|---|
| CPU | 8+ modern cores | single-core performance matters |
| RAM | 32 GB | 64 GB recommended |
| Disk | locally attached NVMe SSD | RAID 0 helps; networked storage does not |
| Filesystem | ext4 | what Base runs in production |

Storage is sized by formula, not by a fixed number:

```
(2 × current chain size) + snapshot size + 20% buffer
```

Current chain size is on [base.org/stats](https://base.org/stats); snapshot
sizes are at [chain.base.org/snapshots](https://chain.base.org/snapshots). The
`2 ×` term exists because restoring a snapshot needs the old data and the new
data on disk at the same time.

Base production uses AWS `i7i.12xlarge` or larger with RAID 0 across every local
NVMe device, ext4. If you are on EBS, `io2` Block Express is the only volume
class that keeps up during initial sync — and local NVMe still beats it.

**Disk I/O is the bottleneck.** Every "my node syncs too slowly" report that is
not an L1 problem is a disk problem. See the sizing and node-type pages before
you provision.

### Networking

Base needs egress as much as ingress, and the egress half is the one operators
forget.

| Direction | Port | Protocol | Purpose |
|---|---|---|---|
| Ingress | `30303` | TCP + UDP | EL P2P discovery (discv4) and RLPx |
| Ingress | `9222` | TCP + UDP | CL P2P discovery (discv5) |
| Egress | `30303` | TCP + UDP | peers |
| Egress | `9222` | TCP + UDP | peers |
| Egress | `30301` | TCP + UDP | **Base bootnodes** |
| Egress | `9200` | UDP | **Base bootnodes** |

If outbound `30301` or `9200` is blocked, the node finds **zero** peers no
matter how correct your ingress rules are. The symptom looks like a P2P bug and
is a firewall rule.

If you use stateless network ACLs rather than a stateful firewall, also allow
outbound ephemeral ports `32768–60999` (TCP + UDP), or peer replies are dropped
silently.

### Docker

Docker Engine with the Compose v2 plugin. Run it as a non-root user in the
`docker` group — using `sudo docker compose` creates a data directory root owns
and a permission failure you will meet two hours later.

---

## 2. Get the source

```bash
git clone https://github.com/base/base.git
cd base
```

The root `docker-compose.yml` is the operator stack. `just devnet up` in the
same tree is a *developer* stack — not what you want on a server.

---

## 3. Configure

Edit `.env.mainnet` (or `.env.sepolia` for testnet). The only values you must
set are the two L1 endpoints:

```bash
BASE_NODE_L1_ETH_RPC=http://127.0.0.1:8545
BASE_NODE_L1_BEACON=http://127.0.0.1:5052
```

Everything else already has a working default:

| Variable | Mainnet | Sepolia |
|---|---|---|
| `RETH_CHAIN` | `base` | `base-sepolia` |
| `BASE_NODE_NETWORK` | `base` | `base-sepolia` |
| `RETH_SEQUENCER_HTTP` | `https://mainnet-sequencer.base.org` | `https://sepolia-sequencer.base.org` |
| `BASE_NODE_L1_TRUST_RPC` | `false` | `false` |

Leave `BASE_NODE_L1_TRUST_RPC=false`. Setting it to `true` tells the rollup node
to accept L1 responses without verifying them, which converts a compromised or
buggy L1 endpoint into a wrong L2 chain.

Compose-level knobs, settable from the shell or a `.env` file:

| Variable | Default | Purpose |
|---|---|---|
| `NODE_TAG` | `latest` | image tag pulled from `ghcr.io/base/node` |
| `NETWORK_ENV` | `.env.mainnet` | which network env file both services load |
| `HOST_DATA_DIR` | `./reth-data` | host path mounted at `/data` in the EL container |
| `PROFILE` | `release` | cargo profile, only used with `--build` |

The docs currently describe `PROFILE` as defaulting to `maxperf`; the
`docker-compose.yml` in the tree says `${PROFILE:-release}`. The file wins. If
the profile matters to you, set it explicitly rather than inheriting either.

### Pin the release. Do not run `latest`.

```bash
NODE_TAG=v1.4.0 docker compose up -d
```

`latest` means your node's version changes whenever you happen to restart, which
is precisely the moment you least want a variable you did not choose. Pin the
tag, record it, and change it deliberately. Pinning also skips the source
compile entirely — the node boots as soon as the image is pulled.

`--build` and `NODE_TAG` are mutually exclusive in effect: `--build` compiles the
local tree and overrides the pinned image.

### The default compose file publishes six ports on every interface

Read this before the first `docker compose up`. The shipped `ports:` mappings
are bare `host:container` pairs, which bind `0.0.0.0`:

| Published | Service | What it is |
|---|---|---|
| `8545` | execution | JSON-RPC |
| `8546` | execution | WebSocket RPC |
| `7301` | execution | Prometheus metrics (container `6060`) |
| `30303` | execution | P2P — **should** be public |
| `7545` | node | rollup node RPC (`optimism_syncStatus`) |
| `9222` | node | P2P — **should** be public |
| `7300` | node | Prometheus metrics |
| `6060` | node | **pprof** |

Only `30303` and `9222` belong on a public interface. Docker's published ports
bypass `ufw`, so a host you believe is firewalled will serve its RPC, its
metrics and its Go pprof profiler to the internet. Bind the rest to loopback
before you start — the exact edit is in **Security Hardening**, and it is the
single most important thing on this page.

---

## 4. Restore from a snapshot first

Syncing Base from genesis takes days and burns your entire L1 request quota.
Restore a snapshot instead. Snapshots are refreshed weekly.

The order matters, and it is the reverse of what feels natural: **download and
place the data before the node has ever run.**

Install the CLI:

```bash
curl -fsSL https://raw.githubusercontent.com/base/base/main/baseup/install | bash
```

Then, from the cloned `base` directory:

```bash
mkdir -p ./reth-data

# Full node, Base Mainnet
base-reth-node download --full --datadir ./reth-data --chain base --resumable
```

| Preset | Flag | Contents |
|---|---|---|
| Minimal | `--minimal` | latest state + headers + the minimum required history |
| Full | `--full` | default full-node prune window of transactions, receipts and history |
| Archive | `--archive` | everything, no pruning |

`--chain` is `base` for mainnet and `base-sepolia` for testnet.

`--download-concurrency` defaults to `8`; roughly 2× your physical core count is
a safe increase on capable hardware.

**Choose the node type now.** Reth cannot convert between archive, full and
pruned after initial sync. Getting this wrong means resyncing. Details and the
custom-pruning path are on the **Pruning & Storage** tab.

If you already have a running node and are replacing its data, stop it first
(`docker compose down`), then clear the *contents* of the data directory
(`rm -rf ./reth-data/*`) — not the directory itself. The chain data must end up
directly inside `./reth-data`, never nested in `./reth-data/reth/`.

If the download reports `Archive extracted, but output verification failed`, a
newer snapshot was published mid-download. Interrupt and re-run: the download is
idempotent and fetches only the difference.

### Migrating a pre-V2 node

Base Mainnet moved to reth V2 storage and V1 snapshots have been decommissioned.
A node still on V1 data has two paths: download a fresh V2 snapshot
(recommended, much faster), or run `base-reth-node db migrate-v2` in place —
archival nodes only, no `--resumable`, and expect it to take far longer than a
download.

---

## 5. Start

```bash
NODE_TAG=v1.4.0 docker compose up -d
docker compose ps
```

Testnet:

```bash
NETWORK_ENV=.env.sepolia NODE_TAG=v1.4.0 docker compose up -d
```

Follow the logs while it comes up:

```bash
docker compose logs -f execution   # base-reth-node
docker compose logs -f node        # base-consensus
```

---

## 6. Verify — four checks, in this order

Do not stop at the first one. A Base node that answers `eth_chainId` correctly
can still be stalled, forked or serving a head from last Tuesday.

### 6.1 The EL answers, and answers for the right chain

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' \
  http://127.0.0.1:8545
```

`0x2105` is Base Mainnet (8453). `0x14a34` is Base Sepolia (84532). Anything
else means the node loaded the wrong network config.

### 6.2 The rollup node reports a recent unsafe head

```bash
echo Latest synced block behind by: $((($(date +%s)-$( \
  curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H "Content-Type: application/json" http://127.0.0.1:7545 | \
  jq -r .result.unsafe_l2.timestamp))/60)) minutes
```

Under a minute behind is healthy at Base's 2-second block time. Hours behind
means it is still syncing; days behind and not moving means it is stuck.

### 6.3 The safe head is advancing, not just the unsafe head

```bash
curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H 'Content-Type: application/json' http://127.0.0.1:7545 \
  | jq '{unsafe: .result.unsafe_l2.number, safe: .result.safe_l2.number, finalized: .result.finalized_l2.number, l1: .result.head_l1.number}'
```

This is the check that catches the failure that looks healthy. The unsafe head
follows the sequencer feed and keeps advancing even when L1 derivation is
broken. The safe head only advances when the node has actually read the batch
from L1. A node whose unsafe head is at the tip and whose safe head is frozen is
not following Ethereum any more — its L1 RPC, beacon endpoint or blob access has
failed, and nothing about the process, the logs or a height-based monitor will
say so.

Alert on `unsafe − safe`, not on `unsafe` alone.

### 6.4 An independent diagnostic

```bash
basectl -c mainnet doctor
```

`basectl doctor` is read-only. It checks declared network against live chain ID,
EL and CL peer counts, the local head against the public tip, safe-head recency,
advertised P2P endpoints and L1 RPC reachability, and exits `1` if any check
fails. Note its built-in mainnet preset expects the CL at
`http://127.0.0.1:9545`, while the Compose stack publishes the rollup node RPC
on `7545` — pass `--cl-rpc http://127.0.0.1:7545` or the CL checks are skipped
with a hint rather than failing loudly.

```bash
basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
```

---

## 7. Optional: Flashblocks

Flashblocks give your RPC consumers 200 ms preconfirmations. The node subscribes
to a WebSocket stream and caches preconfirmation data, then serves it through
the `pending` block tag and the Flashblocks RPC methods.

```bash
RETH_FB_WEBSOCKET_URL="wss://mainnet.flashblocks.base.org/ws"
```

| Network | URL |
|---|---|
| Mainnet | `wss://mainnet.flashblocks.base.org/ws` |
| Sepolia | `wss://sepolia.flashblocks.base.org/ws` |

Set it in the `.env` file and restart, then verify:

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["pending",false],"id":1}' \
  http://127.0.0.1:8545 | jq '.result.number'
```

**These WebSocket endpoints are node infrastructure, not an application API.**
Applications query *your* node; they must not connect to
`wss://mainnet.flashblocks.base.org/ws` directly. If Flashblocks are
unavailable the node falls back to the latest block rather than erroring, so a
successful `pending` response is not by itself proof the stream is connected —
compare the returned number against the current head.

---

## 8. Optional: historical proofs

`eth_getProof`, `debug_executionWitness` and `debug_executePayload` need a
separate proofs database, served by an execution extension:

```bash
RETH_HISTORICAL_PROOFS=true
```

Most operators do not need this. It adds hundreds of GB, wants higher I/O
throughput, and backfills for 24–48 hours on mainnet at first start. Proofs
snapshots exist to skip the backfill; V2 proofs snapshots were still pending at
the time of writing, so the archives are the `aria2c` download described on the
**Snapshots** tab.

Two behaviours worth knowing before you enable it: the earliest block these RPCs
can answer for is the block at which the ExEx first started, and
`--rpc.eth-proof-window` is ignored once it is enabled. Retention defaults to 28
days and is set with `RETH_PROOFS_HISTORY_WINDOW=<blocks>`.

During initial sync the ExEx can fall so far behind it cannot catch up. The fix
is follow mode, which keeps `base-consensus` within 512 blocks of it:

```bash
BASE_NODE_SOURCE_L2_RPC=<trusted-l2-rpc>
BASE_NODE_PROOFS=true
```

---

## 9. Running without Docker

The Compose stack is what Base supports and what this guide assumes. If you
would rather run the binaries under systemd — which also avoids the published-port
problem entirely, because systemd units bind where you tell them to — the
`baseup` installer and a pair of unit files are on the **Binaries & systemd**
tab.

---

## Next

- **Snapshots** — restore, node-type presets, proofs snapshots
- **Pruning & Storage** — the choice you cannot change later
- **Monitoring** — what to alert on, and the two signals that matter most
- **Security Hardening** — fix the published ports before this node is reachable
- **Upgrades** — Cobalt, release cadence, and how to not miss a fork
