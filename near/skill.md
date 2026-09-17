# NEAR AI Validator Skill

This tab links the NEAR-specific AI-agent skill for validator, RPC and archival node operations. The skill is validator-neutral and server-neutral: it does not contain production pool names, private hosts, node keys, staking keys, owner accounts, credentials, or server-provider assumptions.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/near
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/near/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/near/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/near/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/near/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/near/scripts/near-healthcheck.sh
- Scenarios: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/near/evals/near-skill-scenarios.md

## What It Helps Agents Do

- Operate NEAR validators, RPC nodes and split-storage archival nodes on mainnet and testnet.
- Check `neard` sync, protocol drift, peers, and local versus independent height.
- Read the current epoch's produced-versus-expected blocks, chunks and endorsements, and tell a live fault apart from a retrospective cumulative ratio.
- Handle staking-pool operations: creation, `ping`, proposals, commission, staking-key rotation, unstake and withdraw.
- Keep the four NEAR secrets separated — node key, staking key, pool owner full-access key, scoped automation key.
- Bootstrap with Epoch Sync and State Sync instead of the retired public snapshot service.
- Verify archival split storage by cold-head progress rather than by process state.
- Prepare and verify `neard` upgrades, including database migrations and their rollback consequences.
- Write concise operator reports backed by evidence.

## Operational Scope

- Mainnet chain ID: `mainnet`; testnet chain ID: `testnet`
- Binary: `neard` from `near/nearcore`; mainnet runs the latest stable tag, testnet the latest release candidate
- Ports: `24567/tcp` P2P; `3030/tcp` serves both JSON-RPC and Prometheus metrics
- Epoch: 43,200 blocks (~12 h); unbonding: 4 epochs
- Staking-pool factories: `poolv1.near` (mainnet), `pool.f863973.m0` (testnet)
- Pool creation deposit: 30 NEAR

## Safety Boundaries

The skill stops and asks an operator before any key movement or exposure, any staking-pool transaction that moves funds or changes commission or the staking key, starting a second node for an existing pool, deleting storage without a verified recovery path, exposing port `3030` from a validator, or restarting on a retrospective low-endorsement alert while fresh production is healthy.

## Health Check

```bash
git clone https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
./AI-skills-for-networks/near/scripts/near-healthcheck.sh \
  --local --pool <name>.poolv1.near
```

Read-only: it performs no transaction, touches no key, and changes no service.
