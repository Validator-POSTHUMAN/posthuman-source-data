# RPC, Indexes and Public APIs

Bitcoin Core's own RPC is a **local administration interface**, not a public
API. It has no rate limiting, no per-method quotas beyond `rpcwhitelist`, no
read replica and no pagination. Everything you would want to expose to users —
address history, UTXO lookups, mempool visualisation, fee estimates — comes
from an indexer that sits in front of it.

This guide covers the four layers we actually run and recommend.

## 1. Core RPC, locked down

````ini
server=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcthreads=16
rpcworkqueue=64
rest=1

rpcauth=electrs:<salt>$<hash>
rpcwhitelist=electrs:getblockchaininfo,getblockhash,getblockheader,getblock,getrawtransaction,getmempoolinfo,getrawmempool,getmempoolentry,estimatesmartfee,getnetworkinfo,getbestblockhash
````

Rules that do not bend:

- **`8332` never faces the internet.** Not behind a password, not behind a
  "temporary" firewall exception. RPC exposure has drained wallets.
- Every consumer gets its own `rpcauth` identity and its own `rpcwhitelist`.
  A compromised indexer must not be able to call `stop`, `addnode` or anything
  wallet-related.
- `disablewallet=1` on any node that does not need a wallet.
- Raise `rpcthreads`/`rpcworkqueue` before an indexer starts: the default 4/16
  will produce `Work queue depth exceeded` under an Electrum server's fan-out.

Reaching RPC from another host is done with an SSH tunnel or a WireGuard link,
never by binding wider:

````bash
ssh -N -L 8332:127.0.0.1:8332 operator@node
````

### ZMQ

Indexers and Lightning daemons need push notifications, not polling:

````ini
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
zmqpubhashblock=tcp://127.0.0.1:28334
````

ZMQ is unauthenticated. Loopback or a firewalled private interface only.

## 2. Electrum server — address history

Wallets (Electrum, Sparrow, BlueWallet, Specter) speak the Electrum protocol,
not Bitcoin RPC. Two maintained implementations:

| | [romanz/electrs](https://github.com/romanz/electrs) | [cculianu/Fulcrum](https://github.com/cculianu/Fulcrum) (v2.1.2) |
|---|---|---|
| Language | Rust | C++ |
| Index size | ~120 GB | ~90 GB |
| Initial index | 1–4 h on NVMe | 4–12 h |
| Reads blocks | directly from `blocks/` | over RPC |
| Needs `txindex` | no | no |
| Strength | lean, simple, reads block files directly | faster queries, better for many concurrent clients |

Both require an **archive** node. Neither works against a pruned one.

`electrs` minimal config:

````toml
# ~/.electrs/config.toml
network = "bitcoin"
daemon_dir = "/var/lib/bitcoind"
daemon_rpc_addr = "127.0.0.1:8332"
daemon_p2p_addr = "127.0.0.1:8333"
db_dir = "/srv/electrs/db"
electrum_rpc_addr = "127.0.0.1:50001"
````

Expose it to wallets over TLS via a reverse proxy, or over Tor as a hidden
service — the Electrum protocol has no transport security of its own.

## 3. Esplora and mempool.space — the explorer layer

| | [Blockstream/esplora](https://github.com/Blockstream/esplora) | [mempool/mempool](https://github.com/mempool/mempool) (v3.3.1) |
|---|---|---|
| Backend | `electrs` (Blockstream fork) | Core RPC + Electrum server + MariaDB |
| REST API | `/api/…`, the de-facto standard | `/api/…` Esplora-compatible plus `/api/v1/…` |
| Strength | clean address/UTXO API, Liquid and testnet support | mempool visualisation, fee histogram, mining pools, Lightning |
| Public instances | `blockstream.info` | `mempool.space` |

The two REST surfaces overlap deliberately: anything written against
`blockstream.info/api` mostly works against `mempool.space/api` and against a
self-hosted instance of either. That is what makes them a safe dependency —
you can start on the public endpoint and move to your own host without
rewriting the client.

Endpoints worth knowing:

````bash
curl -s https://mempool.space/api/blocks/tip/height
curl -s https://mempool.space/api/blocks/tip/hash
curl -s https://mempool.space/api/block/<hash>
curl -s https://mempool.space/api/tx/<txid>
curl -s https://mempool.space/api/address/<address>
curl -s https://mempool.space/api/address/<address>/utxo
curl -s https://mempool.space/api/v1/fees/recommended
curl -s https://mempool.space/api/v1/difficulty-adjustment
curl -s https://mempool.space/api/v1/mining/hashrate/3d
curl -s https://mempool.space/api/v1/lightning/statistics/latest
````

Self-hosting `mempool` needs Core with `txindex=1`, an Electrum server, MariaDB
and roughly 200 GB beyond the node itself. Its `docker/` directory is the
reference deployment.

## 4. Choosing indexes on the node

| Index | Turn it on when |
|---|---|
| `txindex=1` | anything needs `getrawtransaction` for an arbitrary txid: Electrum servers, explorers, mempool, most wallet backends |
| `blockfilterindex=1` | serving BIP157/158 light clients, or using `scanblocks` instead of a full rescan |
| `coinstatsindex=1` | you query `gettxoutsetinfo` regularly — supply audits, UTXO-set dashboards |
| `txospenderindex=1` | you ask "what spent this output?" for confirmed spends (new in v31.0, used by `gettxspendingprevout`) |

Each is built by a background rescan taking hours. `coinstatsindex` is
re-synced from scratch when upgrading from v29.x or older, because the index
moved to `indexes/coinstatsindex/`; the old `indexes/coinstats/` directory is
left in place for downgrades and is safe to delete once you have committed to
the new version.

## 5. If you must publish an endpoint

Public read-only Bitcoin RPC is a service, not a firewall rule. The pattern we
use for other networks applies unchanged:

1. a reverse proxy in front — never the daemon directly;
2. a **method allowlist** enforced by the proxy, not only by `rpcwhitelist`;
3. per-IP and global rate limits;
4. no wallet on the node, `disablewallet=1`;
5. a separate node from anything that holds keys or backs Lightning;
6. metrics on request rate, error rate and upstream latency.

For most consumers, publishing an **Esplora-compatible REST API** from your own
`mempool`/`esplora` instance is a better product than raw RPC: it is designed
for untrusted callers, it is cacheable, and clients already exist for it.

## Verification

````bash
# from the node itself
bitcoin-cli getrpcinfo | jq '.active_commands'
curl -s http://127.0.0.1:8332/rest/chaininfo.json | jq '.blocks'

# from anywhere else — both must fail
nc -vz <public-ip> 8332
nc -vz <public-ip> 28332
````

A node whose RPC port answers from the internet is an incident, not a
configuration preference. Check it after every firewall or Docker change —
published container ports bypass `ufw` on most hosts.

## Sources

- [bitcoincore.org — v31.0 release notes, `-txospenderindex`](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes, coinstatsindex migration](https://bitcoincore.org/en/releases/30.0/)
- [romanz/electrs](https://github.com/romanz/electrs)
- [cculianu/Fulcrum](https://github.com/cculianu/Fulcrum)
- [Blockstream/esplora](https://github.com/Blockstream/esplora)
- [mempool/mempool — REST API](https://mempool.space/docs/api/rest)
