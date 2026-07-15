---
name: celestia-validator-and-bridge-ops
description: "Operate Celestia mainnet consensus validators/full nodes and Data Availability bridge/light/full nodes: monitor celestia-appd and celestia-node, bridge-node sync, snapshots, upgrades, safe recovery, public endpoints, and concise operator reports."
---

# Celestia Validator and Bridge Ops

Use this skill for Celestia operations on mainnet `celestia`: consensus
validator/full-node checks, `celestia-appd` upgrades, CometBFT signing,
snapshot recovery, public RPC/API/gRPC endpoints, and Celestia Data
Availability nodes (`bridge`, `full`, and `light`) managed by `celestia-node`.

This skill is validator-neutral and provider-neutral. It must work for any
operator and must not assume a specific validator, host, RPC provider, server
provider, wallet, explorer, snapshot provider, or custody model.

## Source Priority

1. Current command output from the target host, local RPC/API/gRPC, Celestia
   node JSON-RPC, logs, and on-chain queries.
2. Local operator inventory, runbooks, deployment files, and monitoring config.
3. Official Celestia sources:
   - https://docs.celestia.org/
   - https://github.com/celestiaorg/celestia-app
   - https://github.com/celestiaorg/celestia-node
   - https://github.com/celestiaorg/networks
   - https://github.com/cosmos/chain-registry/tree/master/celestia
4. Operator-selected service guides such as POSTHUMAN or ITRocket only after
   official and local facts are understood.
5. Explorers and third-party RPCs only as secondary confirmation.

Always refresh official docs, release tags, checksums, genesis, network config,
seeds, upgrade plans, and chain-registry data before upgrades or production
configuration changes.

## Core Chain Facts

- Mainnet chain ID: `celestia`.
- Consensus daemon: `celestia-appd`.
- Default consensus home: `~/.celestia-app`.
- Data Availability daemon: `celestia`.
- DA node stores:
  - bridge: `~/.celestia-bridge`
  - full storage: `~/.celestia-full`
  - light: `~/.celestia-light`
- Native denom: `utia`.
- Bech32 prefixes: `celestia`, `celestiavaloper`, `celestiavalcons`.
- Common consensus service name: `celestia-appd`.
- Common DA service names: `celestia-bridge`, `celestia-full`,
  `celestia-light`.
- Bridge/full DA nodes require a trusted core endpoint. Light nodes verify
  headers and are cheaper to run.
- Bridge nodes need a funded key for PayForBlob transactions and should expose
  metrics only through the operator's intended monitoring path.

These are orientation facts, not authorization to act. Verify live state and
the operator's inventory before changing a production node.

## Operator Inventory Guardrails

Before operating infrastructure, load the current operator's Celestia
inventory from local docs, monitoring config, deployment files, or explicit
task input. Required target fields are:

- Network and chain ID, normally `celestia`.
- Host or SSH target when remote action is needed.
- Runtime: systemd, Docker, Kubernetes, binary, source build, or managed
  service.
- Node role: validator, sentry, fullnode, archive, public RPC/API/gRPC,
  snapshot source, bridge, full-storage, light, or private infrastructure.
- Service/container/pod name.
- Consensus node: local RPC endpoint, daemon name, home directory, Cosmovisor
  layout, binary path, genesis path, config paths, valoper, valcons, and key
  custody references when validator-specific action is requested.
- DA node: node type, node store, systemd service, local JSON-RPC endpoint
  (commonly `http://127.0.0.1:26658`), core RPC/gRPC endpoint, key name,
  metrics endpoint, and whether it is archival.
- Public endpoint, reverse proxy, TLS, firewall, and metrics expectations.
- Maximum acceptable local/public height gap and alert thresholds.

When a machine-readable inventory format is useful, read
`references/inventory.schema.json`. Use `examples/inventory.example.json` only
as a fake-value template; never treat it as production inventory.

If inventory is missing, inconsistent, or ambiguous, ask for the missing target
data before restarting services, changing config, submitting transactions,
restoring snapshots, deleting data, exposing RPC, or touching keys.

## Safety Rules

- Verify live state before claiming health, sync, signing, bridge availability,
  upgrade completion, or recovery success.
- Before restarting, prove the target service maps to the affected Celestia
  chain ID, host, role, service, and, for validators, valoper/consensus
  address.
- Ask before destructive actions: data deletion, snapshot restore, validator
  key changes, signer changes, unjail, governance voting, staking edits,
  transaction broadcast, bridge/full/light unsafe reset, public endpoint
  exposure, or firewall changes.
- Back up `priv_validator_key.json`, `node_key.json`, keyring references,
  `priv_validator_state.json`, `app.toml`, `config.toml`, `client.toml`,
  genesis, Cosmovisor metadata, DA node store metadata, bridge/full/light
  keys, and recent logs before destructive recovery.
- Preserve `priv_validator_state.json` and understand double-sign risk before
  moving validator data between hosts.
- Do not restart-loop during network-wide halts, upgrade boundaries, or public
  RPC stalls. Compare local and public/reference RPC first.
