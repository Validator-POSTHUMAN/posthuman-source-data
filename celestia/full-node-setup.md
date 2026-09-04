# Celestia Full Node Terminology and Legacy DA Role Retirement

There is no current `full` role in celestia-node. The supported data
availability roles are **bridge** and **light**. Older guides used “full storage
node” for a retired DA role; do not use those obsolete commands with current
software.

## Two different meanings

### Consensus full node

A consensus full node runs **celestia-appd** from the celestia-app repository.
It validates the consensus chain, executes application state, and can provide
RPC and gRPC services. A validator is a consensus full node with an active
consensus signer.

Current celestia-app mainnet reference:

- Version: `v9.0.6`
- Commit: `6f4b596e47f80683adb1a161ca7cb640dcd9d206`
- Chain ID: `celestia`

| Consensus profile | CPU | Memory | NVMe | Network |
| --- | ---: | ---: | ---: | ---: |
| Validator or non-archival consensus node | 32 cores | 32 GB | 12 TiB | 1 Gbps |
| Archival consensus node | 32 cores | 64 GB | 624 TiB | 1 Gbps |

The non-archival estimate uses a conservative 7-day planning window; archival
uses one year. Both use the 128 MB per 6 seconds maximum-throughput envelope.
Actual consumption may be lower. Validators must pass the official CPU
benchmark; prefer GFNI and SHA-NI support.

A bridge node's initial sync needs an archival consensus gRPC source. Running a
consensus full node does not automatically make it archival: block retention
and application pruning must be configured and verified deliberately.

### Data availability node

A DA node runs **celestia-node**. Choose one of the current roles:

| Need | Current role | Guide |
| --- | --- | --- |
| Import, erasure-code, retain, and serve blocks | Bridge | [Bridge node setup](bridge-node-setup.md) |
| Verify availability through DAS with low resources | Light | [Light node setup](light-node-setup.md) |

Do not relabel an old DA “full” store as a bridge store. Reinitialize the chosen
current role and apply the correct key-custody and network checks.

## Migration checklist for a legacy DA deployment

1. Record the installed binary version, configured network, store path, peer ID,
   retention intent, and upstream consensus source without exposing key data.
2. Decide whether the workload requires bridge retention/serving or light DAS.
3. Provision the current role in a separate store using its current guide.
4. Keep mainnet RPC `26658` on loopback and expose bridge P2P `2121` over TCP and
   UDP when choosing the bridge role.
5. Prove new-role sync, peer connectivity, storage headroom, and independent
   height freshness before retiring the legacy process.
6. Handle any identity or wallet transfer only through a separately approved
   key procedure.

This page intentionally contains no legacy full-role command examples, reset
steps, key deletion, or transaction actions.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/getting-started/overview`
- `operate/consensus-validators/consensus-node`
- `operate/data-availability/bridge-node`
- `operate/data-availability/light-node/quickstart`
