# Ethereum Operator Tooling

A review of the third-party tools around an Ethereum node: what to run, what to
read, and what not to bother with. Grouped by the job it does, because that is
how you go looking for one.

Everything here is third-party unless stated otherwise. Versions are as
published on 2026-09-18.

---

## Run the node

| Tool | What it is | Verdict |
|---|---|---|
| [eth-docker](https://github.com/ethstaker/eth-docker) `v26.9.0` | Docker Compose stack for every client pair, with Grafana | **The default recommendation.** Removes a whole class of configuration mistakes. See the Docker guide. |
| [Stereum](https://stereum.net/) | GUI node launcher and manager | Reasonable for a single home node; awkward for fleets. |
| [DappNode](https://dappnode.com/) | Appliance OS for home nodes | Good hardware story, opinionated software. |
| [Sedge](https://github.com/NethermindEth/sedge) | Nethermind's setup generator — writes the Compose files and exits | Useful middle ground: generated config you then own. |
| [Rocket Pool](https://rocketpool.net/) / [Lido CSM](https://csm.lido.fi/) | Run a validator with less than 32 ETH of your own | A different business model, not a different node. Both still run the clients above. |

## Generate and manage keys

| Tool | What it is |
|---|---|
| [ethstaker-deposit-cli](https://github.com/ethstaker/ethstaker-deposit-cli) `v1.3.0` | The maintained deposit CLI. `ethereum/staking-deposit-cli` is **deprecated** — do not use it. |
| [Staking Launchpad](https://launchpad.ethereum.org/) | Official deposit flow and checklist |
| [ethdo](https://github.com/wealdtech/ethdo) `v1.39.1` | The validator swiss army knife: status, credentials, exits, BLS-to-execution changes |
| [Wagyu Key Gen](https://github.com/stake-house/wagyu-key-gen) | GUI wrapper around key generation for offline machines |
| [Web3Signer](https://github.com/Consensys/web3signer) | Remote consensus signer with a shared slashing protection database |
| [Dirk](https://github.com/attestantio/dirk) | Distributed key manager with threshold signing |

## Monitor

| Tool | What it is |
|---|---|
| [ethereum-metrics-exporter](https://github.com/ethpandaops/ethereum-metrics-exporter) | Client-independent Prometheus metrics from the EL RPC and Beacon API. The reason one dashboard can survive a client swap. |
| [node_exporter](https://github.com/prometheus/node_exporter) | Host metrics; disk prediction and clock offset come from here |
| [beaconcha.in](https://beaconcha.in/) | External validator monitoring with watchlists and alerts. Free second opinion. |
| [Rated Network](https://www.rated.network/) | Operator-level effectiveness scoring against the network |
| Client Grafana dashboards | Shipped by each client team, maintained against the metric names that client actually emits |

## Block building and MEV

| Tool | What it is |
|---|---|
| [mev-boost](https://github.com/flashbots/mev-boost) `v1.12` | Relay multiplexer between the beacon node and builders |
| [mevboost.pics](https://www.mevboost.pics/) | Relay market share and censorship behaviour |
| [relayscan.io](https://relayscan.io/) | Relay reliability and missed-payload statistics |

## Distributed validators

| Tool | What it is |
|---|---|
| [SSV Network](https://ssv.network/) | Operator registry and DKG; used by Lido. POSTHUMAN has run SSV operators on mainnet and Hoodi. |
| [Obol](https://obol.org/) | Charon middleware for distributed validator clusters |
| [Anchor](https://github.com/sigp/anchor) | Sigma Prime's Rust SSV client |

## Explore and query

| Tool | Use |
|---|---|
| [Etherscan](https://etherscan.io/) | Execution-layer explorer and contract verification |
| [beaconcha.in](https://beaconcha.in/) | Consensus-layer explorer — the operator-facing one |
| [Blockscout](https://eth.blockscout.com/) | Open source, self-hostable |
| [Otterscan](https://otterscan.io/) | Runs directly against your own Erigon or Reth archive node. The right answer when you already have archive data and do not want to depend on a hosted explorer. |
| [Ethplorer](https://ethplorer.io/) | Token holder and distribution views |
| [Chainlist](https://chainlist.org/chain/1) | Public RPC endpoints with latency and privacy notes |
| [Dune](https://dune.com/) | SQL over indexed chain data, for analysis rather than operations |

Two the team has asked about specifically:

- **[ethscanner.io](https://ethscanner.io/)** — a Routescan-hosted explorer. It
  blocks automated access, so it is usable by a human in a browser but is not a
  data source anything can be built on.
- **[CoinTool (ct.app)](https://ct.app/)** — a multi-chain utility site: batch
  transfers, token deployment, approval management. Useful as a reference for
  which small utilities people actually reach for; not an operations tool and
  not something to depend on. Anything it does that matters, do with your own
  node and a wallet you control.

## Interact from the shell

| Tool | What it is |
|---|---|
| [Foundry](https://github.com/foundry-rs/foundry) — `cast` | The fastest way to query a node or decode calldata from a terminal. `cast block`, `cast call`, `cast 4byte-decode`. |
| [ethers.js](https://docs.ethers.org/) / [viem](https://viem.sh/) | The two JavaScript libraries worth using |
| [web3.py](https://web3py.readthedocs.io/) | Python equivalent |

`cast` deserves special mention for operators: it turns most of the CLI sheet's
`curl | jq` incantations into one readable command against your own RPC.

---

## What POSTHUMAN uses, and what it would take to add more

Today the Hub renders reviewed Ethereum guides and links out for live data.
Candidates for first-party integration, in dependency order:

1. **A read-only Ethereum explorer panel** in the Hub — validator, epoch and
   finality data from a beacon API, plus gas and head data from an execution
   RPC. This is the piece with the clearest value and it needs a data source
   decision: a public endpoint, or a POSTHUMAN node. We do not currently run an
   Ethereum node, so today it would read a third-party endpoint.
2. **A validator lookup and performance view** over the beacon API — the thing
   an operator actually opens daily, and the closest analogue to what the Hub
   already does for other networks.
3. **Staking tools on top of the existing EVM wallet layer** — the Hub already
   signs EVM transactions for other networks. Exit, partial withdrawal and
   consolidation requests are ordinary EVM transactions to the two Pectra
   predeploys, so the signing path already exists; only the calldata builders
   and the safety rails are missing.
4. **A client-diversity and fork-readiness panel** — minority client shares and
   the next fork's minimum versions, which is the number an operator needs
   before every upgrade.

Each of those is a separate decision about where the data comes from, and none
of them should quietly depend on a third-party API that can disappear.
