# Monitoring a Base Node

A Base node does not propose, does not attest and cannot be slashed, so there is
no duty-based signal telling you it is unwell. It fails in exactly two ways:
it stops serving, or it serves the wrong answer. The second one is silent and is
what this page is mostly about.

---

## 1. The signal that matters most: safe-head lag

`optimism_syncStatus` on the rollup node reports several heads. Two of them
differ in a way that decides your whole alerting strategy:

| Head | Source | What it proves |
|---|---|---|
| `unsafe_l2` | the sequencer's gossip feed | the sequencer is alive and you can hear it |
| `safe_l2` | batches read back from Ethereum L1 | **your node is actually deriving from L1** |
| `finalized_l2` | L1 finality | the L1 blocks behind it are finalized |

The unsafe head keeps advancing every 2 seconds whether or not your L1 access
works. Your process is up. Your logs look normal. `eth_blockNumber` climbs.
Every height-based monitor is green — and your node has quietly become a
sequencer-trusting mirror rather than a node that verifies Ethereum.

**Alert on `unsafe_l2.number − safe_l2.number`, not on block height.**

```bash
curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H 'Content-Type: application/json' http://127.0.0.1:7545 \
  | jq '{
      unsafe: .result.unsafe_l2.number,
      safe:   .result.safe_l2.number,
      lag:    (.result.unsafe_l2.number - .result.safe_l2.number),
      l1:     .result.head_l1.number,
      age_s:  (now - .result.unsafe_l2.timestamp | floor)
    }'
```

Base posts batches to L1 on a cadence, so a lag of a few hundred blocks is
normal and a lag of zero never happens. Baseline your own node over a week and
alert on sustained excursions above it. `basectl doctor` uses 150 blocks to warn
and 300 to fail for safe-head recency; those are reasonable starting values.

A safe head that is **not advancing at all** for more than a few minutes is an
L1 problem every time: the execution RPC, the beacon endpoint, blob
availability, or a quota that just ran out.

---

## 2. What to alert on

Ranked by what it costs you when it breaks.

| Signal | Where from | Alert when |
|---|---|---|
| Safe head not advancing | `optimism_syncStatus` | no increase for 10 min |
| `unsafe − safe` lag | `optimism_syncStatus` | sustained above your baseline |
| Unsafe head age | `optimism_syncStatus` timestamp | older than 60 s |
| Head vs public tip | `eth_blockNumber` vs `mainnet.base.org` | more than 20 blocks behind |
| EL syncing | `eth_syncing` | not `false` |
| Chain ID | `eth_chainId` | not `0x2105` (mainnet) |
| EL peer count | `net_peerCount` / metrics | below 5 |
| CL peer count | `opp2p_peerCount` / metrics | below 5 |
| Disk free | node_exporter | below 15%, or predicted full within 14 days |
| Disk write latency | node_exporter | p99 above ~10 ms sustained |
| Clock offset | chrony / node_exporter | above 200 ms |
| Container restarts | Docker / systemd | any |
| L1 RPC error rate | rollup node metrics, provider dashboard | any sustained non-zero |
| L1 quota consumed | provider dashboard | above 80% of the period |
| Released version vs running | GitHub releases | a new release exists |

Two of those are easy to skip and expensive to have skipped.

**L1 quota.** A Base node's L1 consumption is not flat — it spikes during
catch-up. The failure is not an error, it is a 429 that the rollup node retries
until the safe head stops moving. If you use a provider, alert on the provider's
own usage metric, not only on your node.

**Version against releases.** Base ships fork-critical releases with a hard
activation timestamp. There is no in-protocol upgrade signal to watch and no
governance proposal to read. If you are not checking the releases page, you will
find out at the fork. See the **Upgrades** tab.

---

## 3. Metrics endpoints

With the loopback bindings from **Security Hardening** in place:

| Process | Host port | Container port |
|---|---|---|
| `base-reth-node` (EL) | `7301` | `6060` |
| `base-consensus` (CL) | `7300` | `7300` |
| `base-consensus` pprof | `6060` | `6060` |
| node_exporter | `9100` | — |

Confirm what each one actually serves before you write scrape config — reth and
the rollup node do not agree on the path:

```bash
curl -s http://127.0.0.1:7301/ | head -5
curl -s http://127.0.0.1:7301/metrics | head -5
curl -s http://127.0.0.1:7300/metrics | head -5
```

Whichever returns Prometheus text is the one to scrape. An empty reply means the
container was started without its metrics flag, or you are hitting the wrong
mapped port.

pprof on `6060` is not monitoring. It is a debugging surface that hands out heap
and CPU profiles and burns CPU doing it. Keep it on loopback or unmapped.

---

## 4. Prometheus

```yaml
scrape_configs:
  - job_name: base-el
    static_configs:
      - targets: ['127.0.0.1:7301']
  - job_name: base-cl
    metrics_path: /metrics
    static_configs:
      - targets: ['127.0.0.1:7300']
  - job_name: node
    static_configs:
      - targets: ['127.0.0.1:9100']
```

