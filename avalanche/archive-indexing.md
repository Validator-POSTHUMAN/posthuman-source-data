# Avalanche C-Chain Archive and Indexing

> Reviewed on 2026-09-14. Choose archive mode before initial bootstrap. This
> page documents configuration; it does not alter a running node.

## Archive mode

A C-Chain archival node retains historical state by disabling pruning. It must
also avoid state sync because state sync downloads a recent state rather than
replaying complete history. Sources: [v1.15.0 C-Chain configuration](https://github.com/ava-labs/avalanchego/blob/v1.15.0/vms/saevm/cchain/config.md), [official installer state-sync guidance](https://build.avax.network/docs/nodes/run-a-node/using-install-script/installing-avalanche-go).

With the default chain-config directory, create
`$HOME/.avalanchego/configs/chains/C/config.json` before the first C-Chain
bootstrap:

```json
{
  "pruning-enabled": false,
  "state-sync-enabled": false
}
```

The C-Chain config path and both option meanings are documented in the pinned
v1.15.0 reference. After Helicon, C-Chain state sync defaults to `true`, so an
archive node must set it explicitly to `false`. Sources: [v1.15.0 C-Chain
configuration](https://github.com/ava-labs/avalanchego/blob/v1.15.0/vms/saevm/cchain/config.md), [v1.15.0 release notes](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#c-chain-state-sync).

Do not convert a partially pruned or state-synced database in place and call it
an archive: the missing historical state was never downloaded. Build a
separate archive node from a clean database and retain the old node until the
new one has replayed and passed historical queries. This follows directly from
the official distinction between replaying history and downloading only recent
state. Sources: [source-build bootstrapping guide](https://build.avax.network/docs/nodes/run-a-node/from-source#bootstrapping), [installer state-sync guidance](https://build.avax.network/docs/nodes/run-a-node/using-install-script/installing-avalanche-go).

## Avalanche indexer

AvalancheGo's `index-enabled` node option is separate from C-Chain archival
state. Setting it to `true` enables the Avalanche indexer and Index API; it is
`false` by default. Source: [AvalancheGo configuration flags](https://build.avax.network/docs/nodes/configure/configs-flags#apis).

```json
{
  "index-enabled": true
}
```

Enable the indexer only when the application needs the Index API. It does not
replace `"pruning-enabled": false` for historical C-Chain state. Sources:
[configuration flags](https://build.avax.network/docs/nodes/configure/configs-flags#apis), [v1.15.0 C-Chain configuration](https://github.com/ava-labs/avalanchego/blob/v1.15.0/vms/saevm/cchain/config.md).

## Capacity and validation

Archive mode retains more state and requires materially more storage and
bootstrap time than a pruned/state-synced validator. Monitor disk headroom and
alert before the node's built-in low-space thresholds. Sources: [C-Chain
pruning configuration](https://github.com/ava-labs/avalanchego/blob/v1.15.0/vms/saevm/cchain/config.md), [recommended disk alerts](https://build.avax.network/docs/nodes/maintain/recommended-metrics#disk-space-remaining).

After bootstrap, verify ordinary health plus a historical C-Chain query at an
old block height required by your application. The Health RPC proves current
node health but not application-specific history completeness. Sources:
[Health RPC](https://build.avax.network/docs/rpcs/other/health-rpc), [C-Chain JSON-RPC reference](https://build.avax.network/docs/rpcs/c-chain).
