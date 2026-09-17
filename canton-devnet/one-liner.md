# Canton Network DevNet — One-Liner Installation

```bash
git clone https://github.com/web3validator/canton-validator-toolkit ~/canton-validator-toolkit && bash ~/canton-validator-toolkit/scripts/setup.sh
```

Already have it:

```bash
cd ~/canton-validator-toolkit && git pull && bash scripts/setup.sh
```

The toolkit is built from running POSTHUMAN validators on MainNet, TestNet and
DevNet. It installs the Splice stack, configures backups, health checks and
monitoring, and leaves one config file — `~/.canton/toolkit.conf` — that
survives every upgrade.

DevNet is the lowest-friction network to start on: Scan is public, the
onboarding secret is self-service, and nothing you break costs anything.

## Before you run it

Read the current version and migration ID from the network rather than from any
guide — including this one:

```bash
curl -s https://docs.dev.global.canton.network.sync.global/info | jq .
```

DevNet was on version `0.8.1` and migration ID `1` when this page was last
verified, 2026-09-18.

> Do not use `https://lighthouse.devnet.cantonloop.com/api/stats` for this. It
> now returns `401 API key required`.

Unlike MainNet and TestNet, DevNet Scan is public, so you can confirm the
network is reachable before installing anything:

```bash
curl -s https://scan.sv-1.dev.global.canton.network.digitalasset.com/api/scan/version
```

## What the installer asks

1. Network — choose **devnet**
2. Party hint — your validator name
3. Migration ID — take it from `/info` above
4. SV sponsor URL and Scan URL — defaults provided
5. Onboarding secret — leave empty if already onboarded
6. Wallet password for nginx basic auth (username `validator`)
7. Backup target — rsync over SSH, Cloudflare R2, or skip
8. Alert channels — Telegram, Discord, Slack, PagerDuty, any combination
9. Auto-upgrade — default **no**
10. Grafana monitoring stack — yes/no
11. Grafana remote access — SSH tunnel, Tailscale, or skip
12. Cloudflare Tunnel for the wallet UI — yes/no

Use credentials, keys and alert channels that are **not** shared with a MainNet
host. DevNet boxes are shared, forgotten and unpatched more often than any
other tier; treat one as untrusted relative to production.

## Already running a validator?

The toolkit adopts an existing node without touching it. Choose **option 4 →
Services**: it detects the running containers and `.env`, auto-fills version,
party hint and SV URLs, and writes `~/.canton/toolkit.conf`.

Watch the Compose project name during adoption. DevNet deployments frequently
use a `splice-devnet-*` prefix instead of `splice-validator-*`, and the
monitoring stack scrapes nothing if `CANTON_NETWORK_NAME` does not match.

## After it finishes

```bash
docker ps --format '{{.Names}}\t{{.Status}}'   # all healthy
docker inspect <validator-container> --format '{{.Config.Image}}'
docker exec <validator-container> \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -5
```

Note the `wget`: the validator image does not contain `curl`, and a `curl` exec
returns an empty body that looks exactly like a dead metrics port.

## Remember the resets

DevNet is reset roughly every three months. A reset is a full redeployment, not
an upgrade: all data is deleted, the onboarding secret must be fresh, and the
identities backup must be retaken. A node that missed a reset cannot be fixed
by upgrading its image — it has to be rebuilt.

Alert on `sv.migration_id` from `/info` changing. POSTHUMAN's own DevNet
validator spent seven weeks `Up (unhealthy)` on a version three releases behind
the network for want of exactly that alert; the full diagnosis is in the
Monitoring tab.

---

**POSTHUMAN validators** — https://posthuman.digital
