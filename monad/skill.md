# Monad AI Validator Skill

This tab links the Monad-specific AI-agent skill for validator and full-node operations. The skill is validator-neutral and server-neutral: it does not contain production validator names, private hosts, real validator IDs, node keys, beneficiary addresses, RPC secrets, OTel credentials, or server-provider assumptions.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/monad
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/monad/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/scripts/monad-healthcheck.sh

## What It Helps Agents Do

- Operate Monad validators and full nodes on mainnet and testnet.
- Monitor `monad-bft`, `monad-execution`, `monad-rpc`, OTel metrics, disk pressure, TrieDB, and JSON-RPC health.
- Confirm `eth_chainId`, local/public height gap, sync state, and recent fatal log patterns.
- Triage RPC, BFT, execution, statesync, TrieDB, staking, and alert-routing issues.
- Prepare and verify upgrades.
- Recover safely from local node, snapshot, or storage failures.
- Use Solonet only for disposable rehearsal and development workflows.
- Write concise operator reports.

## Operational Scope

- Mainnet chain ID: 143
- Testnet chain ID: 10143
- Token: MON
- Default JSON-RPC port in official node-ops docs: 8080
- Mainnet public RPC examples: https://rpc.monad.xyz and https://rpc-mainnet.monadinfra.com
- Testnet public RPC examples: https://testnet-rpc.monad.xyz and https://rpc-testnet.monadinfra.com
- Main services: `monad-bft`, `monad-execution`, `monad-rpc`, `monad-mpt`, `monad-cruft`, `otelcol`
- Default BFT config: `/home/monad/monad-bft/config/node.toml`
- Default validators file: `/home/monad/monad-bft/config/validators/validators.toml`
- Default ledger path: `/home/monad/monad-bft/ledger/`
- Default TrieDB device: `/dev/triedb`
- Staking precompile: `0x0000000000000000000000000000000000001000`
- Official docs: https://docs.monad.xyz/
- Official Solonet repo: https://github.com/monad-crypto/monad-solonet
- Official staking CLI repo: https://github.com/monad-developers/staking-sdk-cli

## Mainnet and Testnet Support

The skill explicitly requires agents to choose the network mode before acting.

For mainnet, agents must verify EVM chain ID `143`, use mainnet RPCs and mainnet inventory, and require explicit operator approval before staking transactions, recovery, destructive state changes, or key-touching actions.

For testnet, agents must verify EVM chain ID `10143`, use testnet RPCs and testnet inventory, and avoid reusing mainnet keys, beneficiary addresses, validator IDs, alert routes, snapshot assumptions, or recovery instructions unless the operator's inventory explicitly allows it.

For tempnet or Solonet, agents must ask for operator-provided chain ID, RPC, service names, and local docs because those environments can be custom or reset.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes a monitoring setup workflow and `scripts/monad-healthcheck.sh`. The helper supports SSH mode and local mode, custom service names, `--network mainnet`, `--network testnet`, expected chain ID checks, default public RPC selection for mainnet/testnet, height comparison, OTel metrics probing, disk/TrieDB checks, recent log scanning, version checks, and optional staking CLI validator queries.

Minimum monitoring coverage:

- `monad-bft`, `monad-execution`, `monad-rpc`, and optional `otelcol.service` systemd state
- `eth_chainId`, `eth_blockNumber`, and `eth_syncing`
- local/public height gap for the same network
- fatal/error patterns in BFT, execution, and RPC logs
- root, home, ledger, and TrieDB storage pressure
- OTel `/metrics` availability when Prometheus scraping is expected
- optional staking CLI validator status when validator ID and CLI inventory are available

Monitoring credentials must stay outside the repository and outside the skill files. Use environment files or the operator's secret manager for Telegram, Slack, webhook, Prometheus, or OTel credentials.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or taking action. It tells agents to load the operator's own Monad inventory first and to match the affected network, host, local RPC, service names, validator ID, node name, keys, beneficiary address, staking CLI, expected version, and alert route before changing anything.

The skill treats `/dev/triedb`, NVMe formatting, `reset-workspace.sh`, hard reset, and snapshot import as destructive. It requires key/config backups and explicit operator approval before data deletion or recovery.

It also warns agents not to use Cosmos SDK assumptions for Monad. There is no Cosmos `unjail`, `valoper`, Tendermint RPC path, or CometBFT missed-signature workflow unless an operator's own tooling explicitly provides an equivalent.

## How to Use

1. Open the raw skill file:
   https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/monad/SKILL.md

2. Give that file to your AI agent as a skill, system context, project instruction, or attached reference. The exact method depends on your agent platform.

3. Prepare your own Monad inventory. At minimum, provide:
   - network: mainnet, testnet, tempnet, or solonet
   - host or SSH target
   - local JSON-RPC endpoint
   - service names for BFT, execution, RPC, and optional OTel
   - validator ID, node name, secp public key, BLS public key, and beneficiary address when validator-specific action is needed
   - staking CLI path and auth method when staking actions are requested
   - expected package/runtime version when checking upgrades

4. For a machine-readable inventory format, use:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/references/inventory.schema.json

5. Use the example inventory only as a template with fake values:
   https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/monad/examples/inventory.example.json

6. Ask your agent to load the skill and your inventory before any Monad operational task, especially alert triage, monitoring setup, restarts, upgrades, staking, storage work, or recovery.

7. For live checks, run the helper script from the skill repository with your own values.

Mainnet example:

~~~bash
monad-healthcheck.sh \
  --host <user>@<host> \
  --network mainnet \
  --rpc http://127.0.0.1:8080 \
  --validator-id <id> \
  --staking-cli <path-to-staking-cli>
~~~

Testnet example:

~~~bash
monad-healthcheck.sh \
  --host <user>@<host> \
  --network testnet \
  --rpc http://127.0.0.1:8080 \
  --public-rpc https://testnet-rpc.monad.xyz
~~~

If you are already on the target host, use local mode:

~~~bash
monad-healthcheck.sh \
  --local \
  --network mainnet \
  --rpc http://127.0.0.1:8080
~~~

## Current Publication

- Repository: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
- Current Monad skill package commit: 5b6e94748912a9e56b3301bf5222ac1045ff29da

