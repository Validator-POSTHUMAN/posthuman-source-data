# Historical Celestia Mocha-4 Decentralization Map

The accompanying `decentralize-map.json` identifies **mocha-4**. It is retained
as historical data, not as Mocha-5 infrastructure or a current health source.
Do not relabel its records, combine them with Mocha-5, or run the legacy
collector/deploy wrapper as part of an app upgrade.

Current Mocha-5 target: **v10.2.0-mocha**, activation height **1082619**.
See the [node-ops index](links.md) and [app upgrade guide](multiplexer.md).

## Historical artifacts

- `decentralize-map.json`: archived Mocha-4 point inventory.
- [Map description](decentralize-map.md): public data and privacy boundaries.
- The repository's legacy map generator and deployment wrapper are not
  validated or recommended for Mocha-5. No current deployment procedure is
  published here.

## Requirements for a future Mocha-5 map

A separate reviewed refresh must verify the exact `mocha-5` chain identity
before collecting or publishing anything. Use only independently verified
public RPC endpoints, publicly advertised bootstrap peers and public peer
observations. Do not import private validator addresses, sentry topology,
local addrbooks or infrastructure deployment details.

The new dataset must carry its own chain ID, collection timestamp, source
provenance and health observations. Validate the schema, unique point IDs,
globally routable addresses and coordinates. Historical Mocha-4 points must
remain distinguishable and must never be represented as current Mocha-5 data.

Publication follows the owning website's reviewed source/build/release
workflow. Host-specific access, scheduling and deployment instructions belong
in private operations documentation, not this public guide.
