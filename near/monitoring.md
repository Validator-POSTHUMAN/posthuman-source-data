# NEAR Validator Monitoring

Three layers, and you need all three. A process that is "up" tells you almost
nothing on NEAR.

1. **Node health** — `neard` running, synced, keeping pace with an independent
   endpoint.
2. **Validator performance** — blocks, chunks and **endorsements** produced
   versus expected in the current epoch.
3. **Host capacity** — memory headroom and disk on every mount.

## 1. `neard` built-in metrics

`neard` exposes Prometheus metrics on the same port as JSON-RPC:

```bash
curl -s http://127.0.0.1:3030/metrics | head
```

There is no separate metrics port. On a validator, keep `3030` on loopback or
a private interface and scrape it from there — see the **Security** guide.

Useful series: `near_block_height_head`, `near_sync_status`,
`near_peer_connections`, and on archival nodes `cold_head_height`.

## 2. NEAR Validator Watcher (Kiln)

[`kilnfi/near-validator-watcher`](https://github.com/kilnfi/near-validator-watcher)
is the most useful single exporter for validator-level signal: it tracks your
pool's produced versus expected work, seat price, rank and kickouts.

```bash
docker run -d --restart unless-stopped --name near-validator-watcher \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/kilnfi/near-validator-watcher:latest \
  --node http://127.0.0.1:3030 \
  --validator <pool-name>.poolv1.near \
  --refresh-rate 30s
```

Metrics (prefix `near_validator_watcher_`):

| Metric | Use |
|--------|-----|
| `validator_blocks_produced` / `validator_blocks_expected` | block production ratio |
| `validator_chunks_produced` / `validator_chunks_expected` | chunk production ratio |
| `validator_stake`, `validator_rank` | position relative to the seat price |
| `seat_price` | how close you are to losing the seat |
| `validator_slashed` | slashing flag |
| `prev_epoch_kickout` | why a validator was removed last epoch |
| `sync_state`, `block_number` | node sync |
| `protocol_version`, `version_build` | upgrade drift |

It also serves `/ready` (OK when the node is synced) and `/live`.

Point `--node` at your **local** RPC. Public endpoints time out under a 10–30 s
refresh rate and turn every scrape into a Prometheus timeout; we have hit
exactly that failure with public mainnet endpoints and had to rebuild the
exporter against local RPC.

Use `127.0.0.1`, not `localhost`. On a dual-stack host the resolver tries
`::1` first, and a service bound to `0.0.0.0` only answers after that attempt
times out — hundreds of milliseconds per request, on every scrape.

## 3. Endorsements

Since stateless validation, endorsements are what actually drives
chunk-validator rewards, and the kickout threshold is on the **cumulative epoch
ratio**. Query it directly:

```bash
POOL=<pool-name>.poolv1.near
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq --arg p "$POOL" '.result.current_validators[] | select(.account_id==$p) |
      {blocks: "\(.num_produced_blocks)/\(.num_expected_blocks)",
       chunks: "\(.num_produced_chunks)/\(.num_expected_chunks)",
       endorsements: "\(.num_produced_endorsements)/\(.num_expected_endorsements)",
       is_slashed: .is_slashed}'
```

**A low-endorsement alert is retrospective.** The ratio is cumulative over the
epoch, so an 18-minute outage keeps the alert firing for hours after the node is
fully healthy again. Before restarting anything, check whether *fresh* expected
endorsements are being produced: sample the counters twice, 30 seconds apart,
and compare. If new endorsements are landing, the node is fine and the alert
clears at the epoch boundary. Restarting at that point only creates a second
gap.

## 4. Prometheus

```yaml
scrape_configs:
  - job_name: near-node
    static_configs:
      - targets: ['127.0.0.1:3030']

  - job_name: near-validator-watcher
    static_configs:
      - targets: ['127.0.0.1:8080']

  - job_name: node-exporter
    static_configs:
      - targets: ['127.0.0.1:9100']
```

Alert rules worth having:

```yaml
groups:
  - name: near
    rules:
      - alert: NearNodeDown
        expr: up{job="near-node"} == 0
        for: 3m

      - alert: NearNotSynced
        expr: near_validator_watcher_sync_state == 0
        for: 5m

      - alert: NearBlockHeightStalled
        expr: increase(near_validator_watcher_block_number[5m]) < 1
        for: 5m

      - alert: NearSeatPriceMargin
        expr: near_validator_watcher_validator_stake
              / near_validator_watcher_seat_price < 1.1
        for: 30m

      - alert: NearValidatorSlashed
        expr: near_validator_watcher_validator_slashed > 0

      - alert: NearLowMemoryHeadroom
        expr: node_memory_MemAvailable_bytes < 8e9
        for: 10m

      - alert: NearDiskFilling
        expr: node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
              / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"} < 0.15
        for: 15m
```

Memory and disk alerts are not optional. In production the two failures that
have actually cost us endorsements were an OOM kill under memory pressure and a
stalled local RPC — not the process exiting.

## 5. External cross-check

Never conclude from local data alone. An independent height, and the public
validator record, are what turn "my node says it is fine" into evidence:

```bash
curl -s -X POST https://rpc.mainnet.near.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '.result.sync_info.latest_block_height'
```

- [nearblocks.io/node-explorer](https://nearblocks.io/node-explorer) — validator
  set, seat price, uptime, your pool page
- [near-staking.com/stats](https://near-staking.com/stats) — validator stats and
  delegation view
- [pikespeak.ai/validators/overview](https://pikespeak.ai/validators/overview) —
  validator and delegation analytics
- [nearvalidate.org](https://nearvalidate.org/) — query any NEAR RPC endpoint
  directly from the browser

## 6. Minimal Telegram watchdog

When there is no Prometheus stack yet, this covers the two failures that matter
most. It is a floor, not a monitoring system.

```bash
#!/usr/bin/env bash
# /usr/local/bin/near-monitor.sh
set -Eeuo pipefail

BOT_TOKEN="${NEAR_MONITOR_BOT_TOKEN:?}"
CHAT_ID="${NEAR_MONITOR_CHAT_ID:?}"
LOCAL_RPC="http://127.0.0.1:3030"
PUBLIC_RPC="https://rpc.mainnet.near.org"
LAG_THRESHOLD=100
STATE_DIR=/var/lib/near-monitor

alert() {
  local key="$1" text="$2" now stamp
  now=$(date +%s)
  stamp=$(cat "$STATE_DIR/$key" 2>/dev/null || echo 0)
  (( now - stamp < 1800 )) && return 0        # 30 min de-duplication
  curl -sS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" --data-urlencode "text=${text}" >/dev/null
  echo "$now" > "$STATE_DIR/$key"
}

mkdir -p "$STATE_DIR"

status=$(curl -sS --max-time 10 -X POST "$LOCAL_RPC" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' || true)

if [[ -z "$status" ]]; then
  alert rpc "NEAR: local RPC did not answer on $LOCAL_RPC"
  exit 0
fi

local_height=$(jq -r '.result.sync_info.latest_block_height' <<<"$status")
syncing=$(jq -r '.result.sync_info.syncing' <<<"$status")
public_height=$(curl -sS --max-time 10 -X POST "$PUBLIC_RPC" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq -r '.result.sync_info.latest_block_height')

[[ "$syncing" == "true" ]] && alert sync "NEAR: node reports syncing=true at height $local_height"
(( public_height - local_height > LAG_THRESHOLD )) && \
  alert lag "NEAR: local height $local_height is $(( public_height - local_height )) blocks behind public $public_height"

exit 0
```

Keep the token in an environment file readable only by the service user — never
inline in the script:

```ini
# /etc/systemd/system/near-monitor.service
[Service]
Type=oneshot
User=near
EnvironmentFile=/etc/near-monitor.env
ExecStart=/usr/local/bin/near-monitor.sh
```

```ini
# /etc/systemd/system/near-monitor.timer
[Timer]
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

## What not to alert on

- **A single process restart.** One `Restart=on-failure` cycle that recovers
  within a block or two is noise. Alert on height stalling instead.
- **Cumulative endorsement ratio without a freshness check.** See section 3.
- **Peer-count dips.** Transient, self-correcting, and a reliable source of
  false pages.

Also alert on the **`ping` timer failing**. A pool that stops being pinged stops
re-proposing, and nothing in the node's own metrics will tell you.

## Related guides

- **Security** — RPC exposure and the scrape path
- **Create validator** — the `ping` timer this section refers to
- **Endpoints** — public RPC endpoints used for cross-checks
