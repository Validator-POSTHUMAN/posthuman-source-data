# Celestia Full Node Terminology and Legacy DA Role Retirement — Mocha-5

There is no current `full` role in celestia-node. The supported data
availability roles are **bridge** and **light**. Older guides used “full storage
node” for a retired DA role; do not use those obsolete commands with current
software.

## Mocha-5 boundary

- Consensus chain ID: `mocha-5`
- DA P2P network: `mocha`
- Mocha-5 began at height 1 and is not an in-place Mocha-4 upgrade.
- Never reuse Mocha-4 chain data, a Mocha-4 DA store, or Mocha-4 signer state.

## Two different meanings

### Consensus full node

A consensus full node runs **celestia-appd** from celestia-app. It validates the
consensus chain, executes application state, and can provide RPC and gRPC. A
validator is a consensus full node with an active consensus signer.

Current Mocha reference:

- celestia-app: `v9.0.6-mocha`
- Commit: `6f4b596e47f80683adb1a161ca7cb640dcd9d206`
- Home must be a dedicated Mocha-5 path, such as
  `$HOME/.celestia-app-mocha-5`.

| Consensus profile | CPU | Memory | NVMe | Network |
| --- | ---: | ---: | ---: | ---: |
| Validator or non-archival consensus node | 32 cores | 32 GB | 12 TiB | 1 Gbps |
| Archival consensus node | 32 cores | 64 GB | 624 TiB | 1 Gbps |

The non-archival estimate uses a conservative 7-day planning window; archival
uses one year. Both use the 128 MB per 6 seconds maximum-throughput envelope.
Actual use may be lower. Validators must pass the official CPU benchmark;
prefer GFNI and SHA-NI support.

A bridge node's initial sync needs an archival Mocha-5 consensus gRPC source.
A consensus node is archival only when its block retention and application
pruning are configured and verified for that purpose.

### Data availability node

A DA node runs **celestia-node**. Choose a current role:

| Need | Current role | Guide | Mocha-5 store |
| --- | --- | --- | --- |
| Import, erasure-code, retain, and serve blocks | Bridge | [Bridge node setup](bridge-node-setup.md) | `$HOME/.celestia-bridge-mocha-5` |
| Verify availability through DAS | Light | [Light node setup](light-node-setup.md) | `$HOME/.celestia-light-mocha-5` |

Do not relabel or copy a legacy DA store. Initialize a separate current-role
store with `--p2p.network mocha` and independently verify Mocha-5 freshness.

## Migration checklist for a legacy DA deployment

1. Record the installed version, configured network, store path, peer ID,
   retention intent, and upstream consensus source without exposing key data.
2. Treat any Mocha-4 identity or height history as incompatible with Mocha-5.
3. Decide whether the workload needs bridge retention/serving or light DAS.
4. Provision the chosen role in its dedicated `-mocha-5` store.
5. Keep JSON-RPC `26658` on loopback and expose bridge P2P `2121` over TCP and
   UDP when choosing the bridge role.
6. Prove new-role sync, peers, storage headroom, and independent Mocha-5 height
   freshness before retiring the legacy process.
7. Handle identity or wallet transfer only through a separately approved key
   procedure.

This page intentionally contains no legacy full-role command examples, reset
steps, key deletion, or transaction actions.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/networks/mocha-testnet`
- `operate/consensus-validators/consensus-node`
- `operate/data-availability/bridge-node`
- `operate/data-availability/light-node/quickstart`
