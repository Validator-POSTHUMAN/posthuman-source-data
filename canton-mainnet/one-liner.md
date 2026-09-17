# Canton Network MainNet — One-Liner Installation

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

## Before you run it on MainNet

MainNet is permissioned. The one-liner cannot skip the parts that are not
technical:

1. Submit the validator request at https://sync.global/validator-request/ from
   a corporate email address. Approval takes roughly two weeks.
2. Get your dedicated MainNet IP whitelisted by the Super Validators — 2/3 must
   approve, typically 2–7 days. The IP may not be shared with a DevNet or
   TestNet node.
3. Ask your SV sponsor for an onboarding secret. It is valid for 48 hours.

Verify the whitelist before installing — every SV should answer with a version
rather than a timeout:

```bash
BASE=https://scan.sv-1.global.canton.network.digitalasset.com
curl -fsS -m 5 "$BASE/api/scan/v0/scans" | jq -r '.scans[].scans[].publicUrl'
```

Then call `/api/scan/version` on each URL the command prints. A `403 RBAC:
access denied` means the address is not whitelisted yet.

Read the current version and migration ID from the network rather than from any
guide — including this one:

```bash
curl -s https://docs.global.canton.network.sync.global/info | jq .
```

MainNet was on version `0.7.5` and migration ID `4` when this page was last
verified, 2026-09-18.

## What the installer asks

1. Network — mainnet / testnet / devnet
2. Party hint — your validator name, e.g. `MyOrg-validator-1`
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

## Already running a validator?

The toolkit adopts an existing node without touching it. Choose **option 4 →
Services**: it detects the running containers and `.env`, auto-fills version,
party hint and SV URLs, and writes `~/.canton/toolkit.conf`.

## After it finishes

Do not consider the install complete until all of these hold:

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep splice   # all healthy
docker inspect splice-validator-validator-1 --format '{{.Config.Image}}'
docker exec splice-validator-validator-1 \
  wget -q -O - --timeout=10 http://localhost:10013/metrics | head -5
```

Note the `wget`: the validator image does not contain `curl`, and a `curl` exec
returns an empty body that looks exactly like a dead metrics port.

Then take the two backups described in the Backup & Recovery tab. A MainNet
validator without an identities backup is one disk failure away from permanent
loss of its Canton Coin.

## What this does not do

The one-liner does not apply for you, does not get your IP whitelisted, and
does not harden the host. Work through the Security Hardening tab afterwards —
a Canton validator needs no inbound ports at all, and most installs leave more
open than that.

---

**POSTHUMAN validators** — https://posthuman.digital
