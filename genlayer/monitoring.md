# GenLayer — Monitoring

A GenLayer node is a Docker Compose stack, not a single daemon, and its health is
not one number. Three things can be independently broken while the container
still reports itself as up: the ops server, the JSON-RPC server, and the LLM
provider the node needs in order to execute Intelligent Contracts at all.

There is no missed-block counter, no signing window and no jail state. What you
watch instead is: the stack is running, the ops endpoint is healthy, the chain
height is advancing and tracking the upstream RPC, the LLM provider answers, and
the node has not silently dropped out of validator mode.

Every command below is the reviewed
[installation guide](install-guide.md)'s own, on the default ports.

---

## 1. The signals worth an alert

| Signal | Check | Page when |
|---|---|---|
| Stack running | `docker compose ps` | any service not `running` |
| Ops health | `GET 127.0.0.1:9153/health` | non-2xx, or no answer |
| RPC alive | `gen_dbg_ping` on `127.0.0.1:9151` | no answer |
| Height advancing | `eth_blockNumber` on `127.0.0.1:9151` | unchanged across three polls |
| Not falling behind | local height vs `rpc-asimov.genlayer.com` | gap widening over three polls |
| Mode | node log for `SWITCHING to FULL MODE` | you intended to run a validator |
| LLM provider | provider account or a node-side probe | provider errors in the log |

Five minutes is a reasonable interval. `eth_blockNumber` is the liveness signal;
`/health` alone is not, for the same reason a green HTTP healthcheck is never
proof of consensus participation anywhere.

---

## 2. Is the stack actually up

```bash
cd ~/genlayer-node    # wherever your compose file lives
docker compose ps
```

Alert on any service that is not `running`, and separately on restart counts:

```bash
docker inspect -f '{{.Name}} restarts={{.RestartCount}}' \
  $(docker compose ps -q) 2>/dev/null
```

A climbing `RestartCount` is the cheapest crash-loop detector available. A
healthy stack sits at a fixed number. The troubleshooting guide's case G is worth
knowing here: a removed network can leave an old `genlayer-node` container
attached, so a stack that looks recreated may still be the previous one — compare
container IDs after any recreate, not just the service list.

---

## 3. Ops health and RPC

```bash
curl -fsS http://127.0.0.1:9153/health
```

```bash
curl -fsS -X POST http://127.0.0.1:9151 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"gen_dbg_ping","params":[],"id":1}'
```

Both of these can answer while the node is making no progress, which is why the
next one exists.

---

## 4. Height, and the gap to upstream

Local height:

```bash
curl -fsS -X POST http://127.0.0.1:9151 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  | jq -r '.result'
```

Upstream height, for comparison:

```bash
curl -fsS -X POST https://rpc-asimov.genlayer.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  | jq -r '.result'
```

Both return hex. Alert on two distinct conditions, because they have different
causes:

- **local height unchanged** across three polls — the node is stalled; look at
  the container logs and at the LLM provider before restarting anything.
- **gap to upstream widening** — the node is running but losing ground, which on
  this chain usually means contract execution is slow or failing rather than that
  networking is broken.

A one-off small gap is normal. Compare the *trend*, not a single reading.

Confirm once, at setup time, that you are pointed at the network you think you
are:

```bash
curl -fsS -X POST https://rpc-asimov.genlayer.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# Asimov answers {"jsonrpc":"2.0","result":"0x107d","id":1}
```

---

## 5. The signal nobody expects: mode

A node configured for validator mode with no `ValidatorWalletAddress` does not
fail. It prints

```
SWITCHING to FULL MODE due to missing addresses
```

and carries on as a full node — correct behaviour if that is what you wanted, and
an invisible outage of your validator if it is not. Grep for it on every start:

```bash
docker logs genlayer-node 2>&1 | grep -F 'SWITCHING to FULL MODE' | tail -3
```

Make this a startup assertion rather than a dashboard panel. It is exactly the
kind of degradation that is only ever noticed weeks later.

---

## 6. The LLM provider is part of the node

GenLayer validators execute Intelligent Contracts through an LLM provider, so the
provider is a dependency with its own failure modes — an expired key, an
exhausted balance, a rate limit, a model withdrawn by the provider. None of them
look like a blockchain problem.

Watch two things:

- **the node's own complaints** — the troubleshooting guide's case E,
  `No LLM provider is configured`, and any provider HTTP error in the container
  logs. Alert on the error text, not on a status code you have to infer.
- **the provider account** — balance or credit, on whatever schedule your
  provider supports. This is a spend alert, and it is the one that stops a node
  quietly at an arbitrary hour.

```bash
docker logs --since 15m genlayer-node 2>&1 \
  | grep -Ei 'llm|provider|unauthorized|rate.?limit|quota' | tail -20
```

---

## 7. Disk

The node's database lives under the compose project's `data/node`. Alert at 80%
and 90% on the filesystem holding it, and note that the documented resync path
is `docker compose down`, remove `data/node`, recreate — which needs room for a
fresh database and takes as long as a sync.

---

## 8. A minimal watchdog

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT=${1:-$HOME/genlayer-node}
RPC=http://127.0.0.1:9151
OPS=http://127.0.0.1:9153
UPSTREAM=https://rpc-asimov.genlayer.com
STATE=/var/lib/genlayer-watch/height
mkdir -p "$(dirname "$STATE")"

fail() { printf 'GENLAYER ALERT: %s\n' "$*" >&2; exit 1; }
rpc() { curl -fsS --max-time 10 -X POST "$1" -H 'Content-Type: application/json' \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | jq -r '.result'; }

cd "$PROJECT"
docker compose ps --status running --quiet | grep -q . || fail "no running services"
curl -fsS --max-time 10 "$OPS/health" >/dev/null || fail "ops /health not answering"

local_hex=$(rpc "$RPC") || fail "local RPC not answering"
up_hex=$(rpc "$UPSTREAM") || up_hex=
local_dec=$((local_hex))
previous=$(cat "$STATE" 2>/dev/null || echo 0)
printf '%s\n' "$local_dec" >"$STATE"

[ "$local_dec" -gt "$previous" ] || fail "height stuck at $local_dec"
if [ -n "$up_hex" ]; then
  gap=$(( $((up_hex)) - local_dec ))
  printf 'ok height=%s upstream_gap=%s\n' "$local_dec" "$gap"
else
  printf 'ok height=%s upstream=unreachable\n' "$local_dec"
fi
```

Deduplicate the alerts — a stalled node repeats the same line every interval —
and do not give the watchdog permission to restart the stack. On this node a
restart hides the two causes that matter, a dead LLM provider and a silent drop
to full mode, and fixes neither.
