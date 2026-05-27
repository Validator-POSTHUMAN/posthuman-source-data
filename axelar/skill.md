# Axelar AI Validator Skill

This tab links the Axelar-specific AI-agent skill for validator operations. The skill is validator-neutral and server-neutral: it does not contain production validator names, private hosts, real valoper addresses, real consensus addresses, RPC provider secrets, or server-provider assumptions.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/axelar
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/axelar/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/scripts/axelar-healthcheck.sh

## What It Helps Agents Do

- Monitor Axelar consensus signing and node health.
- Triage `vald`, `tofnd`, broadcaster, and external-chain maintainer issues.
- Diagnose sequence drift, out-of-gas votes, RPC-client errors, and missed polls.
- Prepare and verify upgrades.
- Recover safely from local node, `vald`, `tofnd`, or data failures.
- Write concise operator reports.

## Operational Scope

- Mainnet chain ID: axelar-dojo-1
- Testnet chain ID: axelar-testnet-lisbon-3
- Daemon: axelard
- Default mainnet home: ~/.axelar
- Default testnet home: ~/.axelar_testnet
- Denom: uaxl
- Companion processes: vald and tofnd
- Official app repo: https://github.com/axelarnetwork/axelar-core
- Official config repo: https://github.com/axelarnetwork/axelar-configs
- Official docs repo: https://github.com/axelarnetwork/axelar-docs

## Safety Guardrails

The skill requires agents to verify live state before claiming health or taking action. It instructs agents to load the operator's own Axelar inventory first and to match the affected consensus address, valoper, broadcaster, host, service names, RPC endpoint, and external-chain maintainer set before restarting anything.

The skill treats `vald` as a critical voting process, not a generic sidecar. It tells agents to investigate broadcaster sequence drift, local RPC latency, failed vote transaction codes, `tofnd` status, and external-chain RPC errors before restarting services. It also warns agents not to restart the consensus node for `vald`-only symptoms unless there is separate evidence of an `axelard` fault.

For external chains, the skill requires RPC config and chain-maintainer registration changes to be handled together. This prevents fee burn when a validator votes for a chain it is not registered to maintain, and prevents missed rewards when the validator is registered but `vald` is not configured for the chain.

The skill also tells agents to avoid restart loops, preserve recent logs before process changes, compare local and public RPC state when possible, keep the broadcaster funded, and ask the operator before destructive recovery, data deletion, snapshot restore, unjail transactions, or key-affecting actions.

## How to Use

1. Open the raw skill file:
   https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/axelar/SKILL.md

2. Give that file to your AI agent as a skill, system context, project instruction, or attached reference. The exact method depends on your agent platform.

3. Prepare your own Axelar inventory. At minimum, provide:
   - host or SSH target
   - Axelar node systemd service name
   - vald service name, if supervised by systemd
   - tofnd service name, if supervised by systemd
   - local RPC endpoint
   - validator moniker or label
   - valoper address
   - consensus address
   - broadcaster address
   - active external chains maintained by the validator

4. For a machine-readable inventory format, use:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/references/inventory.schema.json

5. Use the example inventory only as a template with fake values:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/axelar/examples/inventory.example.json

6. Ask your agent to load the skill and your inventory before any Axelar operational task, especially alert triage, `vald` troubleshooting, external-chain RPC changes, restarts, upgrades, or recovery.

7. For live checks, run the helper script from the skill repository with your own values.

Example:

~~~bash
axelar-healthcheck.sh \
  --host <user>@<host> \
  --node-service <axelard-systemd-service> \
  --vald-service <vald-systemd-service> \
  --tofnd-service <tofnd-systemd-service> \
  --rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<public-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valoper <axelarvaloper...> \
  --broadcaster <axelar1...> \
  --maintainer-chain ethereum \
  --maintainer-chain avalanche
~~~

If you are already on the validator host, use local mode:

~~~bash
axelar-healthcheck.sh \
  --local \
  --node-service <axelard-systemd-service> \
  --vald-service <vald-systemd-service> \
  --tofnd-service <tofnd-systemd-service> \
  --rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<public-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valoper <axelarvaloper...> \
  --broadcaster <axelar1...>
~~~

## Helper Script

The skill includes `scripts/axelar-healthcheck.sh`, which checks:

- systemd state for `axelard`, `vald`, and `tofnd`
- local RPC height and sync state
- optional local/public RPC height gap
- running binary path and version
- peers
- recent consensus block signatures
- staking validator status
- `axelard health-check`
- broadcaster balance
- broadcaster proxy query
- optional external-chain maintainer status
- recent `vald` log counters for sequence drift, out-of-gas votes, poll misses, signing-session issues, RPC-client errors, and panic/fatal patterns

The script supports SSH mode, local mode, configurable daemon name, configurable home path, configurable signing window, request timeouts, broadcaster balance threshold, and repeated `--maintainer-chain` checks.

## Current Publication

- Repository: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
- Current Axelar skill package commit: f843f0cf031db063f8ace6b73e962428fbf3a107
