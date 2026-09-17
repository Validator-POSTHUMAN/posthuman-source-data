# Canton Network TestNet — Validator Monitoring

Canton is not a Cosmos SDK chain. There are no blocks to sign, no missed-block
counter, no jail state and no slashing. Every monitoring habit built around
`missed_blocks` has to be replaced.

TestNet adds one failure mode MainNet does not have: the network is **reset
roughly every three months**. A node that misses a reset keeps running, keeps
looking alive in `docker ps`, and is no longer on the network at all. Version
drift is a first-class alert here, not a nicety.

## What "up" means on Canton

A TestNet validator is fully operational only when all four hold:

1. The validator container reports Docker health `healthy`.
2. Sync lag is under 60 seconds.
3. Every automation background service reports health `0`.
4. The running image version matches the network version from `/info`.

Any one alone is a false positive. POSTHUMAN's DevNet validator sat
`Up 7 weeks (unhealthy)` on version `0.6.14` while the network ran `0.8.1` —
`docker ps` looked normal at a glance.

## Where the metrics come from

Every Splice node exposes Prometheus metrics on port **10013**, path
`/metrics`, enabled by default under Docker Compose. Two components publish on
a validator: the validator app (`validator:10013`) and the participant
(`participant:10013`).

The validator image ships **wget, not curl**. A `curl` exec fails with
`executable file not found in $PATH` and returns an empty body, which reads
exactly like a dead metrics port:

```bash
docker exec splice-validator-validator-1 \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -20
```

A healthy TestNet validator returns roughly 500 KB and about 2,000 lines.
Values come out in scientific notation (`1.789684504197E12`) — use `awk` or
PromQL, never shell integer arithmetic.

Scrape the container ports **directly**, never through the bundled nginx.
Nginx routes by `Host` header and Prometheus cannot set one per target, so a
scrape through nginx returns 404.

```yaml
scrape_configs:
  - job_name: 'canton-validator'
    static_configs:
      - targets: ['validator:10013']
  - job_name: 'canton-participant'
    static_configs:
      - targets: ['participant:10013']
```

Prometheus must join the validator's Docker network to resolve those names —
`splice-validator_splice_validator` with the default project name.

### The bundled Grafana dashboards do not work under Docker Compose

The Splice bundle ships 47 dashboards in
`~/.canton/<version>/splice-node/grafana-dashboards/`. Every query filters on a
`namespace` label injected by the Kubernetes Prometheus operator, and every
panel renders empty under Compose. Use a dashboard built on `job` and
`instance`.

## Ready-made stack

```bash
git clone https://github.com/web3validator/canton-validator-toolkit ~/canton-validator-toolkit
cd ~/canton-validator-toolkit/monitoring
CANTON_NETWORK_NAME=splice-validator docker compose up -d
```

`CANTON_NETWORK_NAME` must equal your validator's Compose project name.

| Component | Bind | Purpose |
|---|---|---|
| Prometheus | `localhost:9091` | scrape and store |
| Grafana | `localhost:3001` | dashboards and alert rules |
| node-exporter | `localhost:9101` | CPU, RAM, disk, network |

All bind to localhost. node-exporter uses 9101 deliberately, to avoid a
collision with a system-level node-exporter on 9100.

```bash
ssh -L 3001:localhost:3001 -L 9091:localhost:9091 user@your-server -N
```

## The metrics that matter

### Liveness and sync

| Metric | Meaning |
|---|---|
| `up{job="canton-validator"}` | validator app scrape succeeded |
| `daml_health_status{job="canton-participant"}` | participant health, `1` = healthy |
| `splice_store_last_seen_record_time_ms` | wall-clock ms of the last record seen |

```promql
time() * 1000 - splice_store_last_seen_record_time_ms
```

Under 30 s normal, over 60 s warning, over 120 s the participant is falling
behind. A healthy POSTHUMAN TestNet validator sits around 40 s.

### Automation health — the replacement for "missed blocks"

```promql
splice_automation_background_service_health != 0
```

The gauge is **0 when healthy**. All 29 series read `0` on a healthy TestNet
validator; a non-zero series names the broken automation in its `service`
label. This is the most important Canton-specific alert.

Reward liveness is two separate facts:

| Metric | Proves |
|---|---|
| `splice_trigger_iterations_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the polling loop is alive |
| `splice_trigger_completed_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the trigger did work |

