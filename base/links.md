# Base Endpoints and Links

> **POSTHUMAN does not operate a Base node.** Every endpoint on this page is a
> third party's. They are listed because they are useful for verification and
> for bootstrapping, not because we run them or guarantee them. Do not build
> production infrastructure on a public endpoint — run your own, or buy one with
> an SLA.

---

## Network parameters

| | Base Mainnet | Base Sepolia |
|---|---|---|
| Chain ID | `8453` (`0x2105`) | `84532` (`0x14a34`) |
| Currency | ETH | ETH (testnet) |
| Block time | 2 s | 2 s |
| Public RPC | `https://mainnet.base.org` | `https://sepolia.base.org` |
| Sequencer | `https://mainnet-sequencer.base.org` | `https://sepolia-sequencer.base.org` |
| Flashblocks WS | `wss://mainnet.flashblocks.base.org/ws` | `wss://sepolia.flashblocks.base.org/ws` |
| `RETH_CHAIN` | `base` | `base-sepolia` |
| `BASE_NODE_NETWORK` | `base` | `base-sepolia` |
| Explorer | [basescan.org](https://basescan.org) | [sepolia.basescan.org](https://sepolia.basescan.org) |
| Explorer (open source) | [base.blockscout.com](https://base.blockscout.com) | [base-sepolia.blockscout.com](https://base-sepolia.blockscout.com) |

The Flashblocks WebSocket endpoints are **node infrastructure, not an
application API**. Your applications query your node; they must not connect to
them directly.

Chain IDs verified live against `mainnet.base.org` and `sepolia.base.org` on
2026-09-18.

---

## Public RPC endpoints

Rate-limited. Fine for a verification `curl`, wrong for an application.

| Endpoint | Network | Notes |
|---|---|---|
| `https://mainnet.base.org` | mainnet | official, rate-limited, not for production apps |
| `https://sepolia.base.org` | sepolia | official, rate-limited |
| `https://base-rpc.publicnode.com` | mainnet | keyless, verified `0x2105` |
| `https://base.drpc.org` | mainnet | keyless, verified `0x2105` |

For an endpoint you can depend on, pick a provider from the
[Base Services Hub](https://docs.base.org/get-started/base-services-hub), or run
your own node — the **installation guide** is the whole point of this page set.

---

## Source and releases

| What | Where |
|---|---|
| Node source and releases | https://github.com/base/base |
| Releases (the upgrade source of truth) | https://github.com/base/base/releases |
| `basectl` | https://github.com/base/base/tree/main/bin/basectl |
| `baseup` installer | https://github.com/base/base/tree/main/baseup |
| **Archived** former node repo | https://github.com/base/node |

`base/node` is archived and read-only as of 4 September 2026. Releases moved to
`base/base` at `v1.3.0`. Clone `base/base`; anything that points you at
`base/node` is out of date.

---

## Snapshots

| What | Where |
|---|---|
| Snapshot index | https://chain.base.org/snapshots |
| Chain size and stats | https://base.org/stats |
| Proofs snapshots (mainnet) | `https://mainnet-reth-proofs-snapshots.base.org/` |
| Proofs snapshots (sepolia) | `https://sepolia-reth-proofs-snapshots.base.org/` |

Download with `base-reth-node download`, not with `wget`. See **Snapshots**.

---

## Documentation

| Topic | Link |
|---|---|
| Run a node | https://docs.base.org/specifications/node-operators/run-a-node |
| Node performance and hardware | https://docs.base.org/specifications/node-operators/performance-tuning |
| Snapshots | https://docs.base.org/specifications/node-operators/snapshots |
| Troubleshooting | https://docs.base.org/specifications/node-operators/troubleshooting |
| Network upgrades | https://docs.base.org/upgrades |
| Cobalt upgrade | https://docs.base.org/upgrades/cobalt/overview |
| Configuration changelog | https://docs.base.org/base-chain/network-information/configuration-changelog |
| Protocol specs | https://specs.base.org |
| Docs index for agents | https://docs.base.org/llms.txt |

---

## Explorers and data

| What | Where | Key required |
|---|---|---|
| Basescan | https://basescan.org | API key for the API |
| Blockscout | https://base.blockscout.com | no — `/api/v2/stats` and `/api/v2/main-page/blocks` are keyless |
| L2BEAT (Base) | https://l2beat.com/scaling/projects/base | no |
| Base stats | https://base.org/stats | no |

Blockscout's keyless v2 API is the practical choice for dashboards and
automation that must not carry a credential.

---

## Community and support

| What | Where |
|---|---|
| Discord — `🛠｜node-operators` | https://discord.gg/buildonbase |
| Issues | https://github.com/base/base/issues |
| Status | https://status.base.org |
| X | https://x.com/base |

Fork coordination and operator incident chatter happen in the Discord channel
before they reach the documentation.

---

## Third-party operator tooling

| Tool | What it is |
|---|---|
| [base-node-helper](https://github.com/imbanytuidoter/base-node-helper) | community CLI wrapping `docker compose` with preflight checks and health notifications |

Not maintained by Base. It reads your `.env`, which holds your L1 credential and
engine secret. Read the source, pin a commit, and do not install it from a
one-line remote pipe on a production host. See **Operator Tooling**.