- Treat inactive, unbonded, or temporarily out-of-active-set status as a
  validator state signal, not automatically a service failure. Query staking
  and slashing state before unjail or restart decisions.
- For bridge nodes, do not wipe the node store or replace keys until the
  operator approves and the wallet address/funding expectations are known.
- Do not publish private keys, mnemonics, P2P private keys, auth tokens,
  monitoring webhooks, RPC credentials, wallet secrets, or private
  infrastructure details in reports, examples, logs, or skill files.

## Health Check Workflow

Use the bundled helper when possible:

~~~bash
scripts/celestia-healthcheck.sh \
  --host <ssh-target> \
  --consensus-service <systemd-service> \
  --consensus-rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<reference-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valoper <celestiavaloper...> \
  --expected-chain-id celestia
~~~

For a bridge node:

~~~bash
scripts/celestia-healthcheck.sh \
  --host <ssh-target> \
  --bridge-service celestia-bridge \
  --bridge-rpc http://127.0.0.1:26658 \
  --bridge-node-type bridge \
  --node-store ~/.celestia-bridge \
  --core-rpc https://<trusted-core-rpc>
~~~

Use `--local` instead of `--host` when already running on the target host. The
consensus and bridge checks can be run together when both services are on the
same host.

Manual consensus baseline:

~~~bash
systemctl is-active <service>; systemctl is-enabled <service> || true

curl -fsS <rpc>/status | jq -r '
  .result.node_info.network,
  .result.sync_info.latest_block_height,
  .result.sync_info.latest_block_time,
  .result.sync_info.catching_up,
  .result.validator_info.voting_power'

curl -fsS <rpc>/net_info | jq -r '.result.n_peers'
pgrep -af 'celestia-appd.*start|cosmovisor.*run start'
readlink -f /proc/$(pgrep -f "celestia-appd.*start" | head -1)/exe
celestia-appd version --long
~~~

Verify recent signatures for validators:

