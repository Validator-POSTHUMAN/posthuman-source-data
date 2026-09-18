# Arc Network test networks

| Network | Chain ID | RPC | Explorer |
|---|---|---|---|
| Arc mainnet | `5042` / `0x13b2` | `https://rpc.mainnet.arc.io` | <https://explorer.arc.io> |
| Arc Testnet | `5042002` / `0x4cef52` | `https://rpc.testnet.arc.io` | <https://explorer.testnet.arc.io> |
| Arc Devnet | `5042001` | — | — |

Chain IDs read from `crates/shared/src/chain_ids.rs` at tag `v0.8.0`; both RPC
endpoints verified live on 2026-09-18.

## The domain moved, and only half of it is aliased

Arc's canonical endpoints are on **`arc.io`**. Older material — including our
own earlier testnet guide — uses `arc.network`. Verified 2026-09-18:

| Old address | State |
|---|---|
| `https://rpc.testnet.arc.network` | still answers, chain `0x4cef52` |
| `https://rpc.mainnet.arc.network` | **does not resolve** |
| `https://testnet.arcscan.app` | `301` → `https://explorer.testnet.arc.io` |
| `https://snapshots.arc.network` | still the snapshot service host |

So the legacy domain carries testnet and snapshots and has no mainnet form at
all. A runbook that pattern-substitutes `testnet` → `mainnet` in an
`arc.network` URL produces a hostname that does not exist. Use `arc.io` for
everything except the snapshot service.

## Testnet

```sh
arc-node-execution node --chain arc-testnet ... \
  --rpc.forwarder https://rpc.testnet.arc.io/

arc-node-consensus start ... \
  --follow.endpoint https://rpc.testnet.arc.io,wss=rpc.testnet.arc.io \
  --follow.endpoint https://rpc.drpc.testnet.arc.io,wss=rpc.drpc.testnet.arc.io \
  --follow.endpoint https://rpc.blockdaemon.testnet.arc.io,wss=rpc.blockdaemon.testnet.arc.io/websocket
```

```sh
arc-snapshots download --chain=arc-testnet --el-profile=full ...
```

Testnet snapshot sizes are the ones Circle publishes: about 68 GB compressed EL
and 16 GB compressed CL, extracting to roughly 103 GB and 36 GB.

Faucet: <https://faucet.circle.com>

Additional testnet RPC providers: `rpc.quicknode.testnet.arc.io`,
`rpc.drpc.testnet.arc.io`, `rpc.blockdaemon.testnet.arc.io`, plus WebSocket
forms of each.

## Which one to run first

Testnet, for one reason that is specific to this network: **Arc hardforks
activate on wall-clock timestamps, and testnet activates first.** Zero8 hit
testnet on 2026-09-03 15:00 UTC and mainnet on 2026-09-10 15:00 UTC — a week
of warning, available only to operators who were running the testnet.

That week is the whole value of the testnet node here. It is not a place to
rehearse a signing procedure, because there is no signing; it is an early
warning that a release is about to become mandatory.

## Keep them separate

- Separate hosts, or at minimum separate `$ARC_HOME`, `$ARC_RUN` and units. The
  EL P2P and CL RPC ports already collide within a single node when
  misconfigured; two nodes on one host multiply that.
- Separate consensus-layer identities. `arc-node-consensus init` per home.
- `--chain` is the setting that decides everything else. Circle's published
  `docker-compose.yml` and every quickstart target `arc-testnet`; a mainnet
  deployment copied from one of them with the RPC URLs changed and `--chain`
  left alone is a testnet node pointed at mainnet relays.

```sh
cast chain-id --rpc-url http://127.0.0.1:8545
```

Run that after any deployment built by copying another one.

## Devnet

`5042001`, supported as `arc-devnet` by both the chain-spec parser and
`arc-snapshots` at `v0.8.0`. Circle publishes no public endpoints or
documentation for it; treat it as internal.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
