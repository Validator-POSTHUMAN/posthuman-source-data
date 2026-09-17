# Canton Network DevNet — Validator Monitoring

Canton is not a Cosmos SDK chain. There are no blocks to sign, no missed-block
counter, no jail state and no slashing. Every monitoring habit built around
`missed_blocks` has to be replaced.

DevNet has one dominant failure mode, and it is not a crash. The network is
**reset roughly every three months**, and a node that misses a reset keeps
running, keeps looking alive in `docker ps`, and is no longer on the network.
Version and migration-ID drift are the primary alerts on DevNet.

## A worked example of the failure this page exists for

POSTHUMAN's own DevNet validator, checked 2026-09-18:

```
check=containers result=fail total=5 unhealthy=1
  unhealthy: splice-validator-validator-1   Up 7 weeks (unhealthy)
check=version_drift result=warn running=0.6.14 network=0.8.1
check=sync_lag result=fail lag_ms=128225261 threshold_ms=60000
check=automation result=fail unhealthy_background_services=2
  service="UpdateIngestionService"
  service="UserWalletAutomationService"
check=retry_failures result=info splice_retries_failures_sum=122127
```

Seven weeks of `Up`. A casual `docker ps` shows containers running. Only the
four checks below tell the truth.

## What "up" means on Canton

A DevNet validator is operational only when all four hold:

1. The validator container reports Docker health `healthy`.
2. Sync lag is under 60 seconds.
3. Every automation background service reports health `0`.
4. The running image version and migration ID match `/info`.

## Where the metrics come from

Every Splice node exposes Prometheus metrics on port **10013**, path
`/metrics`, enabled by default under Docker Compose. Two components publish:
the validator app (`validator:10013`) and the participant
(`participant:10013`).

The validator image ships **wget, not curl**. A `curl` exec fails with
`executable file not found in $PATH` and returns an empty body, which reads
exactly like a dead metrics port:

```bash
docker exec splice-validator-validator-1 \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -20
```

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

Prometheus must join the validator's Docker network. Note the project name: on
a DevNet host the containers are often `splice-devnet-*` rather than
`splice-validator-*`, and the network is `<project>_splice_validator`. Getting
this wrong is the usual reason the stack scrapes nothing.

### The bundled Grafana dashboards do not work under Docker Compose

The 47 dashboards in `~/.canton/<version>/splice-node/grafana-dashboards/` all
filter on a `namespace` label injected by the Kubernetes Prometheus operator.
Under Compose every panel renders empty. Use a dashboard built on `job` and
`instance`.

## Ready-made stack

```bash
git clone https://github.com/web3validator/canton-validator-toolkit ~/canton-validator-toolkit
cd ~/canton-validator-toolkit/monitoring
CANTON_NETWORK_NAME=splice-devnet docker compose up -d
```

`CANTON_NETWORK_NAME` must equal your validator's Compose project name — set
`splice-devnet` if your containers are named `splice-devnet-validator-1`.

| Component | Bind | Purpose |
|---|---|---|
| Prometheus | `localhost:9091` | scrape and store |
| Grafana | `localhost:3001` | dashboards and alert rules |
| node-exporter | `localhost:9101` | CPU, RAM, disk, network |

node-exporter uses 9101 deliberately, to avoid colliding with a system-level
node-exporter on 9100 — likely on a DevNet box that also runs other services.

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
behind. The broken node above read 128,225,261 ms.

### Automation health — the replacement for "missed blocks"

```promql
splice_automation_background_service_health != 0
```

The gauge is **0 when healthy**. All 29 series read `0` on a healthy validator;
a non-zero series names the broken automation in its `service` label. On the
broken DevNet node above it named `UpdateIngestionService` and
`UserWalletAutomationService` directly — far more useful than a container health
flag.

Reward liveness is two separate facts:

