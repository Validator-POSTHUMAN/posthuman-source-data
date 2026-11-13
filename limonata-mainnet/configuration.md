# Configuration, bootstrap files and peers

The checksum-verified final startup package in [Installation](installation-guide.md) supplies genesis, config.toml and app.toml. Final genesis SHA-256: `944ad7370836c7a6f185002f6d599abe29f6cf7ce6ad30c83800537dc8d03460`. The precollection package is historical, not a bootstrap source.

Review TOML sections rather than global search/replace:

| File / section | Setting or action |
| --- | --- |
| config / root | Set your moniker; preserve existing validator key/state paths |
| config / rpc | `laddr = "tcp://127.0.0.1:26657"`; keep CORS restricted |
| config / p2p | Default `laddr = "tcp://0.0.0.0:26656"`; validators retain the P2P port announced in their gentx |
| config / p2p | Review `persistent_peers` from the final package; remove your own node ID, verify reachability and preserve each ID/address pair |
| config / statesync | Leave `enable = false` until a current mainnet trust source is separately reviewed |
| app / evm | `evm-chain-id = 20777`, never the testnet/default ID |
| app / root | `minimum-gas-prices = "0aLIMO"` is the published local setting, not a zero-fee promise |
| app / api | REST binds `tcp://localhost:1317` |
| app / grpc | `127.0.0.1:9090`; gRPC-Web shares the API server |
| app / json-rpc | Disabled by default; if deliberately enabled, HTTP `127.0.0.1:8545`, WS `127.0.0.1:8546` |

Keep pprof, Prometheus and EVM metrics private too. A signing validator must not expose management APIs publicly. A public full node requires a separately hardened access/rate-limit/monitoring design.

The genesis chain-wide fee floor is enforced by x/feemarket: 1,000,000,000 aLIMO/gas (1 gwei) at genesis. Query current parameters and simulate before transactions; a local zero minimum does not waive chain fees.

No POSTHUMAN mainnet seed, addrbook, peer or bootstrap service is asserted. Use the final package's public peer list with current official confirmation, not retired testnet services. Do not replace a working list blindly. Existing nodes must preserve keys, genesis, DKG identity and monotonic state; back up public configuration before changes.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
