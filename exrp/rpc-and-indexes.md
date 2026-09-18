# XRPL EVM Mainnet — RPC, APIs and indexes

One `exrpd` process serves four different APIs. Operators who treat them as one
thing get surprised by which of them needs an index and which does not.

| API | Default port | Speaks | Needed for |
|---|---|---|---|
| CometBFT RPC | `26657` | CometBFT JSON-RPC | consensus state, blocks, `/status` |
| Cosmos REST | `1317` | gRPC-gateway REST | module queries: staking, gov, bank, slashing |
| Cosmos gRPC | `9090` | gRPC | the same modules, typed |
| EVM JSON-RPC | `8545` / `8546` | Ethereum JSON-RPC | wallets, contracts, indexers |

POSTHUMAN publishes all four:

| | |
|---|---|
| RPC | <https://rpc.exrp.posthuman.digital> |
| REST | <https://rest.exrp.posthuman.digital> |
| gRPC | `grpc.exrp.posthuman.digital:443` |
| EVM JSON-RPC | <https://rpc.exrp.posthuman.digital/evm> |

## Enabling them

```toml
# app.toml
[api]
enable = true
address = "tcp://127.0.0.1:1317"
enabled-unsafe-cors = false

[grpc]
enable = true
address = "127.0.0.1:9090"

[json-rpc]
enable = true
address = "127.0.0.1:8545"
ws-address = "127.0.0.1:8546"
api = "eth,net,web3"
```

Bind everything to `127.0.0.1` and terminate TLS, rate limiting and
request-size limits in a reverse proxy. `exrpd` enforces no per-client limit,
so a published port with no proxy is one client away from saturation.

### The namespace list is a security decision

`api = "eth,net,web3"` is the safe public set. Adding `debug` or `txpool`
publishes `debug_traceTransaction` — a single call that can occupy a node for a
long time — and pending-transaction visibility, which is an MEV surface. Enable
them on a private node for your own debugging, never on the endpoint you
advertise.

## The transaction index

```toml
# config.toml
indexer = "kv"     # RPC node
indexer = "null"   # validator
```

This one setting decides whether `/tx?hash=…` and
`eth_getTransactionByHash` can answer at all.

- On an **RPC node** it must be `kv`, or transaction lookup returns null for
  transactions that demonstrably exist, and every integrator opens a ticket.
- On a **validator** it should be `null`. The index grows without a useful
  ceiling and a signer has no reason to serve lookups.

Changing `indexer` does not backfill. A node switched from `null` to `kv`
indexes from that moment forward and stays blind to everything before it. To
serve historical lookups you need a node that has been indexing since the range
you care about — in practice, a resync or a snapshot from a node that was.

## Pruning decides what can be answered at all

```toml
# app.toml
pruning = "custom"
pruning-keep-recent = "100"
pruning-interval = "10"
```

| Setting | State kept | Good for |
|---|---|---|
| `everything` / aggressive custom | ~100 blocks | validator |
| `default` | ~362 880 blocks | general RPC |
| `nothing` | all | archive |

A query against a pruned height fails with a "failed to load state at height"
style error. That is the node telling the truth, not a fault.

An archive node keeps every state version, needs far more than the 1 TB
baseline, and should be a separate host from anything that signs.

## Verifying each surface

```bash
# CometBFT
curl -s https://rpc.exrp.posthuman.digital/status | jq .result.sync_info

# REST
curl -s https://rest.exrp.posthuman.digital/cosmos/base/tendermint/v1beta1/node_info | jq .default_node_info.network

# gRPC — an ordinary HTTPS request to a gRPC root answers HTTP/2 415.
# That is the expected reply, not an outage.
curl -s -o /dev/null -w '%{http_code}\n' https://grpc.exrp.posthuman.digital

# EVM
curl -s -X POST https://rpc.exrp.posthuman.digital/evm \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# {"jsonrpc":"2.0","id":1,"result":"0x15f900"}
```

## The two chain IDs

| | Value |
|---|---|
| Cosmos | `xrplevm_1440000-1` |
| EVM | `1440000` / `0x15f900` |

They are the same chain. A wallet configured with `1440000` and a node
configured with a different `evm-chain-id` will produce signatures the chain
rejects, with no useful error.

## Address duality

One key, two representations: `ethm1…` on the Cosmos side, `0x…` on the EVM
side. They are the same account and the same balance — do not display them as
two assets, and do not add them together.

```bash
exrpd debug addr <ethm1…>
```

## Health checks for a public endpoint

Height and agreement, not HTTP 200:

```bash
H=$(curl -s https://rpc.exrp.posthuman.digital/status | jq -r .result.sync_info.latest_block_height)
curl -s "https://rpc.exrp.posthuman.digital/block?height=$H" | jq -r .result.block.header.app_hash
curl -s "https://cosmos-rpc.xrplevm.org/block?height=$H"     | jq -r .result.block.header.app_hash
```

A node that returns 200 for everything while sitting 40 000 blocks behind is
the failure mode that matters for an RPC provider, and an uptime check will
never see it.
