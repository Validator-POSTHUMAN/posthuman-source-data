# Arc Network AI Operations Skill

This tab links the Arc-specific AI-agent skill for node operations. The skill
is operator-neutral: it names no production host, no credential and no private
endpoint.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/arc
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/arc/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/arc/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/arc/scripts/arc-healthcheck.sh

## Read this first: what an Arc node is not

An Arc node is a **follower**. It verifies every block against the validator
set's signatures and re-executes every transaction locally, but it proposes
nothing, holds no consensus stake and cannot be slashed.

So there is no double-sign risk, no key-uniqueness proof, no slashing-protection
database and no unbonding clock. Restarting is safe. Replacing the data
directory is safe. The one irreplaceable file is the **consensus-layer private
key** in `$ARC_CONSENSUS` — the node's network identity, written once by
`arc-node-consensus init`, unrecoverable if deleted.

## The failures this skill exists for

**The node stops following and nothing says so.** A follow node depends
entirely on relay endpoints reached over the internet. When they stop
answering, the node does not crash — it stops advancing. Both processes stay
`active`, `eth_blockNumber` answers instantly, and the answer is old. Every
process-based monitor reports success.

**Forks activate on a wall-clock timestamp, not a block height.** There is no
on-chain plan to query and no approaching height to watch. Zero7 and Zero8 hit
mainnet at `1789052400` — 2026-09-10 15:00 UTC — and `v0.8.0` became mandatory
at that instant. Testnet activates a week earlier, which is the entire
operational value of running one.

**Circle's documentation lags its own mainnet.** The `node-requirements`
Versions table and the relay-endpoint table both list only Arc Testnet, while
the run-a-node page states the mainnet upgrade deadline and the live fleet
answers `arc_getVersion` with `v0.8.0`. Reading the table alone gives the wrong
answer; reading the chain gives the right one.

**Every quickstart targets `arc-testnet`.** Circle's published
`docker-compose.yml` and all its examples. A mainnet deployment built by
changing the RPC URLs and leaving `--chain` alone is a testnet node pointed at
mainnet relays, and it looks fine until the block hashes are compared.

**`--el-profile` defaults to `minimal`.** Including when an explicit manifest
URL is passed. An archive node bootstrapped without it is a minimal node
wearing archive flags, discovered weeks later by a failing historical query,
and fixable only by another full restore.

## What it helps agents do

- Verify a node in the right order: `eth_chainId`, `arc_getVersion`,
  `eth_blockNumber` sampled twice, then a **hash** comparison against an
  independent RPC.
- Diagnose a frozen height as a relay-endpoint, disk-latency or backpressure
  problem rather than a node defect, and check outbound reachability from the
  node host rather than from a laptop.
- Start and stop the two layers in the order that works — EL first, CL second —
  and recognise a CL that failed because it was started too early.
- Read `arc-snapshots` refusing without `--force` as correct behaviour
  protecting unmarked data, not as a bug.
- Know that automatic snapshot resolution has **no fallback**: a failure means
  the chain has no published storage-v2 listing, not that the command is wrong.
- Review exposure from the fact that Circle's quickstart uses
  `--http.api eth,net,web3,txpool,trace,debug`, and that `ufw status` is not
  evidence when Docker is publishing ports.
- Separate the two USDC representations — 18 decimals native, 6 as ERC-20 —
  without ever adding them together.
- Recognise `GLIBC_2.39 not found` as a distribution problem with no flag that
  fixes it.

## Operational scope

- Arc mainnet `5042` / `0x13b2`; Arc Testnet `5042002` / `0x4cef52`; Arc Devnet
  `5042001`.
- Node release `v0.8.0`, mandatory on mainnet since 2026-09-10 15:00 UTC.
- Binaries `arc-node-execution`, `arc-node-consensus`, `arc-snapshots`;
  installer `arcup`.
- Ports `8545`, `8546`, `8551`, `9001`, `29000`, `31000`; plus `30303` and
  `27000` on RPC provider nodes only. A follow node needs no inbound port.
- EL↔CL over IPC. The RPC transport is deprecated in `v0.8.0` and removed in
  `v0.9.0`.
- glibc **2.39+** for the pre-built binaries.
- Public RPC namespaces: `eth,net,web3,rpc` plus `--public-api`. Prohibited:
  `txpool`, `debug`, `trace`, `admin`, `flashbots`, `mev`, `ots`.
- Genesis sync is not supported. Snapshots in Reth V2 format from `v0.8.0`.

## Safety boundaries

Read-only by default. The skill broadcasts no transaction, moves no funds and
handles no key material.

Explicit operator approval is required before: replacing or deleting a data
directory; running `arc-snapshots --force`; changing `--chain`, flags or unit
files on a production node; restarting a node that serves production RPC;
binding any port off loopback; and anything that touches `$ARC_CONSENSUS`,
which holds the unrecoverable network identity.

`arc-healthcheck.sh` is read-only and prints no credential. A passing check is
evidence, not proof.

## Related guides

The full operator set for this network is on the other tabs of this page:
installation, Docker, snapshots, pruning and storage, RPC and the `arc`
namespace, monitoring, security hardening, upgrades, command sheet,
troubleshooting, test networks, operator toolbox and endpoints.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
