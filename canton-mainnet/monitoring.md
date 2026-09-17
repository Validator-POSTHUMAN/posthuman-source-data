# Canton Network MainNet — Validator Monitoring

Canton is not a Cosmos SDK chain. There are no blocks to sign, no missed-block
counter, no jail state and no slashing. Every monitoring habit built around
`missed_blocks` has to be replaced, or you will watch a green dashboard while
your validator quietly stops earning.

This guide defines what "healthy" means on Canton, which signals prove it, and
how to alert on them.

## What "up" means on Canton

A MainNet validator is fully operational only when all three hold at once:

1. The validator container reports Docker health `healthy`.
2. Sync lag is under 60 seconds — the participant is keeping up with the
   Global Synchronizer.
3. Automation is healthy — every background service reports health `0`, and the
   `ReceiveFaucetCouponTrigger` iteration counter keeps climbing.

Any one of these alone is a false positive:

| Signal alone | What it still misses |
|---|---|
| Container is running | A running container can be unhealthy for weeks |
| Container is `healthy` | Health only probes the local HTTP port, not sync |
| Sync lag is low | A stalled reward trigger earns nothing while in sync |

POSTHUMAN hit exactly this: a DevNet validator sat `Up 7 weeks (unhealthy)`
while `docker ps` looked normal at a glance. Alert on health status, not on
container presence.

## Where the metrics come from

Every Splice node exposes Prometheus metrics on port **10013**, path
`/metrics`. On a validator two components publish:

- the validator app (`validator:10013`)
- the participant (`participant:10013`)

In a Docker Compose deployment metrics are on by default — no configuration
needed.

Scrape the container ports **directly**, never through the bundled nginx.
Nginx routes by `Host` header (`validator.localhost`, `participant.localhost`)
and Prometheus cannot set a custom `Host` per target, so a scrape through nginx
returns 404.

```yaml
scrape_configs:
  - job_name: 'canton-validator'
    static_configs:
      - targets: ['validator:10013']
  - job_name: 'canton-participant'
    static_configs:
      - targets: ['participant:10013']
```

The Prometheus container must join the validator's Docker network to resolve
`validator` and `participant` by name. With the default Compose project name
that network is `splice-validator_splice_validator`.

Quick check that metrics are live. The validator image ships **wget, not
curl** — a `curl` exec fails with
`executable file not found in $PATH` and an empty body, which reads exactly
like a dead metrics port:

```bash
docker exec splice-validator-validator-1 \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -20
```

A healthy MainNet validator returns roughly 600 KB and about 2,000 lines.

Values come out in scientific notation (`1.789684504197E12`). Shell integer
arithmetic cannot parse that; use `awk` or PromQL, not `$(( ))`.

### The bundled Grafana dashboards do not work under Docker Compose

The Splice bundle ships 47 dashboards in
`~/.canton/<version>/splice-node/grafana-dashboards/`. Every query in them
filters on a `namespace` label, which is injected by the Kubernetes Prometheus
operator and does not exist in a Compose deployment. The dashboards also
declare `namespace` as a required template variable, so the dropdown comes up
empty and every panel stays blank.

Use a dashboard built on labels that exist under Compose — `job` and
`instance`. The POSTHUMAN toolkit ships one (38 panels, 8 sections) and
provisions it automatically.

## Ready-made stack

```bash
git clone https://github.com/web3validator/canton-validator-toolkit ~/canton-validator-toolkit
cd ~/canton-validator-toolkit/monitoring
CANTON_NETWORK_NAME=splice-validator docker compose up -d
```

`CANTON_NETWORK_NAME` must equal your validator's Compose project name. It is
`splice-validator` by default; if your containers are named
`splice-devnet-validator-1`, set `splice-devnet`.

| Component | Bind | Purpose |
|---|---|---|
| Prometheus | `localhost:9091` | scrape and store |
| Grafana | `localhost:3001` | dashboards and alert rules |
| node-exporter | `localhost:9101` | CPU, RAM, disk, network |

