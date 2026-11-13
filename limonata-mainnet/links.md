# Mainnet endpoints and references

- [Official release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3): final genesis, configuration and binary.
- [Official repository](https://github.com/Limonata-Blockchain/limonata).
- [Project website](https://limonata.xyz).

These **third-party** providers are not POSTHUMAN services, signing services or uptime guarantees. Identity was checked on 2026-11-13; refresh identity, freshness, privacy and limits before operational use.

| Provider | Protocol | URL |
| --- | --- | --- |
| NodeSafe | CometBFT | https://rpc.nodesafe-app.xyz/limonata |
| NodeSafe | Cosmos REST | https://api.nodesafe-app.xyz/limonata |
| BonyNode | CometBFT | https://limonata-mainnet-rpc.bonynode.online |
| BonyNode | Cosmos REST | https://limonata-mainnet-api.bonynode.online |
| BonyNode | EVM JSON-RPC | https://limonata-mainnet-jsonrpc.bonynode.online |

Comet `/status` and REST `/cosmos/base/tendermint/v1beta1/node_info` must identify `limonata_20777-1`. EVM `eth_chainId` must be `0x5129`. EVM JSON-RPC is not a Comet block/state-sync endpoint. NodeSafe reported transaction indexing off; do not promise transaction search there. Providers may rate-limit and omit historical state.

Never send secrets to providers. Historical project RPC/faucet hostnames may serve the retired testnet; verify chain identity, not branding. No faucet, POSTHUMAN mainnet RPC/gRPC, peer or snapshot endpoint is asserted here.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
