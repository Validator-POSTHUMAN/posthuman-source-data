# Canton Network — Ecosystem Tooling

What is worth running, what is worth reading, and what will waste your time.
Verified 2026-09-18 against MainNet, TestNet and DevNet.

## Read these first

| Source | Use it for |
|---|---|
| [docs.sync.global](https://docs.sync.global/) | the canonical Splice operator documentation: onboarding, Compose and Helm deployment, upgrades, backups, disaster recovery, security hardening, observability, network resets |
| [digital-asset/decentralized-canton-sync](https://github.com/digital-asset/decentralized-canton-sync) | release bundles and images; the only source you should download a node from |
| [canton.network](https://www.canton.network/blog/how-to-get-started-with-a-validator-on-canton) | the project's own getting-started post; good orientation, thin on operations |
| [IBM: Canton validator](https://www.ibm.com/docs/en/daw/1.1.0?topic=network-canton-validator) | an enterprise integrator's framing of the same deployment |
| [scauditstudio.com/blog/CantonValidatorGuide](https://scauditstudio.com/blog/CantonValidatorGuide) | third-party walkthrough; cross-check version numbers before copying commands |

When a third-party guide and `docs.sync.global` disagree, the official docs
win. When `docs.sync.global` and the live network disagree, the live network
wins — check `/info` (below) before believing any written version number.

## Network facts endpoint

The one call that answers "what version and which migration ID is this network
on", public and keyless from anywhere:

```bash
curl -s https://docs.global.canton.network.sync.global/info | jq .       # MainNet
curl -s https://docs.test.global.canton.network.sync.global/info | jq .  # TestNet
curl -s https://docs.dev.global.canton.network.sync.global/info | jq .   # DevNet
```

```json
{"network":"mainnet","sv":{"migration_id":4,"serial_id":5,"version":"0.7.5"},
 "synchronizer":{"current":{"chain_id_suffix":"2","serial_id":5,"version":"0.7.5"},
 "legacy":null,"successor":null}}
```

Use it in upgrade automation and in a version-drift alert. It replaces
`https://lighthouse.cantonloop.com/api/stats`, which now returns
`401 API key required` — any guide or script still polling that URL is broken.

## Scan API

Scan is the Super Validators' read API and the source of truth for the
validator set, the DSO configuration and reward rounds.

```bash
BASE=https://scan.sv-1.dev.global.canton.network.digitalasset.com

curl -s "$BASE/api/scan/version"                                # node version
curl -s "$BASE/api/scan/v0/dso"                                 # SVs, weights, mining round
curl -s "$BASE/api/scan/v0/scans"                               # every SV's public scan URL
curl -s "$BASE/api/scan/v0/admin/validator/licenses?page_size=1000"  # the validator set
```

`validator/licenses` is the closest thing Canton has to a validator list. Each
entry carries the validator party, the sponsoring SV, `lastActiveAt`, and
metadata including the node `version` and a `contactPoint`.

**Access differs sharply by network, and this surprises people:**

| Network | Scan reachable from |
|---|---|
| DevNet | anywhere — fully public |
| TestNet | onboarded validator IPs only |
| MainNet | onboarded validator IPs only |

On MainNet and TestNet every Super Validator mirror answers
`403 RBAC: access denied` to a non-whitelisted source — verified across all
thirteen MainNet scan hosts (digitalasset.com, sync.global, cumberland.io,
tradeweb.com, c7.digital, mpch.io, lcv.mpch.io, orb1lp.mpch.io, fivenorth.io,
proofgroup.xyz, sv-nodeops.com). A 403 from your laptop is normal; the same
call from your validator host succeeds. Build any dashboard that needs MainNet
scan data to run on a whitelisted host.

The `/api/scan/v0/scans` response also doubles as the IP-whitelist test: if
every listed SV answers `/api/scan/version`, your IP is whitelisted.

## Explorers

| Explorer | Notes |
|---|---|
| [cantonscan.com](https://www.cantonscan.com/) | party, transaction and [validator](https://www.cantonscan.com/validators) views. Behind Cloudflare — usable in a browser, not scriptable |
| [lighthouse.cantonloop.com](https://lighthouse.cantonloop.com/) | 5N Lighthouse; MainNet, plus `lighthouse.testnet.` and `lighthouse.devnet.` for the other networks. Its `/api` now requires a key |
| [unityhub.dev/canton/validator](https://unityhub.dev/canton/validator) | third-party validator hub with [tools](https://unityhub.dev/canton/validator#tools) and [monitoring](https://unityhub.dev/canton/validator#monitoring) sections; a client-side app, so it cannot be scraped from a plain fetch |
| POSTHUMAN Hub | validator set, Super Validators and node-operator guides for all three networks, served from first-party data |

For automation prefer the Scan API over any explorer. Explorers change their
frontends; Scan is a documented API.

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
running containers and `.env`, and writes `~/.canton/toolkit.conf` from what it
finds.

### Staketab Canton Validator Tool

[Staketab/canton-validator-tool](https://github.com/Staketab/canton-validator-tool)
— a standalone Docker service with a web UI for **internal party onboarding**:
creating Canton-managed parties, creating users, granting `CanReadAs` and
`CanActAs`, creating Auth0 users and onboarding them to the validator wallet.

It is the right tool if you host users on your validator and are tired of doing
party onboarding by hand. Two cautions before you run it:

- It needs Auth0 credentials including **Management API** client secrets. Those
  can create users in your tenant. Scope the M2M application to `create:users`
  and `read:users`, nothing more.
- It joins the `splice-validator_splice_validator` Docker network and talks
  directly to the ledger API on `participant:7575` and the wallet API on
  `validator:5003`. Its UI defaults to `0.0.0.0:3000`. Do not leave that port
  open — bind it to loopback and reach it over an SSH tunnel, the same way you
  reach the wallet.

### Canton console

The Canton console is the escape hatch for anything the HTTP APIs do not
expose — topology inspection, key export, manual party work. It is also how you
assemble an identities backup from a participant database when no identities
dump exists. See the console access page in the Splice docs, and the Backup &
Recovery tab for the one procedure most operators actually need it for.

## What does not exist on Canton

Time saved by not looking for it:

- no `genesis.json`, no `addrbook.json`, no seeds or persistent peers
- no state sync and no chain snapshots — a validator catches up through the
  synchronizer, and a database backup is the only "snapshot"
- no Cosmovisor; upgrades are a new bundle directory plus an image tag
- no governance module on the validator side — DSO governance is a Super
  Validator function
- no IBC, no relayers
- no delegation, no staking, no commission, no slashing, no jail
- no missed-block counter — reward triggers are the liveness signal instead

If a tool advertises any of the above for Canton, it is describing a different
chain.

## Related

- **Monitoring** — the metrics and alert rules behind the stack above
- **Security Hardening** — before you expose any of these ports
- **Canton AI Skill** — the same procedures as an agent-executable skill

---

**POSTHUMAN validators** — https://posthuman.digital
