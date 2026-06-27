# Provenance AI Skill

This tab links the Provenance-specific AI-agent skill for validator operations,
full-node operations, public endpoint checks, upgrade preparation, governance,
and safe recovery.

The skill is validator-neutral and provider-neutral: it does not contain
production validator names, private hosts, real wallet secrets, RPC
credentials, server-provider assumptions, or custody-specific defaults.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/provenance
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/provenance/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/provenance/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/provenance/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/provenance/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/provenance/scripts/provenance-healthcheck.sh

## What It Helps Agents Do

- Operate Provenance Blockchain mainnet validators and full nodes.
- Check CometBFT RPC health, chain ID, block height, block time, catching-up
  state, voting power, peers, process version, local/public height gap, and
  recent logs.
- Verify recent validator signatures and staking status when valcons and
  valoper inventory is provided.
- Triage RPC, REST/API, gRPC, reverse proxy, firewall, peer, mempool,
  Cosmovisor, public endpoint, and disk-pressure incidents.
- Prepare upgrades using official Provenance docs, GitHub releases, release
  notes, on-chain upgrade plans, plan JSON, checksums, binary verification, and
  rollback notes.
- Recover safely from snapshot or database failures with key/config/state
  preservation, source verification, restart checks, and rollback data.
- Guide staking, governance, marker, metadata, name, attribute, exchange, wasm,
  delegation, and unjail workflows while requiring explicit approval before
  transaction broadcast.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Mainnet chain ID: pio-mainnet-1.
- Daemon: provenanced.
- Default home: ~/.provenanced.
- Native denom: nhash.
- Validator prefix: pbvaloper.
- Runtime modes: systemd, Docker, Docker Compose, Kubernetes, binary, source
  build, or managed service.
- Official docs: https://docs.provenance.io/
- Provenance repository: https://github.com/provenance-io/provenance
- Mainnet repository: https://github.com/provenance-io/mainnet

Always refresh official docs and releases before using versions, network
parameters, module commands, gas prices, genesis files, peer lists, upgrade
plans, or validator commands.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes a monitoring baseline and
scripts/provenance-healthcheck.sh. The helper supports SSH mode and local mode,
optional systemd checks, local and public RPC comparison, expected chain ID
validation, peer checks, process and version checks, disk/inode checks, and
validator signing checks when valcons is provided.

Minimum monitoring coverage:

- service/container state and restart count
- local height and block-time freshness
- local/public height gap for pio-mainnet-1
- chain ID and catching-up state
- peer count
- voting power and recent signatures for validators
- staking status and jailed state when the daemon is available
- recent RPC, P2P, database, Cosmovisor, mempool, governance, and application
  module errors
- disk and inode pressure
- reverse proxy and public endpoint health when relevant

Monitoring credentials must stay outside the repository and outside the skill
files. Use environment files or the operator's secret manager for webhook,
Prometheus, Grafana, RPC token, wallet, keyring, signer, and public endpoint
credentials.

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
operational changes. It tells agents to load the operator's own Provenance
inventory first and to match the affected chain ID, host, service, local RPC,
runtime, data directory, valoper, consensus address, signer/key custody
reference, and public endpoint path before changing anything.

It treats governance votes, create-validator, edit-validator, delegation,
unjail, marker/metadata/name/attribute/exchange transactions, wasm
transactions, key changes, transaction submission, database replacement,
snapshot restore, public endpoint exposure, and firewall changes as
approval-gated operations.

The skill also warns agents never to paste private keys, mnemonics, P2P private
keys, RPC tokens, signer credentials, wallet secrets, or keyring passwords into
chat, logs, docs, or skill files.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Provenance skill.
Network: pio-mainnet-1.
Runtime: <systemd|docker|kubernetes|binary|managed>.
Local RPC: <CometBFT RPC URL>.
Service/container: <name>.
Valoper: <pbvaloper...>.
Valcons: <HEX_CONSENSUS_ADDRESS>.
Task: run a health check / plan snapshot recovery / prepare upgrade / triage validator signing / prepare governance or application transaction.
~~~

Keep production inventory, secrets, and real validator-specific details in your
private operational docs, not in the public skill repository.
