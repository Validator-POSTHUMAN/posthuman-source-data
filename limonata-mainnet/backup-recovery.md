# Backup and recovery

Keep public configs/genesis and release checksums separate from secret backups. Wallet, consensus signer, P2P and DKG ECIES identities are different recovery domains; a wallet mnemonic alone does not prove consensus recovery.

1. Inventory exact home, service, running binary and signer backend. Prove one active signing location and record height/state without printing secrets.
2. For a consistent backup, stop and fence the signer under planned maintenance, preserving latest monotonic signing state together with protected identity material. Use encrypted custody and verify recovery without launching a duplicate signer.
3. Preserve public configuration, checksum-verified final genesis/binary identity and forensic data before destructive recovery. Locate/preserve the ECIES key through current official path semantics. DKG shares and QUAL reconstruct from chain state, not invented local share files.
4. Restore only under a reviewed chain-specific plan. Never import testnet state, initialize over identities or restore signing state older than the highest signed vote. Database rollback does not permit signer-state rollback.
5. Prove the former signer cannot restart before activation. Afterwards require sync, independent same-height block hash, fresh commit signatures, validator status and DKG readiness. Keep rollback evidence; never retry a failed cutover automatically.

No key export/copy commands are provided. Snapshot/state-sync recovery remains gated on verified mainnet artifacts and trust data; see their sections.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
