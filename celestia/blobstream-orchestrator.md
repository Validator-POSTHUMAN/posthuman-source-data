# Blobstream Orchestrator — Celestia Mainnet

The legacy Blobstream design used a validator-side orchestrator to query
attestations from celestia-app, sign them with the validator's registered EVM
identity, and publish signatures to a **separate Blobstream P2P network**. It
was not a DA bridge/light node and did not replace the consensus signer. The
current deployment status is blocked by the compatibility gate below.

## Fail-closed binary gate

The pinned official docs are internally inconsistent about the
`orchestrator-relayer` release: `constants/general.json` names `v1.0.1`, while
the install page names `v1.2.0`. The archived official repository's newest
published tag is `v1.1.0` at exact commit
`dce85159724ef4996a67c068c8823eec6d2db65d`; no official `v1.2.0` tag or
release exists. That tag is a historical release baseline, not proof of current
compatibility: its `go.mod` depends on celestia-app `v1.6.0`. More importantly,
`blobstream` appears in the celestia-app v1 module spec but not in v2 through
v9, and v9.0.6 does not register a `blobstream` module or CLI.

Therefore this guide does not publish a build, install, registration, or start
command. Obtain an explicit current release tag **and commit**, supported
celestia-app version and interface, and mainnet bootstrapper set from an
official upgrade announcement before staging anything. If those cannot be
reconciled, status is **blocked**.

## Requirements

- An active Celestia mainnet validator running the approved celestia-app binary.
- Read access to a trusted, fresh celestia-app RPC endpoint (normally `26657`)
  and gRPC endpoint (normally `9090`). Prefer loopback or a private protected
  path.
- A dedicated orchestrator home, for example `$HOME/.orchestrator-celestia`.
- The validator's Blobstream EVM identity in the orchestrator keystore and the
  matching EVM address registered on-chain.
- A dedicated Blobstream P2P identity.
- A current, network-specific Blobstream bootstrapper list from an official
  source.
- Public inbound TCP `30000` for Blobstream P2P. This is distinct from
  consensus P2P and DA P2P `2121`.
- Monitoring for process state, input freshness, P2P peers, and newly signed
  attestations.

Never place secret key material or unlock values in CLI arguments, service
units, environment files, documentation, or logs. Use an operator-approved
secret delivery mechanism supported by the selected binary. If unattended
unlock cannot be implemented without exposing a secret, do not run the service.

## Read-only registration checks

The current consensus binary can establish mainnet identity, but it cannot run
the stale `query blobstream` command:

```bash
celestia-appd status --node <trusted-mainnet-rpc> | \
  jq -e '.NodeInfo.network == "celestia"'
```

After the binary and current registration interface are officially approved,
use their read-only forms to compare public identifiers. This shape is
intentionally non-runnable:

```text
<OFFICIAL-CURRENT-REGISTRATION-QUERY> \
  <VALIDATOR-OPERATOR-ADDRESS> <TRUSTED-MAINNET-ENDPOINT>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys evm list \
  --home <REVIEWED-MAINNET-ORCHESTRATOR-HOME>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys p2p list \
  --home <REVIEWED-MAINNET-ORCHESTRATOR-HOME>
```

The registered EVM address must exactly match the public address selected by
the orchestrator. Do not print keystore contents.

## Registration transaction gate

The current v9 binary has no `tx blobstream register` command. Do not translate
the stale docs example into a transaction. If an official replacement
interface is announced, an operator-controlled procedure must prepare a
non-broadcast document containing the reviewed chain ID, signer, validator
operator address, EVM address, fees, account number, and sequence. Preparing,
signing, simulating, or broadcasting that transaction is outside this guide
and requires explicit approval.

## Staged configuration shape

After the binary, commit, compatibility, bootstrapper set, registration, and
secret-delivery method are approved, use its reviewed initialization interface.
The shape below is intentionally non-runnable:

```text
<APPROVED-BLOBSTREAM-BINARY> orchestrator init \
  --home <REVIEWED-MAINNET-ORCHESTRATOR-HOME>
```

The reviewed start configuration must provide:

- consensus RPC host/port;
- consensus gRPC host/port;
- the registered EVM **public address**;
- current Blobstream bootstrappers;
- Blobstream listen address `/ip4/0.0.0.0/tcp/30000`;
- the dedicated orchestrator home;
- no secret-bearing CLI flags.

Do not reuse a relayer home or assume consensus/DA peers are valid Blobstream
peers.

## Health verification

```bash
systemctl is-active blobstream-orchestrator.service
ss -lntp | grep ':30000'
celestia-appd status --node <trusted-mainnet-rpc> | \
  jq '{network: .NodeInfo.network, height: .SyncInfo.latest_block_height, time: .SyncInfo.latest_block_time, catching_up: .SyncInfo.catching_up}'
journalctl -u blobstream-orchestrator.service \
  --since "30 minutes ago" --no-pager
```

Correlate logs with current on-chain attestations; do not accept old log lines
as proof of current signing.

| Status | Required evidence |
| --- | --- |
| Healthy | Process stable; mainnet RPC/gRPC fresh; registered EVM address matches; Blobstream peers present; recent required attestations signed and propagated |
| Degraded | Process running but peer count, attestation freshness, or propagation is below the documented alert contract |
| Critical | Process stopped, wrong registration, stale consensus input, no peers, repeated signing errors, or required attestations missed |
| Blocked | Binary/commit compatibility, bootstrapper source, or secure unattended unlock is unverified |

Unknown evidence is not healthy. Do not restart repeatedly when registration,
binary compatibility, or secret access is unresolved.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `learn/blobstream`
- `operate/blobstream/orchestrator`
- `operate/blobstream/install-binary`
- `operate/blobstream/key-management`
- `constants/general.json`

Evidence reviewed from official celestia-app tag `v9.0.6`, commit
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
celestia-app v9 or current mainnet compatibility.
