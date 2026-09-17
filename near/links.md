# NEAR Endpoints, Explorers and Tools

## POSTHUMAN

| Resource | Value |
|----------|-------|
| Validator pool | [`posthuman.poolv1.near`](https://nearblocks.io/node-explorer/posthuman.poolv1.near) |
| Delegate | [nearblocks.io/address/posthuman.poolv1.near](https://nearblocks.io/address/posthuman.poolv1.near) |

## Public RPC — mainnet

`rpc.mainnet.near.org` is severely rate limited and is not a dependable
automation target. For anything that polls, use FastNEAR's free endpoint or run
your own RPC node.

| Provider | Endpoint | Archival | Notes |
|----------|----------|----------|-------|
| FastNEAR | `https://free.rpc.fastnear.com` | paid only | free tier, recommended public default |
| NEAR | `https://archival-rpc.mainnet.near.org` | yes | severely rate limited |
| dRPC | `https://near.drpc.org` | no | free tier |
| BlockPI | `https://near.blockpi.network/v1/rpc/public` | no | 20 req/s free |
| 1RPC | `https://1rpc.io/near` | no | 200 req/day free |
| Intear | `https://rpc.intea.rs` | no | free |
| ZAN | `https://api.zan.top/node/v1/near/mainnet/` | no | ~20 req/s free |

## Public RPC — testnet

| Provider | Endpoint | Archival |
|----------|----------|----------|
| FastNEAR | `https://test.rpc.fastnear.com` | paid only |
| NEAR | `https://archival-rpc.testnet.near.org` | yes, rate limited |
| dRPC | `https://near-testnet.drpc.org` | no |
| Intear | `https://testnet-rpc.intea.rs` | no |

The canonical, maintained list is
[docs.near.org/api/rpc/providers](https://docs.near.org/api/rpc/providers).
FastNEAR publishes a
[public latency dashboard](https://grafana.fastnear.com/public-dashboards/577b37c6cfe84b2bae23af471d27cade)
for most of these endpoints.

## Health-check any endpoint

```bash
RPC=https://free.rpc.fastnear.com
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{chain: .result.chain_id,
         version: .result.version.version,
         protocol: .result.protocol_version,
         height: .result.sync_info.latest_block_height,
         syncing: .result.sync_info.syncing}'
```

Compare `latest_block_height` across two independent endpoints before trusting
either. [nearvalidate.org](https://nearvalidate.org/) does the same check from
a browser against any endpoint you paste in.

## Explorers

| Tool | Use |
|------|-----|
| [nearblocks.io](https://nearblocks.io) | blocks, transactions, accounts, contracts |
| [nearblocks.io/node-explorer](https://nearblocks.io/node-explorer) | validator set, live seat price, uptime |
| [near-staking.com/stats](https://near-staking.com/stats) | validator and delegation statistics |
| [pikespeak.ai](https://pikespeak.ai/) | account analytics, portfolio tracking, [validator overview](https://pikespeak.ai/validators/overview) |
| [nearvalidate.org](https://nearvalidate.org/) | real-time data from any NEAR RPC node |

## Operator tooling

| Tool | Use |
|------|-----|
| [near-cli-rs](https://github.com/near/near-cli-rs) | the current NEAR CLI |
| [near-validator-cli-rs](https://github.com/near-cli-rs/near-validator-cli-rs) | `proposals`, `validators now/next`, staking |
| [kilnfi/near-validator-watcher](https://github.com/kilnfi/near-validator-watcher) | Prometheus exporter for produced vs expected work |
| [near/nearcore](https://github.com/near/nearcore) | `neard` source and releases |
| [near/core-contracts](https://github.com/near/core-contracts/tree/master/staking-pool) | staking-pool contract source |
| [FastNEAR Data API](https://docs.fastnear.com/neardata) | hosted indexed chain data |

## Wallets

| Wallet | Notes |
|--------|-------|
| [Meteor Wallet](https://meteorwallet.app/) | browser extension and mobile, NEAR-native |
| [MyNearWallet](https://app.mynearwallet.com/) | web wallet, successor to the retired `wallet.near.org` |
| [HERE Wallet](https://herewallet.app/) | mobile |
| Ledger | hardware signing, supported by `near-cli-rs` via `sign-with-ledger` |

Pool ownership keys belong on a hardware wallet or an operator workstation
keychain — never on the validator host. See **Keys & custody**.

## Documentation

- [near-nodes.io](https://near-nodes.io/) — node operator documentation
- [docs.near.org/protocol/network/validators](https://docs.near.org/protocol/network/validators)
- [docs.near.org/protocol/network/staking](https://docs.near.org/protocol/network/staking)
- [docs.near.org/tools/cli](https://docs.near.org/tools/cli)
