# Celestia Testnet Snapshot (Mocha-5)

**Network:** Mocha-5 (`mocha-5`)
**DB backend:** PebbleDB
**Provider:** ITRocket (external)

**Checked 2026-10-28 22:42 UTC:** metadata names
`celestia_2026-10-28_2107634_snap.tar.lz4` at height `2107634` and size
`851M`; the exact archive responds HTTP 200 with a 892,312,272-byte
Content-Length. POSTHUMAN's Mocha-5 RPC was synced above height `2112100`.
The archive was **not** downloaded, checksummed, inspected or restore-tested
in this audit. Re-read metadata before each use; the filename changes every
publication cycle. This is not a POSTHUMAN-operated snapshot.

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
