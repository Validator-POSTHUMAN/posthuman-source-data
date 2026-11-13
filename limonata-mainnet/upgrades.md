# Controlled upgrades

Reviewed baseline: `v0.4.0-mainnet.3+src.c43879f764ef`; binary SHA-256 `594d36fb0874b9abfbc182e7e104a0333f7df365d8d656d2f492a5f2fdf0724b`. The approved binary includes a modified source tree recorded in release.json. Do not assume rebuilding the tag reproduces that binary; use the verified official artifact.

1. Query current on-chain upgrade plan and official mainnet instructions; identify exact plan name/height, artifact, checksum and compatibility. A newer GitHub release alone is not upgrade authorization.
2. Prove unique signer control; record running binary/config, height, capacity, backups and rollback boundary. Preserve keys, latest signing state and DKG identity without printing them.
3. Stage a verified replacement in a separate versioned directory without altering the running daemon. Confirm version and architecture. Disable automatic unverified binary downloads.
4. Switch only under the exact chain halt or approved upgrade procedure. Routine restarts require ACTIVE epoch without an open DKG round. Do not restart repeatedly on a network-wide halt.
5. Verify service stability, exact binary, applied plan, advancing sync, same-height block hash, fresh external signatures and DKG finalization/QUAL membership. Retain evidence and monitoring.

Cosmovisor is optional supervision, not compatibility proof; its plan directory must exactly match the chain plan and auto-download should remain disabled. No future binary or generic Cosmovisor installer is asserted here. Never downgrade across an applied state-breaking upgrade or roll signing state backward; obtain chain-specific recovery guidance if verification fails.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
