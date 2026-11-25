# Historical Celestia Mocha-4 Decentralization Map

The accompanying `decentralize-map.json` identifies **mocha-4**. It is retained
as historical data, not as Mocha-5 infrastructure or a current health source.
Do not relabel its records, combine them with Mocha-5, or run the legacy
collector/deploy wrapper as part of an app upgrade.

Current Mocha-5 app: **v11.0.0-mocha**; app v11 activated at **2760281**; app v10 height **1082619** is historical.
See the [node-ops index](https://github.com/Validator-POSTHUMAN/posthuman-source-data/blob/main/celestia-testnet/links.md) and [app upgrade guide](/chains/celestia-testnet?tab=multiplexer).

## Historical artifacts

- `decentralize-map.json`: archived Mocha-4 point inventory.
- [Map description](https://github.com/Validator-POSTHUMAN/posthuman-source-data/blob/main/celestia-testnet/decentralize-map.md): public data and privacy boundaries.
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