| Metric | Proves |
|---|---|
| `splice_trigger_iterations_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the polling loop is alive |
| `splice_trigger_completed_total{trigger_name="ReceiveFaucetCouponTrigger"}` | the trigger did work |

> **The completion series does not exist until the first completion.** An alert
> written as `rate(splice_trigger_completed_total{...}[1h]) == 0` never fires:
> PromQL returns *no data* for a missing series, not zero. Note also that the
> broken node's iteration counter still read 140,734 and kept climbing — a
> polling loop that spins is not a node that works. Pair it with automation
> health and sync lag.

| Metric | Use |
|---|---|
| `splice_wallet_unlocked_amulet_balance` | CC balance |
| `splice_retries_failures` | retry failures by `operation` and `error_kind`; low tens on a healthy node, 122,127 on the broken one |
| `splice_validator_scan_bft_calls_total` | BFT scan reads; failures mean the node cannot read the network |

### Version and migration drift — the DevNet alert that matters most

```bash
curl -s https://docs.dev.global.canton.network.sync.global/info | jq .
```

```json
{"network":"devnet","sv":{"migration_id":1,"serial_id":5,"version":"0.8.1"},
 "synchronizer":{"current":{"chain_id_suffix":"0","serial_id":5,"version":"0.8.1"},
 "legacy":null,"successor":null}}
```

Compare against what is actually running:

```bash
docker inspect splice-validator-validator-1 --format '{{.Config.Image}}'
```

A stale `~/.canton/current` symlink is a known trap — POSTHUMAN found one
pointing at `0.6.1` while the node ran `0.6.14`. The running image is the only
version truth.

A change in `migration_id` means a **network reset**: full redeployment, all
data deleted. See the Backup & Recovery tab.

> `https://lighthouse.devnet.cantonloop.com/api/stats` now requires an API key
> and returns `401`. Any script still polling it is broken; use `/info`.

## Alert rules

| Alert | Condition | For | Severity |
|---|---|---|---|
| MigrationIdChanged | `sv.migration_id` from `/info` ≠ recorded value | — | critical |
| AutomationUnhealthy | `splice_automation_background_service_health != 0` | 5m | critical |
| ValidatorDown | `up{job="canton-validator"} == 0` | 2m | critical |
| ParticipantUnhealthy | `daml_health_status{job="canton-participant"} != 1` | 2m | critical |
| SyncLagCritical | `time()*1000 - splice_store_last_seen_record_time_ms > 120000` | 2m | critical |
| VersionBehind | running image ≠ `sv.version` for over 24 h | — | warning |
| SyncLagWarning | `time()*1000 - splice_store_last_seen_record_time_ms > 60000` | 5m | warning |
| RetryFailuresGrowing | `increase(sum(splice_retries_failures)[1h:]) > 50` | — | warning |
| DiskLow | node-exporter free bytes < 20 GB | — | warning |

## Cheap monitoring without Prometheus

```bash
~/canton-validator-toolkit/scripts/check_health.sh
```

Runs every 15 minutes via cron; container health, sync lag, retry failures and
disk space, with a state machine so a persistent failure alerts once. Telegram,
Discord, Slack, PagerDuty.

The read-only agent healthcheck covers all four layers plus Scan reachability
in one call, and is what produced the worked example at the top of this page:
[canton-healthcheck.sh](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/scripts/canton-healthcheck.sh).

## Scan is public on DevNet

Unlike MainNet and TestNet, DevNet Scan answers from anywhere — no whitelisting
and no API key:

```bash
BASE=https://scan.sv-1.dev.global.canton.network.digitalasset.com
curl -s "$BASE/api/scan/version"
curl -s "$BASE/api/scan/v0/dso" | jq '.voting_threshold, .latest_mining_round.contract.payload.round'
```

This makes DevNet the right place to build and test any dashboard or automation
that will later read Scan on a whitelisted MainNet host.

## Verification checklist

- `docker ps | grep canton-` shows Prometheus, Grafana and node-exporter up
- Prometheus targets `canton-validator` and `canton-participant` both `UP`
- sync lag under 60 s and all automation health series at `0`
- `/info` `sv.version` and `sv.migration_id` match what the node runs
- a test alert reaches the contact point

## Related

- **Security Hardening** — exposure, auth, secrets, firewall
- **Backup & Recovery** — network resets and what survives them
- **Ecosystem Tooling** — explorers, scan API, third-party monitors

---

**POSTHUMAN validators** — https://posthuman.digital
