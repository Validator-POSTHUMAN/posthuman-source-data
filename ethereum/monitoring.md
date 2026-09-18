# Monitoring an Ethereum Node and Validator

An Ethereum validator fails quietly. There is no jail, no slash notification and
no log line that says "you are losing money" — there are simply attestations
that do not land, and a balance that drifts down instead of up. Monitoring is
not optional; it is the only way you find out.

Set this up **before** you deposit.

---

## 1. What actually matters

Ranked by how much it costs you when it breaks.

| Signal | Where from | Alert when |
|---|---|---|
| Validator attestation effectiveness | Beacon API / beaconcha.in | below ~95% over an hour |
| Missed block proposals | Beacon API / beaconcha.in | any |
| CL `is_optimistic` | `/eth/v1/node/syncing` | `true` for more than 2 minutes |
| CL sync distance | `/eth/v1/node/syncing` | more than 4 slots |
| EL syncing | `eth_syncing` | not `false` |
| Clock offset | `chrony` / node_exporter | more than 200 ms |
| Peer counts | both clients | EL < 10, CL < 20 |
| Disk free | node_exporter | below 15%, and predicted-full within 14 days |
| Disk write latency | node_exporter | p99 above ~10 ms sustained |
| Process up | systemd / node_exporter | any restart |
| Validator key count loaded | VC metrics | not equal to the expected number |

The last one catches a whole class of silent failure: a keystore that fails to
decrypt is skipped, the client starts happily, and one validator earns nothing
until someone notices.

**Balance is not a fast signal.** By the time the balance chart visibly bends,
you have missed hours of duties. Alert on effectiveness, not on balance.

---

## 2. Metrics endpoints

Everything binds to loopback. Nothing here is safe to publish — the beacon API
and the metrics ports leak enough to fingerprint your validator set.

| Process | Default metrics port (as configured in the installation guide) |
|---|---|
| Execution client | `6060` |
| Consensus client | `5054` (Lighthouse) / `8008` (Teku, Nimbus, Lodestar) / `8080` (Prysm) |
| Validator client | `5064` (Lighthouse) / `8081` (Prysm) |
| node_exporter | `9100` |

````bash
curl -s http://127.0.0.1:6060/debug/metrics/prometheus | head
curl -s http://127.0.0.1:5054/metrics | head
````

If either returns nothing, the client was started without its metrics flag.

---

## 3. Prometheus + Grafana

### node_exporter

````bash
NE_VERSION=1.9.1
cd /tmp
curl -fsSLO https://github.com/prometheus/node_exporter/releases/download/v${NE_VERSION}/node_exporter-${NE_VERSION}.linux-amd64.tar.gz
tar xzf node_exporter-${NE_VERSION}.linux-amd64.tar.gz
sudo install -m 0755 node_exporter-${NE_VERSION}.linux-amd64/node_exporter /usr/local/bin/
````

````ini
# /etc/systemd/system/node_exporter.service
[Service]
User=nobody
ExecStart=/usr/local/bin/node_exporter --web.listen-address=127.0.0.1:9100
Restart=always
````

### ethereum-metrics-exporter

[`ethpandaops/ethereum-metrics-exporter`](https://github.com/ethpandaops/ethereum-metrics-exporter)
polls the EL JSON-RPC and the Beacon API and exports a **client-independent**
metric set. This is what makes one dashboard work across Geth+Lighthouse and
Nethermind+Teku, instead of rewriting every panel when you switch clients.

````yaml
# /etc/ethereum-metrics-exporter/config.yaml
execution:
  enabled: true
  url: http://127.0.0.1:8545
  modules: [eth, net, web3]
consensus:
  enabled: true
  url: http://127.0.0.1:5052
````

### Prometheus scrape config

````yaml
scrape_configs:
  - job_name: node
    static_configs: [{ targets: ['127.0.0.1:9100'] }]
  - job_name: execution
    metrics_path: /debug/metrics/prometheus
    static_configs: [{ targets: ['127.0.0.1:6060'] }]
  - job_name: consensus
    static_configs: [{ targets: ['127.0.0.1:5054'] }]
  - job_name: validator
    static_configs: [{ targets: ['127.0.0.1:5064'] }]
  - job_name: eth-metrics-exporter
    static_configs: [{ targets: ['127.0.0.1:9090'] }]
````

### Dashboards

Start from the dashboard your client team publishes — they are maintained
against the metric names the client actually emits, which generic dashboards are
not:

- Lighthouse: `sigp/lighthouse-metrics`
- Prysm: the Grafana dashboards in the Prysm repository
- Teku: Consensys publishes a Teku dashboard
- Nimbus: dashboards ship in `nimbus-eth2/grafana`
- Geth / Nethermind / Besu / Reth: each repository ships a Grafana JSON

If you run eth-docker, `./ethd start` with the `grafana.yml` module brings up
Prometheus, Grafana and pre-wired dashboards in one command. That is the fastest
correct path and there is no shame in taking it.

---

## 4. Alert rules worth having

````yaml
groups:
  - name: ethereum
    rules:
      - alert: ExecutionNotSynced
        expr: eth_exe_sync_is_syncing == 1
        for: 10m
      - alert: ConsensusOptimistic
        expr: eth_con_sync_is_optimistic == 1
        for: 2m
      - alert: ConsensusSyncDistance
        expr: eth_con_sync_distance > 4
        for: 5m
      - alert: LowPeers
        expr: eth_con_peers_connected < 20
        for: 15m
      - alert: DiskWillFill
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 14*24*3600) < 0
        for: 1h
      - alert: ClockDrift
        expr: abs(node_timex_offset_seconds) > 0.2
        for: 5m
      - alert: ServiceRestarted
        expr: changes(process_start_time_seconds[15m]) > 0
