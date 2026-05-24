# Shentu AI Validator Skill

This tab links the Shentu-specific AI-agent skill for validator operations.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/shentu
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/shentu/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/scripts/shentu-healthcheck.sh

## What It Helps Agents Do

- Monitor Shentu validator health and signing status.
- Prepare and verify upgrades.
- Triage Tenderduty and missed-block alerts.
- Recover safely from local node failures.
- Write concise operator reports.

## Operational Scope

- Chain ID: shentu-2.2
- Daemon: shentud
- Default home: ~/.shentud
- Denom: uctk
- Official app repo: https://github.com/shentufoundation/shentu
- Official mainnet repo: https://github.com/shentufoundation/mainnet

## Safety Guardrails

The skill requires agents to verify live state before claiming health or taking action. It also warns agents to match the affected consensus address before restarting any Shentu node, because POSTHUMAN monitors multiple Shentu validators and ShentuCyb/cyberG still had unresolved host mapping when the skill was created.

## Helper Script

The skill includes scripts/shentu-healthcheck.sh, which checks:

- systemd state
- local RPC height and sync state
- running binary path and version
- peers
- recent block signatures
- staking validator status

Example:

~~~bash
shentu-healthcheck.sh \
  --host ubuntu@142.132.158.158 \
  --service shentu \
  --rpc http://127.0.0.1:35657 \
  --valcons EA4A6B5765D8DC4F663A71693E6459B15194544E \
  --valoper shentuvaloper1036rphfnyw49fzm5ajfud743j2qutlk9v8lgp2
~~~

## Current Publication

- Repository: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
- Current Shentu skill fix commit: bef814cecba8dd25fd1a64dcfb21129ab5071ca5
