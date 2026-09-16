# Espresso — Monitoring

Espresso validators are not Cosmos validators: there is no missed-block counter,
no signing window and no jail state to alert on. Liveness is measured in
**consensus views**, and proposal quality is measured by a **participation
score** published by any query node.

This page lists what to scrape, what to alert on, and what each signal means.
Verified against the official operator documentation on 2026-09-16.

---

## 1. Metrics endpoint

The node exposes Prometheus metrics on `ESPRESSO_NODE_API_PORT` (default
`8080`):

```
/status/metrics
```

Depending on the release and how the API is mounted, the versioned path
`/v1/status/metrics` serves the same document. Check once on your own node and
pin whichever answers:

```bash
curl -fsS localhost:8080/v1/status/metrics | head -5 \
  || curl -fsS localhost:8080/status/metrics | head -5
```

The `status` module must be enabled. A node running with
`-- query -- light-client` gets it implicitly; a non-query validator must pass
`-- status` explicitly, otherwise **it exposes no consensus metrics at all** and
nothing on this page works.

> `/healthcheck` is a static liveness probe for the HTTP server. It does **not**
> reflect consensus health. Never page on it alone, and never treat a green
> healthcheck as evidence the validator is participating.

Keep the API port on loopback or behind a reverse proxy — see the
[security guide](/node-ops/espresso/security-hardening).

### Prometheus scrape

```yaml
scrape_configs:
  - job_name: espresso
    metrics_path: /v1/status/metrics
    scrape_interval: 15s
    static_configs:
      - targets: ["127.0.0.1:8080"]
        labels:
          network: mainnet
          node: espresso-01
```

---

## 2. The five signals that matter

| Signal                                 | Source                                 | Healthy                                    |
| -------------------------------------- | -------------------------------------- | ------------------------------------------ |
| Consensus liveness                     | `consensus_current_view`               | Advances continuously at the network rate  |
| Decide liveness                        | `consensus_last_decided_view`          | Tracks current view closely                |
| Time since last decide                 | `/status/time-since-last-decide`       | Low and flat                               |
| Missed proposals                       | `consensus_number_of_timeouts_as_leader` | Never increments                         |
| Participation score                    | Query-node participation API           | Close to `1.0`, never below `0.95`         |

### Consensus liveness

```
consensus_current_view
consensus_last_decided_view
```

`consensus_current_view` must advance continuously. **Static for more than a
minute** means the node has fallen out of sync or the network has lost liveness.

`consensus_last_decided_view` must track the current view closely. Current view
advancing while last decided view stalls points at a **network-wide** consensus
problem, not a local one — check other operators before touching your node.

`/status/time-since-last-decide` returns seconds since the last decide and is
**the single best liveness alert**.

### Missed proposals

```
consensus_number_of_timeouts_as_leader
```

Counts views where this node was leader and failed to propose. **Every
increment is a missed proposal and warrants investigation.** There is no
separate missed-proposal or missed-vote metric in Espresso.

### Participation score

Participation is not visible from the node itself — read it from another query
node, for example the Espresso-hosted service:

```bash
QUERY=https://query.main.net.espresso.network      # Decaf: https://query.decaf.testnet.espresso.network

curl -fsS "$QUERY/node/participation/proposal/current"
curl -fsS "$QUERY/node/participation/vote/current"
```

The response maps BLS public keys to participation scores.

| Score          | Reading                                                          |
| -------------- | ---------------------------------------------------------------- |
| close to `1.0` | Healthy                                                          |
| below `0.95`   | Investigate                                                      |
| dip after restart or outage | Expected for up to one epoch                        |

Replace `current` with an epoch number to read a past epoch. That path segment
must be a number — there is no `previous` shorthand.

Scrape this on a timer (every 10–15 minutes is enough) keyed on your own
`BLS_VER_KEY~…`, and alert when your key's score drops below `0.95` for more
than one epoch, or when your key disappears from the response entirely.

