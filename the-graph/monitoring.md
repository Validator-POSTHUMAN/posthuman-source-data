# The Graph — Indexer Monitoring

What an Indexer must watch, which metric says it, and which failures are silent
until they cost money.

The stack shipped by `graphprotocol-mainnet-docker` already contains
Prometheus, Grafana, Alertmanager, cAdvisor and node_exporter. This page is
about what to do with them.

---

## Scrape targets

| Job | Target | Serves |
| --- | --- | --- |
| `index-node-0` | `index-node-0:8040` | indexing progress, RPC health, store pool |
| `query-node-0` | `query-node-0:8040` | query latency, cache, store pool |
| `indexer-agent` | `indexer-agent:7300` | allocations, RAV redemption, operator ETH balance |
| `indexer-service` | `indexer-service:7300` | query handling, cost models, invalid receipts |
| `indexer-tap` | `indexer-tap:7300` | GraphTally receipts, RAVs, sender escrow |
| `nodeexporter` | `nodeexporter:9100` | host CPU, RAM, disk |
| `cadvisor` | `cadvisor:8080` | per-container CPU, RAM, restarts |
| `traefik` | `traefik:8082` | ingress |

Keep the target list exact. Jobs for components you do not run (e.g.
`subgraph-radio`, `autoagora`) sit permanently `down` and train the team to
ignore red, which is how a real outage gets missed.

---

## Layer 1 — the indexing stack

Metrics below are the real names exposed by the current stack; verify them
against your own `/metrics` before writing alerts.

### graph-node (`:8040`)

| Metric | Watch for |
| --- | --- |
| `deployment_head` | flat value = deployment stopped advancing |
| `deployment_synced` | drops to 0 when a deployment falls behind |
| `deployment_failed` / `deployment_status` | a failed deployment still answers `/status` but stops earning |
| `ethereum_chain_head_number` | flat = the RPC, not the subgraph, is stuck |
| `deployment_eth_rpc_errors`, `eth_rpc_errors` | archive-RPC degradation, the most common root cause |
| `query_execution_time` | p95 above a few seconds fails the gateway's quality bar |
| `store_connection_wait_time_ms`, `store_connection_error_count` | PostgreSQL pool exhaustion |

Alert on **lag**, not on absolute height:
`ethereum_chain_head_number − deployment_head` per deployment.

### indexer-agent (`:7300`)

| Metric | Watch for |
| --- | --- |
| `indexer_agent_operator_eth_balance_eip155:42161` | **the classic silent failure** — out of gas on Arbitrum One means no allocation, no POI, no rewards. Alert well above zero. |
| `indexer_agent_rav_v2_redeems_failed_eip155:42161` | unredeemed query fees |
| `indexer_agent_rav_v2_exchanges_invalid_eip155:42161` | receipt/aggregator mismatch |
| `indexer_error` | agent-level errors by class |

### indexer-service (`:7300`)

| Metric | Watch for |
| --- | --- |
| `indexer_query_handler_seconds` | served-query latency |
| `indexer_tap_invalid_total` | rejected receipts — non-zero means paid queries are being refused |
| `indexer_cost_model_batch_seconds` | cost-model evaluation cost |

### indexer-tap (`:7300`)

| Metric | Watch for |
| --- | --- |
| `tap_receipts_received_total` | flat = gateway stopped sending traffic |
| `tap_sender_denied` | a denied sender earns nothing; check sender allow-list after any billing change |
| `tap_unaggregated_fees_grt_total_by_version` | growth without RAVs = aggregation broken |
| `tap_pending_rav_grt_total` | fees earned but not yet redeemable |
| `tap_sender_escrow_balance_grt_total` | the payer's escrow running dry |

---

## Layer 2 — external truth

Container metrics prove your processes are alive. They do not prove the
gateway can reach you. Check from **outside the host**:

```bash
# public endpoint reachable through DNS/CDN/proxy, not just locally
curl -s -o /dev/null -w '%{http_code}\n' https://<your-index-host>/
curl -s https://<your-index-host>/healthz
curl -s https://<your-index-host>/status
```

- `/` and `/healthz` — HTTP 200, healthy database and graph-node checks.
- `/status` — every deployment `synced` and `healthy` at chain head.
- Public DNS resolution, TLS validity and certificate expiry.

A DNS record removed by mistake, an expired origin certificate, or a proxy
misconfiguration takes an Indexer off the network while every local container
stays green. Run this probe from a **different host** on a timer and alert
after two consecutive failures.

---

## Layer 3 — protocol and economics

These are not in Prometheus. Poll them on a schedule.

### Allocations and pending actions

```bash
docker exec cli graph indexer status --network arbitrum-one
docker exec cli graph indexer allocations get all --network arbitrum-one
docker exec cli graph indexer actions get all --network arbitrum-one
```

Alert when: an allocation is missing, an action is stuck in
`queued`/`approved`/`pending` rather than a terminal state, or endpoint checks
are not `up`.

### POI staleness — Horizon

Under Graph Horizon allocations may stay open indefinitely, but a POI must be
submitted before `maxPOIStaleness` (**28 days**). Miss it and any network
participant can force-close the allocation; the uncollected rewards are gone
with **no retroactive recovery**. Track the age of each allocation's last POI
submission and alert with days of margin, not hours.

### Rewards eligibility (REO, GIP-0079)

Indexing rewards additionally require gateway-observed activity:

- active on **5+ days** in a rolling 28-day window,
- at least **one qualifying query** on each counted day,
- qualifying = HTTP 200, under 5,000 ms, under 50,000 blocks behind chain head.

Eligibility is renewed daily and lasts 14 days by default. Current criteria:
<https://hub.thegraph.foundation/reo/>

Two traps:

1. `getRewards()` does **not** account for eligibility and can overstate a
   claim. Watch `RewardsDeniedDueToEligibility` outcomes instead.
2. If the oracle itself has not updated within its timeout, the contract is in
   **fail-open** mode and returns `isEligible=true` for everyone — including
   addresses that never qualified. `isEligible=true` alone is not proof.

Only the gateway holds the query record, so local health checks are necessary
but never sufficient.

### Network subgraph

Self-hosted network-subgraph data drives allocation decisions. If that
deployment fails or lags, the agent reasons from stale state. Check its health
alongside the revenue-earning deployments — a `health: failed` network
subgraph that still answers queries is easy to miss.

---

## Alert routing

- Route to a channel a human actually reads; a silenced channel is not
  monitoring.
- Keep the alert credential out of the config file. Alertmanager supports
  `bot_token_file:`; the file should be mode `0600` and owned by the container
  UID.
- Test the delivery path with a synthetic alert and confirm the notification
  counter increases and the failure counter does not. "Config reloaded" is not
  proof of delivery.
- Alert after two consecutive failures for external probes, immediately for
  operator-balance and POI-staleness alerts.

---

## Minimum viable alert set

1. Any scrape target down.
2. Deployment lag above threshold, or `deployment_synced` = 0.
3. Public endpoint failing from an external host, twice in a row.
4. Operator wallet ETH balance below a funding floor.
5. `tap_sender_denied` non-zero, or `indexer_tap_invalid_total` rising.
6. Allocation POI age approaching 28 days.
7. Host disk above 85%, PostgreSQL container down or restarting.
8. TLS certificate expiring within 14 days.

---

## Related

- [Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide)
- [Security hardening](https://nodes.posthuman.digital/chains/the-graph?tab=security-hardening)
- [Tooling](https://nodes.posthuman.digital/chains/the-graph?tab=tooling)
- Official: <https://thegraph.com/docs/en/indexing/tooling/graph-node/>
