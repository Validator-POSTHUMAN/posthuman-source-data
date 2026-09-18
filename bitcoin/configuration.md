# bitcoin.conf Reference for Operators

Every option below exists in Bitcoin Core v31.1. Defaults given are the v31.1
defaults, which differ from older material in several places that matter.

`bitcoin.conf` lives in the data directory (`/var/lib/bitcoind/bitcoin.conf` if
you followed the installation guide). Mode `0600`, owned by the daemon user.
Changes take effect on restart; a handful can also be set at runtime through
`bitcoin-cli` but the config file is the source of truth.

## Section headers

Without a header, an option applies to **every** network. With one, only to
that network:

````ini
# applies everywhere
dbcache=4096

[main]
rpcport=8332

[test]
rpcport=18332

[signet]
rpcport=38332
````

This is the single most common configuration mistake: setting `rpcport=8332`
globally and then wondering why testnet refuses to start.

## Resources

| Option | Default | Notes |
|---|---|---|
| `dbcache=<MiB>` | 1024 on hosts with ≥4096 MiB RAM, else 450 | Biggest single IBD lever. **Set it explicitly in containers** — detected RAM can exceed the cgroup limit and the node gets OOM-killed. |
| `par=<n>` | number of cores | Script verification threads. `par=1` leaves the box responsive; `0` = auto. |
| `maxmempool=<MB>` | 300 | Raise on a node feeding a mempool dashboard or a miner; lower on a small VPS. |
| `maxconnections=<n>` | 125 | Each peer costs memory and file descriptors. |
| `blocksonly=1` | off | Stops relaying loose transactions. Big bandwidth saving; **breaks fee estimation and any mempool-dependent service**, and is wrong for a Lightning or explorer backend. |

The `-dbcache` default was raised from 450 MiB in v31.0. If you deliberately
want the old behaviour on a small host, `dbcache=450` still works.

## Storage and indexes

| Option | Default | Notes |
|---|---|---|
| `prune=<MiB>` | 0 (archive) | `550` is the minimum; `prune=550000` keeps ~550 GB. Mutually exclusive with `txindex`. |
| `txindex=1` | off | Full transaction index, ~50 GB. Required by Electrum servers, explorers, and any `getrawtransaction` on an arbitrary txid. |
| `blockfilterindex=1` | off | BIP157/158 compact filters. Needed for `scanblocks` and light-client serving. |
| `coinstatsindex=1` | off | `gettxoutsetinfo` without a full scan. Re-synced from scratch on upgrade from ≤29.x — the index moved to `indexes/coinstatsindex/`. |
| `txospenderindex=1` | off | New in v31.0. Lets `gettxspendingprevout` find a confirmed spender, not just a mempool one. |

Adding an index later is safe but triggers a rescan that takes hours. Switching
between `prune` and `txindex` requires `-reindex`, which is a full revalidation.

## Network and privacy

| Option | Default | Notes |
|---|---|---|
| `listen=1` | 1 | Accept inbound peers on 8333. |
| `natpmp=1` | **1 since v30.0** | Will ask the router to forward the port. Set `natpmp=0` if you manage exposure yourself. |
| `onlynet=onion` | — | Restricts *all* peer traffic to one network. `tor` as a value was removed in v31.0 — use `onion`. |
| `proxy=127.0.0.1:9050` | — | SOCKS5 for outbound. With `listen=1` and a Tor control port, Core creates its own hidden service. |
| `bind=` / `whitebind=` | — | `whitebind` peers bypass banning and relay limits. Use for your own infrastructure only. |
| `asmap` / `asmap=1` | off | Uses ASN-aware peer bucketing. **v31.0 embeds an asmap** (built 2026-03-05), so no external file is needed — but it stays off unless you set the flag. An external file now requires an explicit name: `asmap=ip_asn.map`. |
| `privatebroadcast=1` | off | New in v31.0: `sendrawtransaction` broadcasts only over Tor/I2P, one connection per transaction. **Requires v31.1** — v31.0 leaked the clear-net IP under some conditions. |

## RPC and IPC

