# Monad Testnet archive and indexing boundary

Monad's [data waterfall](https://docs.monad.xyz/node-ops/archive-data/data-waterfall) separates cache, MonadDB, Archive Server and object storage. Transactional artifacts and historical state are different products. MonadDB can overwrite older data near its retention threshold; a synced node must not be described as a full-history service by default.

## Read-only design questions

Define the query first: block/header, transaction, receipt, log, trace, state, or derived analytics. Then record oldest proven coverage, owner, retention, finality/reorg handling, request limits, privacy classification and failure behavior.

No Archive Server, database, indexer, trace mode, listener, credential, container, storage or retention change is configured here. A later surface needs a reviewed data source and coverage contract; absent data is unknown, not a Cosmos-style pruned/jailed status.
