# Avalanche Monitoring Baseline

> Reviewed on 2026-09-14. Collect from a private network or secured proxy;
> never expose the Prometheus or Grafana setup described here directly to the
> public internet. Source: [official monitoring security warning](https://build.avax.network/docs/nodes/maintain/monitoring#caveat-security).

## Collection

Avalanche's supported stack uses Prometheus for storage, `node_exporter` for
host metrics, AvalancheGo's `/ext/metrics` endpoint for node metrics, and
Grafana with the published Avalanche dashboards. Source: [Monitoring](https://build.avax.network/docs/nodes/maintain/monitoring).

Use the unfiltered Health RPC for the primary service check; HTTP 200 means
healthy and HTTP 503 means unhealthy. Filtered health responses cover only a
subset and must not replace the aggregate check. Source: [Health RPC](https://build.avax.network/docs/rpcs/other/health-rpc#get-request).

```bash
API=http://127.0.0.1:9650
curl -fsS "$API/ext/health" | jq '{healthy, checks}'
curl -fsS "$API/ext/metrics" >/dev/null
```

## Required alerts

Start with the official priority alerts below; thresholds are operational
baselines and should be tuned against the node's normal behavior. Source for
every metric and threshold: [Key Metrics & Alerts](https://build.avax.network/docs/nodes/maintain/recommended-metrics).

| Signal | Baseline alert |
|---|---|
| Snowman query success ratio from `polls_successful` and `polls_failed` | warn below 95%; page below 90% |
| `avalanche_resource_tracker_disk_available_percentage` | warn below 20%; page below 10% |
| `avalanche_evm_eth_chain_block_bad_count{chain="C"}` | page on any sustained increase |
| `avalanche_stake_percent_connected{chain="<chain>"}` | page below `0.8` |
| `avalanche_health_checks_failing{check="health",tag="all"}` | page when non-zero persists |
| `avalanche_snowman_blks_processing{chain="<chain>"}` | alert on a sustained rise |
| `avalanche_benchlist_benched_num{chain="<chain>"}` | page above one for ten minutes |
| `avalanche_resource_tracker_cpu_usage` plus host CPU | alert on sustained saturation |

Also alert on service inactivity, restart-count growth, any P/X/C bootstrap
regression, stale P-Chain or C-Chain height, TCP `9651` becoming unreachable
from outside, validator disappearance/disconnection, and validation-period
expiry. Sources: [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc), [validator requirements](https://build.avax.network/docs/primary-network/validate/node-validator#requirements), [validator verification](https://build.avax.network/docs/primary-network/validate/node-validator#verify-validator-status).

## External validator truth

`info.uptime` is the node API's authoritative stake-weighted view of how peers
observe this node. Check the P-Chain validator record independently as well;
local process health alone is not evidence that the network can reach the
validator. Sources: [Info RPC uptime](https://build.avax.network/docs/rpcs/other/info-rpc#infouptime), [P-Chain current validators](https://build.avax.network/docs/rpcs/p-chain#platformgetcurrentvalidators).

## Helicon observability

AvalancheGo v1.15.0 adds C-Chain SAE metrics for last executed and last settled
height, execution queue duration, block execution duration, queued blocks,
queued gas, and execution gas totals. Source: [v1.15.0 metrics changes](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#metrics).

Add dashboards and alerts for at least:

```text
avalanche_evm_transition_sae_last_executed_height
avalanche_evm_transition_sae_last_settled_height
avalanche_evm_transition_sae_execution_queue_duration_seconds
avalanche_evm_transition_sae_execute_block_duration_seconds
avalanche_evm_transition_sae_execution_queue_blocks
avalanche_evm_transition_sae_execution_queue_gas_limit
```

Alert on a persistent gap between executed and settled heights or sustained
queue growth relative to the node's post-activation baseline; the release
publishes the metrics but does not prescribe universal thresholds. Source:
[v1.15.0 release metrics](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#metrics).

## Minimum dashboard

Keep one operator dashboard with service/restarts, P/X/C bootstrap, aggregate
health, P- and C-height progression, peers, observed uptime, connected stake,
query success ratio, disk, CPU, memory, filesystem I/O, network I/O, and the
Helicon execution/settlement queue. Sources: [official monitoring stack](https://build.avax.network/docs/nodes/maintain/monitoring), [recommended metrics](https://build.avax.network/docs/nodes/maintain/recommended-metrics), [v1.15.0 metrics](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0#metrics).
