# State-sync prerequisites

The final config disables state sync. No pair of current independently reviewed mainnet snapshot-serving RPCs and trust anchors is published here. No runnable reset/state-sync recipe is provided. Use ordinary block sync from the final genesis.

Before enabling state sync establish two distinct providers for `limonata_20777-1`, actual application snapshot availability, an independently checked recent trust height/hash and a trust period shorter than current unbonding with an adequate time margin. Refresh at execution time; never reuse a hardcoded historical trust anchor.

Use Comet RPC, not EVM JSON-RPC. Check application snapshot/database compatibility, current release requirements, capacity and `evm-chain-id = 20777`. Answering /status does not prove snapshot support.

Validator recovery requires one-signer proof and protected consensus/P2P/DKG identities with the newest monotonic signing state. Never reset or roll back that state. Follow [Snapshot safety](snapshots.md) and [Backup and recovery](backup-recovery.md); verify block identity, sync, signatures and DKG after recovery.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
