# Arc Network mainnet — endpoints and resources

All values verified 2026-09-18.

## Chain

| | |
|---|---|
| Chain ID | `5042` / `0x13b2` |
| CAIP-2 | `eip155:5042` |
| Gas token | USDC — 18 decimals natively, 6 as ERC-20 |
| Finality | sub-second, deterministic |
| Mainnet live since | 2026-09-16 |
| Node release | `v0.8.0` |

```sh
curl -s -X POST https://rpc.mainnet.arc.io -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# {"jsonrpc":"2.0","id":1,"result":"0x13b2"}
```

## RPC — mainnet

| Provider | Endpoint | WebSocket |
|---|---|---|
| Arc | `https://rpc.mainnet.arc.io` | `wss://rpc.mainnet.arc.io` |
| dRPC | `https://rpc.drpc.mainnet.arc.io` | `wss://rpc.drpc.mainnet.arc.io` |
| Blockdaemon | `https://rpc.blockdaemon.mainnet.arc.io` | `wss://rpc.blockdaemon.mainnet.arc.io/websocket` |
| QuickNode | `https://rpc.quicknode.mainnet.arc.io` | `wss://rpc.quicknode.mainnet.arc.io` |
| Alchemy | — | `wss://arc-mainnet.g.alchemy.com/v2/YOUR_API_KEY` |

All four HTTPS endpoints answered `0x13b2` on 2026-09-18.

These are Circle's **developer** RPC endpoints. Circle's `node-requirements`
page, which lists the relay endpoints a consensus layer should follow, still
carries only Arc Testnet — see the installation guide.

## RPC — testnet

| | |
|---|---|
| Arc | `https://rpc.testnet.arc.io` (also `wss://`) |
| dRPC | `https://rpc.drpc.testnet.arc.io` |
| Blockdaemon | `https://rpc.blockdaemon.testnet.arc.io` |
| QuickNode | `https://rpc.quicknode.testnet.arc.io` |
| Legacy alias | `https://rpc.testnet.arc.network` — still answers |

There is no `rpc.mainnet.arc.network`. The legacy domain has a testnet form and
no mainnet form.

## Explorers

| | |
|---|---|
| Arc Explorer (official) | <https://explorer.arc.io> |
| Etherscan | <https://arc.etherscan.io> |
| ExploreMe | <https://arc.exploreme.pro> |
| Arc Testnet Explorer | <https://explorer.testnet.arc.io> |

`testnet.arcscan.app` redirects to `explorer.testnet.arc.io`.

## Official

| | |
|---|---|
| Website | <https://www.arc.io/> |
| Documentation | <https://docs.arc.io> |
| Node repository | <https://github.com/circlefin/arc-node> |
| Releases | <https://github.com/circlefin/arc-node/releases> |
| Node requirements | <https://docs.arc.io/arc/references/node-requirements> |
| Run an Arc node | <https://docs.arc.io/arc/tutorials/run-an-arc-node> |
| EVM differences | <https://docs.arc.io/arc/references/evm-differences> |
| Contract addresses | <https://docs.arc.io/arc/references/contract-addresses> |
| Gas and fees | <https://docs.arc.io/arc/references/gas-and-fees> |
| Snapshot service | <https://snapshots.arc.network> |
| Faucet (testnet) | <https://faucet.circle.com> |
| Community | <https://community.arc.io/> |
| Discord | <https://discord.com/invite/buildonarc> |
| X | <https://x.com/arc> |
| Brand guidelines | <https://www.arc.io/brand-guidelines-and-partner-toolkit> |

## Node ports

| Port | Service | Exposure |
|---|---|---|
| `8545` | EL JSON-RPC | loopback on a follow node |
| `8546` | EL WebSocket | loopback on a follow node |
| `8551` | EL Engine API | never |
| `9001` | EL metrics | loopback |
| `29000` | CL metrics | loopback |
| `31000` | CL RPC | never |
| `30303` | EL P2P | RPC provider nodes only |
| `27000` | CL P2P | RPC provider nodes only, IP-restricted |

A follow node needs no inbound ports at all.

## Contract addresses worth knowing

| | |
|---|---|
| USDC system emitter | `0xffffFFFfFFffffffffffffffFfFFFfffFFFfFFfE` |
| Denylist proxy (mainnet) | `0x3600000000000000000000000000000000000004` |

The emitter logs all USDC `Transfer` events; an indexer that does not know
about it will miss them. The denylist address is read from
`crates/execution-config/src/chainspec.rs` at tag `v0.8.0`.

Full list: <https://docs.arc.io/arc/references/contract-addresses>

## POSTHUMAN

POSTHUMAN supports Arc. We run an Arc **testnet** full node and publish these
operator guides; we operate no public Arc RPC and claim no validator role,
partnership or endorsement.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
