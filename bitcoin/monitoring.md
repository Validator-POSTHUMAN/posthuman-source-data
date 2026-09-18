# Bitcoin Node Monitoring

Bitcoin Core exposes **no Prometheus endpoint**. Everything below is built from
RPC, and the exporter ecosystem is thin — the most-used third-party exporter,
[jvstein/bitcoin-prometheus-exporter](https://github.com/jvstein/bitcoin-prometheus-exporter),
is a small script with a modest maintenance cadence. That is fine, because the
metrics that matter are a handful of RPC fields and a textfile collector covers
them in twenty lines you can read end to end.

Three layers, and you need all three:

1. **Chain health** — synced, on the *right* chain, keeping pace.
2. **Peer and service health** — reachable, relaying, serving what depends on it.
3. **Host capacity** — disk above all, then RAM, CPU and clock.

## 1. The three RPCs that carry the signal

````bash
bitcoin-cli getblockchaininfo | jq '{chain, blocks, headers, verificationprogress, initialblockdownload, size_on_disk, pruned}'
bitcoin-cli getnetworkinfo    | jq '{version, subversion, connections, connections_in, connections_out, networkactive, warnings}'
bitcoin-cli getmempoolinfo    | jq '{size, bytes, usage, maxmempool, mempoolminfee}'
````

| Field | Healthy | What it means when it is not |
|---|---|---|
| `blocks` vs `headers` | equal | headers ahead = downloading; both frozen = stalled, check peers |
| `verificationprogress` | ~1.0 | still in IBD |
| `initialblockdownload` | `false` | node is not yet trustworthy for services |
| `connections_out` | ≥ 8 | outbound peering broken — DNS, firewall or `onlynet` |
| `connections_in` | > 0 if you meant to serve | 8333 unreachable; harmless for a private backend |
| `networkactive` | `true` | someone ran `setnetworkactive false` and forgot |
| `warnings` | empty | **alert on any content** — unknown block versions, consensus warnings |
| `mempoolminfee` | 0.00001 | rising means the mempool is full and evicting |

### The check that actually catches disasters

Block height agreement is not chain agreement. Compare the **tip hash** against
independent sources:

````bash
LOCAL=$(bitcoin-cli getbestblockhash)
A=$(curl -s https://blockstream.info/api/blocks/tip/hash)
B=$(curl -s https://mempool.space/api/blocks/tip/hash)
[ "$LOCAL" = "$A" ] && [ "$LOCAL" = "$B" ] || echo "CHAIN DIVERGENCE: local=$LOCAL a=$A b=$B"
````

A node at the same height on a different chain is the failure that silently
corrupts everything downstream — payment credits, explorer data, Lightning
channel decisions. Height lag is an inconvenience; a hash mismatch is an
incident. Allow one block of skew for timing, alert on anything persistent.

## 2. Textfile collector

Requires `node_exporter` with `--collector.textfile.directory=/var/lib/node_exporter/textfile`.

````bash
#!/usr/bin/env bash
# /usr/local/bin/bitcoind-metrics.sh — run every 60s from a systemd timer
set -euo pipefail
OUT=/var/lib/node_exporter/textfile/bitcoind.prom
CLI="bitcoin-cli -datadir=/var/lib/bitcoind"

chain=$($CLI getblockchaininfo)
net=$($CLI getnetworkinfo)
mem=$($CLI getmempoolinfo)

{
  echo "# HELP bitcoind_blocks Current block height"
  echo "# TYPE bitcoind_blocks gauge"
  echo "bitcoind_blocks $(jq -r .blocks <<<"$chain")"
  echo "bitcoind_headers $(jq -r .headers <<<"$chain")"
  echo "bitcoind_verification_progress $(jq -r .verificationprogress <<<"$chain")"
  echo "bitcoind_ibd $(jq -r 'if .initialblockdownload then 1 else 0 end' <<<"$chain")"
  echo "bitcoind_size_on_disk $(jq -r .size_on_disk <<<"$chain")"
  echo "bitcoind_connections_in $(jq -r .connections_in <<<"$net")"
  echo "bitcoind_connections_out $(jq -r .connections_out <<<"$net")"
  echo "bitcoind_warnings $(jq -r 'if (.warnings | length) > 0 then 1 else 0 end' <<<"$net")"
  echo "bitcoind_mempool_txs $(jq -r .size <<<"$mem")"
  echo "bitcoind_mempool_bytes $(jq -r .bytes <<<"$mem")"
  echo "bitcoind_mempool_min_fee $(jq -r .mempoolminfee <<<"$mem")"
} > "${OUT}.tmp"
mv "${OUT}.tmp" "$OUT"
````

Write to a temporary file and rename — `node_exporter` will read a half-written
file otherwise and produce parse errors instead of metrics.

Add the external tip comparison as a second metric
(`bitcoind_tip_matches_external 0|1`) from the same script, with a timeout so a
slow third-party API cannot block the collector.

## 3. Alerts worth having

| Alert | Condition | Why |
|---|---|---|
| Node behind | `headers - blocks > 3` for 15 min | stalled sync |
| Chain divergence | tip hash ≠ two independent sources for 10 min | consensus problem, the one that matters |
| No progress | `blocks` unchanged for 90 min | plausible naturally (~1 in 8,000), so page only after two intervals |
| Warnings present | `getnetworkinfo.warnings` non-empty | unknown consensus rules, version alerts |
| Peers low | `connections_out < 4` for 10 min | network or DNS-seed failure |
| Disk | free space below 90 days of growth | ~60 GB/year archive; on pruned, alert if pruning falls behind |
| Service down | `systemctl is-active bitcoind` ≠ active, or `NRestarts` increased | crash loop |
| RPC latency | `getblockchaininfo` > 2 s | `rpcworkqueue` exhausted, or disk saturated |
| Mempool floor | `mempoolminfee` above default for > 1 h | eviction — affects fee estimates you publish |

Do not alert on `connections_in == 0` unless the node is meant to serve peers,
and do not alert on a single missed block interval. Ten-minute blocks are a
Poisson process: gaps of an hour happen without anything being wrong.

## 4. Downstream services

A node can be perfectly healthy while everything built on it is broken. Monitor
the layer you actually sell:

| Component | Signal |
|---|---|
| ZMQ | a subscriber that reports the age of the last `hashblock` message; stale ZMQ silently breaks Lightning and indexers |
| electrs / Fulcrum | index height vs node height; connected client count |
| mempool / esplora | API latency, the difference between its tip and the node's |
| LND / CLN | see the **Lightning node** guide — `synced_to_chain`, `synced_to_graph`, inactive channels |

ZMQ failure deserves its own alert. Nothing in `bitcoind` reports it, the
daemon stays perfectly healthy, and the dependent service simply stops being
told about new blocks.

## 5. Logs

````bash
journalctl -u bitcoind -f
journalctl -u bitcoind --since "1 hour ago" | grep -Ei "error|warning|corrupt|invalid"
bitcoin-cli logging   # which categories are active
````

Patterns worth a rule:

| Log line | Meaning |
|---|---|
| `Corrupted block database detected` | unclean shutdown — see **Pruning and storage** |
| `Warning: unknown new rules activated` | a soft fork you do not understand is live; upgrade |
| `Work queue depth exceeded` | raise `rpcworkqueue`/`rpcthreads`, or throttle the caller |
| `Potential stale tip detected` | no new block for a long time; usually the network, sometimes you |
| `[*]` prefix | rate-limited logging is suppressing a source location, not silence |

## Dashboards

Grafana panels that earn their space: height and headers on one axis; tip-hash
agreement as a 0/1 state timeline; inbound/outbound peers; `size_on_disk` with
a projected-full annotation; mempool bytes and `mempoolminfee`; RPC latency.

For mempool and fee visualisation specifically, a self-hosted
[mempool](https://github.com/mempool/mempool) instance is better than anything
you will build in Grafana, and it doubles as the public-facing explorer — see
**RPC, indexes and APIs**.

## Sources

- [bitcoin/bitcoin — RPC reference](https://developer.bitcoin.org/reference/rpc/)
- [jvstein/bitcoin-prometheus-exporter](https://github.com/jvstein/bitcoin-prometheus-exporter)
- [0xB10C/bitcoind-observer — tracepoint-based metrics](https://github.com/0xB10C/bitcoind-observer)
- [bitcoincore.org — v30.0 release notes, log rate limiting](https://bitcoincore.org/en/releases/30.0/)
- [mempool/mempool](https://github.com/mempool/mempool)
