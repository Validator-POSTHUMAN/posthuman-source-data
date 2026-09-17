# Canton AI Validator Skill

This tab links the Canton-specific AI-agent skill for validator operations. The skill is operator-neutral and provider-neutral: it contains no production validator names, party IDs, hosts, onboarding secrets, identities dumps, database passwords or alert tokens. Those belong in the operator's own inventory, whose non-secret shape the skill documents.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/canton
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/canton/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/canton/scripts/canton-healthcheck.sh

## What it helps agents do

- Verify a Splice validator across four layers: containers, sync, automation, and position relative to the network.
- Read the metrics that actually exist on a live node, and avoid the alert rules that silently never fire.
- Use the Scan API correctly, including the per-network IP restrictions that make a `403` normal rather than an outage.
- Take and verify both required backups — node identities and the two Postgres databases — in the order the protocol requires.
- Choose between the two recovery paths and state which one the available backups actually permit.
- Plan an upgrade with pre-pulled images, a rollback copy, and post-upgrade verification.
- Review port exposure on a node that should have no inbound ports at all.
- Triage the failure modes that look like something else.
- Write a concise operator report that names its sources.

## Operational scope

- Networks: MainNet, TestNet, DevNet
- Stack: Splice — validator app, Canton participant, PostgreSQL, nginx, wallet and ANS web UIs
- Deployment models: Docker Compose and Kubernetes/Helm
- Metrics: Prometheus on port `10013`, path `/metrics`, on both the validator app and the participant
- Validator admin API: `5003`; ledger API: `7575`; wallet and ANS UIs: nginx on `127.0.0.1:8888`
- MainNet migration ID `4`, version `0.7.5`; TestNet migration ID `1`, version `0.8.0`; DevNet migration ID `1`, version `0.8.1` — all read from `/info` on 2026-09-18, and all subject to change
- Network facts endpoint: `https://docs.<mainnet|test|dev>.global.canton.network.sync.global/info`
- Official docs: https://docs.sync.global/
- Releases: https://github.com/digital-asset/decentralized-canton-sync
- Operator toolkit: https://github.com/web3validator/canton-validator-toolkit

## What it adds on TestNet

TestNet and DevNet are reset roughly every three months. The skill treats a
change in `sv.migration_id` as a network reset rather than an upgrade, and
requires the full redeployment path: delete all volumes and databases, obtain a
fresh onboarding secret from the SV sponsor, redeploy on the announced
migration ID, and take a **new** identities backup, because identities change
as part of the reset.

It also refuses to treat a node that is merely running as a node that is on the
network: the running image and migration ID are checked against `/info` on
every health pass.

## What the skill refuses to assume

Canton is neither a Cosmos SDK chain nor an EVM chain, and the skill states the differences explicitly so an agent does not carry the wrong reflex in:

- no slashing, no jail, no unbonding, no delegation, no commission
- no missed-block counter — automation health and reward triggers replace it
- no genesis file, addrbook, seeds, state sync, chain snapshots or Cosmovisor
- no governance module on the validator side, and no IBC
- the irreversible risk is **key loss**, not double-signing: the participant namespace key cannot be rotated and cannot be reconstructed from the network

## Facts the skill carries because they were verified on live nodes

Checked against running POSTHUMAN MainNet, TestNet and DevNet validators on 2026-09-18:

- The validator image ships `wget`, not `curl`. An exec with the missing binary returns an empty body that reads exactly like a dead metrics port.
- `splice_automation_background_service_health` is a gauge where `0` means healthy. All 29 series read `0` on a healthy validator; a non-zero series names the broken automation in its `service` label.
- `splice_trigger_completed_total` for `ReceiveFaucetCouponTrigger` does not exist until the first completion, so `rate(...) == 0` never fires — PromQL returns no data for a missing series, not zero.
- MainNet and TestNet Scan answer `403 RBAC: access denied` from any non-onboarded address, on every Super Validator mirror. DevNet Scan is public.
- Metric values are exported in scientific notation, which shell integer arithmetic cannot parse.

## Safety gates

The skill requires operator approval before: exporting, moving or restoring identities; any transaction or Canton Coin transfer; dropping a database volume or deleting node data; re-onboarding; changing the party hint or participant ID; changing the sponsor or scan endpoint; opening a port or changing the firewall; enabling unsafe auth mode; and any upgrade that crosses a migration ID.

It also forbids printing `.env` in full, and forbids passing any secret as a command-line argument.

## Helper script

`canton-healthcheck.sh` is read-only. It never writes, never restarts a container, never submits a transaction and never reads secret material. It checks container health, running image against the network version, sync lag, automation health, reward-trigger progress, CC balance, retry failures, free disk and Scan reachability, and exits non-zero on failure.

It was exercised against all three POSTHUMAN validators before publication: it passed on MainNet and TestNet, and correctly failed a broken DevNet node on container health, sync lag and automation health simultaneously.

---

**POSTHUMAN validators** — https://posthuman.digital