~~~bash
H=$(curl -fsS <rpc>/status | jq -r .result.sync_info.latest_block_height)
for B in $((H-1)) $((H-2)) $((H-3)) $((H-4)) $((H-5)); do
  curl -fsS "<rpc>/block?height=$B" |
    jq -r --arg v "<HEX_CONSENSUS_ADDRESS>" \
      '"flag=" +
      ([.result.block.last_commit.signatures[]? |
        select(.validator_address==$v) | .block_id_flag][0] // "missing")'
done
~~~

Manual bridge-node baseline:

~~~bash
systemctl is-active celestia-bridge
celestia bridge version 2>/dev/null || celestia version
celestia bridge auth admin --node.store ~/.celestia-bridge
celestia header sync-state --node.store ~/.celestia-bridge
celestia p2p info --node.store ~/.celestia-bridge
celestia state balance --node.store ~/.celestia-bridge
journalctl -u celestia-bridge --since '30 minutes ago' --no-pager
~~~

Interpretation:

- Consensus node: `network=celestia`, `catching_up=false`, recent block
  times, enough peers, and local/public height agreement mean the node is
  operational.
- Validator: positive voting power, bonded status, not jailed, and recent
  commit signatures are required before claiming active signing.
- Bridge node: service active, header sync progressing or complete, core RPC
  reachable, p2p info available, wallet funded as required, and logs without
  repeated header/core/P2P errors mean it is operational.
- `block_id_flag` may be numeric or string depending on CometBFT JSON. Treat
  `2` and `BLOCK_ID_FLAG_COMMIT` as commit signatures.
- Peer churn such as EOF, connection reset, or pong timeout is not by itself an
  incident if blocks/headers progress and the service is healthy.

## Alert Triage

For a missed-block, RPC, sync, jail, public endpoint, bridge-node, or DA-node
alert:

1. Extract chain ID, node role, moniker/label, valoper, consensus address,
   host, service, local RPC, public/reference RPC, node store, and bridge/full
   node type from the alert or inventory.
2. Match the consensus address and valoper to the actual target before acting.
3. Compare local and public/reference RPC height. If both are stuck at the
   same height, suspect a network-wide halt or upgrade.
4. For validators, check recent signing for the last 5-10 finalized blocks.
5. Query validator and slashing state:

~~~bash
celestia-appd query staking validator <celestiavaloper...> --node <rpc> -o json |
  jq -r '(.validator // .) as $v | $v.status, $v.jailed, $v.tokens'

celestia-appd query slashing signing-info <celestiavalcons...> --node <rpc> -o json
~~~

6. For bridge/full/light nodes, check node store, header sync, p2p info, core
   endpoint reachability, wallet balance, and recent logs before restart.
7. Preserve recent logs before changing process state:

~~~bash
journalctl -u <service> --since '30 minutes ago' --no-pager
~~~

8. Restart only for clear local failure: process dead, RPC down, local height
   stuck while public height advances, bridge header sync stuck while core is
   healthy, unrecoverable panic, or exhausted local resources. Do at most one
   controlled restart before escalating.

Report format:

~~~text
Celestia status:
- Target: <role/moniker/host>
- Consensus: local <h>, public <h>, gap <n>, catching_up=<true|false>, peers=<n>
- Validator: signing <N>/<M>, voting_power=<vp>, status=<bonded/...>, jailed=<true|false>
- DA node: type=<bridge/full/light>, service=<state>, header_sync=<state>, core=<ok/problem>, p2p=<ok/problem>
- Endpoints: RPC/API/gRPC/bridge <ok/problem/unknown/not checked>
- Action: <none/restart/recovery/escalation>
- Notes: <one concise cause or uncertainty>
~~~

## Upgrade Workflow

Consensus upgrades:

1. Confirm the on-chain upgrade plan:

~~~bash
celestia-appd query upgrade plan --node <rpc> -o json
~~~

2. Confirm official `celestia-app` release/tag, release notes, checksums,
   build requirements, and network-specific instructions.
3. Confirm current binary, Cosmovisor environment, home, data directory, disk,
   backup location, and rollback path.
4. Build or install the target binary on the target host unless the operator's
   runbook says otherwise.
5. If using Cosmovisor, place the binary at:

~~~bash
~/.celestia-app/cosmovisor/upgrades/<upgrade-name>/bin/celestia-appd
~~~

6. Validate:

~~~bash
celestia-appd version --long
cosmovisor version
systemctl cat <service>
journalctl -u <service> --since '10 minutes ago' --no-pager
~~~

DA node upgrades:

1. Confirm official `celestia-node` release/tag and compatibility with the
   running Celestia network.
2. Stop only the affected DA service.
3. Build/install `celestia` and `cel-key`.
4. Run the matching config update:

~~~bash
celestia bridge config-update
celestia full config-update
celestia light config-update
~~~

5. Start the service and verify header sync, p2p info, wallet balance, metrics,
   and logs.

## Snapshot and Recovery

Snapshot recovery is approval-gated because it replaces database state.

Consensus node recovery:

1. Confirm chain ID, service, home, data directory, snapshot source, snapshot
   height, checksum or metadata, compression format, disk space, and ownership.
2. Stop the service cleanly.
3. Preserve configs, keys, validator state, keyring references, recent logs,
   and current metadata.
4. Move existing `data/` aside when disk allows; delete only after approval.
5. Download and verify the operator-selected snapshot.
6. Extract with correct ownership and permissions.
7. Restore `priv_validator_state.json` only when required and approved.
8. Start the service.
9. Verify chain ID, height progression, `catching_up=false`, logs,
   local/public gap, and validator signing if applicable.

POSTHUMAN consensus snapshot, when selected by the operator:

~~~bash
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"
export SNAP_DIR="$HOME/celestia-mainnet-snapshot-restore"

rm -rf "$SNAP_DIR"
mkdir -p "$SNAP_DIR"
curl -fL https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.lz4 | \
  lz4 -dc | tar -xf - -C "$SNAP_DIR"
test -d "$SNAP_DIR/data/application.db"

cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup"

sudo systemctl stop "$SERVICE_NAME"
BACKUP_DIR="$CELESTIA_HOME/data.before-snapshot-$(date +%Y%m%d-%H%M%S)"
mv "$CELESTIA_HOME/data" "$BACKUP_DIR"
mv "$SNAP_DIR/data" "$CELESTIA_HOME/data"

mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
   "$CELESTIA_HOME/data/priv_validator_state.json"
sudo systemctl start "$SERVICE_NAME"
~~~

Bridge/full/light recovery:

- Confirm node type, node store, service, key name, keyring backend, core RPC,
  wallet address, and wallet funding expectations.
- Stop only the affected DA service.
- Back up node-store config, keys, and logs.
- Remove or replace bridge/full/light stores only after approval.
- After restore, verify `celestia <type> header sync-state`, p2p info, wallet
  balance, metrics, and recent logs.

Do not mix consensus snapshots with DA node stores. `celestia-appd` snapshots
restore `~/.celestia-app/data`; bridge/full/light snapshots restore their own
`~/.celestia-*` stores.

## Public Endpoint Checks

Check endpoint class explicitly:

~~~bash
curl -fsS https://<rpc>/status | jq -r '.result.node_info.network,.result.sync_info.latest_block_height'
curl -fsS https://<rest>/cosmos/base/tendermint/v1beta1/node_info | jq .
grpcurl -plaintext <grpc-host:port> list
curl -fsS https://<bridge-rpc-or-health-endpoint>/  # only if operator exposes it intentionally
~~~

Do not expose bridge JSON-RPC publicly unless the operator deliberately wants
that surface and has reviewed auth, firewall, reverse proxy, and rate limits.

## Governance and Transactions

Prepare transactions offline or as unsigned drafts when possible. For any
staking, unjail, governance, PayForBlob, key, wallet, or bridge transaction:

1. Show chain ID, signer, account, sequence, fee, gas, messages, and target.
2. Confirm the signer and custody path.
3. Do not broadcast without explicit operator approval.

## Reports

Keep operator reports concise and evidence-backed:

- What was checked.
- What was found.
- What was changed, if anything.
- Current risk.
- Verification result.
- Next step or blocker.

Do not include secrets, raw auth tokens, mnemonics, private keys, private host
details, or sensitive wallet material.
