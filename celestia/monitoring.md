# Celestia Mainnet Monitoring

Monitor consensus/validator and data availability as separate systems. Monitor
Blobstream only for an existing deployment whose release, compatibility, and
network configuration have passed the blocked gate in
[the orchestrator guide](blobstream-orchestrator.md). A healthy process is not
enough: each role needs fresh external network evidence.

## Authoritative context

- [Celestia mainnet status](https://status.celestia.dev/status/mainnet)
- [Celestia status and incident history](https://status.celestia.org)
- [Mainnet explorer](https://celenium.io)
- [Mainnet upgrade signaling](https://celenium.io/upgrade/9?tab=signals&page=1)

Status pages provide incident context, not node-local health. Record the URL and
observation time in every incident.

## Freshness and alert contract

Tune thresholds to the current observed block cadence and operational SLO, but
make them explicit. A conservative starting contract is:

| Signal | Warning | Critical | Recovery evidence |
| --- | --- | --- | --- |
| Check execution | No sample for 2 intervals | No sample for 3 intervals | 3 consecutive fresh successful samples |
| Consensus height | No increase for 30 seconds while independent references advance | No increase for 60 seconds | 3 advancing samples aligned with two references |
| Consensus block time | More than 30 seconds old | More than 60 seconds old | Fresh and advancing for 3 samples |
| Validator signing | Any unexpected miss or consecutive-miss trend | Jailing risk or no signatures across multiple fresh commits | Validator signature seen in 3 fresh external commits |
| DA header height | No increase for 30 seconds while references advance | No increase for 60 seconds | 3 advancing samples near references |
| DA peers/sampling | Persistent peer or sampling errors for 2 intervals | No peers or sampling cannot proceed | Peers present and successful sampling across 3 intervals |
| Blobstream | Attestation or P2P evidence late for 2 expected windows | Service stopped, no peers, wrong registration, or required attestations missed | Registration matches and new attestations propagate for 3 windows |
| Disk | Projected free space below 30 days at observed growth | Below 14 days or filesystem/pool error | Capacity restored and projection above 30 days |

Treat missing, stale, unparsable, or single-source data as **unknown/degraded**,
not healthy. Include role, network, node height, reference heights, last-success
time, and runbook link in every alert. Deduplicate repeated alerts and send a
recovery only after the stated evidence is met.

## Consensus and validator signals

Collect independently:

- service state, restart count, and recent fatal/panic logs;
- local chain ID, `catching_up`, height, and latest block time;
- height and block time from at least two independent mainnet references;
- validator jailed/bonded status, voting power, and signatures in fresh external
  commits;
- consensus peers;
- disk capacity, latency, inode use, CPU, memory, clock, and filesystem/pool
  errors;
- pending CIP-10 upgrade version, tally, and activation height.

```bash
systemctl is-active celestia-appd.service
systemctl show celestia-appd.service \
  -p ActiveState -p SubState -p NRestarts
celestia-appd status | \
  jq '{network: .NodeInfo.network, height: .SyncInfo.latest_block_height, time: .SyncInfo.latest_block_time, catching_up: .SyncInfo.catching_up}'
curl --fail --silent --show-error http://127.0.0.1:26657/net_info | \
  jq '{peers: (.result.n_peers | tonumber)}'
celestia-appd query staking validator <validator-operator-address> \
  --node <trusted-mainnet-rpc>
celestia-appd query signal upgrade --node <trusted-mainnet-rpc>
journalctl -u celestia-appd.service --since "15 minutes ago" --no-pager
```

When Prometheus is enabled in `config.toml`, scrape the configured consensus
metrics endpoint (official examples use loopback `26660`). Discover and pin the
actual metric names exposed by the deployed binary; do not invent names or
silently treat a failed scrape as zero.

## Data availability signals

Monitor bridge and light stores separately:

- service state and restart count;
- header sync state and header age versus independent references;
- peer presence and persistent sampling/header/core connection errors;
- role, network, and exact store path;
- bridge archival consensus source freshness and retention;
- bridge public TCP+UDP `2121` reachability;
- JSON-RPC `26658` remaining loopback-only unless intentionally protected;
- store growth and projected exhaustion.

```bash
celestia header sync-state --node.store "$HOME/.celestia-bridge"
celestia p2p info --node.store "$HOME/.celestia-bridge"
celestia header sync-state --node.store "$HOME/.celestia-light"
celestia p2p info --node.store "$HOME/.celestia-light"
ss -lntup | grep -E '(:2121|:26658)'
```

celestia-node can export OTLP metrics when configured. Verify the local
collector/export path, scrape timestamp, and transport errors end to end. Use
only metric series observed from the pinned binary and collector configuration.

## Blobstream signals

The pinned celestia-app v9 source does not register the legacy `blobstream`
module or its query/transaction CLI. Do not use the stale
`celestia-appd query blobstream ...` examples that remain in the docs. For an
existing, separately approved legacy deployment, monitor:

- orchestrator process and restart count;
- freshness of consensus RPC/gRPC inputs;
- registration through the exact interface approved for that deployment;
- Blobstream P2P listener on TCP `30000` and peer connectivity;
- new attestations observed, signed, and propagated within expected windows;
- repeated validator-set, signing, keystore, or DHT errors.

```bash
systemctl show blobstream-orchestrator.service \
  -p ActiveState -p SubState -p NRestarts
ss -lntp | grep ':30000'
journalctl -u blobstream-orchestrator.service \
  --since "30 minutes ago" --no-pager
```

A listener and running process do not prove attestation delivery. If the
approved registration or attestation interface is unavailable, report
**blocked**, not healthy.

## Incident workflow

1. Timestamp local and external samples; preserve relevant logs and status-page
   state.
2. Assess validator slashing/double-sign risk before any restart or failover.
3. Classify the failing plane: consensus, validator signing, DA, Blobstream,
   host/storage, or external dependency.
4. Prefer read-only diagnosis and one controlled change at a time.
5. Verify recovery against independent network truth and the recovery contract.
6. Record root cause, impact window, residual risk, and links to the status or
   incident record.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/consensus-validators/metrics`
- `operate/data-availability/metrics`
- `operate/networks/mainnet-beta`
- `operate/blobstream/orchestrator`
- `operate/maintenance/network-upgrades`

The Blobstream compatibility warning was cross-checked against official
celestia-app tag `v9.0.6`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`, especially `app/app.go`,
`app/modules.go`, and `specs/src/state_machine_modules_v1.md` through
`state_machine_modules_v9.md`.
