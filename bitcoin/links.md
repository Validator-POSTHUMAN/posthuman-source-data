# Bitcoin Endpoints, Explorers and References

## Network identity

Check these against your own node after every version change — they are what
prove which network you joined.

| | Mainnet | Testnet4 | Signet | Regtest |
|---|---|---|---|---|
| Chain name | `main` | `testnet4` | `signet` | `regtest` |
| P2P port | 8333 | 48333 | 38333 | 18444 |
| RPC port | 8332 | 48332 | 38332 | 18443 |
| Chain size | ~856 GB | ~31 GB | small | none |

Genesis block hash, mainnet:

````
000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
````

Testnet3 (`-testnet`, ports 18333/18332, ~245 GB) still exists and is
deprecated in practice — see **Testnets**.

## Software

| | |
|---|---|
| Bitcoin Core downloads | <https://bitcoincore.org/en/download/> |
| Release notes | <https://bitcoincore.org/en/releases/> |
| Security announcements list | <https://bitcoincore.org/en/list/announcements/join/> |
| Source | <https://github.com/bitcoin/bitcoin> |
| Builder signatures | <https://github.com/bitcoin-core/guix.sigs> |
| LND | <https://github.com/lightningnetwork/lnd> |
| Core Lightning | <https://github.com/ElementsProject/lightning> |

Current versions, verified 2026-09-18: Bitcoin Core **v31.1**, LND
**v0.21.3-beta**, Core Lightning **v26.06.7**.

## Public RPC and APIs

| Endpoint | Type |
|---|---|
| <https://bitcoin-rpc.publicnode.com> | JSON-RPC, public, read-only |
| <https://mempool.space/api> | Esplora-compatible REST plus `/api/v1/…` |
| <https://blockstream.info/api> | Esplora REST |

Public endpoints are for cross-checking and light integration. Anything that
credits money or makes a consensus decision runs against your own node.

## Explorers

| | |
|---|---|
| POSTHUMAN Hub | <https://hub-preview.posthuman.digital/explorer/bitcoin> |
| mempool.space | <https://mempool.space> |
| Blockstream.info | <https://blockstream.info> |
| Blockchair | <https://blockchair.com/bitcoin> |
| 3xpl | <https://3xpl.com/bitcoin> |

## Documentation

| | |
|---|---|
| RPC reference | <https://developer.bitcoin.org/reference/rpc/> |
| Developer documentation | <https://developer.bitcoin.org/> |
| Bitcoin Core `doc/` | <https://github.com/bitcoin/bitcoin/tree/master/doc> |
| BIPs | <https://github.com/bitcoin/bips> |
| Optech newsletter | <https://bitcoinops.org/en/newsletters/> |
| Stack Exchange | <https://bitcoin.stackexchange.com> |

Core's own `doc/` directory is under-read and is the authority on
`assumeutxo.md`, `tor.md`, `i2p.md`, `reduce-memory.md`,
`managing-wallets.md` and the mempool policy documents.

## Learning

| | |
|---|---|
| Mastering Bitcoin | <https://github.com/bitcoinbook/bitcoinbook> |
| Bitcoin protocol curriculum | <https://github.com/chaincodelabs/bitcoin-curriculum> |
| Lightning curriculum | <https://github.com/chaincodelabs/lightning-curriculum> |
| Programming with BitcoinJS and Core CLI | <https://github.com/bitcoin-studio/Bitcoin-Programming-with-BitcoinJS> |
| Awesome Bitcoin | <https://github.com/igorbarinov/awesome-bitcoin> |

## Mining

| | |
|---|---|
| Ocean | <https://ocean.xyz> |
| Braiins Pool and academy | <https://braiins.com/pool> · <https://academy.braiins.com> |
| Solo CKPool | <https://solo.ckpool.org> |
| public-pool | <https://github.com/benjamin-wilson/public-pool> |
| Bitaxe | <https://bitaxe.org> |
| Stratum v2 | <https://stratumprotocol.org> |

## POSTHUMAN

| | |
|---|---|
| Website | <https://posthuman.digital> |
| Node guides | <https://nodes.posthuman.digital> |
| Network Hub | <https://hub-preview.posthuman.digital> |

## Sources

- [bitcoincore.org](https://bitcoincore.org/)
- [bitcoin/bitcoin — `src/kernel/chainparams.cpp` at v31.1](https://github.com/bitcoin/bitcoin/blob/v31.1/src/kernel/chainparams.cpp)
- [developer.bitcoin.org](https://developer.bitcoin.org/)
