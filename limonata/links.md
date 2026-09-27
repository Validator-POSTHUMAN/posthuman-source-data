# Limonata Testnet Links

## Network

- Website: https://limonata.xyz/
- Explorer: https://explorer.limonata.xyz/
- Faucet: https://faucet.limonata.xyz/
- Proving Grounds: https://grounds.limonata.xyz/
- Validator guide: https://limonata.xyz/VALIDATOR.md

## Source and releases

- GitHub: https://github.com/Limonata-Blockchain/limonata
- Releases: https://github.com/Limonata-Blockchain/limonata/releases
- v0.3.6: https://github.com/Limonata-Blockchain/limonata/releases/tag/limonata-v0.3.6
- Encrypted mempool: https://github.com/Limonata-Blockchain/limonata/blob/limonata-v0.3.6/ENCRYPTED_MEMPOOL.md

## POSTHUMAN public endpoints

- CometBFT RPC: https://rpc-limonata.posthuman.digital
- Cosmos REST: https://rest-limonata.posthuman.digital
- Cosmos gRPC: grpc-limonata.posthuman.digital:443
- Snapshots: https://snapshots-limonata.posthuman.digital
- Persistent peer:
  `aff8565175a96ad97ff22af9e6f90542fcf722a3@peer-limonata.posthuman.digital:45656`

RPC, REST, gRPC, and snapshot traffic is proxied through Cloudflare. The peer
record is DNS-only for raw TCP P2P. API clients are rate-limited to 300
requests per 10 seconds per source IP. Snapshot metadata and checksums are
published alongside the latest restore-tested archive, refreshed every four
hours.

## Official Limonata endpoints

- CometBFT RPC: https://cosmos-rpc.limonata.xyz
- Cosmos REST: https://rest.limonata.xyz
- EVM JSON-RPC: https://rpc.limonata.xyz

Network identifiers:

- Cosmos chain ID: `limonata_10777-1`
- EVM chain ID: `10777` (`0x2a19`)
- Base denomination: `aLIMO`

> **Restore-verified on 2026-09-27.** The published archive at height `4041596` was
> restored end to end on a throwaway node: it reached the chain tip, ran 1,693 blocks
> past the snapshot height with `catching_up=false`, and logged no app-hash
> divergence. That test exists because this pipeline used to prune the copy offline
> with `cosmprund`, which rewrote the application state and produced a Celestia
> archive that stalled a restored node with `APP HASH MISMATCH` at height
> `14443346`. Offline pruning is now off, so the archive is a copy of the node's own
> data — which is also why it grew from 9.7 GB to about 21 GB. That is the real size
> of a snapshot that restores.

Node parameters the archive inherits: `pruning = "default"`, `min-retain-blocks = 0`,
`indexer = "kv"` (so it includes the transaction index, about 5 GB of the total),
goleveldb. Snapshot metadata and checksums are published beside the archive and
refreshed every four hours; read `snapshot_time` from `snapshot.json` rather than
assuming freshness.
