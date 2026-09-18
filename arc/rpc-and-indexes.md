# Arc Network mainnet — RPC and the `arc` namespace

Two kinds of node serve RPC on Arc, and Circle's rules for them are different.

| | Follow node | RPC provider node |
|---|---|---|
| Gets blocks from | relay endpoints over HTTP/WS | direct peering, devp2p + libp2p |
| Exposure | loopback | public, behind a proxy |
| Namespaces | your choice locally | `eth,net,web3,rpc` **only** |
| `--rpc.forwarder` | recommended | **prohibited** |
| Peering | `--disable-discovery` | `--trusted-peers` from onboarding |

Most operators want the first. The second requires enode URLs and sentry
multiaddrs that Circle provides during onboarding — without them you cannot
build one, whatever the flags say.

## Namespaces

```sh
--http.api eth,net,web3,rpc
--ws.api eth,net,web3,rpc
--public-api
```

Prohibited on a public endpoint: `txpool`, `debug`, `trace`, `admin`,
`flashbots`, `mev`, `ots`.

`--public-api` enforces this at runtime — it hides pending-transaction RPCs, an
MEV vector, and warns at startup if the namespace list exceeds the safe set. It
is a guard, not a substitute for setting the list correctly.

Circle's own quickstart uses `--http.api eth,net,web3,txpool,trace,debug`. That
is reasonable on `127.0.0.1` and is a remote denial-of-service on anything
reachable: `debug_traceTransaction` is one call that can occupy a node
indefinitely.

Verify what you actually exposed:

```sh
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"rpc_modules","params":[],"id":1}' | jq .result
```

Expected on a correctly configured node with `--enable-arc-rpc`:

```json
{ "arc": "1.0", "net": "1.0", "rpc": "1.0", "eth": "1.0", "web3": "1.0" }
```

Anything else in that object is a misconfiguration. Confirm the pending-tx
guard separately — this should return an error with code `-32001`, not a filter
id:

```sh
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_newPendingTransactionFilter","params":[],"id":1}' | jq .error
```

Note that Circle's own public endpoint does not answer `rpc_modules` at all —
`{"code":-32601,"message":"method not supported"}`, verified 2026-09-18. Your
own node will.

## The `arc` namespace

`--enable-arc-rpc` adds two methods:

| Method | Returns |
|---|---|
| `arc_getCertificate(height)` | the BFT commit certificate for that block height |
| `arc_getVersion()` | build and version information |

```sh
curl -s -X POST https://rpc.mainnet.arc.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'
```

On 2026-09-18 the official mainnet endpoint answered:

```json
{"git_version":"v0.8.0","git_commit":"5abb64c185d02dd1b3996f15c187020c98171f8d",
 "git_short_hash":"5abb64c1","cargo_version":"v0.8.0 (5abb64c1)"}
```

That is the cleanest way to establish what version the network is running,
without trusting a documentation table.

The EL **proxies** certificate requests to the co-located CL's REST API,
defaulting to `http://127.0.0.1:31000`. Which is why `--rpc.addr` on the CL is
required whenever the EL runs `--enable-arc-rpc`, and why a load balancer in
front of 8545 must allow `arc_getCertificate` through.

## Caching

Two things are safe to cache by height at the edge, because finality on Arc is
deterministic and a finalized block is immutable:

- `arc_getCertificate` — any valid certificate for a height stays valid;
- `eth_getBlockByNumber` for finalized blocks.

Nothing about the pending state is cacheable, and on a correctly configured
public node nothing about the pending state is served.

## Connection limits

| Flag | Default | Note |
|---|---|---|
| `--rpc.max-connections` | `250` | lowered from 500 in `v0.7.1` |
| `--rpc.max-subscriptions-per-connection` | `32` | lowered from 1024 in `v0.7.1` |

Raise them only if clients report `MaxConnections` or `TooManySubscriptions`.
The defaults bound WebSocket log-fanout memory growth; they should be raised,
never lowered.

The node enforces **no per-client request limit**. Without a reverse proxy
doing rate limiting, request-size limits and connection throttling, one client
can saturate the interface. That is not a hardening nicety on Arc; it is the
difference between an endpoint and an outage.

## Transaction submission

On a follow node, `--rpc.forwarder https://rpc.mainnet.arc.io/` routes
transactions the node cannot serve locally to an upstream RPC for broadcast.

On an RPC provider node, `--rpc.forwarder` is **prohibited**, and propagation
is restricted instead:

```sh
--tx-propagation-policy Trusted
```

## EVM behaviours that surprise people

Arc targets the Osaka EVM baseline, and several runtime behaviours diverge from
Ethereum. The ones that break indexers and wallets:

- **USDC is the gas token, with 18 decimals natively and 6 as an ERC-20.** The
  same balance, two representations. Never display them as separate assets and
  never add them together.
- The system emitter `0xffffFFFfFFffffffffffffffFfFFFfffFFFfFFfE` logs all USDC
  `Transfer` events.
- The mempool enforces a **20 Gwei `maxFeePerGas` floor**.
- Blocklist reverts consume gas **without producing a receipt**.
- Sends to `address(0)` revert rather than succeed.

The canonical reference is
<https://docs.arc.io/arc/references/evm-differences>. Read it before writing
anything that touches balances, transaction history or gas estimation.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
