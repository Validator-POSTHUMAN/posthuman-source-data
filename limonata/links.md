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

> **Restore-verified: not yet.** The pipeline that produced this archive used to
> prune the copy offline with `cosmprund`; that rewrote the application state and
> made the Celestia archive unrestorable (`APP HASH MISMATCH` at height
> `14443346`, 2026-09-27). The offline prune is now **off** for this publisher, so
> new archives are copies of the node's own pruned data — the same change that made
> the Celestia archive restore cleanly in an end-to-end test. This archive has not
> had that test yet. Until it does, keep a rollback of your old database and verify
> the height against a live RPC. Detail: POSTHUMAN decision record
> `2026-09-27-our-own-snapshot-could-not-restore.md`.
