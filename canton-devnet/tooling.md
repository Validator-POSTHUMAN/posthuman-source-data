# Canton Network DevNet — Ecosystem Tooling

What is worth running, what is worth reading, and what will waste your time.
Verified 2026-09-18 against the live DevNet Scan API.

DevNet's distinguishing feature for tooling is simple: **its Scan API is
public**. MainNet and TestNet Scan answer only from onboarded validator IPs, so
DevNet is where any dashboard, exporter or agent that reads Scan should be
built and tested before it is pointed at a whitelisted host.

## Read these first

| Source | Use it for |
|---|---|
| [docs.sync.global](https://docs.sync.global/) | canonical Splice operator documentation: onboarding, Compose and Helm deployment, upgrades, backups, disaster recovery, security hardening, observability, **network resets** |
| [Network resets](https://docs.sync.global/validator_operator/validator_network_resets.html) | the DevNet-defining page; read it before you build anything long-lived |
| [digital-asset/decentralized-canton-sync](https://github.com/digital-asset/decentralized-canton-sync) | release bundles and images; the only source you should download a node from |
| [canton.network](https://www.canton.network/blog/how-to-get-started-with-a-validator-on-canton) | orientation; thin on operations |
| [IBM: Canton validator](https://www.ibm.com/docs/en/daw/1.1.0?topic=network-canton-validator) | an enterprise integrator's framing of the same deployment |
| [scauditstudio.com/blog/CantonValidatorGuide](https://scauditstudio.com/blog/CantonValidatorGuide) | third-party walkthrough; cross-check version numbers before copying commands |

## Network facts endpoint

Public and keyless from anywhere:

```bash
curl -s https://docs.dev.global.canton.network.sync.global/info | jq .
```

```json
{"network":"devnet","sv":{"migration_id":1,"serial_id":5,"version":"0.8.1"},
 "synchronizer":{"current":{"chain_id_suffix":"0","serial_id":5,"version":"0.8.1"},
 "legacy":null,"successor":null}}
```

It replaces `https://lighthouse.devnet.cantonloop.com/api/stats`, which now
returns `401 API key required`. Any guide or script still polling that URL is
broken.

Use it for two alerts: version drift, and — more important on DevNet — a change
in `migration_id`, which is how a network reset announces itself.

## Scan API — public on DevNet

```bash
BASE=https://scan.sv-1.dev.global.canton.network.digitalasset.com

curl -s "$BASE/api/scan/version"
curl -s "$BASE/api/scan/v0/dso"
curl -s "$BASE/api/scan/v0/scans"
curl -s "$BASE/api/scan/v0/admin/validator/licenses?page_size=1000"
```

| Endpoint | What it gives you |
|---|---|
| `/api/scan/version` | the SV node's version and commit timestamp |
| `/api/scan/v0/dso` | Super Validators with reward weights, voting threshold, latest mining round, amulet rules |
| `/api/scan/v0/scans` | every SV's public scan URL — also the IP-whitelist test on the permissioned networks |
| `/api/scan/v0/admin/validator/licenses` | the validator set: party, sponsoring SV, `lastActiveAt`, node `version`, `contactPoint` |

`validator/licenses` is the closest thing Canton has to a validator list. The
DevNet response is about 1.9 MB and paginates with `next_page_token`.

| Network | Scan reachable from |
|---|---|
| DevNet | anywhere — fully public |
| TestNet | onboarded validator IPs only |
| MainNet | onboarded validator IPs only |

On the permissioned networks every Super Validator mirror answers `403 RBAC:
access denied` to a non-whitelisted source — verified across all thirteen
MainNet scan hosts. A 403 from your laptop is normal; the same call from the
validator host succeeds.

## Explorers

| Explorer | Notes |
|---|---|
| [lighthouse.devnet.cantonloop.com](https://lighthouse.devnet.cantonloop.com/) | 5N Lighthouse for DevNet; its `/api` now requires a key |
| [cantonscan.com](https://www.cantonscan.com/) | party, transaction and validator views; behind Cloudflare, so usable in a browser but not scriptable |
| [unityhub.dev/canton/validator](https://unityhub.dev/canton/validator) | third-party validator hub with [tools](https://unityhub.dev/canton/validator#tools) and [monitoring](https://unityhub.dev/canton/validator#monitoring) sections; a client-side app, so it cannot be scraped from a plain fetch |
| POSTHUMAN Hub | validator set, Super Validators and node-operator guides for all three networks, served from first-party data |

For automation prefer the Scan API. Explorers change their frontends; Scan is a
documented API — and on DevNet it is free to hit.

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

Set `CANTON_NETWORK_NAME` to the real Compose project name — DevNet
deployments often use `splice-devnet` rather than `splice-validator`, and the
monitoring stack silently scrapes nothing if it is wrong.

### Staketab Canton Validator Tool

[Staketab/canton-validator-tool](https://github.com/Staketab/canton-validator-tool)
— a standalone Docker service with a web UI for **internal party onboarding**:
creating Canton-managed parties and users, granting `CanReadAs` and `CanActAs`,
creating Auth0 users, and onboarding them to the validator wallet.

DevNet is the right place to evaluate it. Two cautions:

- It needs Auth0 **Management API** client secrets, which can create users in
  your tenant. Scope the M2M application to `create:users` and `read:users`,
  nothing more, and use a tenant or application separate from MainNet.
- It joins the `splice-validator_splice_validator` Docker network and talks
  directly to the ledger API on `participant:7575` and the wallet API on
  `validator:5003`. Its UI defaults to `0.0.0.0:3000` — bind it to loopback and
  reach it over an SSH tunnel. On a shared DevNet host that default is the
  whole risk.

### Canton console

The escape hatch for anything the HTTP APIs do not expose — topology
inspection, key export, manual party work. It is also how an identities backup
is assembled from a participant database when no identities dump exists. DevNet
is where to practise that, because it is the procedure you cannot afford to
learn during a MainNet outage.

## Agent tooling

`canton-healthcheck.sh` from the POSTHUMAN skill is read-only and checks
containers, version drift against `/info`, sync lag, automation health, reward
triggers, balance, retry failures, disk and Scan reachability in a single call:
<https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/scripts/canton-healthcheck.sh>

It is what diagnosed the broken POSTHUMAN DevNet node quoted in the Monitoring
tab, and it runs unchanged against all three networks.

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
- **Security Hardening** — shared hosts, volume ownership, duplicate identity
- **Canton AI Skill** — the same procedures as an agent-executable skill

---

**POSTHUMAN validators** — https://posthuman.digital
