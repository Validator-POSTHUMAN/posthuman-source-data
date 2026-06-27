# Celestia AI Skill

This tab links the Celestia-specific AI-agent skill for consensus validator
operations, full-node operations, Data Availability bridge/full/light node
checks, public endpoint checks, upgrade preparation, snapshot recovery, and
safe incident triage.

The skill is validator-neutral and provider-neutral: it does not contain
production validator names, private hosts, real wallet secrets, RPC
credentials, server-provider assumptions, or custody-specific defaults.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/celestia
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/celestia/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/references/inventory.schema.json
- Example inventory: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/examples/inventory.example.json
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/scripts/celestia-healthcheck.sh

## What It Helps Agents Do

- Operate Celestia mainnet consensus validators and full nodes.
- Check CometBFT RPC health, chain ID, block height, block time, catching-up
  state, voting power, peers, process version, local/public height gap, and
  recent logs.
- Verify recent validator signatures and staking status when valcons and
  valoper inventory is provided.
- Operate Celestia Data Availability nodes: bridge, full storage, and light
  nodes managed by `celestia-node`.
- Check bridge-node service state, local JSON-RPC, auth-token workflow, p2p
  info, header sync, core RPC reachability, wallet balance, metrics, and logs.
- Prepare `celestia-appd` and `celestia-node` upgrades using official
  releases, compatibility notes, on-chain upgrade plans, checksums, binary
  verification, and rollback notes.
- Recover safely from consensus snapshots or bridge/full/light node-store
  failures with key/config/state preservation, source verification, restart
  checks, and rollback data.
- Write concise operator reports with verified facts, risks, and next steps.

## Operational Scope

- Mainnet chain ID: `celestia`.
- Consensus daemon: `celestia-appd`.
- Consensus home: `~/.celestia-app`.
- Data Availability daemon: `celestia`.
- Active mainnet consensus app version at guide update time: `v8.0.8`.
- Published app v9 release: `v9.0.4`, signaled at height `11771698`.
- Current mainnet `celestia-node` release for DA nodes: `v0.31.3`.
- Common DA node stores:
  - bridge: `~/.celestia-bridge`
  - full storage: `~/.celestia-full`
  - light: `~/.celestia-light`
- Native denom: `utia`.
- Validator prefix: `celestiavaloper`.
- Official docs: https://docs.celestia.org/
- Consensus repository: https://github.com/celestiaorg/celestia-app
- DA node repository: https://github.com/celestiaorg/celestia-node

Always refresh official docs and releases before using versions, network
parameters, module commands, gas prices, genesis files, peer lists, upgrade
plans, or validator commands.

## Monitoring

Yes, monitoring is part of the skill.

The skill includes `scripts/celestia-healthcheck.sh`. The helper supports SSH
mode and local mode, optional systemd checks, local and public RPC comparison,
expected chain ID validation, peer checks, process and version checks, disk
context via logs, validator signing checks when valcons is provided, and
bridge/full/light node checks when DA-node inventory is provided.

Minimum consensus monitoring coverage:

- service/container state and restart count
- local height and block-time freshness
- local/public height gap for `celestia`
- chain ID and catching-up state
- peer count
- voting power and recent signatures for validators
- staking status and jailed state when the daemon is available
- recent RPC, P2P, database, Cosmovisor, mempool, governance, and upgrade
  errors
- disk and inode pressure
- reverse proxy and public endpoint health when relevant

Minimum bridge/full/light monitoring coverage:

- service/container state and restart count
- `celestia-node` version
- local JSON-RPC/auth-token availability
- header sync state
- p2p info and peer identity
- trusted core RPC reachability
- wallet balance when a funded DA node key is expected
- metrics endpoint configuration and recent logs
- node-store disk pressure and unsafe-reset risk

Monitoring credentials must stay outside the repository and outside the skill
files. Use environment files or the operator's secret manager for webhook,
Prometheus, Grafana, auth tokens, RPC tokens, wallet, keyring, signer, and
public endpoint credentials.

## Snapshot Recovery

Snapshot recovery is explicitly covered by the skill.

For consensus nodes, the skill supports operator-selected snapshots and
includes the POSTHUMAN Celestia mainnet snapshot flow:

```bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"

sudo systemctl stop "$SERVICE_NAME"
cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup"
rm -rf "$CELESTIA_HOME/data"

curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$CELESTIA_HOME"

mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
   "$CELESTIA_HOME/data/priv_validator_state.json"
sudo systemctl restart "$SERVICE_NAME"
```

The public snapshot index is available at
https://snapshots.posthuman.digital/celestia-mainnet/.

Before restore, compare `snapshot.json` against a trusted live RPC. Stop if
the snapshot height or chain ID is inconsistent with live network state.

For bridge/full/light nodes, the skill requires separate node-store handling.
Do not mix consensus snapshots with `~/.celestia-bridge`, `~/.celestia-full`,
or `~/.celestia-light` stores. Agents must confirm node type, node store,
service, key name, wallet address, core RPC, and funding expectations before
resetting or restoring a DA node.

## Safety Guardrails

The skill requires agents to verify live state before claiming health or
making operational changes. It tells agents to load the operator's own
Celestia inventory first and to match the affected chain ID, host, service,
local RPC, runtime, data directory, valoper, consensus address, signer/key
custody reference, DA node store, and public endpoint path before changing
anything.

It treats governance votes, create-validator, edit-validator, delegation,
unjail, PayForBlob transactions, wallet/key changes, transaction submission,
database replacement, consensus snapshot restore, bridge/full/light unsafe
reset, public endpoint exposure, and firewall changes as approval-gated
operations.

The skill also warns agents never to paste private keys, mnemonics, P2P
private keys, auth tokens, RPC tokens, signer credentials, wallet secrets, or
keyring passwords into chat, logs, docs, or skill files.

## How to Use

For an AI-agent session, reference the skill and provide your own inventory:

~~~text
Use the Celestia skill.
Network: celestia.
Role: validator / full node / bridge / full-storage / light.
Runtime: <systemd|docker|kubernetes|binary|managed>.
Consensus RPC: <CometBFT RPC URL>.
DA node RPC: <JSON-RPC URL, if bridge/full/light>.
Service/container: <name>.
Valoper: <celestiavaloper...>.
Valcons: <HEX_CONSENSUS_ADDRESS>.
Node store: <~/.celestia-bridge|~/.celestia-full|~/.celestia-light>.
Task: run a health check / plan snapshot recovery / prepare upgrade / triage validator signing / triage bridge-node sync.
~~~

Keep production inventory, secrets, and real validator-specific details in your
private operational docs, not in the public skill repository.
