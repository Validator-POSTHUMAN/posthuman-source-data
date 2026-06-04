# Cosmos Hub AI Validator Skill

This tab links the Cosmos Hub-specific AI-agent skill for Gaia validator and
node operations. The skill is validator-neutral and provider-neutral: it does
not contain production validator names, private hosts, real wallet secrets, RPC
credentials, server-provider assumptions, snapshot-provider defaults, or
custody-specific settings.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/cosmoshub
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/cosmoshub/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/cosmoshub/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/cosmoshub/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/cosmoshub/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/cosmoshub/scripts/cosmoshub-healthcheck.sh

## What It Helps Agents Do

- Operate Cosmos Hub Gaia validators, sentries, full nodes, public RPC/API/gRPC
  endpoints, and archive nodes.
- Check gaiad service state, CometBFT RPC health, chain ID, height, sync state,
  peer count, binary version, disk pressure, logs, and recent consensus
  signatures.
- Triage missed blocks, local/public height gaps, jail/slashing state, RPC/API
  failures, P2P problems, Cosmovisor failures, and upgrade halts.
- Prepare and verify Gaia upgrades from official release notes, on-chain
  upgrade plans, checksums, target-host binaries, and Cosmovisor layout.
- Recover safely from snapshot, state-sync, or database failures with key/config
  backups, old-data preservation, compatibility checks, and post-restore
  verification.
- Guide governance, staking, unjail, validator edit, provider-security, and IBC
  workflows while requiring explicit approval before transaction broadcast.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Mainnet chain ID: cosmoshub-4
- Daemon: gaiad
- Default home: ~/.gaia
- Bond and fee denom: uatom
- Address prefixes: cosmos, cosmosvaloper, cosmosvalcons
- Official Gaia repo: https://github.com/cosmos/gaia
- Official Cosmos Hub docs: https://docs.cosmos.network/hub/latest
- Chain registry: https://github.com/cosmos/chain-registry/tree/master/cosmoshub

Always refresh official docs and releases before using versions, upgrade names,
network parameters, genesis files, checksums, provider-security commands,
governance details, seeds, or peer lists.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes scripts/cosmoshub-healthcheck.sh. The helper supports SSH
mode and local mode, configurable service names, local/public RPC height
comparison, expected chain ID validation, binary version inspection, recent
signing checks, staking/slashing queries, provider-chain query attempts, recent
log scanning, and disk checks.

Minimum monitoring coverage:

- service/container state and restart behavior
- local block height progression
- local/public height gap for the same network
- chain ID, catching-up state, peers, and voting power
- recent consensus signatures for validator nodes
- staking status and jail state
- recent consensus, mempool, database, p2p, keyring, and Cosmovisor errors
- disk and inode pressure
- provider-security and IBC/relayer state when those roles are expected

Monitoring credentials must stay outside the repository and outside the skill
files. Use environment files or the operator's secret manager for webhooks,
Prometheus, Grafana, RPC tokens, wallet secrets, and keyring credentials.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or making
operational changes. It tells agents to load the operator's own Cosmos Hub
inventory first and to match the affected chain ID, host, service name, local
RPC, valoper, consensus address, data directory, Cosmovisor layout, key custody
reference, and alert route before changing anything.

The skill treats database replacement, snapshot restore, validator-state moves,
key changes, signer changes, unjail, governance voting, staking edits,
commission edits, provider-security changes, IBC transactions, public endpoint
exposure, and firewall changes as approval-gated operations.

It also warns agents never to paste private keys, mnemonics, keyring passwords,
RPC tokens, wallet secrets, monitoring webhooks, or private infrastructure
details into chat, logs, reports, examples, or skill files.

## Related Skill

Fuel Sequencer uses Cosmos SDK and CometBFT concepts, but it has its own
network-specific skill:

- Fuel skill: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/fuel

Use the Cosmos Hub skill for Gaia and cosmoshub-4. Use the Fuel skill for Fuel
Ignition or Fuel Sequencer operations.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Cosmos Hub skill.
Network: cosmoshub-4.
Runtime: <systemd|docker|kubernetes|binary>.
Local RPC: <http://127.0.0.1:26657 or custom>.
Service/container: <name>.
Valoper: <cosmosvaloper...>.
Consensus address: <hex and/or cosmosvalcons...>.
Task: run a health check / triage missed blocks / prepare upgrade / plan snapshot recovery / review governance transaction.
~~~

Keep production inventory, secrets, and real validator-specific details in your
private operational docs, not in the public skill repository.
