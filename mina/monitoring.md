# Mina Node Monitoring

Three layers, and you need all three. "The process is up" tells you almost
nothing on Mina: a daemon can be running, peered and completely useless because
it lost its producer key or drifted off the chain you meant to join.

1. **Node health** — synced, on the right chain, peered, keeping pace.
2. **Producer health** — key loaded, slots won, blocks actually landing.
3. **Host capacity** — RAM headroom, CPU contention, disk, clock.

## 1. `mina client status`

The single most informative command. Alert on the fields, not the exit code.

````bash
mina client status
mina client status --json | jq          # for scripting
docker exec mina mina client status     # container
````

| Field | Healthy | Meaning when it is not |
|---|---|---|
| `Sync status` | `Synced` | `Bootstrap`/`Catchup` after a restart is normal; `Offline` means no peer messages for ~24 min |
| `Chain id` | `0718f61a…3886` (mainnet) | you are on a different network than you think |
| `Block height` | equals `Max observed block length` | catchup in progress, or a stall |
| `Peers` | non-trivial | connectivity or firewall problem |
| `Block producers running` | `1 (B62q…)` | `0` on a producer means the key never loaded |
| `Next block will be produced in` | present when you have won slots | absent is normal with small stake |

During catchup the block height stays flat and then jumps. That is the designed
behaviour, not a stall — see **Troubleshooting** before restarting anything.

## 2. Prometheus metrics

Start the daemon with a metrics port:

````
--metrics-port 6060
--libp2p-metrics-port 6061      # optional, libp2p-level metrics
````

````bash
curl -s http://127.0.0.1:6060/metrics | head
````

Neither port is served by default and neither belongs on a public interface.
Bind them to loopback or a private interface and scrape from there.

The metric namespace is `Coda` (Mina's former name). Series worth alerting on:

| Metric | Use |
|---|---|
| `Coda_Transition_frontier_best_tip_block_height` | height; alert on "no increase for N minutes" |
| `Coda_Transition_frontier_max_blocklength_observed` | network height; alert on divergence from your best tip |
| `Coda_Network_peers` | peer count floor |
| `Coda_Block_producer_slots_won` | slots the VRF gave you |
| `Coda_Block_producer_blocks_produced` | blocks you actually submitted |
| `Coda_Transition_frontier_slot_fill_rate` | how full the chain's slots are — network-wide health |
| `Coda_Transition_frontier_empty_blocks_at_best_tip` | rising values suggest SNARK work is not being bought |
| `Coda_Bootstrap_bootstrap_time_ms` | how long restarts really cost you |

The pair that matters most is `slots_won` versus `blocks_produced`. Equal is
healthy. A gap is the only direct, node-side evidence that you are losing blocks
you were entitled to — usually because the host cannot build and gossip the block
inside its 90-second slot.

## 3. GraphQL health check

The daemon's GraphQL server (`3085`, or the read-only limited port) answers the
same questions as the CLI and is easier to poll:

````bash
curl -s http://127.0.0.1:3085/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ syncStatus daemonStatus { blockchainLength chainId numAccounts peers { host } consensusTimeNow { epoch slot } } }"}' | jq
````

Compare your node against an independent endpoint — your own node's opinion of
the chain is not evidence:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { blockchainLength chainId } }"}' | jq
````

A height that matches an external node and a chain ID that matches the release
are the two checks that catch the failures nobody notices for days.

## 4. The weekly self-stop is a feature

The daemon stops itself after `--stop-time` hours — **default 168** — plus a
random 0–9 hours (`--stop-time-interval`), and only when no slot was won in the
hour after that point. Consequences:

- With `Restart=always` (systemd) or `--restart=always` (Docker), this is a
  rolling weekly restart. Expect it, and do not treat the restart as an
  incident.
- **Without** a restart policy, your node simply disappears about once a week.
  This is the most common cause of "my node was fine and then it was gone".