All three bind to localhost only. node-exporter deliberately uses 9101, not
9100, so it does not collide with a system-level node-exporter installed
outside Docker.

Reach them over an SSH tunnel:

```bash
ssh -L 3001:localhost:3001 -L 9091:localhost:9091 user@your-server -N
```

Or put the host on a Tailscale network and bind the stack to the Tailscale
address — no tunnel, works from a phone:

```bash
CANTON_NETWORK_NAME=splice-validator MONITOR_BIND_IP=<tailscale-ip> docker compose up -d
```

Change the default Grafana password on first login.

## The metrics that matter

### Liveness and sync

| Metric | Meaning |
|---|---|
| `up{job="canton-validator"}` | validator app scrape succeeded |
| `daml_health_status{job="canton-participant"}` | participant self-reported health, `1` = healthy |
| `splice_store_last_seen_record_time_ms` | wall-clock ms of the last record the store saw |

Sync lag is derived, not exported directly:

```promql
time() * 1000 - splice_store_last_seen_record_time_ms
```

Under 30 s is normal, over 60 s is a warning, over 120 s means the participant
is falling behind the synchronizer and needs attention.

### Automation health — the Canton replacement for "missed blocks"

Rewards arrive because automation triggers run, not because a block was signed.
Splice exports the health of every background service as a gauge where **0
means healthy**:

```promql
splice_automation_background_service_health != 0
```

On a healthy MainNet validator all 29 series read `0`. Any non-zero series
names the broken automation in its `service` label, which is far more precise
than a container health flag. This is the single most important Canton-specific
alert — treat it the way you would treat a jailed Cosmos validator.

Reward liveness itself is two different facts, and conflating them is the usual
mistake:

| Metric | Proves |
|---|---|
| `splice_trigger_iterations_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the polling loop is alive |
| `splice_trigger_completed_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the trigger actually collected something |

> **The completion series does not exist until the first completion.** It is
> absent on both the POSTHUMAN MainNet and TestNet validators today, while the
> iteration counter climbs normally. An alert written as
> `rate(splice_trigger_completed_total{...}[1h]) == 0` therefore never fires:
> PromQL returns *no data* for a missing series, not zero. Alert on the
> iteration counter going flat, on automation health, and on the balance —
> and use `absent()` if you want to assert the completion series exists.

Related:

| Metric | Use |
|---|---|
| `splice_wallet_unlocked_amulet_balance` | CC balance; flat for hours means rewards stopped |
| `splice_wallet_locked_amulet_balance` | locked portion, for reconciliation |
| `splice_retries_failures` | cumulative retry failures by `operation` and `error_kind`; sustained growth is a defect. A healthy node sits in the low tens; a broken one reached 122,127 |
| `splice_trigger_latency_duration_seconds` | trigger latency histogram |
| `splice_validator_scan_bft_calls_total` | BFT scan reads; failures here mean the node cannot read the network |

### Participant internals

| Metric | Why it matters |
|---|---|
| `daml_sequencer_client_submissions_dropped_total` | submissions dropped on overload or timeout — direct loss |
| sequencer client delay | submission delay to the synchronizer |
| submissions in flight | backlog forming |
| gRPC error rate | broken client or misconfiguration |

### Host and JVM

Heap above 85 %, GC time climbing, DB queue depth growing, connection pool
saturated, disk free under 20 GB, disk I/O pinned — all of these precede a
participant stall. MainNet needs 250 GB minimum and grows; alert on free space,
not on percentage used.

## Alert rules

Configure in Grafana under Alerting → Alert rules.

