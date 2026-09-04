# Complete Axelar Validator Setup

This guide turns a reviewed, synchronized Axelar full node into a classic Axelar validator with the complete companion stack:

- `axelard` for consensus and Cosmos SDK state;
- `vald` for Axelar protocol events and external-chain voting;
- one dedicated `tofnd` instance for classic threshold signing;
- separate validator and broadcaster accounts;
- one reviewed RPC source for every enabled external chain.

Amplifier is a separate verifier plane. Do not share its node, `tofnd`, keys, handlers, or failure domain with the classic validator stack.

## Official sources reviewed

- [Validator setup sequence](https://docs.axelar.dev/validator/setup/overview/)
- [Companion configuration](https://docs.axelar.dev/validator/setup/config/)
- [Account and key backup](https://docs.axelar.dev/validator/setup/backup/)
- [Launch `vald` and `tofnd`](https://docs.axelar.dev/validator/setup/vald-tofnd/)
- [Broadcaster registration](https://docs.axelar.dev/validator/setup/register-broadcaster/)
- [External-chain maintenance](https://docs.axelar.dev/validator/external-chains/overview/)
- Reviewed Axelar docs source: `1e9fedd2c70043c612f3febdad94e3da3acb5335`

Refresh the official documentation, Axelar release, network configuration, checksums, genesis, upgrade plan, and chain-maintainer set before every real installation. The source commit above records what this guide was compared against; it is not a permanent version pin for a running validator.

## 1. Choose the production topology

Use independent service supervision and explicit private interfaces.

| Plane | Required components | Failure boundary |
| --- | --- | --- |
| Consensus | `axelard`, database, consensus signer | Never start the same consensus key on two hosts |
| Classic protocol | `vald`, classic `tofnd`, broadcaster | A `vald` fault must not trigger an `axelard` restart |
| External chains | One RPC/full node per enabled chain | Failure must identify the exact chain and provider |
| Amplifier | Separate Axelar node, separate `tofnd`, `ampd`, handlers | Never share classic validator signer state |

Official baseline hardware is 16 CPU cores, 16 GB RAM, and 1.5 TB storage. The official recommendation is 32 cores, 32 GB RAM, and at least 2 TB. Size storage from observed database growth, snapshot/rollback requirements, and the retention policy rather than from the minimum alone.

Before installation, record:

- target host, service users, service names, data paths, and ports;
- `axelar-dojo-1` as the expected mainnet chain ID;
- exact `axelard` and `tofnd` releases, source commits, and checksums;
- validator operator, consensus, broadcaster, and `tofnd` custody references;
- expected external-chain maintainer set and one primary/fallback RPC per chain;
- backup destination, restore test date, monitoring target, and rollback owner.

## 2. Install and synchronize the Axelar node

Use the Node Ops bootstrap, peers, snapshot, state-sync, indexer, and upgrade tabs for the consensus node. A safe source-build review starts with explicit values:

```bash
set -Eeuo pipefail
AXELAR_REPO='https://github.com/axelarnetwork/axelar-core'
AXELARD_VERSION='<reviewed-release-tag>'
EXPECTED_COMMIT='<official-release-commit>'
BUILD_ROOT="$(mktemp -d)"

test "$AXELARD_VERSION" != '<reviewed-release-tag>'
test "$EXPECTED_COMMIT" != '<official-release-commit>'

git clone --filter=blob:none "$AXELAR_REPO" "$BUILD_ROOT/axelar-core"
git -C "$BUILD_ROOT/axelar-core" checkout --detach "$AXELARD_VERSION"
test "$(git -C "$BUILD_ROOT/axelar-core" rev-parse HEAD)" = "$EXPECTED_COMMIT"
git -C "$BUILD_ROOT/axelar-core" status --short
```

Review the release notes, required Go toolchain, dependency lock, and official binary signatures/checksums before building or installing. Do not substitute a moving branch for the exact release commit.

Initialize only the intended home and verify the downloaded genesis against an independent checksum or trusted release channel. Keep RPC, REST, gRPC, and Prometheus loopback-only unless a separately reviewed reverse proxy is needed. Expose only the P2P port required by the network.

Do not proceed to validator duties until all checks pass:

```bash
axelard status --home "$HOME/.axelar" | jq -e '
  .node_info.network == "axelar-dojo-1"
  and (.sync_info.catching_up == false)
  and ((.sync_info.latest_block_height | tonumber) > 0)
'
```

Also require advancing height, fresh block time, healthy peers, stable service state, expected binary version, sufficient disk/inodes, and agreement with an independent mainnet RPC.

## 3. Configure `vald` and classic `tofnd`

The official setup uses the Axelar community configuration workflow to obtain and initialize companion binaries. Treat the setup script as code: pin the exact repository commit, inspect its diff, verify downloaded signatures, and run it only after its network and paths match the target.

The resulting validator home is expected to contain:

```text
.axelar/
├── bin/                 # pinned axelard and tofnd binaries
├── config/              # app.toml, config.toml, genesis and consensus state
├── data/                # consensus application database
├── logs/                # bounded companion logs when file logging is used
├── tofnd/               # encrypted classic threshold-signer state
└── vald/state.json      # last event height processed by vald
```

Review these companion settings before launch:

- `vald` points to the exact local Axelar RPC/gRPC interfaces and expected chain;
- classic `tofnd` listens only on loopback or an approved private network;
- `vald` is the only expected client of this `tofnd` instance;
- service users and file permissions prevent unrelated processes reading state;
- restart policies are bounded and do not restart `axelard` for a companion fault;
- logs, state files, credentials, and passwords are not passed on command lines;
- `vald/state.json` and signer state have explicit backup and recovery ownership.

Use supervised services rather than an interactive terminal. Unit templates must retain non-runnable placeholders until adapted to the target:

```ini
[Service]
User=<dedicated-axelar-user>
WorkingDirectory=<absolute-axelar-home>
ExecStart=<absolute-axelard-path> vald-start --validator-addr <validator-valoper> --chain-id axelar-dojo-1 --home <absolute-axelar-home>
Restart=on-failure
RestartSec=10
```

```ini
[Service]
User=<dedicated-axelar-user>
WorkingDirectory=<absolute-axelar-home>
ExecStart=<absolute-tofnd-path> -m existing -d <absolute-axelar-home>/tofnd
Restart=on-failure
RestartSec=10
```

Provide keyring and `tofnd` passwords through the operator's credential manager or a restricted service mechanism. Never use an `echo $PASSWORD | ...` command, store a mnemonic in an environment file, or expose signer ports publicly.

## 4. Create and protect custody roles

The classic validator needs four separately understood assets:

1. Tendermint/CometBFT consensus key and final signer state;
2. validator account mnemonic/keyring entry;
3. broadcaster account mnemonic/keyring entry;
4. encrypted classic `tofnd` mnemonic/state.

Create them only through the operator custody runbook. Immediately make access-restricted, independently authenticated backups and perform a restore test in isolation. The official `tofnd` workflow creates an export file; back it up through the approved channel and remove the plaintext export from the validator host after verification.

Never print, copy, or inspect key contents in monitoring or support sessions. Before any migration or restore, prove that the same consensus key and `tofnd` identity cannot remain active elsewhere. Preserve `priv_validator_state.json` and reconcile it with the selected snapshot height before starting a signer.

## 5. Register the broadcaster and stake

Use the dedicated **Broadcaster proxy** guide. The validator and broadcaster are distinct accounts, and the proxy mapping is immutable for the lifetime of the validator. Generate and inspect an unsigned registration document first; signing and broadcast stay in the operator-controlled wallet workflow.

After registration, verify the exact proxy mapping from chain state. Fund the broadcaster conservatively, alert before fees are exhausted, and prevent any second process from using its account sequence while `vald` is broadcasting.

Stake and validator creation are separate signed operations. Before broadcast, review chain ID, valoper, consensus pubkey, amount, commission, fee, gas, contact metadata, and signer. After inclusion, verify bonded/non-jailed state and recent consensus signatures from independent chain evidence.

## 6. Select external-chain RPC sources

Each enabled external chain needs an endpoint that is correct, fresh, stable, and independently monitored. Three sourcing models are valid.

### Self-hosted RPC

Use your own full node when the chain's hardware, archive/finality mode, operations cost, and maintenance burden are justified. This gives the most control, but it also creates another node, database, upgrade, and alerting responsibility.

### Rented or managed RPC

A paid provider can be more economical for chains whose full-node footprint is large. Require the exact chain/network, required methods, rate and concurrency limits, historical/finality depth, geographic redundancy, authentication and IP policy, incident history, SLA, and an independently tested fallback. Keep credentials outside the Hub and repository.

### Public RPC

Use public endpoints for bootstrap, comparison, and emergency diagnosis only when their terms and observed limits support the required calls. A single uncontracted public endpoint is not a production voting design: it can rate limit, change history retention, or disappear without notice.

For every enabled chain, maintain a row with primary and fallback source, network identity proof, latest/finalized height, latency, required method test, rate-limit headroom, last successful vote, and owner.

## 7. Configure external chains and maintainer state together

For each selected EVM chain, `vald` configuration requires the exact chain entry, its `rpc_addr`, and `start-with-bridge = true`. The corresponding on-chain maintainer registration must be changed in the same controlled window.

Fail closed on either mismatch:

- RPC enabled but not registered: votes are ignored and broadcaster fees can be lost;
- registered but RPC disabled/unhealthy: expected votes are missed and rewards/performance suffer.

Do not copy a generic IP placeholder into production. Verify the source-chain identity and finality semantics before enabling it. Restart only `vald` and its classic `tofnd` when the approved runbook requires it; do not restart the consensus node for a companion-only configuration change.

The official policy may automatically deregister a maintainer after poor recent poll performance. Monitor the current on-chain parameters rather than hard-code historical thresholds. Query chain-maintainer membership and compare it with the intended `vald` configuration after every change.

Registration and deregistration are signed transactions. Keep executable transaction commands outside this public guide; prepare, review, sign, and broadcast them through the approved operator workflow.

## 8. Monitoring and acceptance

Do not call the validator ready until every line below has live evidence:

- `axelard` active, expected version/commit, `axelar-dojo-1`, fresh advancing height, `catching_up=false`, healthy peers, stable restart count;
- bonded, not jailed or tombstoned, and signing recent consensus blocks;
- `vald` and classic `tofnd` active, private connectivity healthy, bounded restart count, and `axelard health-check` successful;
- exact broadcaster proxy mapping, funded fee balance, stable account sequence, and successful recent transaction inclusion;
- intended versus observed maintainer set identical;
- every external-chain RPC proves identity, freshness, finality, latency, and required calls; recent polls/votes show no late, missing, or incorrect trend;
- disk bytes/inodes, database growth, CPU/RAM, clock sync, certificates, backup recency, and end-to-end alert delivery are healthy.

Run the published Axelar healthcheck with the operator's private inventory. A passing helper is evidence, not proof: confirm consensus signing, on-chain maintainer state, broadcaster activity, and external-chain truth independently.

## Rollback boundary

Keep the previous binaries, service definitions, configuration, `vald` state, and verified backups until the new stack has completed the observation window. If identity, signer uniqueness, chain state, companion health, or external-chain coverage cannot be proved, stop the affected duty and restore the exact reviewed rollback point. Never solve a companion problem by deleting the Axelar home or resetting signer state.
