# The Graph — Indexer Security Hardening

An Indexer holds six figures of GRT, signs transactions from a hot wallet, and
exposes a public HTTP endpoint. The failure modes are theft, slashing, and
silent loss of rewards. Treat all three as security problems.

---

## 1. Key custody

### Two wallets, always

| Wallet | Holds | Lives | Purpose |
| --- | --- | --- | --- |
| **Staking wallet** | the staked GRT (≥100,000) | hardware wallet, off the server | stake, set cuts, authorize the operator |
| **Operator wallet** | a little ETH for gas | hot, on the indexer host | open/close allocations, submit POIs |

The operator wallet can act **on behalf of** the staking wallet for
operational transactions but cannot withdraw the stake. A fully compromised
indexer host therefore costs gas and uptime, not the stake — provided the two
are genuinely separate mnemonics.

Never generate the operator mnemonic from the same seed as the staking wallet.
Never put the staking wallet's key material on the server.

### Handling the operator mnemonic

- It lives in `.env` as `OPERATOR_SEED_PHRASE`. That file must be mode `0600`,
  owned by the service user, and excluded from version control.
- Every `.env.backup.*` you create inherits the same secret. Keep them `0600`
  too, or delete them.
- Never `cat` the file into a terminal that is being recorded, pasted into
  chat, or shipped to a log collector. Grep for the single variable you need.
- Never pass secrets as command-line arguments — they land in `ps` output and
  shell history.
- Revoking a compromised operator is a single transaction from the staking
  wallet: remove the old operator address, add a new one. Know how to do it
  **before** you need it.

---

## 2. Network exposure

The Graph's documentation is unambiguous: *exposing Graph Node's internal
ports can lead to a full system compromise.*

| Port | Component | Exposure |
| --- | --- | --- |
| 7600 | indexer-service — paid queries | **public**, behind TLS and a real proxy |
| 8000 | graph-node GraphQL HTTP | private — proxy it, never publish directly |
| 8001 | graph-node GraphQL WS | private |
| 8020 | graph-node JSON-RPC admin (deploy/remove subgraphs) | **never public** |
| 8030 | indexing status API | **never public** |
| 8040 | graph-node Prometheus metrics | private |
| 7300 | agent/service/TAP metrics | private |
| 8000 (agent) | indexer management API | **never public** — it controls allocations |
| 5432 | PostgreSQL | **never public** |
| 3000 | Grafana | authenticated, ideally VPN-only |

Practical rules:

- Default-deny inbound at the host firewall. Open 22 (restricted source), 80
  and 443 only.
- Publishing a container port bypasses the host firewall on many Docker
  setups. Bind internal services to `127.0.0.1` or to the compose network,
  not `0.0.0.0`.
- Verify from **outside** the host, not with a local port scan.
- The indexer management API and the admin JSON-RPC are the two that convert a
  network foothold into allocation control. Audit them specifically after
  every compose change.

---

## 3. The public endpoint

- Terminate TLS with a real certificate and monitor its expiry; an expired
  origin certificate takes you off the network as effectively as a crash.
- A CDN/proxy in front of the endpoint is useful for DDoS absorption, but the
  gateway must still reach it — verify end to end after every DNS or proxy
  change.
- The endpoint registered on-chain must be the one that actually answers.
  After any cutover, confirm the registered URL from the network's own view,
  not from your notes.
- Rate-limit and cap query cost. `indexer_query_handler_seconds` and
  PostgreSQL statement timeouts are your protection against a single
  pathological query starving the node.

---

## 4. Payments and GraphTally (TAP)

- Receipts are only accepted from **allow-listed senders** mapped to their
  aggregator endpoint. When the Foundation rotates a sender, add the new
  mapping and **keep the old one** until traffic has clearly moved.
- A missing mapping is a silent revenue outage: queries are denied, containers
  stay green. Alert on `tap_sender_denied`.
- `tap.trusted_senders` permits escrow-debt overdraft — serving work that may
  never be paid for. Leave it unset unless you have an explicit commercial
  reason.
- `max_receipt_value_grt` set too low rejects legitimate paid queries with
  HTTP 400. Re-check it when the gateway changes receipt sizing.

---

## 5. Slashing and disputes

- Disputes are opened by Fishermen with a minimum **10,000 GRT** deposit.
- Windows: **7 epochs** for query/attestation disputes, **56 epochs** for
  allocation disputes.
- Under Horizon, slashing is flexible up to a **10% cap**, with **2.5%**
  recommended by the Arbitration Charter.
- Delegated stake is **not** slashable today; the capability exists, and if it
  were ever enabled, indexer stake would be slashed first.

The practical defence is boring: serve correct data, never restore a database
from an unverified source, never run a modified graph-node that could produce
a wrong POI, and keep deployments healthy rather than merely running.

---

## 6. Host and supply chain

- Dedicated host or strong isolation. The PostgreSQL instance holds all
  indexed data and will happily consume every byte of RAM you configure for
  it — size `shared_buffers` for a shared host rather than copying a
  single-purpose example.
- SSH: keys only, no password auth, no root login, restricted source
  addresses, fail2ban.
- Pin image versions. Verify release notes and image digests before an
  upgrade; upgrade one component at a time with a rollback copy of the compose
  file kept on disk.
- Keep a rollback for **every** config change: a timestamped copy of the file
  you are editing, in place, before you edit it.
- Back up what cannot be rebuilt — `.env`, compose files, `config.toml`,
  indexer-rs config, Grafana/Alertmanager config. Subgraph data can be
  re-synced; operator identity and configuration cannot.
- Storage: RAID0 across NVMe devices is common for Graph data and loses
  everything on a single device failure. That is an acceptable trade **only**
  if the recovery path is tested.

---

## 7. Monitoring credentials

Alerting tokens are credentials. Keep them in a file read by the process
(`bot_token_file:` for Alertmanager), mode `0600`, not inline in a config that
gets committed, diffed, or pasted into a support channel. Rotate immediately
if one is exposed, and verify delivery after rotation.

---

## 8. Pre-flight checklist

- [ ] Staking and operator wallets are separate mnemonics; staking key is off the host.
- [ ] `.env` and every `.env.backup.*` are `0600` and untracked.
- [ ] Ports 8020, 8030, 5432 and the agent management API are unreachable from the internet — verified externally.
- [ ] Host firewall default-deny; only 22/80/443 open.
- [ ] TLS valid, expiry monitored, registered endpoint answers from outside.
- [ ] TAP sender allow-list current; `trusted_senders` unset.
- [ ] Operator wallet funded above the alert floor.
- [ ] Rollback copies exist for compose, `.env`, and service configs.
- [ ] Alert channel tested end to end with a synthetic alert.
- [ ] Recovery path for the PostgreSQL volume is documented and tested.

---

## Related

- [Monitoring](https://nodes.posthuman.digital/chains/the-graph?tab=monitoring)
- [Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide)
- Official: <https://thegraph.com/docs/en/indexing/overview/>
- Graph Node ports and warnings: <https://thegraph.com/docs/en/indexing/tooling/graph-node/>