| Alert | Condition | For | Severity |
|---|---|---|---|
| ValidatorDown | `up{job="canton-validator"} == 0` | 2m | critical |
| ParticipantUnhealthy | `daml_health_status{job="canton-participant"} != 1` | 2m | critical |
| AutomationUnhealthy | `splice_automation_background_service_health != 0` | 5m | critical |
| SyncLagCritical | `time()*1000 - splice_store_last_seen_record_time_ms > 120000` | 2m | critical |
| TriggerLoopStalled | `increase(splice_trigger_iterations_total{trigger_name="ReceiveFaucetCouponTrigger"}[1h]) == 0` | 90m | critical |
| SyncLagWarning | `time()*1000 - splice_store_last_seen_record_time_ms > 60000` | 5m | warning |
| RetryFailuresGrowing | `increase(sum(splice_retries_failures)[1h:]) > 50` | — | warning |
| DroppedSubmissions | `rate(daml_sequencer_client_submissions_dropped_total[5m]) > 0` | 5m | warning |
| HeapHigh | heap used / heap max > 0.85 | 5m | warning |
| DiskLow | node-exporter free bytes < 20 GB | — | warning |
| VersionBehind | node version ≠ `sv.version` from `/info` for over 24 h | — | warning |

`TriggerLoopStalled` needs a long `for` window: rounds are not instantaneous
and a short window produces noise. Ninety minutes is short enough to catch a
real stall within one operational shift.

Do not write the reward alert against `splice_trigger_completed_total` unless
you have first confirmed that series exists on your node — see the warning
above.

## Cheap monitoring without Prometheus

If you do not want a full stack, a cron health check covers the basics. The
toolkit ships one that runs every 15 minutes and checks container health, sync
lag, retry failures and disk space, with a state machine so a persistent
failure alerts once rather than every run:

```bash
~/canton-validator-toolkit/scripts/check_health.sh
```

It supports Telegram, Discord, Slack and PagerDuty independently, alerts on
failure, stays silent while still failing, and sends one recovery message. On
Telegram it also pins the failure message and unpins it on recovery.

Configure channels in `~/.canton/toolkit.conf`. Keep the tokens out of the
guide, out of `.bash_history` and out of any world-readable file — see the
Security Hardening tab.

## Watching the network, not just your node

Version and migration ID for MainNet are published at a public endpoint that
needs no whitelisting and no API key:

```bash
curl -s https://docs.global.canton.network.sync.global/info | jq .
```

```json
{"network":"mainnet","sv":{"migration_id":4,"serial_id":5,"version":"0.7.5"},
 "synchronizer":{"current":{"chain_id_suffix":"2","serial_id":5,"version":"0.7.5"},
 "legacy":null,"successor":null}}
```

Alert when your running image tag falls behind `sv.version`. Compare against
what is actually running, not against a symlink:

```bash
docker inspect splice-validator-validator-1 --format '{{.Config.Image}}'
```

A stale `~/.canton/current` symlink is a known trap — POSTHUMAN found one
pointing at `0.6.1` while the node ran `0.6.14`. The running image is the only
version truth.

> `https://lighthouse.cantonloop.com/api/stats` now requires an API key and
> returns `401 API key required`. Older guides that poll it for the network
> version are broken; use the `/info` endpoint above.

Scan health from a whitelisted MainNet host:

```bash
curl -s --max-time 5 https://scan.sv-1.global.canton.network.digitalasset.com/api/scan/version
```

MainNet Scan endpoints reject requests from any IP that is not an onboarded
validator, on every Super Validator mirror. A `403 RBAC: access denied` from
your laptop is expected and is not an outage.

## Verification checklist

After any change to the monitoring stack:

- `docker ps | grep canton-` shows Prometheus, Grafana and node-exporter up
- Prometheus → Status → Targets shows `canton-validator` and
  `canton-participant` both `UP`
- the Overview dashboard renders a non-empty CC balance and a sync lag under
  60 s
- a deliberately fired test alert reaches the contact point
- `check_health.sh` run by hand exits 0

## Related

- **Security Hardening** — exposure, auth, secrets, firewall
- **Backup & Recovery** — what monitoring cannot save you from
- **Ecosystem Tooling** — explorers, scan API, third-party monitors

---

**POSTHUMAN validators** — https://posthuman.digital
