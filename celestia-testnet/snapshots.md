# Celestia Testnet Snapshot (Mocha-5)

**Network:** Mocha-5 (`mocha-5`)
**DB backend:** PebbleDB
**Provider:** ITRocket (external)

**Checked 2026-11-25:** external ITRocket metadata reports height `2953831`;
Mocha-5 runs protocol app `11` / binary `11.0.0-mocha`. This is publication
and chain-context evidence, not a checksum, archive-layout or restore test.
Re-read metadata before every use: the exact filename changes each cycle.
The October example in older revisions is historical, not the current target.
This is not a POSTHUMAN-operated snapshot.

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