---

## 3. Peer connectivity

All cliquenet metrics are prefixed `consensus_cliquenet_` and carry a `peer`
label holding a **base58-encoded x25519 public key**, without the `X25519_PK~`
prefix used at registration. The label means two different things depending on
the metric:

| Metric                                  | Type    | `peer` label | Meaning                                                              |
| --------------------------------------- | ------- | ------------ | -------------------------------------------------------------------- |
| `consensus_cliquenet_peer_tasks`        | gauge   | own          | Established peer connections                                         |
| `consensus_cliquenet_accept_tasks`      | gauge   | own          | Inbound TCP connections currently in the handshake                   |
| `consensus_cliquenet_hello_tasks`       | gauge   | own          | Inbound connections currently exchanging hellos                      |
| `consensus_cliquenet_connect_tasks`     | gauge   | own          | Outbound dials in flight                                             |
| `consensus_cliquenet_channel_size`      | gauge   | own          | Queued outbound commands                                             |
| `consensus_cliquenet_lower_bound`       | gauge   | own          | Lowest message slot still retained                                   |
| `consensus_cliquenet_hellos`            | counter | remote       | Inbound connections from that peer past the Noise handshake          |
| `consensus_cliquenet_connect_attempts`  | counter | remote       | Outbound dial tasks started for that peer                            |
| `consensus_cliquenet_errors`            | counter | remote       | Peer failures after a connection was established                     |
| `consensus_cliquenet_outbound_messages` | gauge   | remote       | Messages queued for that peer                                        |
| `consensus_cliquenet_retrying_messages` | gauge   | remote       | Messages awaiting retry for that peer                                |
| `consensus_cliquenet_remaining_budget`  | gauge   | remote       | Remaining send budget for that peer                                  |

```bash
curl -fsS localhost:8080/v1/status/metrics | grep consensus_cliquenet
```

**These metrics are created lazily on first update, so a missing series carries
information.** A node that has never established a peer connection exports no
`consensus_cliquenet_peer_tasks` at all — write alert rules with `absent()`,
not only on thresholds.

Reading the numbers:

- `peer_tasks` absent or `0` — no P2P mesh connections at all.
- `peer_tasks` well below the number of other validators in the stake table —
  partial connectivity; compare `peer` labels on `outbound_messages` against the
  stake table to find which peers are missing.
- **No `hellos` series at all** — nothing has ever reached the node inbound.
  Because each side dials the other and one connection serves both directions,
  your own outbound dials can keep `peer_tasks` looking healthy while the
  inbound path is completely broken. Signature of an inspecting proxy, a closed
  port, or a registered P2P address that does not route to the node.
- `connect_attempts` climbing for a peer while the connection never establishes
  — misregistered P2P address or x25519 key. Fix it by **re-registering the
  correct values with `staking-cli`**, not by changing node environment
  variables.
- `errors` rising for one peer — connections establish and then drop. Look for
  byte corruption in the path: TLS termination or a PROXY protocol header.

`connect_attempts` is not a retry counter. One dial task retries internally and
never gives up, so the counter sits at `1` per peer for as long as that first
dial is outstanding. It increments again only when an established connection
drops and a fresh dial task starts.

---

## 4. Node resources and version

| Metric                           | Alert on                                                     |
| -------------------------------- | ------------------------------------------------------------ |
| `process_resident_memory_bytes`  | Sustained growth toward the container/host limit             |
| `process_open_fds`               | Approaching the file-descriptor limit                        |
| `consensus_version{desc=…}`      | Value differs from the tag you intended to run               |

**Database size is not exposed as a metric.** Watch it at the operating-system
level (`du` on `ESPRESSO_NODE_STORAGE_PATH`) or at the Postgres level, and alert
well before the disk fills — the pruner does not bound the hash and aggregate
tables, so a query node grows past its retention window by design.

---

## 5. L1 dependency

