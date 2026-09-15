# Monad Mainnet monitoring boundary

Monitor component state (`monad-bft`, `monad-execution`, `monad-rpc`), local/reference progress, restart count, bounded errors, storage/inodes, time synchronization and public endpoint identity. Measure validator participation/signing separately from process health; an active process or advancing height is not a signing-health verdict.

## Alert design

Compare local progress with an independently measured public reference, then alert only on state changes and send a recovery notice when evidence returns. Record comparison source, measured time, threshold, missing-data behavior and notification delivery. Treat a failed or stale external reference as unknown rather than calling the node unhealthy.

## Security

Keep bot tokens, webhooks, private endpoints and host identity outside the guide and repository. Alert delivery requires separately approved secret-managed configuration. This guide does not create a bot, timer, alert, metrics listener or firewall change.

For advanced telemetry, verify release compatibility, overhead, data retention and listener privacy before collectors. Do not treat ledger/event data as complete archival history without its own coverage contract.
