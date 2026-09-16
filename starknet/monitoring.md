# Starknet validator monitoring

A Starknet validator fails quietly. There is no slashing event and no jail
signal — a broken validator simply stops earning, and looks identical to a
healthy one until someone checks the rewards. Monitoring is therefore not
optional; it is the only thing that tells you the validator works.

## What actually costs you rewards

Ordered by how often it happens in production:

1. The node falls behind chain head → wrong block hash → attestation fails.
2. The Ethereum WebSocket endpoint dies → the node stops advancing verified
   state → same outcome.
3. The operational account runs out of STRK → transactions never land.
4. The attestation service crashes, or was restarted with a stale node URL.
5. Disk fills → the database stops writing.
6. An RPC version mismatch after a node upgrade.

Every one of these is detectable minutes before or right as it starts costing
an epoch.

## Layer 1 — node health

### Sync state

```bash
# Pathfinder
curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_syncing","params":[],"id":1}'

# Juno
curl -s -X POST http://127.0.0.1:6060/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_syncing","params":[],"id":1}'
```

`false` means at head. Anything else means you are behind — alert if the state
is not `false` for longer than one attestation window.

### Height gap against an independent source

Self-reported sync is not enough: a node can be confidently stuck. Compare
against a public RPC for the same network.

```bash
LOCAL=$(curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}' \
  | grep -o '"result":[0-9]*' | cut -d: -f2)

PUBLIC=$(curl -s -X POST https://<public-starknet-rpc>/rpc/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}' \
  | grep -o '"result":[0-9]*' | cut -d: -f2)

echo "local=$LOCAL public=$PUBLIC gap=$((PUBLIC - LOCAL))"
```

Alert on a gap above ~10 blocks, page above ~30. Mainnet blocks are seconds
apart, so a growing gap becomes a missed attestation within one window.

### Chain ID

```bash
curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_chainId","params":[],"id":1}'
```

Assert `SN_MAIN` (`0x534e5f4d41494e`) on mainnet. Cheap check, catches an
entire class of "why are there no rewards" incidents after a config change.

### Use 127.0.0.1, not localhost

For high-frequency local RPC checks always write `127.0.0.1` explicitly. With
`localhost` the resolver tries `::1` first; if the service binds only IPv4 you
pay a timeout plus fallback on every single request. This has cost real
latency in production.

## Layer 2 — attestation health

The attestation log is the primary signal. Per epoch you must see:

```
New epoch started epoch_id=…
Attestation transaction sent transaction_hash=0x…
Attestation confirmed epoch_id=…
```

Alert rules:

- No `New epoch started` for longer than one epoch duration (mainnet ~1 h) →
  the service is dead or disconnected.
- `Attestation transaction sent` without a matching `Attestation confirmed`
  within the window → treat as a failed epoch and investigate immediately.
- Any `signer`, `RPC`, `contract address` or `sequence` error → page.

```bash
docker logs --since 2h attestation 2>&1 | grep -E "New epoch|sent|confirmed|ERROR"
journalctl -u starknet-attestation --since -2h | grep -E "epoch|confirmed|ERROR"
```

### Operational account balance

The Nethermind service has `--balance-threshold` (default 100 STRK) and emits a
warning below it. Wire that warning into alerting rather than reading logs.
With the Equilibrium service, poll the balance yourself and alert at a
threshold that covers several days of fees.

## Layer 3 — onchain truth

Logs say what your software believes; the chain says what happened. Poll
`get_staker_info_v1` and alert if **unclaimed rewards stop growing** across
consecutive epochs while the service reports success.

```bash
sncast call \
  --contract-address=0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7 \
  --function=get_staker_info_v1 \
  --arguments=$STAKING_ADDRESS \
  --network=mainnet
```

This is the check that catches everything the other layers miss. It is the
definition of validator health on Starknet.

## Prometheus

Both clients and both attestation services expose Prometheus metrics.

| Component | Flag | Default in these guides |
|---|---|---|
| Pathfinder | `--monitor-address=0.0.0.0:9000` | `:9000` |
| Juno | `--metrics --metrics-port 9090` | `:9090` |
| Equilibrium attestation | `VALIDATOR_ATTESTATION_METRICS_ADDRESS=0.0.0.0:9090` | `:9091` on the host |
| Nethermind attestation | see its metrics documentation | — |

```yaml
# prometheus.yml
scrape_configs:
  - job_name: starknet-node
    static_configs:
      - targets: ['127.0.0.1:9000']
  - job_name: starknet-attestation
    static_configs:
      - targets: ['127.0.0.1:9091']
```

Bind metrics ports to the loopback interface or to a private network, and never
expose them publicly — they leak operational topology. See
[Security](/networks/starknet/guides/security).

## Layer 4 — host

- **Disk**: alert at 80%, page at 90%. Check every mounted volume, not just
  `/` — the database is usually on a separate mount.
- **Inodes**: `df -i`. A full inode table fails writes while `df -h` looks fine.
- **Open files**: both clients exceed the default 1024 limit; `Too many open
  files` in logs means the limit was never raised.
- **Container restarts**: a `restart: unless-stopped` loop hides a crash.
  Alert on restart count, not just on "container running".
- **Ethereum WebSocket**: monitor the dependency itself. Repeated
  `WebSocket stream closed` entries predict a stall.

## Minimum alert set

If you implement nothing else, implement these six:

| Alert | Condition | Severity |
|---|---|---|
| Node behind | local/public gap > 30 blocks | page |
| Node stalled | block number unchanged for 5 min | page |
| No attestation | no `Attestation confirmed` for 2 epochs | page |
| Rewards flat | unclaimed rewards unchanged across 2 epochs | page |
| Operational balance low | below N days of fees | warn |
| Disk | above 90% on the data mount | page |

## Dashboards

Third-party views of your validator, useful as an external cross-check:

- [Voyager staking dashboard](https://voyager.online/staking-dashboard)
- [Endur dashboard](https://dashboard.endur.fi/)
- [AlignedStake](https://www.aligned-stake.com/)

An external dashboard disagreeing with your own monitoring is a signal, not
noise — investigate before dismissing it.

## Reference

- [Pathfinder monitoring options](https://github.com/eqlabs/pathfinder)
- [Nethermind attestation metrics](https://nethermindeth.github.io/starknet-staking-v2/metrics)
- Starknet docs — [Staking protocol](https://docs.starknet.io/learn/protocol/staking)
