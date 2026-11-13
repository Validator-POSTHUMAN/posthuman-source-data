# Troubleshooting

| Symptom | Evidence and action |
| --- | --- |
| Wrong Cosmos/EVM chain | Stop before transactions. Check final genesis, explicit home and evm-chain-id=20777; never overwrite a signing node with a different genesis |
| No peers | Check P2P bind, announced port, self-peer removal and final-package node IDs/reachability; do not copy testnet peers |
| Height stalled | Compare independent mainnet RPCs and logs. Distinguish local lag from network halt before any controlled restart |
| catching_up=true | Measure progress, disk/CPU and peers. Slow sync does not authorize an unverified snapshot/reset |
| AppHash mismatch | Preserve binary/genesis hashes, logs and height; obtain chain-specific guidance, never roll back signing state |
| Jailed / zero power | Query current validator, tombstone, jail and missed blocks. Resolve the cause, confirm eligibility and review one unjail transaction, never broadcast automatically |
| DKG unready | Inspect round/finalization events, ECIES persistence, current committee and QUAL; do not restart through an open round or run disruptive mainnet experiments |
| Tx lookup empty | Check provider indexing/rate limits. NodeSafe reported indexing off; an empty search does not prove non-inclusion |
| Fee failure | Query live feemarket and simulate the exact operation. Local 0aLIMO minimum does not waive the chain-wide floor |

Do not reuse historical testnet genesis-validation workarounds on mainnet. Diagnose unexpected validation failures against the exact approved binary and final file hash. For failed new full nodes stop the process and retain stage/home/logs. For existing signers preserve keys, DKG identity and monotonic state throughout recovery.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
