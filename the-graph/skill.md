# The Graph AI Skill

This tab links the Graph Protocol indexer skill for AI agents. It is
operator-neutral and provider-neutral: it contains no production hosts, wallet
secrets, RPC credentials, allocation rules, or private inventory.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/the-graph
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/the-graph/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/the-graph/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/the-graph/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/the-graph/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/the-graph/scripts/the-graph-healthcheck.sh

## What It Helps Agents Do

- Verify an indexer across all four layers: containers, deployments, protocol
  state, and external reachability — because a green stack is not the same as
  an earning indexer.
- Read the metrics that actually predict lost revenue: deployment lag, operator
  wallet ETH balance, denied GraphTally senders, invalid receipts, unaggregated
  fees, and RAV redemption failures.
- Track the two economics facts no dashboard reports: POI staleness against the
  28-day limit, and gateway-observed rewards eligibility under GIP-0079.
- Query the network subgraph for authoritative on-chain facts — stake,
  delegation, allocations, cuts, delegation capacity — instead of trusting a
  dashboard's presentation of them.
- Detect dead indexer profiles before anyone is pointed at them for delegation.
- Triage the common failure modes: no gateway traffic, rejected paid queries,
  stalled allocations, degraded archive RPC, DNS/TLS breakage, PostgreSQL
  memory pressure.
- Apply configuration changes with rollback copies, one component at a time,
  followed by real verification.

## Operational Scope

- Protocol network: Arbitrum One, under Graph Horizon.
- Stack: graph-node, indexer-agent, indexer-service-rs, indexer-tap-agent,
  PostgreSQL, proxy, Prometheus/Grafana/Alertmanager.
- Runtime: Docker Compose, local or over SSH.
- External dependency: an EIP-1898-capable Arbitrum One archive RPC.
- Official docs: https://thegraph.com/docs/en/indexing/overview/
- Horizon changes: https://thegraph.com/docs/en/graph-horizon/what-changes/
- Rewards eligibility: https://hub.thegraph.foundation/reo/

Always refresh official docs before relying on protocol parameters, contract
addresses, minimum stake, version requirements, or command syntax.

## Health Check Helper

`scripts/the-graph-healthcheck.sh` runs the read-only checks against a local or
remote host. It never writes, never submits a transaction, and never reads
secret material.

~~~bash
the-graph-healthcheck.sh --local \
  --status-url http://127.0.0.1:8030/graphql \
  --public-endpoint https://index.example.com \
  --agent-metrics http://127.0.0.1:7300/metrics \
  --service-metrics http://127.0.0.1:7301/metrics \
  --tap-metrics http://127.0.0.1:7302/metrics \
  --min-operator-eth 0.05 --max-block-lag 200
~~~

It reports deployment health and lag, non-terminal indexer actions, public
endpoint status, operator ETH balance against a floor, denied GraphTally
senders, and invalid receipts. It deliberately does **not** claim to cover POI
staleness or rewards eligibility — those need their own verification.

## Safety Guardrails

The skill requires the agent to load the operator's own inventory first and to
match host, Compose path, addresses, endpoints and expected deployments before
changing anything.

These operations are approval-gated: stake or provision changes, reward and
query fee cut changes, any on-chain transaction, node data replacement or
deletion, public endpoint or DNS changes, adding `tap.trusted_senders`, and any
movement or exposure of key material.

The skill also forbids printing the environment file in full, pasting a
mnemonic or token into chat or logs, and passing secrets as command-line
arguments.

## How to Use

~~~text
Use The Graph indexer skill. Host: <local|user@host>. Compose path: <path>.
Staking address: <0x…>. Public endpoint: <url>. Task: run a health check /
review allocations / triage missing query traffic / plan an upgrade /
review an indexer before delegating.
~~~

Keep production inventory, secrets, and real indexer-specific details in your
private operational docs, not in the public skill repository.

## Related

- [Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide)
- [Monitoring](https://nodes.posthuman.digital/chains/the-graph?tab=monitoring)
- [Security hardening](https://nodes.posthuman.digital/chains/the-graph?tab=security-hardening)
- [Tooling](https://nodes.posthuman.digital/chains/the-graph?tab=tooling)