The node needs a working Ethereum RPC at all times. Espresso does not publish a
dedicated L1-health metric, so monitor the dependency directly:

```bash
# L1 head, from the same provider the node uses.
curl -fsS -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  "$ESPRESSO_L1_PROVIDER" | jq -r .result
```

Alert on: provider HTTP errors or rate-limit responses, a stalled L1 head, and
WebSocket reconnect storms in the node logs. A degraded L1 provider surfaces
first as errors in the node log, not as a consensus metric.

Use a provider with a real quota, and configure `ESPRESSO_L1_WS_PROVIDER` —
it noticeably reduces request volume.

---

## 6. Alert rules

Adjust thresholds to the observed view rate on your network before enabling.

```yaml
groups:
  - name: espresso
    rules:
      - alert: EspressoConsensusViewStalled
        expr: increase(consensus_current_view[2m]) == 0
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "Espresso current view has not advanced for 2 minutes"

      - alert: EspressoDecideStalled
        expr: increase(consensus_last_decided_view[5m]) == 0
          and increase(consensus_current_view[5m]) > 0
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Views advance but nothing decides — likely network-wide"

      - alert: EspressoMissedProposal
        expr: increase(consensus_number_of_timeouts_as_leader[15m]) > 0
        labels: { severity: warning }
        annotations:
          summary: "Validator was leader and failed to propose"

      - alert: EspressoNoPeerConnections
        expr: absent(consensus_cliquenet_peer_tasks) or consensus_cliquenet_peer_tasks == 0
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "No cliquenet peer connections"

      - alert: EspressoNoInboundHellos
        expr: absent(consensus_cliquenet_hellos)
        for: 30m
        labels: { severity: warning }
        annotations:
          summary: "No inbound P2P connection has ever completed — check port, proxy and registered P2P address"

      - alert: EspressoVersionDrift
        expr: count(count by (desc) (consensus_version)) > 1
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Espresso node version differs from the fleet"

      - alert: EspressoFileDescriptorPressure
        expr: process_open_fds / process_max_fds > 0.8
        for: 10m
        labels: { severity: warning }

      - alert: EspressoDown
        expr: up{job="espresso"} == 0
        for: 2m
        labels: { severity: critical }
```

`time-since-last-decide` is an HTTP route, not a metric. Cover it with a
blackbox probe or a small exporter, and page when it exceeds a few multiples of
the normal view interval.

---

## 7. Dashboard panels

A useful Espresso validator dashboard is built from these groups. Panel names
are ours; bind each one to the exact metric present on your node after a first
scrape, and do not assume a series exists until you have seen it.

**Consensus health** — current view, last decided view, view lag
(`consensus_current_view - consensus_last_decided_view`), views since last
decide, seconds since last decide, timeouts as leader (5 m), proposal→decide
latency, last voted view.

**Participation** — proposal and vote score for your BLS key over the last
epochs, from the query-node participation API.

**Peers** — established peer connections, inbound hellos per peer, outbound
dials in flight, per-peer errors, queued and retrying messages, remaining send
budget.

**L1** — provider head, finalized height, failed requests (5 m), provider
failovers (1 h), WebSocket reconnects (1 h).

**Node & database** — resident memory, open file descriptors, storage-path
size, container restarts, running image tag.

---

## 8. Minimal alerting without Prometheus

A small timer-driven script covers the critical path on a single node. It fires
only on state change, keeping a flag file so a continuing outage does not spam.

