# Fuel Network AI Skill

This tab links the Fuel-specific AI-agent skill for operations and development.
The skill is validator-neutral and provider-neutral: it does not contain
production validator names, private hosts, real wallet secrets, RPC credentials,
Ethereum endpoint tokens, server-provider assumptions, or custody-specific
defaults.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/fuel
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fuel/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/fuel/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fuel/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fuel/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fuel/scripts/fuel-healthcheck.sh

## Related Cosmos Hub Skill

The Cosmos Hub Gaia skill is separate from the Fuel skill and is useful for
operators who also run cosmoshub-4 infrastructure:

- Cosmos Hub skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/cosmoshub
- Cosmos Hub raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/cosmoshub/SKILL.md

Use the Fuel skill for Fuel Ignition or Fuel Sequencer. Use the Cosmos Hub
skill for Gaia and cosmoshub-4.

## What It Helps Agents Do

- Operate Fuel Ignition fuel-core full nodes and public/private GraphQL APIs.
- Check Fuel GraphQL health, node version, chain name, DA height, local/public
  block gap, and recent runtime logs.
- Operate Fuel Sequencer fuelsequencerd nodes and validators using
  CometBFT/Cosmos SDK checks.
- Triage Sequencer RPC, P2P, mempool, signing, Cosmovisor, sidecar, bridge, and
  Ethereum dependency issues.
- Prepare Fuel Ignition and Fuel Sequencer upgrades with official release,
  config, binary, database, and rollback checks.
- Recover safely from snapshot or database failures with backups,
  old-data preservation, verification, and rollback notes.
- Guide bridge, staking, validator creation, and withdrawal workflows while
  requiring explicit approval before transaction broadcast.
- Guide Sway, forc, fuelup, SDK, and app integration work without hardcoding
  wallet, RPC, bridge, or custody assumptions.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Fuel Ignition: fuel-core, GraphQL /v1/graphql, fuelup, forc node, P2P, local
  and mainnet/testnet node workflows.
- Fuel Sequencer: fuelsequencerd, Cosmovisor, CometBFT RPC, REST, gRPC, sidecar,
  bridge helper workflows, and validator signing checks.
- Network modes: mainnet, testnet, local, devnet, or operator-defined
  deployment.
- Runtime modes: systemd, Docker Compose, Docker, Kubernetes, binary, source
  build, or managed service.
- Critical dependency: operator-selected Ethereum endpoint or full node for
  Fuel Ignition relayer and Sequencer sidecar/bridge workflows.
- Official docs: https://docs.fuel.network/
- fuel-core repo: https://github.com/FuelLabs/fuel-core
- Sequencer deployments repo: https://github.com/FuelLabs/fuel-sequencer-deployments
- Chain configuration repo: https://github.com/FuelLabs/chain-configuration

Always refresh official docs and releases before using versions, network
parameters, contract addresses, bridge commands, sequencer release tags,
genesis files, bootstrap nodes, or validator commands.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes a monitoring baseline and scripts/fuel-healthcheck.sh. The
helper supports SSH mode and local mode, Fuel Ignition GraphQL checks, Fuel
Sequencer CometBFT checks, optional systemd or Docker runtime checks, optional
public/reference endpoint comparison, expected chain validation, recent log
scanning, disk usage, and validator signing checks.

Minimum monitoring coverage:

- service/container state and restart count
- local block height progression
- local/public height gap for the same network
- Fuel Ignition GraphQL chain name, DA height, and node version
- Fuel Sequencer chain ID, catching-up state, peers, voting power, and recent
  signatures when validator checks are configured
- recent GraphQL/RPC, P2P, database, relayer, Ethereum, sidecar, consensus,
  bridge, and keyring errors
- disk and inode pressure
- Ethereum dependency and reverse proxy health when relevant

Monitoring credentials must stay outside the repository and outside the skill
files. Use environment files or the operator's secret manager for webhook,
Prometheus, Grafana, RPC token, Ethereum endpoint, wallet, and keyring
credentials.

## Snapshot Recovery

Snapshot recovery is explicitly covered by the skill.

The workflow requires agents to ask before replacing or deleting database
state. It tells agents to back up config, keys, validator state, keyring
references, recent logs, and current metadata before restore. It also requires
snapshot source, network, client compatibility, checksum, size, block height,
disk space, and ownership checks.

The generic recovery flow is:

1. Confirm network, node mode, runtime, service/container name, data directory,
   home directory, and snapshot source.
2. Stop the service cleanly.
3. Preserve current config, logs, keys, validator state, and metadata.
4. Move the existing data directory aside instead of deleting it when disk
   allows.
5. Download and verify the operator-selected snapshot using its documented
   command.
6. Extract with correct ownership and permissions.
7. Restore validator state before start when this is a Sequencer validator.
8. Start the service.
9. Verify service state, chain/network, height, height progression, logs,
   local/public gap, sidecar, Ethereum dependency, and validator signing.
10. Roll back to the preserved pre-snapshot data directory if the restore is
    incompatible.

The skill does not recommend a default snapshot provider. The operator supplies
the snapshot source or asks the agent to compare options by requirements and
tradeoffs.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or making
operational changes. It tells agents to load the operator's own Fuel inventory
first and to match the affected network, host, local GraphQL or CometBFT RPC,
runtime, service names, data directory, Ethereum dependency, sidecar, metrics,
validator consensus address, and key custody references before changing
anything.

It treats bridge withdrawals/deposits, staking, validator creation/editing,
signer changes, key changes, transaction submission, database replacement,
snapshot restore, and public RPC exposure as approval-gated operations.

The skill also warns agents never to paste private keys, mnemonics, P2P private
keys, RPC tokens, Ethereum endpoint credentials, wallet secrets, or keyring
passwords into chat, logs, docs, or skill files.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Fuel skill.
Mode: <ignition|sequencer>.
Network: <mainnet|testnet|local>.
Runtime: <systemd|docker|kubernetes|binary>.
Local endpoint: <GraphQL URL for Ignition or CometBFT RPC URL for Sequencer>.
Service/container: <name>.
Ethereum dependency: configured in <env-file-or-secret-manager>.
Task: run a health check / plan snapshot recovery / prepare upgrade / triage validator signing / prepare bridge transaction.
~~~

Keep production inventory, secrets, and real validator-specific details in your
private operational docs, not in the public skill repository.
