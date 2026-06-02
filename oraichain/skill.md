# Oraichain AI Skill

This tab links the Oraichain-specific AI-agent skill for validator operations,
node operations, and Oraichain ecosystem workflows.

The skill is validator-neutral and provider-neutral: it does not contain
production validator names, private hosts, real wallet secrets, RPC
credentials, bridge custody data, server-provider assumptions, or
custody-specific defaults.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/oraichain
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/oraichain/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/oraichain/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/oraichain/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/oraichain/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/oraichain/scripts/oraichain-healthcheck.sh

## What It Helps Agents Do

- Operate Oraichain mainnet oraid validators and full nodes.
- Check CometBFT RPC health, chain ID, block height, block time, catching-up
  state, voting power, peers, process version, local/public height gap, and
  recent logs.
- Verify recent validator signatures and staking status when valcons and
  valoper inventory is provided.
- Triage RPC, REST/API, gRPC, reverse proxy, firewall, peer, mempool,
  Cosmovisor, and disk-pressure incidents.
- Prepare upgrades using official Oraichain docs, GitHub releases, release
  notes, on-chain upgrade plans, build requirements, binary verification, and
  rollback notes.
- Recover safely from snapshot or database failures with key/config/state
  preservation, source verification, restart checks, and rollback data.
- Guide staking, create-validator, edit-validator, delegation, and unjail
  workflows while requiring explicit approval before transaction broadcast.
- Guide CosmWasm, oracle, price-feed, VRF, OraiDEX, OBridge, OraiBTC, and
  OraichainEVM workflows without hardcoding wallet, contract, bridge, or
  custody assumptions.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Mainnet chain ID: Oraichain.
- Daemon: oraid.
- Default home: ~/.oraid.
- Native denom: orai.
- Validator prefix: oraivaloper.
- Runtime modes: systemd, Docker, Docker Compose, Kubernetes, binary, source
  build, or managed service.
- Official docs: https://docs.orai.io/
- Oraichain repositories: https://github.com/oraichain
- Main app repository: https://github.com/oraichain/orai

Always refresh official docs and releases before using versions, network
parameters, contract addresses, bridge commands, oracle/VRF commands, gas
prices, genesis files, peer lists, or validator commands.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes a monitoring baseline and scripts/oraichain-healthcheck.sh.
The helper supports SSH mode and local mode, optional systemd checks, local and
public RPC comparison, expected chain ID validation, peer checks, process and
version checks, disk/inode checks, recent log scanning, and validator signing
checks when valcons is provided.

Minimum monitoring coverage:

- service/container state and restart count
- local height and block-time freshness
- local/public height gap for the same chain
- chain ID and catching-up state
- peer count
- voting power and recent signatures for validators
- staking status and jailed state when the daemon is available
- recent RPC, P2P, database, oracle, VRF, bridge, and EVM-related errors
- disk and inode pressure
- reverse proxy and public endpoint health when relevant

Monitoring credentials must stay outside the repository and outside the skill
files. Use environment files or the operator's secret manager for webhook,
Prometheus, Grafana, RPC token, wallet, keyring, signer, bridge, oracle, and
VRF credentials.

## Snapshot Recovery

Snapshot recovery is explicitly covered by the skill.

The workflow requires agents to ask before replacing or deleting database
state. It tells agents to back up config, keys, validator state, keyring
references, recent logs, and current metadata before restore. It also requires
snapshot source, network, client compatibility, checksum, size, block height,
disk space, and ownership checks.

The generic recovery flow is:

1. Confirm network, runtime, service/container name, home directory, data
   directory, and snapshot source.
2. Stop the service cleanly.
3. Preserve current config, logs, keys, validator state, and metadata.
4. Move the existing data directory aside instead of deleting it when disk
   allows.
5. Download and verify the operator-selected snapshot using its documented
   command.
6. Extract with correct ownership and permissions.
7. Restore validator state only when the selected recovery method requires it
   and the operator approves.
8. Start the service.
9. Verify service state, chain ID, height progression, logs, local/public gap,
   and validator signing.
10. Roll back to the preserved pre-snapshot data directory if the restore is
    incompatible.

The skill does not recommend a default snapshot provider. The operator supplies
the snapshot source or asks the agent to compare options by requirements and
tradeoffs.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or making
operational changes. It tells agents to load the operator's own Oraichain
inventory first and to match the affected chain ID, host, service, local RPC,
runtime, data directory, valoper, consensus address, signer/key custody
reference, and public endpoint path before changing anything.

It treats create-validator, edit-validator, delegation, unjail, key changes,
transaction submission, database replacement, snapshot restore, public endpoint
exposure, bridge transfers, contract migrations, oracle/VRF provider updates,
and OraichainEVM/precompile changes as approval-gated operations.

The skill also warns agents never to paste private keys, mnemonics, P2P private
keys, RPC tokens, bridge credentials, signer credentials, wallet secrets, or
keyring passwords into chat, logs, docs, or skill files.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Oraichain skill.
Network: mainnet.
Runtime: <systemd|docker|kubernetes|binary|managed>.
Local RPC: <CometBFT RPC URL>.
Service/container: <name>.
Valoper: <oraivaloper...>.
Valcons: <HEX_CONSENSUS_ADDRESS>.
Task: run a health check / plan snapshot recovery / prepare upgrade / triage validator signing / prepare oracle or bridge workflow.
~~~

Keep production inventory, secrets, and real validator-specific details in your
private operational docs, not in the public skill repository.