```bash
#!/usr/bin/env bash
# /usr/local/bin/espresso-watch.sh — state-change Telegram alerts.
set -euo pipefail

API=http://127.0.0.1:8080
TG_TOKEN="__SET_ME__"
TG_CHAT="__SET_ME__"
STATE=/var/lib/espresso-watch
MAX_DECIDE_AGE=120          # seconds; tune to the observed view rate
mkdir -p "$STATE"

notify() {
  curl -fsS -m 10 -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
    -d chat_id="${TG_CHAT}" -d text="$1" >/dev/null
}

flag() {  # flag <name> <is_bad> <bad_text> <ok_text>
  local name=$1 bad=$2 bad_text=$3 ok_text=$4
  if [ "$bad" = 1 ] && [ ! -f "$STATE/$name" ]; then
    : > "$STATE/$name"; notify "🔴 $bad_text"
  elif [ "$bad" = 0 ] && [ -f "$STATE/$name" ]; then
    rm -f "$STATE/$name"; notify "🟢 $ok_text"
  fi
}

metrics=$(curl -fsS -m 10 "$API/v1/status/metrics" || true)
if [ -z "$metrics" ]; then
  flag api 1 "espresso-node: metrics endpoint unreachable" ""
  exit 0
fi
flag api 0 "" "espresso-node: metrics endpoint back"

decide_age=$(curl -fsS -m 10 "$API/v1/status/time-since-last-decide" | tr -dc '0-9.' || echo 99999)
awk -v a="$decide_age" -v m="$MAX_DECIDE_AGE" 'BEGIN{exit !(a>m)}' \
  && flag decide 1 "espresso-node: ${decide_age}s since last decide" "" \
  || flag decide 0 "" "espresso-node: deciding again"

view=$(awk '/^consensus_current_view /{print $2}' <<<"$metrics")
prev=$(cat "$STATE/view" 2>/dev/null || echo "")
printf '%s' "$view" > "$STATE/view"
[ -n "$prev" ] && [ "$view" = "$prev" ] \
  && flag view 1 "espresso-node: current view stuck at $view" "" \
  || flag view 0 "" "espresso-node: views advancing again"

peers=$(awk '/^consensus_cliquenet_peer_tasks/{print $2; exit}' <<<"$metrics")
[ -z "${peers:-}" ] || [ "${peers%.*}" -eq 0 ] \
  && flag peers 1 "espresso-node: no cliquenet peer connections" "" \
  || flag peers 0 "" "espresso-node: peers reconnected"
```

```ini
# /etc/systemd/system/espresso-watch.service
[Unit]
Description=Espresso validator watch
[Service]
Type=oneshot
ExecStart=/usr/local/bin/espresso-watch.sh
```

```ini
# /etc/systemd/system/espresso-watch.timer
[Unit]
Description=Run the Espresso validator watch every 5 minutes
[Timer]
OnBootSec=3min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
```

```bash
sudo chmod 700 /usr/local/bin/espresso-watch.sh
sudo systemctl daemon-reload
sudo systemctl enable --now espresso-watch.timer
sudo systemctl start espresso-watch.service && journalctl -u espresso-watch -n 30 --no-pager
```

Keep the bot token in a root-only file or a systemd credential — never in a
world-readable script, a repository, or a shell history.

The script is deliberately single-node. It does not replace the participation
check in section 2, which is the only signal that proves the **network** still
counts your validator.

---

## 9. Triage order

1. `time-since-last-decide` and `consensus_current_view` — is consensus moving?
2. Is the current view moving while decides stall? Then the problem is
   network-wide; check other operators before restarting anything.
3. `consensus_cliquenet_*` — does the node have peers, and does it have
   **inbound** hellos?
4. Node logs for `handshake failed`, `party has invalid ip addr`,
   `noise error: decrypt error`, `unknown party`, `connect/handshake error`.
5. `stake-table-entry` — does the registered x25519 key and P2P address still
   match this node?
6. L1 provider health.
7. Participation score over the last epoch.

Full P2P triage, including the `nc` probes, is in the
[security guide](/node-ops/espresso/security-hardening).

---

## Official resources

- Status API: <https://docs.espressosys.com/network/developer/espresso-api/status-api>
- Run a Validator Node → Monitoring: <https://docs.espressosys.com/network/developer/operators/run-a-node>
- Debug P2P connectivity: <https://docs.espressosys.com/network/developer/operators/run-a-node/p2p-troubleshooting>
