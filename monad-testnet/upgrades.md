# Monad Testnet upgrades and protocol changes

Official [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions) reviewed on 2026-09-15 list a `v0.16.2` coordinated raptorcast rollout and a separate MIP-8/page-storage migration. Treat these as distinct changes; do not infer that every upgrade requires reset or that a historical example applies now.

Monad does not use the Cosmos Cosmovisor/on-chain-height template. Do not publish Cosmovisor commands, Cosmos governance votes, or automatic service changes for this network.

## Controlled review sequence

1. identify official release, activation condition and exact network;
2. inspect compatibility, storage/recovery impact and advisories;
3. preserve a rollback point and prove one signer before validator cutover;
4. stage only after operator approval; and
5. verify chain identity, advancing state, component health and monitoring after the approved change.

This is a review record, not an activation runbook. The Hub does not install, restart, reset, sign or broadcast.
