# Snapshot recovery boundary

No checksum-verified mainnet snapshot artifact has been reviewed for this guide; there is no runnable restore command. Use block sync from the final genesis, or independently review a current `limonata_20777-1` artifact before planning recovery. Never relabel a testnet snapshot or endpoint.

A usable artifact requires publisher provenance, immutable digest, chain ID, height/time, database/binary compatibility, free capacity and a verified restore layout. Check its height and block identity against independent mainnet sources. Download availability is not restore readiness.

Before validator recovery, prove unique signer control and preserve consensus/P2P identity, latest signing state and DKG ECIES key. Retain a verified rollback/forensic copy. Never delete the home, use `unsafe-reset-all`, copy a live key to another runnable node or restore older signing state. Database rollback never authorizes signer-state rollback.

After a reviewed restore, verify the correct chain, advancing sync, same-height block hashes, bonded/not-jailed state, fresh external signatures and DKG readiness. If provenance, signer uniqueness or backups are unproven, retain the data and escalate instead of improvising destructive commands.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
