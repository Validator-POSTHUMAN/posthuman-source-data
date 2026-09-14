# Helicon Mainnet Upgrade

> Publication status: guidance only. Switching a node to AvalancheGo v1.15.0
> is a separate, explicitly authorized operational task. This guide does not
> perform or claim that cutover.

## Activation and required release

Helicon activates on Avalanche Mainnet at **2026-09-22 15:00 UTC**. The
AvalancheGo v1.15.0 release states that every Mainnet node must upgrade before
that time and that older releases will not remain compatible at activation.
Source: [AvalancheGo v1.15.0 release](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

Reviewed release identity:

```text
Version:            v1.15.0
Commit:             70bd6d063b7343fd2cd8217200aaf77b57f19f68
Linux AMD64 asset:  avalanchego-linux-amd64-v1.15.0.tar.gz
SHA-256:            ca5330e6cf8f31106f89929db84c65af7bf2a6a74789bad36a7bbde4cbea7019
Plugin protocol:    46
```

The release page publishes the asset and states that plugin protocol 46 is
required. The tag commit and digest are pinned here so the artifact can be
checked without trusting a moving branch. Source: [v1.15.0 release and assets](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

## Helicon changes

- C-Chain asynchronous execution is activated by [ACP-194](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/194-continuous-execution/README.md). Source: [v1.15.0 feature list](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#features).
- Auto-renewed staking is introduced by [ACP-236](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/236-auto-renewed-staking/README.md). Source: [v1.15.0 feature list](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#features).
- The validator reward uptime requirement rises to 90% for validation periods that begin at or after activation; existing periods keep the prior rule. Source: [ACP-267](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/267-uptime-requirement-increase/README.md).
- The Primary Network minimum staking duration drops to 48 hours at activation. Source: [ACP-273](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/273-reduce-minimum-staking-duration/README.md).
- C-Chain receives a dynamic minimum gas-price mechanism. Source: [ACP-283](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/283-dynamic-minimum-gas-price/README.md).
- The staking reward curve changes for new staking periods; already-staked validations retain their existing reward terms. Source: [ACP-285](https://github.com/avalanche-foundation/ACPs/blob/main/ACPs/285-reduce-minimum-consumption-rate/README.md).

## Operator preflight for the separate cutover task

Before scheduling the separate node switch, review the release for plugin
compatibility, removed APIs, configuration type changes, state-sync limits,
and rollback constraints. Source: [complete v1.15.0 release notes](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

Specific Helicon gates from that release:

- Do not have a C-Chain state sync in progress at activation; it may stall.
- Restarting a post-Helicon state sync restarts that sync from the beginning.
- A Firewood node cannot use state sync.
- `state-sync-ids` becomes a JSON array.
- `api-max-duration` accepts a duration string rather than a number.
- C-Chain `state-sync-enabled` defaults to `true` after activation.
- `eth-apis` is deprecated in favor of `apis`, and removed API namespaces or
  methods must not be relied on.

Source for every gate above: [v1.15.0 C-Chain State Sync, APIs, and Configs](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#c-chain-state-sync).

The separate cutover task should preserve the running binary and configuration
as rollback evidence, stage and verify the new artifact before downtime,
restart only the intended node once, then verify version/commit, P/X/C
bootstrap, aggregate health, advancing height, peers, external validator
connectivity, and monitoring. Sources: [official upgrade guide](https://build.avax.network/docs/nodes/maintain/upgrade), [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc), [Health RPC](https://build.avax.network/docs/rpcs/other/health-rpc).