- A restart counter that never increases over several weeks is itself worth a
  look — it usually means the flags you think are in effect are not.

## 5. Logs

| File (under `~/.mina-config/`) | Contents | Limit |
|---|---|---|
| `mina.log` | main daemon log | 10 MiB × 50 files |
| `mina-best-tip.log` | best-tip transitions, useful around hard forks | 5 MiB |
| `mina-prover.log` | prover memory and batch sizes | 128 MiB |
| `mina-verifier.log` | verifier memory and batch sizes | 128 MiB |

````bash
journalctl --user -u mina -n 1000 -f     # systemd
docker logs --follow mina                # docker
tail -f ~/.mina-config/mina.log          # direct
````

Use `--log-json` if you ship logs to a collector. Messages about the prover or
verifier being killed and restarted periodically are **normal** and are not an
incident unless they end in a fatal error.

Export a bundle for a bug report:

````bash
mina client export-logs -tarfile incident-$(date +%Y%m%dT%H%M%SZ)
mina client export-local-logs -tarfile incident-offline   # daemon not running
````

After a crash, `~/.mina-config/` holds a crash report — `crash_summary.json`,
`mina_status.json`, `mina_short.log`, `daemon.json`. Only the most recent one is
kept, so collect it before the next crash overwrites it.

## 6. Delegation-program uptime

If you participate in the Mina Foundation Delegation Program, uptime is measured
by the SNARK-work-based system built into the daemon, in 20-minute windows over
a rolling 90 days. Monitor it as a first-class signal, because a node that is
"up" but not submitting scores zero:

- Official leaderboard: <https://uptime.minaprotocol.com>
- Community leaderboard: <https://minataur.net/uptime>

Setup and the flags involved are in the **Delegation program** guide.

## 7. External verification

Your node cannot tell you that a block was accepted by the network. Confirm
production from outside:

- `https://minascan.io/mainnet/validator/<YOUR_PUBLIC_KEY>/delegations`
- `https://minataur.net/account/<YOUR_PUBLIC_KEY>`

For a definitive stake figure, export the staking ledger from your own synced
node rather than reading an explorer — see **Block producer**.

## 8. Host capacity

- **RAM** is the resource Mina runs out of. `Fatal error: out of memory` under
  load is a known failure mode; watch free memory and swap, not just averages.
- **CPU contention** matters more than utilisation. A SNARK worker sharing a
  host with a producer is the classic way to lose blocks while every graph looks
  fine.
- **Clock.** NTP must be running. Slot timing is consensus-critical.
- **Disk.** Chain data is modest, but log files, crash reports and — on archive
  nodes — PostgreSQL are not.

## Alert checklist

| Condition | Severity |
|---|---|
| `Sync status` not `Synced` for > 30 min | page |
| `Chain id` ≠ expected | page |
| best tip height flat > 10 min while an external node advances | page |
| `Block producers running` = 0 on a producer | page |
| `slots_won` > `blocks_produced` (new gap) | page |
| peers below floor | warn |
| container/unit restart loop (repeated restarts, not the weekly one) | warn |
| uptime leaderboard score dropping | warn |
| host memory headroom below threshold | warn |

## Related guides

- **Troubleshooting** — what each unhealthy state actually means
- **Block producer** — proving production and stake
- **Security hardening** — keeping metrics and GraphQL ports private
- **Delegation program** — uptime scoring

## Sources

- [docs.minaprotocol.com — logging](https://docs.minaprotocol.com/node-operators/validator-node/logging)
- [docs.minaprotocol.com — querying data](https://docs.minaprotocol.com/node-operators/validator-node/querying-data)
- [docs.minaprotocol.com — troubleshooting](https://docs.minaprotocol.com/node-operators/troubleshooting)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
- [MinaProtocol/mina — `mina_metrics.ml`](https://github.com/MinaProtocol/mina/blob/4.0.0-mainnet-mesa/src/lib/mina_metrics/prometheus_metrics/mina_metrics.ml)
