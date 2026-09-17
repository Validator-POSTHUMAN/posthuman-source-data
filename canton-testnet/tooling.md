# Canton Network TestNet — Ecosystem Tooling

What is worth running, what is worth reading, and what will waste your time.
Verified 2026-09-18 against a live TestNet validator.

## Read these first

| Source | Use it for |
|---|---|
| [docs.sync.global](https://docs.sync.global/) | canonical Splice operator documentation: onboarding, Compose and Helm deployment, upgrades, backups, disaster recovery, security hardening, observability, **network resets** |
| [Network resets](https://docs.sync.global/validator_operator/validator_network_resets.html) | the TestNet-specific page most operators find out about too late |
| [digital-asset/decentralized-canton-sync](https://github.com/digital-asset/decentralized-canton-sync) | release bundles and images; the only source you should download a node from |
| [canton.network](https://www.canton.network/blog/how-to-get-started-with-a-validator-on-canton) | orientation; thin on operations |
| [IBM: Canton validator](https://www.ibm.com/docs/en/daw/1.1.0?topic=network-canton-validator) | an enterprise integrator's framing of the same deployment |
| [scauditstudio.com/blog/CantonValidatorGuide](https://scauditstudio.com/blog/CantonValidatorGuide) | third-party walkthrough; cross-check version numbers before copying commands |

When a third-party guide and `docs.sync.global` disagree, the official docs
win. When the docs and the live network disagree, the live network wins.

## Network facts endpoint

Public and keyless from anywhere — no whitelisting needed, so it works before
your node exists:

```bash
curl -s https://docs.test.global.canton.network.sync.global/info | jq .
```

```json
{"network":"testnet","sv":{"migration_id":1,"serial_id":2,"version":"0.8.0"},
 "synchronizer":{"current":{"chain_id_suffix":"5","serial_id":2,"version":"0.8.0"},
 "legacy":null,"successor":null}}
```

Use it for the version-drift alert and, more importantly on TestNet, the
**migration-ID change alert** — that is how a network reset announces itself to
your monitoring.

It replaces `https://lighthouse.testnet.cantonloop.com/api/stats`, which now
returns `401 API key required`. Any guide or script still polling that URL is
broken.

## Scan API

Scan is the Super Validators' read API and the source of truth for the
validator set, DSO configuration and reward rounds.

```bash
BASE=https://scan.sv-2.test.global.canton.network.digitalasset.com

curl -s "$BASE/api/scan/version"
curl -s "$BASE/api/scan/v0/dso"
curl -s "$BASE/api/scan/v0/scans"
curl -s "$BASE/api/scan/v0/admin/validator/licenses?page_size=1000"
```

`validator/licenses` is the closest thing Canton has to a validator list: each
entry carries the validator party, the sponsoring SV, `lastActiveAt`, and
metadata including the node `version` and a `contactPoint`.

**TestNet Scan is not public.** It answers `200` from an onboarded validator IP
and `403 RBAC: access denied` from anywhere else. A 403 from your laptop is
normal, not an outage. Build any dashboard that needs TestNet scan data to run
on a whitelisted host.

`/api/scan/v0/scans` doubles as the whitelist test: if every SV it lists
answers `/api/scan/version`, your IP is whitelisted.

| Network | Scan reachable from |
|---|---|
| DevNet | anywhere — fully public |
| TestNet | onboarded validator IPs only |
| MainNet | onboarded validator IPs only |

## Explorers

| Explorer | Notes |
|---|---|
| [lighthouse.testnet.cantonloop.com](https://lighthouse.testnet.cantonloop.com/) | 5N Lighthouse for TestNet; its `/api` now requires a key |
| [cantonscan.com](https://www.cantonscan.com/) | party, transaction and validator views; behind Cloudflare, so usable in a browser but not scriptable |
| [unityhub.dev/canton/validator](https://unityhub.dev/canton/validator) | third-party validator hub with [tools](https://unityhub.dev/canton/validator#tools) and [monitoring](https://unityhub.dev/canton/validator#monitoring) sections; a client-side app, so it cannot be scraped from a plain fetch |
| POSTHUMAN Hub | validator set, Super Validators and node-operator guides for all three networks, served from first-party data |

For automation prefer the Scan API. Explorers change their frontends; Scan is a
documented API.

## Operator tooling

### POSTHUMAN Canton Validator Toolkit

[web3validator/canton-validator-toolkit](https://github.com/web3validator/canton-validator-toolkit)
— built from running MainNet, TestNet and DevNet validators in production.

```bash
git clone https://github.com/web3validator/canton-validator-toolkit ~/canton-validator-toolkit
bash ~/canton-validator-toolkit/scripts/setup.sh
```

| Script | What it does |
|---|---|
| `setup.sh` | interactive install / update / status / services menu |
| `auto_upgrade.sh` | guarded auto-upgrader; backs up first, waits out fresh releases, refuses downgrades, rolls back on unhealthy |
| `backup.sh` | both Postgres dumps → rsync or Cloudflare R2, with retention and failure-only alerts |
| `check_health.sh` | 15-minute health check with a state machine; Telegram, Discord, Slack, PagerDuty |
| `transfer.sh` | CLI wallet: balance, send CC, history, pending offers |
| `monitoring/` | Prometheus + Grafana + node-exporter with a dashboard that works under Docker Compose |

It adopts an existing validator without touching it: `Services` detects the
running containers and `.env` and writes `~/.canton/toolkit.conf` from what it
finds.

TestNet is the right place to exercise `auto_upgrade.sh` and the reset
procedure before either runs against MainNet.

### Staketab Canton Validator Tool

[Staketab/canton-validator-tool](https://github.com/Staketab/canton-validator-tool)
— a standalone Docker service with a web UI for **internal party onboarding**:
creating Canton-managed parties and users, granting `CanReadAs` and `CanActAs`,
creating Auth0 users, and onboarding them to the validator wallet.

TestNet is where you should try it. Two cautions:

- It needs Auth0 **Management API** client secrets, which can create users in
  your tenant. Scope the M2M application to `create:users` and `read:users`,
  nothing more, and use a separate tenant or application from MainNet.
- It joins the `splice-validator_splice_validator` Docker network and talks
  directly to the ledger API on `participant:7575` and the wallet API on
  `validator:5003`. Its UI defaults to `0.0.0.0:3000` — bind it to loopback and
  reach it over an SSH tunnel.

### Canton console

The escape hatch for anything the HTTP APIs do not expose — topology
inspection, key export, manual party work. It is also how an identities backup
is assembled from a participant database when no identities dump exists. See
the Backup & Recovery tab.

## Agent tooling

`canton-healthcheck.sh` from the POSTHUMAN skill is read-only and checks
containers, version drift against `/info`, sync lag, automation health, reward
triggers, balance, retry failures, disk and Scan reachability in a single call:
<https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/scripts/canton-healthcheck.sh>

## What does not exist on Canton

- no `genesis.json`, no `addrbook.json`, no seeds or persistent peers
- no state sync and no chain snapshots — a database backup is the only
  "snapshot"
- no Cosmovisor; upgrades are a new bundle directory plus an image tag
- no governance module on the validator side; DSO governance is an SV function
- no IBC, no relayers
- no delegation, no staking, no commission, no slashing, no jail
- no missed-block counter — automation health and reward triggers replace it

If a tool advertises any of the above for Canton, it is describing a different
chain.

## Related

- **Monitoring** — the metrics and alert rules behind the stack above
- **Security Hardening** — before you expose any of these ports
- **Canton AI Skill** — the same procedures as an agent-executable skill

---

**POSTHUMAN validators** — https://posthuman.digital
