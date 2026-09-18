# Bitcoin Operator Toolbox

A curated set, filtered for people who **run** infrastructure rather than write
wallet apps. The wider catalogue is
[awesome-bitcoin](https://github.com/igorbarinov/awesome-bitcoin); most of it is
language bindings and is out of scope here.

Selection rule for this page: maintained, verifiable, and useful at least once
in a real operational week.

## CLI utilities

| Tool | What it does | Use it when |
|---|---|---|
| [hal](https://github.com/stevenroose/hal) | Rust "swiss army knife" — decode and inspect transactions, scripts, addresses, keys, PSBTs and BIP32 paths, offline | Inspecting a raw transaction or descriptor without a node, on a machine you would not put a node on |
| [bx (libbitcoin-explorer)](https://github.com/libbitcoin/libbitcoin-explorer) | Long-lived C++ CLI: encode/decode, key derivation, script tooling | You want one binary covering key and script maths in scripts |
| [btcdeb](https://github.com/kallewoof/btcdeb) | Step-through Bitcoin Script debugger | Debugging a failing script or a non-standard spend path |
| [bitcoin-toolkit](https://github.com/bartobri/bitcoin-toolkit) | Small C utilities for addresses, keys and node queries | Quick address and key inspection in shell pipelines |
| [Nigiri](https://github.com/vulpemventures/nigiri) | One-command regtest box with Electrs, Esplora, faucet and push | Bringing up a full local test stack in seconds |

`hal` and `btcdeb` are the two worth installing on every operator workstation.
Neither needs a node, and both answer questions that otherwise cost an hour.

## Node distributions and stacks

| Project | Shape | Use it when |
|---|---|---|
| [nix-bitcoin](https://github.com/fort-nix/nix-bitcoin) | NixOS modules: Core plus Core Lightning, hardened, declarative | You want a reproducible, security-focused node definition in git |
| [btcpayserver-docker](https://github.com/btcpayserver/btcpayserver-docker) | Compose stack: Core, NBXplorer, LND/CLN, BTCPay | Payments, or a reference for what a full stack needs |
| [RaspiBolt](https://raspibolt.org) | Build-from-parts guide, Pi and Debian | Teaching the stack, or a lab node |
| [Cyphernode](https://github.com/SatoshiPortal/cyphernode) | Modular node backend, optional indexers | Commercial backends that need a subset of services |
| [Umbrel](https://umbrel.com) / [Start9](https://start9.com) | Appliance distributions | Home nodes, non-operator users |

Even when we deploy by hand, these Compose files are the compact record of
which ports, volumes and ZMQ topics a real stack actually needs.

## Indexers and explorer backends

| Tool | Notes |
|---|---|
| [romanz/electrs](https://github.com/romanz/electrs) | Rust Electrum server, reads block files directly, ~120 GB index |
| [cculianu/Fulcrum](https://github.com/cculianu/Fulcrum) | C++ Electrum server, faster queries, ~90 GB index |
| [Blockstream/esplora](https://github.com/Blockstream/esplora) | Self-hosted explorer and the de-facto REST API shape |
| [mempool/mempool](https://github.com/mempool/mempool) | Mempool, fee and Lightning explorer; Esplora-compatible REST plus `/api/v1/…` |
| [chaingraph](https://github.com/bitauth/chaingraph) | Multi-node indexer with a GraphQL API |

All require an **archive** node. Configuration is in **RPC, indexes and APIs**.

## Public APIs

| API | Good for |
|---|---|
| [mempool.space](https://mempool.space/docs/api/rest) | Tip, blocks, transactions, addresses, fee recommendations, difficulty adjustment, mining and Lightning statistics |
| [blockstream.info](https://github.com/Blockstream/esplora/blob/master/API.md) | The same Esplora surface; a good independent second source |
| [3xpl](https://3xpl.com/bitcoin), [blockchair](https://blockchair.com/bitcoin) | Ad-hoc lookups and cross-checking |

Two independent public APIs are the cheapest chain-divergence check there is —
that check is in **Monitoring**, and it is the one we actually run.

## Libraries, when tooling has to be written

| Language | Library |
|---|---|
| Rust | [rust-bitcoin](https://github.com/rust-bitcoin/rust-bitcoin), [BDK](https://bitcoindevkit.org/), [LDK](https://lightningdevkit.org/) |
| TypeScript | [scure-btc-signer](https://github.com/paulmillr/scure-btc-signer) — audited, minimal, PSBT and Taproot; [bitcoinjs-lib](https://github.com/bitcoinjs/bitcoinjs-lib) |
| Python | [pycoin](https://github.com/richardkiss/pycoin), [bitcoin_tools](https://github.com/sr-gi/bitcoin_tools) |
| C | [libsecp256k1](https://github.com/bitcoin-core/secp256k1) |

For anything that touches keys, prefer the audited minimal library over the
convenient one. `scure-btc-signer` and `libsecp256k1` are the defaults.

## Playgrounds and references

| | |
|---|---|
| [Bitauth IDE](https://ide.bitauth.com/) | Interactive contract and script development |
| [Script Playground](https://www.crmarsh.com/script-playground/) | Quick script evaluation in a browser |
| [ChainQuery](https://chainquery.com) | Run RPC calls and read the full RPC documentation in a browser |
| [Mastering Bitcoin](https://github.com/bitcoinbook/bitcoinbook) | The reference text, free and current |
| [Chaincode protocol curriculum](https://github.com/chaincodelabs/bitcoin-curriculum) | Structured deep study, Bitcoin and Lightning |

## What we deliberately do not use

- **Custodial or API-key-gated node services** as a primary data source. The
  point of running a node is not having to trust one.
- **Unmaintained container images** for `bitcoind`. Build from the verified
  release — the three-line Dockerfile is in **Docker install**.
- **`curl … | sh` installers**, for anything in this stack.
- **Price, "cycle top" and profitability dashboards.** Plenty exist in
  awesome-bitcoin; none belong in node operations.

## Adoption shortlist

If you install nothing else:

1. `hal` — offline inspection of anything hex-shaped.
2. `btcdeb` — when a script fails and the error is unhelpful.
3. `Nigiri` — a whole regtest stack, one command, for testing before mainnet.
4. A self-hosted `mempool` instance — replaces both the public explorer
   dependency and half a Grafana dashboard.
5. Two public Esplora-compatible APIs wired into monitoring as independent
   chain-tip sources.

## Sources

- [igorbarinov/awesome-bitcoin](https://github.com/igorbarinov/awesome-bitcoin)
- [bitcoin.org — running a full node](https://bitcoin.org/en/full-node)
- [bitcoiner.guide — node options](https://bitcoiner.guide/node/)
- [mempool.space — REST API](https://mempool.space/docs/api/rest)
- [Blockstream/esplora — API](https://github.com/Blockstream/esplora/blob/master/API.md)
