# Signing and host security

Run an unprivileged dedicated account. Restrict SSH/management access; expose only the intended P2P port. Retain private Comet RPC, REST, gRPC, EVM RPC/WS, telemetry and pprof. Review management access and rollback before firewall changes.

One consensus key must have only one possible active signer. Before movement/failover stop and fence the old signer and prove it cannot restart. Never copy a live key into a runnable standby, replace/roll back `priv_validator_state.json`, or use `unsafe-reset-all` on a signer.

Protect consensus, P2P and DKG ECIES key files with owner-only permissions. Resolve the DKG path from the approved release's current configuration/documentation instead of guessing. Keep account keyrings, mnemonics and grant recovery material outside the validator home. An account mnemonic is not a consensus backup.

Backups need encrypted, separately controlled custody and a tested procedure that cannot create another signer. DKG shares, threshold key and committee/QUAL reconstruct from committed state; do not invent a local-share backup scheme. Never print secrets in logs or support chat. Verify release integrity via trusted official channels before executing code.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
