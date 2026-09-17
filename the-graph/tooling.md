# The Graph — Ecosystem Tooling

A working review of the tools around The Graph: what each one is for, who it
serves, and whether an Indexer should run it, read it, or ignore it.

All links checked 2026-09-17.

---

## Official

### Graph Explorer — <https://thegraph.com/explorer>

Canonical profiles, subgraphs, curation and delegation. Everything else in
this list is a different view of the same on-chain data. When a dashboard and
the Explorer disagree, the network subgraph decides — not either UI.

**Use:** the source of truth for Indexer profiles and delegation.

### Delegate — <https://thegraph.com/explorer/delegate>

The delegation UI. Under Graph Horizon you choose an Indexer **and** a data
service (`SubgraphService`). See the [Delegation tab](https://nodes.posthuman.digital/chains/the-graph?tab=delegation).

### Rewards Eligibility Oracle — <https://hub.thegraph.foundation/reo/>

Reads the live eligibility criteria straight from the oracle repository:
active on 5+ days per rolling 28 days, at least one qualifying query per
counted day, qualifying = HTTP 200 / under 5,000 ms / under 50,000 blocks
behind head. Established by GIP-0079.

**Use:** required reading for any Indexer whose indexing rewards matter. The
criteria are gateway-observed, so no local check can replace it.

### Graph Node docs — <https://thegraph.com/docs/en/indexing/tooling/graph-node/>

Ports, `config.toml`, horizontal scaling, dedicated query nodes, and the
explicit warning never to expose the admin ports.

### Subgraph Gateway — <https://thegraph.com/docs/en/gateways/subgraphs/overview/>

Documentation for **operating** a gateway: the entry point between data
consumers and Indexers, handling routing, QoS, auth, billing and per-query
payment over Graph Tally / Horizon Escrow. It gives an operator branded,
metered access to 15,000+ published subgraphs without running indexing
infrastructure for each one.

**Note:** this is a different business from indexing — consumer-side revenue
rather than protocol rewards. Worth a separate evaluation, not an afternoon.

---

## Indexer operations

### graphprotocol-mainnet-docker — <https://github.com/StakeSquid/graphprotocol-mainnet-docker>

The one-host Compose stack: graph-node, indexer-agent, indexer-service-rs,
indexer-tap-agent, PostgreSQL, Traefik, Prometheus, Grafana, Alertmanager,
cAdvisor, node_exporter, plus a CLI container. Requires an external
EIP-1898-capable archive RPC; the archive node is **not** included.

**Use:** the basis of the POSTHUMAN indexer deployment. See the
[Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide).

### Indexer Tools v3 — <https://github.com/vincenttaglia/indexer-tools-v3>

Allocation Dashboard, Subgraph Dashboard and Allocation Wizard in one Vue 3
app. Self-hostable:

```bash
docker pull ghcr.io/vincenttaglia/indexer-tools:latest
docker run -p 3000:3000 -e GRAPH_API_KEY=<studio-api-key> \
  ghcr.io/vincenttaglia/indexer-tools
```

Needs a Graph Studio API key (<https://thegraph.com/studio/apikeys/>).

**Use:** the highest-value optional tool for an Indexer. Self-host it rather
than using a shared deployment — allocation planning should not leak through
someone else's analytics.

### Allocation Optimizer — <https://github.com/graphprotocol/allocation-optimizer>

The optimiser The Graph's own docs recommend, integrated with the indexer
stack. Proposes allocation sizes from signal and competing stake.

**Use:** evaluate against real closed-allocation returns before trusting it
with size decisions. An optimiser's model of the reward curve changes as your
own stake moves.

---

## Analytics and dashboards (read-only)

| Tool | What it is | Verdict |
| --- | --- | --- |
| [GraphSeer](https://graphseer.com/indexers) | GraphOps analytics for Indexers, deployments and network performance | Good cross-check for allocation decisions |
| [graphtools.pro/delegators](https://graphtools.pro/delegators/) | Delegator activity log, regenerated every 8 hours (04:00/12:00/20:00 UTC) | Useful for watching delegation flows; not real-time |
| [Lodestar](https://www.lodestar-dashboard.com/) | Protocol analytics site; the current front page is a public roadmap-progress board | Check what it is serving before citing it |
| [okgraph](https://okgraph.data.nexus/) | Lightweight, fast subgraph browsing UI | Handy for quick deployment lookups |
| [The Graph Market](https://thegraph.market/) | Client-rendered marketplace front-end; no server-side content to inspect | Confirm scope in-app before relying on it |

None of these is a monitoring system. They are periodic, external, and can be
stale or wrong; alerting belongs on your own Prometheus.

---

## Data consumption

### Pinax API — <https://pinax.network/products/api>

Token, NFT, balance, perp and prediction-market data over REST, built with The
Graph, with a native MCP server for agents. 70+ chains, sub-second on hot
endpoints.

**Use:** consumer-side. Relevant if you build products on blockchain data, not
for running an Indexer.

---

## AI agents

### Subgraph MCP — <https://thegraph.com/docs/en/subgraphs/tooling/subgraph-mcp/introduction/>

An open-source Model Context Protocol server exposing The Graph's subgraph
data as MCP tools: search subgraphs, inspect GraphQL schemas, run queries
against deployments, fetch 30-day query volumes. It holds no model — it
translates MCP calls into subgraph queries. Works with Claude, Cline and
Cursor.

**Use:** low cost, immediately useful for any agent-assisted analysis of
network data.

### Agent Skills for Subgraphs — <https://thegraph.com/docs/en/subgraphs/tooling/skills/>

Subgraph development, optimization and testing knowledge packaged for AI
coding assistants, shipped in **two** formats: a Claude Code plugin and
**OpenClaw skills**.

```bash
# Claude Code
claude plugins add PaulieB14/subgraphs-skills

# OpenClaw
cp -r openclaw/subgraph-* ~/.openclaw/skills/
```

**Use:** directly compatible with the agent framework POSTHUMAN already runs.
These cover subgraph *development*; indexer *operations* are covered by the
POSTHUMAN skill on the [Skill tab](https://nodes.posthuman.digital/chains/the-graph?tab=skill).

---

## Summary — what an Indexer should actually run

| Priority | Tool | Why |
| --- | --- | --- |
| Required | graphprotocol-mainnet-docker + own Prometheus/Alertmanager | the stack and the only real monitoring |
| Required | REO criteria page | rewards depend on gateway-observed quality |
| High | Self-hosted Indexer Tools v3 | allocation and subgraph decisions |
| High | Own external endpoint probe | catches DNS/TLS/proxy failures the stack cannot see |
| Medium | Allocation Optimizer | after validating against realized returns |
| Medium | Subgraph MCP + agent skills | agent-assisted analysis and development |
| Read-only | GraphSeer, graphtools.pro, okgraph | cross-checks, never alert sources |
| Strategic | Subgraph Gateway | a separate consumer-side business decision |

---

## Related

- [Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide)
- [Delegation](https://nodes.posthuman.digital/chains/the-graph?tab=delegation)
- [Monitoring](https://nodes.posthuman.digital/chains/the-graph?tab=monitoring)
- [Security hardening](https://nodes.posthuman.digital/chains/the-graph?tab=security-hardening)
