# Serving RPC from a Base Node

Most people run a Base node to serve an RPC. This page is about doing that
without giving away your hardware.

---

## 1. The block tags mean L2 things

On an L1 these tags are about finality gadgets. On Base they are about where the
data came from, and the difference is the whole safety story.

| Tag | Source | Trust |
|---|---|---|
| `pending` | Flashblocks cache, if enabled | sequencer preconfirmation, ~200 ms |
| `latest` | sequencer gossip feed | the sequencer said so; not yet on L1 |
| `safe` | batches read back from Ethereum L1 | derived, verifiable |
| `finalized` | L1 finality | as final as Ethereum |

An application doing a balance read is fine on `latest`. An application making
an irreversible decision — crediting a deposit, releasing goods, settling
off-chain — should read `safe` or `finalized`. Tell your consumers this; most
of them default to `latest` without thinking about what it means on an L2.

A node whose `latest` is at the tip and whose `safe` is frozen is serving
sequencer-trusted data and nothing else. See **Monitoring** §1.

---

## 2. Never publish the node's port

The stock `docker-compose.yml` publishes `8545`, `8546` and `7545` on
`0.0.0.0`, past `ufw`, with `debug` in the HTTP namespace list and
`--http.corsdomain="*"`. That is a development configuration.

Bind everything to loopback (see **Security Hardening**) and put a reverse proxy
in front. The proxy owns the policy:

- TLS termination
- **method allowlist by name in the JSON body** — permit `eth_*`, `net_*`,
  `web3_*`; reject `debug_*`, `txpool_*`, `miner_*`, `admin_*`
- per-source rate limits
- request body size cap and batch length cap
- separate limits for the expensive methods

`base/base` ships a reference configuration for a method-aware Base RPC proxy at
`etc/docker/proxyd/proxyd.toml`. Start there rather than writing JSON-RPC
filtering rules in nginx by hand — a path-based rule cannot see a method name,
because every JSON-RPC call is a `POST /`.

### A minimal nginx front, if you must

```nginx
server {
  listen 443 ssl http2;
  server_name base-rpc.example.com;

  client_max_body_size 256k;

  limit_req_zone $binary_remote_addr zone=rpc:10m rate=20r/s;
  limit_req zone=rpc burst=40 nodelay;

  location / {
    proxy_pass http://127.0.0.1:8545;
    proxy_http_version 1.1;
    proxy_read_timeout 30s;
    proxy_set_header Host $host;
  }
}
```

This caps body size and rate. It does **not** filter methods — nginx cannot read
the JSON body without Lua or a module. If `debug_*` must be unreachable, either
start the node without the `debug` namespace (the systemd unit in
**Binaries & systemd** does exactly that) or use `proxyd`. Removing the
namespace at the node is the stronger control: a proxy misconfiguration then
fails closed.

---

## 3. Sizing the node to its consumers

The node type decides which questions your RPC can answer, and it cannot be
changed later.

| Consumer | Minimum node type |
|---|---|
| Wallets, balance reads, sending transactions | minimal |
| dApp backend reading recent events | pruned with an explicit distance |
| Indexer, subgraph, analytics, explorer | archive |
| `eth_getProof`, `debug_executionWitness`, `debug_executePayload` | archive + proofs ExEx |

**`--full` on Base keeps 10,064 blocks — about five to six hours.** Ethereum
operators read "full node" and assume days of history. An `eth_getLogs` for
yesterday fails on a Base full node. Pick from the table above, not from the
word. Details on **Pruning & Storage**.

---

## 4. Flashblocks

Flashblocks give consumers 200 ms preconfirmations. The node subscribes to a
WebSocket stream, caches preconfirmation data, and serves it through
Flashblocks-aware RPC methods and the `pending` tag.

```bash
RETH_FB_WEBSOCKET_URL="wss://mainnet.flashblocks.base.org/ws"
```

| Network | URL |
|---|---|
| Mainnet | `wss://mainnet.flashblocks.base.org/ws` |
| Sepolia | `wss://sepolia.flashblocks.base.org/ws` |

Set it in the `.env` file and restart. With `NODE_TAG` pinned there is no source
compile; `--build` is not required for Flashblocks.

Verify:

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["pending",false],"id":1}' \
  http://127.0.0.1:8545 | jq '{number, timestamp}'

docker compose logs execution | grep -i flashblock
```

`Running in vanilla node mode (no Flashblocks URL provided)` in the startup log
means the variable never reached the container.

Two things that catch people out:

- **A successful `pending` response is not proof the stream is connected.** When
  Flashblocks are unavailable the node falls back to returning the latest block
  rather than erroring. Compare the returned number against the head.
- **The upstream WebSocket is node infrastructure, not an application API.**
  Applications must query *your* node. Pointing a browser app at
  `wss://mainnet.flashblocks.base.org/ws` is not a supported integration.

`basectl flashblocks` streams live flashblocks as NDJSON;
`basectl monitor flashblocks` is the interactive view.

---

## 5. Historical proofs

For `eth_getProof`, `debug_executionWitness` and `debug_executePayload`:

```bash
RETH_HISTORICAL_PROOFS=true
```

Most operators do not need this. The cost is real: hundreds of GB in
`<datadir>/proofs`, higher I/O throughput, and a 24–48 hour backfill on mainnet
at first start. Proofs snapshots skip the backfill — see **Snapshots**.

Behaviours worth knowing before enabling it:

- The earliest block these RPCs can answer for is the block at which the ExEx
  first started. Enabling it later does not give you earlier proofs.
- `--rpc.eth-proof-window` is ignored once the ExEx is enabled.
- Retention defaults to 28 days; `RETH_PROOFS_HISTORY_WINDOW=<blocks>` changes
  it.
- During initial sync the ExEx can fall behind far enough that it cannot catch
  up. The fix is follow mode, which keeps `base-consensus` within 512 blocks of
  it:

  ```bash
  BASE_NODE_SOURCE_L2_RPC=<trusted-l2-rpc>
  BASE_NODE_PROOFS=true
  ```

  It is working efficiently when state-root and execution durations are `0` —
  the ExEx is writing data from already-executed blocks rather than executing
  them itself.

---

## 6. Operating an RPC people depend on

- **Two nodes, not one.** A single node is a maintenance window every time
  there is a fork, and Base has one this month and another next month.
- **Load-balance on health, not round-robin.** The health check must include the
  safe-head lag, or the balancer will happily send traffic to a node that
  stopped verifying Ethereum an hour ago.
- **Publish which tag you serve.** Consumers making irreversible decisions on
  `latest` are relying on the sequencer, and most of them do not know it.
- **Watch the L1 quota, not just the node.** A rate-limited L1 provider degrades
  the safe head first and the RPC not at all, so your users see correct-looking
  answers from a node that has stopped verifying.
- **Cap batch size at the proxy.** A single JSON-RPC batch with a thousand
  `debug_traceTransaction` calls is one HTTP request and an hour of CPU.

---

## Related

- **Security Hardening** — bind to loopback before any of this matters
- **Pruning & Storage** — which questions your node can answer at all
- **Monitoring** — the safe-head lag your load balancer should be reading
