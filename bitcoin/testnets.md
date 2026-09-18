# Testnet, Signet and Regtest

Four chains ship in v31.1. Picking the wrong one wastes days.

| Chain | Flag | P2P | RPC | Size | Use it for |
|---|---|---|---|---|---|
| testnet3 | `-testnet` | 18333 | 18332 | ~245 GB | legacy compatibility only — **do not start here** |
| **testnet4** | `-testnet4` | 48333 | 48332 | ~31 GB | public testing with real proof of work and BIP94 difficulty rules |
| **signet** | `-signet` | 38333 | 38332 | small | integration testing with predictable, reliable blocks |
| **regtest** | `-regtest` | 18444 | 18443 | none | CI and local development — you mine blocks on demand |

Sizes are Core's own v31.1 assumptions.

## Which one

- **regtest** for anything automated. Instant, deterministic, disposable, and
  you control block production.
- **signet** for realistic integration testing. Blocks are produced by a signer
  on a predictable schedule, testnet coins have no market so nobody spams it,
  and the chain stays small.
- **testnet4** when you need real proof of work — mining software, difficulty
  logic, reorg behaviour. It replaced testnet3, which suffered from difficulty
  resets, block-storm miners and a multi-gigabyte chain full of junk.
- **testnet3** only when a counterparty forces you to.

testnet4 enforces **BIP94** ("testnet timewarp fix"): the 20-minute
minimum-difficulty rule no longer lets a miner reset difficulty at will, which
is what made testnet3 unusable. `enforce_BIP94` is `true` on testnet4 and
`false` on mainnet and testnet3.

## Running one alongside mainnet

Section headers are mandatory — an option outside a section applies to every
chain:

````ini
# ~/.bitcoin/bitcoin.conf
server=1

[main]
rpcport=8332
txindex=1

[signet]
rpcport=38332
prune=550

[regtest]
rpcport=18443
fallbackfee=0.0002
````

````bash
bitcoind -signet -daemon
bitcoin-cli -signet getblockchaininfo | jq '{chain, blocks}'
````

Each chain gets its own subdirectory under the datadir (`signet/`, `testnet4/`,
`regtest/`) and its own wallets. Setting `rpcport` globally and wondering why
two chains fight over one port is the classic mistake.

## Regtest in practice

````bash
bitcoind -regtest -daemon -fallbackfee=0.0002
bitcoin-cli -regtest createwallet "test"
ADDR=$(bitcoin-cli -regtest getnewaddress)

bitcoin-cli -regtest generatetoaddress 101 "$ADDR"     # 101 blocks: coinbase matures after 100
bitcoin-cli -regtest getbalance
bitcoin-cli -regtest sendtoaddress "$ADDR" 1.0
bitcoin-cli -regtest generatetoaddress 1 "$ADDR"       # confirm it

bitcoin-cli -regtest invalidateblock <hash>            # force a reorg
bitcoin-cli -regtest reconsiderblock <hash>
````

`fallbackfee` is required on regtest: there is no fee history to estimate from,
and the wallet refuses to build transactions without it.

Regtest is where you test the things you cannot rehearse on mainnet: reorgs,
double spends, RBF, package relay, force closes, and every failure path in your
own software.

## Signet

Default signet is shared and public. Faucets and explorers exist:

````bash
bitcoind -signet -daemon
bitcoin-cli -signet getblockchaininfo | jq '{chain, blocks, headers}'
bitcoin-cli -signet getnewaddress
````

For a private test network, a **custom signet** gives you a chain only you can
produce blocks on, with none of regtest's isolation:

````ini
[signet]
signetchallenge=512103...51ae
signetseednode=<your-seed>:38333
````

The signer runs `contrib/signet/miner` from the Core repository. This is the
right shape for a shared team environment or a long-running integration chain.

## Testnet4

````bash
bitcoind -testnet4 -daemon
bitcoin-cli -testnet4 getblockchaininfo | jq '{chain, blocks, headers, size_on_disk}'
````

~31 GB and real proof of work. Coins have no value and faucets are chronically
empty — ask another operator rather than hunting for a working faucet.

## Testing a stack end to end

[Nigiri](https://github.com/vulpemventures/nigiri) brings up a regtest box with
Electrs and Esplora, plus faucet and push commands, in one step:

````bash
nigiri start
nigiri faucet <address>
nigiri push <hex>
nigiri stop --delete
````

That gives you node + indexer + explorer API locally, which is exactly the
surface most applications integrate against. For Lightning, run LND or CLN
against the same regtest node and open channels between two local instances —
the only safe way to rehearse force closes and SCB recovery.

## What to rehearse before touching mainnet

| Rehearse | On |
|---|---|
| Upgrade and rollback, including index migrations | signet or testnet4 |
| Reorg handling in your own software | regtest (`invalidateblock`) |
| RBF, package relay, cluster-mempool limits | regtest |
| Wallet backup and restore, descriptor import, rescan | signet |
| Lightning force close, SCB recovery, watchtower justice | regtest |
| Mining pipeline: template → stratum → share → block | regtest or signet |

Everything in the **Upgrades** guide about v31.0's cluster mempool and removed
options is best verified here first, on a chain where being wrong costs
nothing.

## Sources

- [bitcoin/bitcoin — `src/kernel/chainparams.cpp` at v31.1](https://github.com/bitcoin/bitcoin/blob/v31.1/src/kernel/chainparams.cpp)
- [BIP94 — testnet timewarp fix](https://github.com/bitcoin/bips/blob/master/bip-0094.mediawiki)
- [bitcoin/bitcoin — `contrib/signet`](https://github.com/bitcoin/bitcoin/tree/master/contrib/signet)
- [vulpemventures/nigiri](https://github.com/vulpemventures/nigiri)
- [en.bitcoin.it — Testnet](https://en.bitcoin.it/wiki/Testnet)