Base publishes Grafana dashboards in the repo under
`etc/scripts/devnet/grafana/dashboards/`. They target the devnet stack, so
treat them as a starting point for panel and metric names rather than something
to import unchanged.

### The blackbox check that catches what metrics do not

Metrics tell you the process is happy. They do not tell you the answers are
right. Run a small external prober that does what a consumer does:

```bash
#!/usr/bin/env bash
# base-probe.sh — read-only. Exit 0 healthy, 1 degraded.
set -euo pipefail
EL=${EL:-http://127.0.0.1:8545}
CL=${CL:-http://127.0.0.1:7545}
REF=${REF:-https://mainnet.base.org}

rpc() { curl -fsS -m 10 -X POST -H 'Content-Type: application/json' --data "$2" "$1"; }

chain=$(rpc "$EL" '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' | jq -r .result)
[ "$chain" = "0x2105" ] || { echo "chain_id=$chain expected=0x2105"; exit 1; }

syncing=$(rpc "$EL" '{"jsonrpc":"2.0","id":1,"method":"eth_syncing","params":[]}' | jq -r '.result')
[ "$syncing" = "false" ] || { echo "el_syncing=$syncing"; exit 1; }

status=$(rpc "$CL" '{"jsonrpc":"2.0","id":1,"method":"optimism_syncStatus","params":[]}')
unsafe=$(echo "$status" | jq -r .result.unsafe_l2.number)
safe=$(echo "$status" | jq -r .result.safe_l2.number)
age=$(( $(date +%s) - $(echo "$status" | jq -r .result.unsafe_l2.timestamp) ))

local_head=$(rpc "$EL" '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' | jq -r .result)
ref_head=$(rpc "$REF" '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' | jq -r .result)
behind=$(( $(printf %d "$ref_head") - $(printf %d "$local_head") ))

echo "unsafe=$unsafe safe=$safe lag=$((unsafe - safe)) head_age_s=$age behind_ref=$behind"
[ "$age" -le 60 ]        || { echo "head stale"; exit 1; }
[ "$((unsafe-safe))" -le 300 ] || { echo "safe head lagging"; exit 1; }
[ "$behind" -le 20 ]     || { echo "behind public tip"; exit 1; }
```

The public reference call is the part that earns its keep: a node that agrees
with itself and disagrees with the rest of the network is the case no
self-reported metric will ever show you.

Run it from a machine that is not the node, so the check fails when the node's
host does.

---

## 5. `basectl` as a monitoring tool

```bash
basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545 --json
```

Read-only, exits `1` if any check fails, and `--json` makes it scriptable. It
covers declared network against live chain ID, EL and CL peer counts, local head
against the public tip, safe-head recency, advertised P2P endpoint sanity,
bootnode configuration and L1 RPC reachability.

Thresholds worth setting explicitly rather than inheriting:

| Flag | Default |
|---|---|
| `--peer-warn-threshold` | `5` |
| `--head-lag-warn-blocks` | `10` |
| `--head-lag-fail-blocks` | `20` |
| `--safe-recency-warn-blocks` | `150` |
| `--safe-recency-fail-blocks` | `300` |
| `--tip-tolerance` | `5` |

Note that `doctor`'s built-in mainnet preset looks for the CL at
`127.0.0.1:9545` while the Compose stack publishes it on `7545`. Without an
explicit `--cl-rpc`, the CL-dependent checks are **skipped with a hint**, not
failed — a cron job that only reads the exit code will report success while
checking half of what you think.

For interactive triage, `basectl monitor` opens a TUI; `basectl monitor upgrades`
shows the activation countdown and history, and `basectl sync-status` prints the
CL/EL join with a `tip_reference` comparison in one shot.

---

## 6. Logs worth alerting on

Both services log JSON to stdout (`--log.stdout.format json` on the EL), so
`docker compose logs` feeds a log pipeline directly.

Patterns that deserve a page rather than a dashboard:

- repeated L1 RPC errors, timeouts or `429` from the rollup node
- `failed to fetch blob` or blob-sidecar retrieval errors — your beacon endpoint
  has pruned past what derivation needs
- reth database errors, `MDBX` errors, or anything mentioning corruption
- the rollup node restarting in a loop
- `Could not retrieve public IP` followed by exit code `8` — the container
  cannot reach any of its IP-discovery providers and will not start at all
- peer count reaching zero

---

## 7. What not to alert on

- **Block height alone.** It advances while the node is broken. See §1.
- **Container "up".** Docker reports a container as healthy that has been unable
  to reach L1 for an hour.
- **A single missed scrape.** Alert on sustained conditions; Base's 2-second
  blocks make transient jitter constant.
- **`finalized_l2` briefly stalling.** It follows Ethereum finality and moves in
  steps, not smoothly. Alert on the safe head instead.

---

## Related

- **Security Hardening** — bind the ports these checks use to loopback first
- **Troubleshooting** — what to do when one of these alerts fires
- **Upgrades** — the fork deadlines no metric will warn you about
