# Shentu AI Validator Skill

This tab links the Shentu-specific AI-agent skill for validator operations. The skill is validator-neutral and server-neutral: it does not contain production validator names, private hosts, real valoper addresses, or real consensus addresses.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/shentu
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/shentu/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/examples/inventory.example.json
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

The skill requires agents to verify live state before claiming health or taking action. It instructs agents to load the operator's own Shentu inventory first and to match the affected consensus address to the correct host, service, RPC endpoint, and valoper before restarting anything.

The skill also tells agents to avoid restart loops, preserve recent logs before process changes, compare local and public RPC state when possible, and ask the operator before destructive recovery, data deletion, snapshot restore, or unjail transactions.

## How to Use

1. Open the raw skill file:
   https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/shentu/SKILL.md

2. Give that file to your AI agent as a skill, system context, project instruction, or attached reference. The exact method depends on your agent platform.

3. Prepare your own Shentu inventory. At minimum, provide:
   - host or SSH target
   - systemd service name
   - local RPC endpoint
   - validator moniker or label
   - valoper address
   - consensus address

4. For a machine-readable inventory format, use:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/references/inventory.schema.json

5. Use the example inventory only as a template with fake values:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/shentu/examples/inventory.example.json

6. Ask your agent to load the skill and your inventory before any Shentu operational task, especially alert triage, restarts, upgrades, or recovery.

7. For live checks, run the helper script from the skill repository with your own values.

Example:

~~~bash
shentu-healthcheck.sh \
  --host <user>@<host> \
  --service <systemd-service> \
  --rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<public-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valoper <shentuvaloper...>
~~~

If you are already on the validator host, use local mode:

~~~bash
shentu-healthcheck.sh \
  --local \
  --service <systemd-service> \
  --rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<public-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valoper <shentuvaloper...>
~~~

## Helper Script

The skill includes `scripts/shentu-healthcheck.sh`, which checks:

- systemd state
- local RPC height and sync state
- optional local/public RPC height gap
- running binary path and version
- peers
- recent block signatures
- staking validator status

The script supports SSH mode, local mode, configurable daemon name, configurable signing window, and request timeouts.

## Current Publication

- Repository: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
- Current Shentu skill package commit: 6dca889628b96c1cffa89de633b2410c70a33b45

