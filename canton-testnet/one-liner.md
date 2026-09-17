# Canton Network TestNet — One-Liner Installation

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

## Before you run it on TestNet

TestNet is permissioned, though less demanding than MainNet:

1. Submit the validator request at https://sync.global/validator-request/ from
   a corporate email address.
2. Get your dedicated TestNet IP whitelisted by the Super Validators — 2/3 must
   approve, typically 2–7 days. The IP may not be shared with a MainNet or
   DevNet node.
3. Ask your SV sponsor for an onboarding secret. It is valid for 48 hours.

Verify the whitelist before installing:

```bash
BASE=https://scan.sv-2.test.global.canton.network.digitalasset.com
curl -fsS -m 5 "$BASE/api/scan/v0/scans" | jq -r '.scans[].scans[].publicUrl'
```

Then call `/api/scan/version` on each URL the command prints. A `403 RBAC:
access denied` means the address is not whitelisted yet.

Read the current version and migration ID from the network rather than from any
guide — including this one:

```bash
curl -s https://docs.test.global.canton.network.sync.global/info | jq .
```

TestNet was on version `0.8.0` and migration ID `1` when this page was last
verified, 2026-09-18.

> Do not use `https://lighthouse.testnet.cantonloop.com/api/stats` for this. It
> now returns `401 API key required`.

## What the installer asks

1. Network — choose **testnet**
2. Party hint — your validator name, e.g. `MyOrg-TestNet-1`
3. Migration ID — take it from `/info` above
4. SV sponsor URL and Scan URL — defaults provided
5. Onboarding secret — leave empty if already onboarded
6. Wallet password for nginx basic auth (username `validator`)
7. Backup target — rsync over SSH, Cloudflare R2, or skip
8. Alert channels — Telegram, Discord, Slack, PagerDuty, any combination
9. Auto-upgrade — default **no**; TestNet is the right place to try it
10. Grafana monitoring stack — yes/no
11. Grafana remote access — SSH tunnel, Tailscale, or skip
12. Cloudflare Tunnel for the wallet UI — yes/no

Use credentials, keys and alert channels that are **not** shared with a MainNet
host. A TestNet box is the usual path into production.

## Already running a validator?

The toolkit adopts an existing node without touching it. Choose **option 4 →
Services**: it detects the running containers and `.env`, auto-fills version,
party hint and SV URLs, and writes `~/.canton/toolkit.conf`.

## After it finishes

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep splice   # all healthy
docker inspect splice-validator-validator-1 --format '{{.Config.Image}}'
docker exec splice-validator-validator-1 \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -5
```

Note the `wget`: the validator image does not contain `curl`, and a `curl` exec
returns an empty body that looks exactly like a dead metrics port.

Then take an identities backup. On TestNet it is worth doing even though the
coin is not, because identities change on every network reset and re-taking the
backup afterwards is the step operators forget.

## Remember the resets

TestNet is reset roughly every three months. A reset is a full redeployment,
not an upgrade: all data is deleted, the onboarding secret must be fresh, and
the identities backup must be retaken. Alert on `sv.migration_id` from `/info`
changing — see the Backup & Recovery tab.

---

**POSTHUMAN validators** — https://posthuman.digital
