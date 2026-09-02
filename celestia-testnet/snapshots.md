# Celestia Testnet Snapshot (Mocha-5)

**Network:** Mocha-5 (`mocha-5`)
**DB backend:** PebbleDB
**Provider:** ITRocket (external)

## Current source

- Index: https://server-6.itrocket.net/testnet/celestia/
- Metadata: https://server-6.itrocket.net/testnet/celestia/.current_state.json
- Live RPC: https://celestia-testnet-rpc.itrocket.net

> POSTHUMAN does not currently publish a Mocha-5 snapshot. The older
> `snapshots.posthuman.digital/celestia-testnet` bundle is for retired
> `mocha-4` and is incompatible with Mocha-5.

Before downloading, verify that the live RPC reports `mocha-5`, is not
catching up, and is ahead of the height in `.current_state.json`. Download the
exact `snapshot_name` listed in that metadata file, then validate the complete
archive with `lz4 -t` before stopping a node.

For validator recovery, preserve the local consensus key and the newest
`priv_validator_state.json`. Never restore signer state from a snapshot.
