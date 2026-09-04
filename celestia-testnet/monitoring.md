# Celestia Mocha-5 Monitoring

Monitor consensus/validator and data availability as separate systems. Monitor
Blobstream only for an existing deployment whose release, v9 compatibility,
and Mocha-5 network configuration passed the blocked gate in
[the orchestrator guide](blobstream-orchestrator.md). Every sample must identify
consensus chain ID `mocha-5`, DA P2P network `mocha`, and a dedicated
`-mocha-5` home or store. Any Mocha-4 identity is a hard failure.

## Authoritative context

- [Celestia Mocha status](https://status.celestia.dev/status/mocha)
- [Celestia status and incident history](https://status.celestia.org)
- [Mocha-5 restart incident](https://status.celestia.org/incidents/nc1nkb54)
- [Mocha explorer](https://mocha.celenium.io)
- [Mocha upgrade signaling](https://mocha.celenium.io/upgrade/9?tab=signals&page=1)

Status pages provide incident context, not node-local health. Record URL and
observation time in incidents.

## Freshness and alert contract

Tune thresholds to current cadence and SLO, but keep them explicit. Suggested
starting values:

| Signal | Warning | Critical | Recovery evidence |
| --- | --- | --- | --- |
| Check execution | No sample for 2 intervals | No sample for 3 intervals | 3 consecutive fresh successful samples |
| Consensus height | No increase for 30 seconds while Mocha-5 references advance | No increase for 60 seconds | 3 advancing samples aligned with two references |
| Consensus block time | More than 30 seconds old | More than 60 seconds old | Fresh and advancing for 3 samples |
| Validator signing | Any unexpected miss or consecutive trend | Jailing risk or no signatures across multiple fresh commits | Signature in 3 fresh external Mocha-5 commits |
| DA header height | No increase for 30 seconds while references advance | No increase for 60 seconds | 3 advancing samples near references |
| DA peers/sampling | Persistent errors for 2 intervals | No peers or sampling cannot proceed | Peers and successful sampling for 3 intervals |
| Blobstream | Attestation/P2P evidence late for 2 expected windows | Stopped, no peers, wrong registration/network, or required attestations missed | Correct registration and propagation for 3 windows |
| Disk | Projected free space below 30 days at observed growth | Below 14 days or filesystem/pool error | Projection above 30 days |

Missing, stale, unparsable, Mocha-4, or single-source evidence is
**unknown/degraded**, never healthy. Alerts must include role, chain/network,
store, local/reference heights, last-success time, and runbook link. Deduplicate
and require the stated recovery evidence before clearing.

## Consensus and validator signals

Use the dedicated Mocha-5 home:

- service state, restart count, recent fatal/panic logs;
- chain ID, `catching_up`, height, block time, and peer count;
- two independent Mocha-5 height/time references;
- validator bonded/jailed status, voting power, and fresh external commit
  signatures;
- disk, latency, inodes, CPU, memory, clock, and filesystem/pool errors;
- pending CIP-10 version, tally, and activation height.

```bash
systemctl is-active celestia-appd-mocha-5.service
systemctl show celestia-appd-mocha-5.service \
  -p ActiveState -p SubState -p NRestarts
celestia-appd status --home "$MOCHA_5_HOME" | \
  jq '{network: .NodeInfo.network, height: .SyncInfo.latest_block_height, time: .SyncInfo.latest_block_time, catching_up: .SyncInfo.catching_up}'
curl --fail --silent --show-error http://127.0.0.1:26657/net_info | \
  jq '{peers: (.result.n_peers | tonumber)}'
celestia-appd query staking validator <validator-operator-address> \
  --home "$MOCHA_5_HOME" --node <trusted-mocha-5-rpc>
celestia-appd query signal upgrade \
  --home "$MOCHA_5_HOME" --node <trusted-mocha-5-rpc>
journalctl -u celestia-appd-mocha-5.service \
  --since "15 minutes ago" --no-pager
```

When Prometheus is enabled, scrape the configured consensus metrics endpoint
(official examples use loopback `26660`). Pin metric names observed from the
actual binary and treat scrape failure as unknown, not zero.

## Data availability signals

Monitor each dedicated store:

- bridge: `$HOME/.celestia-bridge-mocha-5`;
- light: `$HOME/.celestia-light-mocha-5`.

Check service/restarts, header age and height, peers, persistent sampling/header
errors, exact role/network/store, bridge archival Mocha-5 source retention,
public bridge TCP+UDP `2121`, loopback-only JSON-RPC `26658`, and capacity.

```bash
celestia header sync-state \
  --node.store "$HOME/.celestia-bridge-mocha-5"
celestia p2p info \
  --node.store "$HOME/.celestia-bridge-mocha-5"
celestia header sync-state \
  --node.store "$HOME/.celestia-light-mocha-5"
celestia p2p info \
  --node.store "$HOME/.celestia-light-mocha-5"
ss -lntup | grep -E '(:2121|:26658)'
```

celestia-node can export OTLP metrics when configured. Verify collector/export
freshness and transport errors end to end, using only metric series observed
from the pinned binary. Never merge Mocha-4 and Mocha-5 series under one label.

## Blobstream signals

The pinned celestia-app v9 source does not register the legacy `blobstream`
module or its query/transaction CLI. Do not use stale
`celestia-appd query blobstream ...` examples. For an existing, separately
approved deployment, use `$HOME/.orchestrator-mocha-5` and monitor:

- process/restart count;
- fresh Mocha-5 consensus RPC/gRPC inputs;
- registration through the exact Mocha-5 interface approved for that deployment;
- Blobstream TCP `30000` listener and peers;
- new attestations observed, signed, and propagated;
- wrong-chain, validator-set, signing, keystore, or DHT errors.

```bash
systemctl show blobstream-orchestrator-mocha-5.service \
  -p ActiveState -p SubState -p NRestarts
ss -lntp | grep ':30000'
journalctl -u blobstream-orchestrator-mocha-5.service \
  --since "30 minutes ago" --no-pager
```

A running process and listener do not prove delivery. If a current Mocha-5
registration or attestation interface is unavailable, report **blocked**, not
healthy.

## Incident workflow

1. Timestamp local and external samples and preserve relevant logs/status state.
2. Verify chain ID and store suffix first; stop on Mocha-4 reuse.
3. Assess double-sign risk before validator restart or failover.
4. Classify consensus, signing, DA, Blobstream, storage, or dependency failure.
5. Make one controlled change at a time.
6. Verify against independent Mocha-5 truth and the recovery contract.
7. Record cause, impact window, residual risk, and incident/status links.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/consensus-validators/metrics`
- `operate/data-availability/metrics`
- `operate/networks/mocha-testnet`
- `operate/blobstream/orchestrator`
- `operate/maintenance/network-upgrades`

The Blobstream compatibility warning was cross-checked against official
celestia-app tag `v9.0.6-mocha`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`, especially `app/app.go`,
`app/modules.go`, and `specs/src/state_machine_modules_v1.md` through
`state_machine_modules_v9.md`.
