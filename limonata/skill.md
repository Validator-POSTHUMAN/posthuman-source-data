# Limonata AI Validator Skill

This public, validator-neutral skill helps AI agents operate Limonata testnet
full nodes and validators without embedding POSTHUMAN infrastructure, keys,
credentials, private endpoints, or wallet data.

## Repository

- Skill package: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/limonata
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/limonata/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/limonata/SKILL.md

## What it helps agents do

- Check chain identity, local and reference height, sync state, peers, service
  identity, validator status, and recent signatures.
- Use the CometBFT RPC correctly for state-sync trust data.
- Observe encrypted-mempool DKG participation and QUAL results.
- Plan and verify safe ACTIVE-epoch restarts and non-signing recovery.
- Keep encrypted transaction testing low-rate, explicitly approved, and
  independently verified.
- Keep malformed, Byzantine, and phase-precise DKG cases on an isolated devnet.
- Prepare upgrades only after refreshing the official release, checksum,
  genesis, and upgrade-plan evidence.

## Safety guardrails

The skill requires the operator's own inventory before any live action. It
never authorizes consensus-key movement, duplicate signing, database
replacement, transaction broadcast, public endpoint exposure, or DKG
disruption without explicit operator approval.

It requires preservation of consensus key material, monotonic signer state,
and the mode-`0600` DKG ECIES key before destructive recovery. DKG shares,
the threshold key, QUAL, and committee membership reconstruct from committed
chain state; they are not independent local backup artifacts.

## How to use

Give an agent the raw skill file together with your own target inventory:

```text
Use the Limonata validator operations skill.
Network: limonata_10777-1.
Role: <validator|full node|non-signing recovery node>.
Runtime: <systemd|container|other>.
Local CometBFT RPC: <URL>.
Service: <name>.
Task: <health check|state sync|restart plan|DKG observation|upgrade plan>.
```

Keep real hosts, keys, credentials, and unapproved endpoints in private
operator inventory, never in the public skill or chat.
