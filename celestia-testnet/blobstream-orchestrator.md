# Blobstream Orchestrator — Mocha-5

The legacy Blobstream design used a validator-side orchestrator to query
attestations from celestia-app, sign them with the validator's registered EVM
identity, and publish signatures to a **separate Blobstream P2P network**. It
was not a DA bridge/light node and did not replace the consensus signer. The
current Mocha-5 deployment status is blocked by the compatibility gate below.

## Mocha-5 and binary gates

- Consensus chain ID: `mocha-5`
- Dedicated home: `$HOME/.orchestrator-mocha-5`
- Never reuse a Mocha-4 orchestrator store, chain data, registration assumption,
  or signer state.

The pinned official docs conflict on the `orchestrator-relayer` release:
`constants/general.json` names `v1.0.1`, while the install page names `v1.2.0`.
The archived official repository's newest published tag is `v1.1.0` at exact
commit `dce85159724ef4996a67c068c8823eec6d2db65d`; no official `v1.2.0` tag or
release exists. That tag is a historical release baseline, not proof of current
compatibility: its `go.mod` depends on celestia-app `v1.6.0`. More importantly,
`blobstream` appears in the celestia-app v1 module spec but not in v2 through
v9, and v9.0.6 does not register a `blobstream` module or CLI. The docs show a
generic Mocha bootstrapper, but do not establish that it is valid for a current
v9/Mocha-5 deployment.

This guide therefore omits build, install, registration, and start commands.
Obtain an explicit release tag and commit, supported celestia-app version and
interface, and Mocha-5 bootstrapper set from an official announcement.
Otherwise status is **blocked**.

## Requirements

- An active Mocha-5 validator using the dedicated Mocha-5 consensus home.
- Fresh Mocha-5 celestia-app RPC (`26657` normally) and gRPC (`9090` normally),
  preferably over loopback or a private protected path.
- A dedicated `$HOME/.orchestrator-mocha-5` store.
- The validator's Blobstream EVM identity and matching Mocha-5 on-chain
  registration.
- A dedicated Blobstream P2P identity.
- A current official Mocha-5 Blobstream bootstrapper set.
- Public inbound TCP `30000` for Blobstream P2P, separate from consensus and DA
  P2P `2121`.
- Monitoring for service state, input freshness, P2P peers, and new
  attestations.

Never place secret key material or unlock values in CLI arguments, service
units, environment files, documentation, or logs. If unattended unlock cannot
be implemented with an approved secret-delivery mechanism supported by the
selected binary, do not run the service.

## Read-only registration checks

The current consensus binary can establish Mocha-5 identity, but it cannot run
the stale `query blobstream` command:

```bash
celestia-appd status --home "$MOCHA_5_HOME" \
  --node <trusted-mocha-5-rpc> | \
  jq -e '.NodeInfo.network == "mocha-5"'
```

After the binary and current Mocha-5 registration interface are officially
approved, use their read-only forms to compare public identifiers. This shape
is intentionally non-runnable:

```text
<OFFICIAL-CURRENT-MOCHA-5-REGISTRATION-QUERY> \
  <VALIDATOR-OPERATOR-ADDRESS> <TRUSTED-MOCHA-5-ENDPOINT>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys evm list \
  --home <REVIEWED-MOCHA-5-ORCHESTRATOR-HOME>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys p2p list \
  --home <REVIEWED-MOCHA-5-ORCHESTRATOR-HOME>
```

The selected EVM public address must exactly match the Mocha-5 on-chain mapping.
Do not print keystore contents.

## Registration transaction gate

The current v9 binary has no `tx blobstream register` command. Do not translate
the stale docs example into a transaction. If an official replacement
interface is announced, an operator-controlled procedure must prepare a
non-broadcast document containing chain ID `mocha-5`, the reviewed signer,
validator operator address, EVM address, fees, account number, and sequence.
Preparing, signing, simulating, or broadcasting that transaction is outside
this guide and requires explicit approval.

## Staged configuration shape

After all gates pass, use the approved binary's initialization interface only
for the dedicated Mocha-5 store. This shape is intentionally non-runnable:

```text
<APPROVED-BLOBSTREAM-BINARY> orchestrator init \
  --home <REVIEWED-MOCHA-5-ORCHESTRATOR-HOME>
```

The reviewed start configuration must provide the Mocha-5 consensus RPC/gRPC
endpoints, registered EVM public address, current Mocha-5 Blobstream
bootstrappers, `/ip4/0.0.0.0/tcp/30000`, dedicated home, and no secret-bearing
CLI flags.

Do not reuse any Mocha-4 bootstrapper unless an official Mocha-5 source
explicitly confirms it.

## Health verification

```bash
systemctl is-active blobstream-orchestrator-mocha-5.service
ss -lntp | grep ':30000'
celestia-appd status --home "$MOCHA_5_HOME" \
  --node <trusted-mocha-5-rpc> | \
  jq '{network: .NodeInfo.network, height: .SyncInfo.latest_block_height, time: .SyncInfo.latest_block_time, catching_up: .SyncInfo.catching_up}'
journalctl -u blobstream-orchestrator-mocha-5.service \
  --since "30 minutes ago" --no-pager
```

Correlate current logs with Mocha-5 on-chain attestations; old or Mocha-4 log
lines are not evidence of current health.

| Status | Required evidence |
| --- | --- |
| Healthy | Process stable; chain ID `mocha-5`; RPC/gRPC fresh; registration matches; Blobstream peers present; recent required attestations signed and propagated |
| Degraded | Running, but peer count, attestation freshness, or propagation falls below the alert contract |
| Critical | Process stopped, wrong chain/registration, stale inputs, no peers, repeated signing errors, or required attestations missed |
| Blocked | Binary compatibility, release commit, Mocha-5 bootstrapper source, or secure unattended unlock is unverified |

Unknown evidence is not healthy. Fail closed on any Mocha-4 reuse.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/networks/mocha-testnet`
- `learn/blobstream`
- `operate/blobstream/orchestrator`
- `operate/blobstream/install-binary`
- `operate/blobstream/key-management`
- `constants/general.json`

Evidence reviewed from official celestia-app tag `v9.0.6-mocha`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`:

- `specs/src/state_machine_modules_v1.md`
- `specs/src/state_machine_modules_v2.md` through
  `specs/src/state_machine_modules_v9.md`
- `app/app.go`
- `app/modules.go`

Evidence reviewed from the archived official `orchestrator-relayer` repository:

- newest published tag `v1.1.0`, commit
  `dce85159724ef4996a67c068c8823eec6d2db65d`
- `v1.1.0` `go.mod`: celestia-app `v1.6.0`
- no official `v1.2.0` tag or release exists

`v1.1.0` is only the newest published historical baseline; it does not establish
celestia-app v9 or Mocha-5 compatibility.
