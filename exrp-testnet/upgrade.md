# XRPL EVM Testnet upgrades

Testnet requires `exrpd v10.1.0` after upgrade height `7,725,000`.

## v10.1.0

- Release: <https://github.com/xrplevm/node/releases/tag/v10.1.0>
- Linux amd64 archive:
  `node_10.1.0_Linux_amd64.tar.gz`
- Published SHA-256:
  `92cf140a3af8dcb48afd0fb9b923ab96a1a242b75efda9d4796c5cda05d00a76`

For Cosmovisor, use the on-chain plan name from
`data/upgrade-info.json`; do not infer it from the release tag.

## Validator-safe sequence

1. Download and verify the artifact before stopping.
2. Confirm that only one active signer has the validator key.
3. Preserve `priv_validator_state.json`.
4. Stop at the official height, install the binary in the plan directory, and
   start once.
5. Verify `v10.1.0`, current network height, fresh block time, peers, and
   signing against an independent RPC.

The planned v11 rehearsal is not ready to execute until the project publishes
the release artifact and authoritative Testnet activation details.