````

Metric names differ by exporter and client version. Check the names against your
own `/metrics` output before trusting a rule — an alert with a typo in the metric
name is silently always-green, which is worse than no alert at all.

---

## 5. Monitor from outside the box, too

Everything above runs on the machine it is watching. When the machine dies, so
does the alerting. Add at least one external check:

- **[beaconcha.in](https://beaconcha.in/)** — add your validators to a watchlist
  and enable email/push alerts for offline, missed attestation and missed
  proposal. Free, and it is the community's default second opinion.
- **[Rated Network](https://www.rated.network/)** — operator-level effectiveness
  scoring; useful for comparing your performance against the network rather than
  against yesterday.
- A dead-man's-switch: have Prometheus push a heartbeat to an external service
  and alert when the heartbeat stops. This is the check that fires when the
  server is off.
- POSTHUMAN operators: wire the alert channel into the existing monitoring
  pipeline rather than into one person's email.

---

## 6. Triage — missed attestations

Work down this list, in order. It is ordered by how often each one is the
answer.

1. **Clock.** `timedatectl status`. Drift over a second breaks attestation
   timing and looks exactly like a network fault.
2. **`is_optimistic`.** `curl -s http://127.0.0.1:5052/eth/v1/node/syncing`.
   If `true`, the EL is the problem, not the VC.
3. **Engine API.** Check the CL log for `Unauthorized`, `error connecting to
   execution` or `execution engine offline`. JWT or a dead EL.
4. **Peers.** Below 20 CL peers, attestations arrive too late to be included.
   Verify the P2P port is reachable *from another host*.
5. **Disk latency.** `iostat -x 5`. A saturated or failing SSD delays block
   import, which delays attestation, which drops inclusion.
6. **VC key count.** Compare the loaded key count in the VC log against what you
   expect.
7. **Beacon node behind.** Compare head slot against beaconcha.in.
8. **Relay.** If running MEV-Boost and only *proposals* are missed, suspect the
   relay. Check that local block building fallback is enabled.

Inclusion distance tells you which half is broken: attestations that land but
late point at timing, networking or disk; attestations that never land point at
the VC or the beacon node.

---

## 7. Security baseline

Full detail is in the **Security hardening** guide. The monitoring-relevant
minimum:

- Only `30303` (EL) and `9000`/`9001` (CL) are reachable from the internet.
  `8545`, `8551`, `5052` and every metrics port stay on loopback.
- Docker publishes ports past ufw. Verify with `ss -tlnp`, not with
  `ufw status`.
- The validator keystores and the slashing protection database live on one host
  and are backed up as a pair. Restoring a keystore without its slashing
  protection database is how people get slashed during a "recovery".
- Alert on `sshd` authentication failures and on any change to the validator
  service unit.

## Sources

- [ethpandaops/ethereum-metrics-exporter](https://github.com/ethpandaops/ethereum-metrics-exporter)
- [prometheus/node_exporter](https://github.com/prometheus/node_exporter)
- [eth-docker monitoring modules](https://ethdocker.com/)
- [beaconcha.in](https://beaconcha.in/) · [Rated Network](https://www.rated.network/)
