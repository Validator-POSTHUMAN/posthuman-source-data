# Monad Mainnet recovery and state sync

## Recovery is a decision, not a generic reset

[Monad recovery documentation](https://docs.monad.xyz/node-ops/node-recovery/) distinguishes soft reset, hard reset, and fuller recovery paths. A soft reset is suitable only when local state is trustworthy and near the network tip. A hard reset/replay can remove local artifacts and is slower; it is not a default fix.

Monad state sync is not Cosmos SDK trust-height state sync. Do not use a Tendermint/CometBFT trust height, `priv_validator_state.json`, or Cosmos state-sync template for Monad.

## Read-only gate

Before a recovery proposal, collect the `143` (`0x8f`) identity from local and independent sources; component state/restarts/bounded errors/local-reference progress; storage/inode headroom and affected paths; backup/rollback evidence; and proof that the same validator identity cannot sign elsewhere.

Keep recovery type, artifact provenance, timing and post-recovery acceptance evidence in the incident record. An RPC response alone does not prove consensus participation or signing safety.
