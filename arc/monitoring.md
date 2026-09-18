# Arc Network mainnet — monitoring

## The failure that looks healthy

An Arc node has no consensus role, so nothing it does can fail loudly. Both
processes can be `active (running)`, `eth_blockNumber` can answer instantly,
and the answer can be forty thousand blocks old.

A follow node depends entirely on relay endpoints it reaches over the internet.
When they stop answering, the node does not crash — it stops advancing.

**Alert on block-number progress and on agreement with an independent RPC.
Never on the process being up.**

## The four checks

| Check | How | Alert when |
|---|---|---|
| Height advancing | `eth_blockNumber` twice, 30 s apart | unchanged |
| Agreement | local head vs `rpc.mainnet.arc.io`, **by hash** | differs |
| Version | `arc_getVersion` local vs official RPC | behind the fleet |
| Both layers | `systemctl is-active arc-execution arc-consensus` | either not active |

```sh
LOCAL=http://127.0.0.1:8545
REF=https://rpc.mainnet.arc.io

cast block-number --rpc-url "$LOCAL"
cast block-number --rpc-url "$REF"

# agreement by hash at a common height, which is the check that matters
H=$(cast block-number --rpc-url "$LOCAL")
cast block --rpc-url "$LOCAL" "$H" --json | jq -r .hash
cast block --rpc-url "$REF"   "$H" --json | jq -r .hash
```

Two chains can sit at the same block number. Only the hash settles it.

Sample the height **twice**. One reading cannot distinguish "advancing" from
"stopped a second ago" — the single most common way a monitoring check reports
a frozen node as healthy.

Use `127.0.0.1` rather than `localhost` for a high-frequency check. `localhost`
resolves `::1` first; against a service bound to IPv4 only, every request pays
an IPv6 timeout before falling back, around 200 ms each.

## Version, from the chain

```sh
curl -s -X POST https://rpc.mainnet.arc.io -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'
```

On 2026-09-18 this returned `v0.8.0`, commit `5abb64c1…`. Running the same call
against your own node and comparing is more reliable than any documentation
table — Circle's `node-requirements` Versions table still lists only Arc
Testnet.

## Prometheus and Grafana

Both layers expose metrics. The EL serves them at `/`, the CL at `/metrics` —
different paths, which is the detail that produces an empty dashboard.

```sh
curl -s http://127.0.0.1:9001 | head
curl -s http://127.0.0.1:29000/metrics | head
```

Start flags:

```sh
# execution layer
--metrics 127.0.0.1:9001
# consensus layer
--metrics 127.0.0.1:29000
```

`prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "arc_execution"
    metrics_path: "/"
    static_configs:
      - targets: ["127.0.0.1:9001"]
        labels: { client_name: "reth", client_type: "execution" }

  - job_name: "arc_consensus"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["127.0.0.1:29000"]
        labels: { client_name: "malachite", client_type: "consensus" }
```

Circle's example uses `scrape_interval: 1s`. That is a demo value. It produces
a large amount of data for a follow node and buys nothing on a chain whose
sub-second finality you are observing rather than participating in. 15 s is a
reasonable default; go lower only with a reason.

The `arc-node` repository ships Grafana dashboards at
`deployments/monitoring/config-grafana/provisioning/dashboards-data`.

## Bind monitoring to loopback

Circle's Compose example runs Prometheus on `127.0.0.1:9090`, Grafana on
`127.0.0.1:3000`, and reaches them over SSH port forwarding:

```sh
ssh -N -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 user@host
```

That is the right shape. Its Grafana credentials are `admin`/`admin`, which is
fine only for as long as nothing can reach it. Change them before any reverse
proxy or shared access, not after.

If Prometheus restarts with a permissions error about `queries.active`:

```sh
sudo chown -R 65534:65534 "$ARC_MONITORING"/prometheus-data
docker compose restart prometheus
```

## Host metrics

`node_exporter`, and alert on:

- **disk** — a 1 TB baseline and a chain that only grows;
- **disk write latency** — the reason
  `--execution-persistence-backpressure` exists; if execution outruns disk
  writes, EL memory grows. Lower
  `--execution-persistence-backpressure-threshold` from its default of `16` if
  you see memory pressure;
- **memory** — Circle notes the EL can surge during startup or a long
  catch-up on some hardware.

## Security hardening

The hardening checklist for this network lives alongside this section: ports,
namespaces, the Engine API, the consensus-layer private key, and the supply
chain around `arcup`. Read it before exposing anything.

## What not to alert on

- The process being up. It is up in every failure described here.
- Peer count on a follow node — it uses `--disable-discovery` and has no peers
  by design.
- A single relay endpoint failing. Three are configured for exactly that
  reason; alert when the **head stops moving**, not when one endpoint blips.
- `arc_getCertificate` latency against a cached edge. Certificates for
  finalized heights are immutable and safe to cache; a fast answer may be the
  cache, not your node.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
