# Starknet AI Skill

This tab links the Starknet-specific AI-agent skill for development and operations. The skill is validator-neutral and provider-neutral: it does not contain production validator names, private hosts, real wallet secrets, RPC credentials, Ethereum WebSocket credentials, server-provider assumptions, or custody-specific defaults.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/starknet
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/starknet/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/starknet/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/starknet/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/starknet/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/starknet/scripts/starknet-healthcheck.sh

## What It Helps Agents Do

- Operate Starknet full nodes with Pathfinder, Juno, or another operator-selected client.
- Check Starknet JSON-RPC health, chain ID, RPC version path, local/public block gap, sync status, and recent logs.
- Monitor process/runtime state, Starknet RPC/sync state, Ethereum WebSocket dependency health, disk pressure, and attestation service health.
- Recover safely from local node, database, or snapshot failures with explicit backups, old-data preservation, verification, and rollback notes.
- Prepare validator staking and attestation workflows while requiring current official docs for contract addresses, minimum stake, and phase-specific details.
- Triage node, RPC, Ethereum WS, SDK, transaction, staking, attestation, and Starkzap/app integration issues.
- Guide Cairo, Starknet.js, and Starkzap work without hardcoding wallet, RPC, paymaster, or custody assumptions.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Network modes: mainnet, Sepolia, appchain, devnet, or local.
- Node clients: Pathfinder, Juno, or another client from the operator's inventory.
- Runtime modes: Docker Compose, Docker container, systemd binary, source build, or managed service.
- Required dependency: a reliable Ethereum WebSocket endpoint.
- Common local RPC shape: http://127.0.0.1:<port>/rpc/<version>.
- Validator workflows: staking, operational account setup, rewards address, attestation service, signer custody, and confirmation monitoring.
- Development workflows: Cairo contracts, Scarb, Starknet Foundry, Devnet/Katana, Starknet.js, and Starkzap.
- Official docs: https://docs.starknet.io/
- Official docs source: https://github.com/starknet-io/starknet-docs
- Official Starknet.js repo: https://github.com/starknet-io/starknet.js

Always refresh official docs before using versions, contract addresses, staking minimums, RPC paths, attestation flags, or command syntax.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes a monitoring baseline and scripts/starknet-healthcheck.sh. The helper supports SSH mode and local mode, systemd or Docker deployments, local RPC checks, optional public RPC comparison, expected chain ID validation, recent log scanning, and attestation-service checks.

Minimum monitoring coverage:

- node service or container state
- local block number progression
- starknet_syncing
- local/public height gap for the same network
- expected chain ID
- RPC version path compatibility
- recent L1, Ethereum WS, database, trie, and RPC errors
- disk and inode pressure
- Ethereum WebSocket dependency health
- attestation service state, epoch detection, transaction hashes, confirmations, and signer/RPC/contract-address errors when validator attestation is configured

Monitoring credentials must stay outside the repository and outside the skill files. Use environment files or the operator's secret manager for Telegram, Slack, webhook, Prometheus, Grafana, RPC token, and Ethereum WS credentials.

## Snapshot Recovery

Snapshot recovery is explicitly covered by the skill.

The workflow requires agents to ask before replacing or deleting database state. It tells agents to back up config, key material, signer configuration, recent logs, and current metadata before restore. It also requires snapshot source, network, client compatibility, checksum, size, block height, disk space, and ownership checks.

The generic recovery flow is:

1. Confirm network, client, runtime, data directory, RPC path, and snapshot source.
2. Stop the node cleanly.
3. Preserve current config, logs, keys, signer config, and metadata.
4. Move the existing data directory aside instead of deleting it.
5. Download and verify the snapshot using the snapshot source's documented command.
6. Extract with correct ownership and permissions.
7. Start the node.
8. Verify service state, chain ID, block height, starknet_syncing, height progression, logs, local/public gap, public RPC, indexers, and attestation services.
9. Roll back to the preserved pre-snapshot data directory if the restore is incompatible.

The skill does not recommend a default snapshot provider. The operator supplies the snapshot source or asks the agent to compare options by requirements and tradeoffs.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or making operational changes. It tells agents to load the operator's own Starknet inventory first and to match the affected network, host, local RPC path, client, runtime, service names, data directory, Ethereum WS dependency, metrics endpoint, staking address, operational address, and rewards address before changing anything.

It treats staking, unstaking, commission changes, validator key changes, signer changes, transaction submission, database replacement, snapshot restore, and public RPC exposure as approval-gated operations.

The skill also warns agents never to paste private keys, mnemonics, RPC tokens, Ethereum WS credentials, wallet secrets, or paymaster secrets into chat, logs, docs, or skill files.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Starknet skill. Target network: <mainnet|sepolia|devnet>. Client: <pathfinder|juno>. Runtime: <systemd|docker>. Local RPC: <url>. Service/container: <name>. Ethereum WS source is configured in <env-file-or-secret-manager>. Task: run a health check / plan snapshot recovery / triage attestation / prepare upgrade.
~~~

Keep production inventory, secrets, and real validator-specific details in your private operational docs, not in the public skill repository.
