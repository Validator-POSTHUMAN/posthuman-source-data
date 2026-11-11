# Celestia Testnet Snapshot (Mocha-5)

**Network:** Mocha-5 (`mocha-5`)
**DB backend:** PebbleDB
**Provider:** ITRocket (external)

**Checked 2026-11-11 22:38 UTC:** ITRocket metadata names
`celestia_2026-11-11_2532763_snap.tar.lz4` at height `2532763`,
PebbleDB, size `982M`. The exact archive responded HTTP 200 with a
1,029,168,879-byte Content-Length and byte-range support. POSTHUMAN's
Mocha-5 RPC was synced at height `2534504`. This is a current external
candidate, **not** a verified restore: the full archive was not downloaded,
checksummed, inspected or restore-tested. Re-read metadata before each use;
the filename changes every publication cycle.

## Current source

- Index: https://server-6.itrocket.net/testnet/celestia/
- Metadata: https://server-6.itrocket.net/testnet/celestia/.current_state.json
- Live RPC: https://celestia-testnet-rpc.itrocket.net

> POSTHUMAN does not currently publish a Mocha-5 snapshot. The older
> `snapshots.posthuman.digital/celestia-testnet` bundle is for retired
> `mocha-4` and is incompatible with Mocha-5. The similarly named
> `snapshots-celestia-testnet.posthuman.digital` hostname did not resolve
> in this audit; do not use either legacy address as a Mocha-5 source.

Before downloading, verify that the live RPC reports `mocha-5`, is not
catching up, and is ahead of the height in `.current_state.json`. Download the
exact `snapshot_name` listed in that metadata file, then validate the complete
archive with `lz4 -t` before stopping a node.

For validator recovery, preserve the local consensus key and the newest
`priv_validator_state.json`. Never restore signer state from a snapshot.
