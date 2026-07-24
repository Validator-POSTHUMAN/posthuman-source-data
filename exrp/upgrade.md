# XRPL EVM Mainnet upgrades

Mainnet currently uses `exrpd v10.0.2`. Confirm the target release, upgrade
height, checksum, and on-chain plan from the official project before changing
the binary. Do not apply a Testnet schedule to Mainnet.

## Validator-safe sequence

1. Verify the release at <https://github.com/xrplevm/node/releases>.
2. Record the current height and signer state.
3. Download and checksum the target artifact while the node is online.
4. Confirm that no second process or host can sign with the same validator
   key.
5. Stop the service at the official upgrade gate.
6. Install the binary in the exact Cosmovisor plan directory, or replace the
   standalone binary while retaining the old binary for rollback.
7. Start once and verify version, chain ID, advancing height, peers, and
   signing.

Never replace `priv_validator_state.json` with a snapshot copy. The planned
v11 upgrade is not ready to execute until the project publishes the release
artifact and authoritative Mainnet activation details.