> **The completion series does not exist until the first completion.** It is
> absent on the POSTHUMAN TestNet validator today while iterations climb past
> 8,900. An alert written as `rate(splice_trigger_completed_total{...}[1h]) == 0`
> never fires: PromQL returns *no data* for a missing series, not zero. Alert
> on iterations, on automation health and on the balance, and use `absent()` if
> you want to assert the series exists.

| Metric | Use |
|---|---|
| `splice_wallet_unlocked_amulet_balance` | CC balance |
| `splice_retries_failures` | retry failures by `operation` and `error_kind`; low tens on a healthy node, 122,127 on a broken one |
| `splice_validator_scan_bft_calls_total` | BFT scan reads; failures mean the node cannot read the network |
| `daml_sequencer_client_submissions_dropped_total` | submissions lost to overload or timeout |

### Version drift — the TestNet-specific alert

```bash
curl -s https://docs.test.global.canton.network.sync.global/info | jq .
```

```json
{"network":"testnet","sv":{"migration_id":1,"serial_id":2,"version":"0.8.0"},
 "synchronizer":{"current":{"chain_id_suffix":"5","serial_id":2,"version":"0.8.0"},
 "legacy":null,"successor":null}}
```

Compare `sv.version` against what is actually running:

```bash
docker inspect splice-validator-validator-1 --format '{{.Config.Image}}'
```

A stale `~/.canton/current` symlink is a known trap; the running image is the
only version truth. A change in `migration_id` means a **network reset**, and a
reset means full redeployment — see the Backup & Recovery tab.

> `https://lighthouse.testnet.cantonloop.com/api/stats` now requires an API
> key. Any script still polling it for the network version is broken; use
> `/info`.

## Alert rules

| Alert | Condition | For | Severity |
|---|---|---|---|
| ValidatorDown | `up{job="canton-validator"} == 0` | 2m | critical |
| ParticipantUnhealthy | `daml_health_status{job="canton-participant"} != 1` | 2m | critical |
| AutomationUnhealthy | `splice_automation_background_service_health != 0` | 5m | critical |
| SyncLagCritical | `time()*1000 - splice_store_last_seen_record_time_ms > 120000` | 2m | critical |
| MigrationIdChanged | `sv.migration_id` from `/info` ≠ recorded value | — | critical |
| TriggerLoopStalled | `increase(splice_trigger_iterations_total{trigger_name="ReceiveFaucetCouponTrigger"}[1h]) == 0` | 90m | warning |
| VersionBehind | running image ≠ `sv.version` for over 24 h | — | warning |
| SyncLagWarning | `time()*1000 - splice_store_last_seen_record_time_ms > 60000` | 5m | warning |
| DiskLow | node-exporter free bytes < 20 GB | — | warning |

`MigrationIdChanged` is critical on TestNet and only informational on MainNet.
It is how you learn a reset happened before your node silently falls off the
network.

## Cheap monitoring without Prometheus

```bash
~/canton-validator-toolkit/scripts/check_health.sh
```

Runs every 15 minutes via cron, checks container health, sync lag, retry
failures and disk space, with a state machine so a persistent failure alerts
once rather than every run. Telegram, Discord, Slack and PagerDuty
independently; failure alert, silence while still failing, one recovery
message.

There is also a read-only agent healthcheck that covers containers, version
drift against `/info`, sync lag, automation health, reward triggers, balance,
retry failures, disk and Scan reachability in one call:
[canton-healthcheck.sh](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/scripts/canton-healthcheck.sh).

## Scan reachability

TestNet Scan is **not public**. It answers only from onboarded validator IPs:

```bash
curl -s --max-time 5 \
  https://scan.sv-2.test.global.canton.network.digitalasset.com/api/scan/version
```

`200` from the validator host, `403 RBAC: access denied` from anywhere else.
The 403 is expected and is not an outage — re-run from the node before
reporting anything.

## Verification checklist

- `docker ps | grep canton-` shows Prometheus, Grafana and node-exporter up
- Prometheus targets `canton-validator` and `canton-participant` both `UP`
- Overview dashboard shows a CC balance and sync lag under 60 s
- a test alert reaches the contact point
- `/info` `sv.version` and `sv.migration_id` match what the node runs

## Related

- **Security Hardening** — exposure, auth, secrets, firewall
- **Backup & Recovery** — network resets and what survives them
- **Ecosystem Tooling** — explorers, scan API, third-party monitors

---

**POSTHUMAN validators** — https://posthuman.digital