| Option | Default | Notes |
|---|---|---|
| `server=1` | off for `bitcoin-qt`, on for `bitcoind` | |
| `rpcbind=127.0.0.1` | loopback | Binding anywhere else requires `rpcallowip` and a very good reason. |
| `rpcallowip=` | loopback only | CIDR allowlist. Never `0.0.0.0/0`. |
| `rpcauth=<user>:<salt>$<hash>` | — | Hashed credential, safe to commit to config. Generate with `share/rpcauth/rpcauth.py`. |
| `rpcwhitelist=<user>:<methods>` | — | **Per-user method allowlist.** The single most useful RPC hardening option and the most overlooked. |
| `rpcthreads` / `rpcworkqueue` | 4 / 16 | Raise for an Electrum server or explorer backend that fans out requests. |
| `rest=1` | off | Read-only HTTP REST on the RPC port. Convenient for indexers; still must not face the internet. |

Example of a least-privilege service account:

````ini
rpcauth=electrs:<salt>$<hash>
rpcwhitelist=electrs:getblockchaininfo,getblockhash,getblockheader,getblock,getrawtransaction,getmempoolinfo,getrawmempool,estimatesmartfee,getnetworkinfo
````

That account cannot touch a wallet, cannot stop the node and cannot change
peers, regardless of what the service is later compromised into trying.

## ZMQ

Required by Lightning daemons, Electrum servers and most indexers:

````ini
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
zmqpubhashblock=tcp://127.0.0.1:28334
````

ZMQ has **no authentication**. Bind it to loopback, or to a private interface
protected by the firewall, and never to a public address.

## Wallet

| Option | Default | Notes |
|---|---|---|
| `disablewallet=1` | off | Correct for a pure infrastructure node. Nothing to steal, one less attack surface. |
| `wallet=<name>` | — | Load a named wallet at startup. |

`-paytxfee` and the `settxfee` RPC were **removed in v31.0** after deprecation
in 30.0. Use fee estimation, or pass `fee_rate` per transaction to `send`,
`sendtoaddress`, `sendall`, `sendmany` and `fundrawtransaction`.

## Policy and fees

Defaults changed in v30.0 and old guides are wrong about them:

| Option | v31.1 default | Was |
|---|---|---|
| `minrelaytxfee` | 0.1 sat/vB | 1 sat/vB |
| `incrementalrelayfee` | 0.1 sat/vB | 1 sat/vB |
| `blockmintxfee` | 0.001 sat/vB | 1 sat/vB |
| `datacarriersize` | 100000 | 83 |
| `maxorphantx` | **removed** | 100 |

Change `minrelaytxfee` and `incrementalrelayfee` together or not at all. Set
`datacarriersize=83` to restore the pre-30.0 OP_RETURN limit if that is your
policy — but note that a relay policy only your node enforces changes nothing
about what gets mined.

`maxorphantx` was removed outright. Leaving it in the config is harmless today
and **will be a startup error in a future release** — delete it now.

## Cluster mempool, v31.0 onwards

The mempool was reimplemented. Ancestor and descendant count/size limits no
longer exist; instead a *cluster* — any set of mempool transactions connected
by parent/child links — is limited to 64 transactions and 101 kvB. RBF is now
accepted only when the resulting mempool feerate diagram is strictly better.
The CPFP carve-out is gone; use TRUC transactions and sibling eviction instead.

Two new RPCs come with it: `getmempoolcluster` and `getmempoolfeeratediagram`.
`getmempoolentry` now also reports chunk size and chunk fees.

If you run software that parses `getmempoolancestors`/`getmempooldescendants`
limits or relies on the carve-out, test it against v31 before upgrading.

## Logging

````ini
debug=net
debug=mempool
logips=1
shrinkdebugfile=1
````

Unconditional logging (`info` and above) is rate-limited to 1 MiB per hour per
source location since v30.0. A `[*]` prefix in the log means at least one
source location is currently suppressed — the node is not idle, it is quiet on
purpose.

## Applying and checking changes

````bash
sudo systemctl restart bitcoind
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getrpcinfo
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind logging          # active categories
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getmempoolinfo   # policy values in effect
````

`getmempoolinfo` now returns `permitbaremultisig` and `maxdatacarriersize`, and
`getmininginfo` returns `blockmintxfee` — read the effective value back from the
node rather than trusting the file.

## Sources

- [bitcoincore.org — v31.0 release notes](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes](https://bitcoincore.org/en/releases/30.0/)
- [bitcoin/bitcoin — `doc/policy/mempool-terminology.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/policy/mempool-terminology.md)
- [bitcoin/bitcoin — `doc/policy/mempool-replacements.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/policy/mempool-replacements.md)
- [bitcoin/bitcoin — `doc/reduce-memory.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/reduce-memory.md)
- [delvingbitcoin.org — cluster mempool proposal](https://delvingbitcoin.org/t/an-overview-of-the-cluster-mempool-proposal/393)
