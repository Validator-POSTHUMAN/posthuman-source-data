# Celestia Mocha-5 App Upgrade and Multiplexer

**Mocha-5 only; checked 2026-10-28.** The activation height below is historical
and does not apply to mainnet. The current patch is `v10.5.0-mocha` on an
already-active app-v10 chain; it is not a new height fork.

## Current release and activation

| Item | Mocha-5 value |
| --- | --- |
| Consensus chain ID | `mocha-5` |
| Current multiplexer release | `v10.5.0-mocha` (GitHub pre-release; running on POSTHUMAN signer and zero-power RPC) |
| Source commit | `6013e758d5dceb75827ad191c8d739d7c43cfa04` |
| App v10 activation height | **1082619** |
| Source module | `github.com/celestiaorg/celestia-app/v10` |
| Source-build Go | `1.26.6` |
| Linux runtime floor | glibc `2.38`; Ubuntu 24.04 or equivalent; Ubuntu 22.04 and older unsupported |
| Release architectures | Linux and macOS, `amd64` and `arm64`; Linux x86_64 tested in CI |

The binary version and protocol app version are different. Live Mocha-5 already
reports app version `10`; upgrading an existing v10 node to this patch does
not replay the old activation at height `1082619`.

The multiplexer keeps one CometBFT instance and selects the historical or
native app. Use the official **Mocha multiplexer** archive for existing homes;
source builds use `make install` from the pinned tag. Do not use Cosmovisor
for this upgrade. It is not a `celestia-node` DA role.

At the historical v10.2.0-mocha commit, embedding constants were `v3.12.0`, `v4.1.0`,
`v5.0.12`, `v6.4.4`, `v7.0.2-mocha`, `v8.0.8`, and `v9.0.7-corto` for app
versions 3 through 9. The `corto` child label is the upstream embedding pin;
it does not change the consensus chain ID to Corto. Source builds download
those seven historical assets. This is a record of the original v9-to-v10
activation, not a current pre-activation checklist.

Historical `v9.0.6-mocha` and mainnet `v9.0.6` shared commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`. That is historical provenance,
not the current target or permission to interchange network state. Mocha-5
started at height 1: never reuse Mocha-4 data, signer state, homes or snapshots.

## Stage an official release without activating it

Select the platform archive and validate the official checksum before opening
it. This example stages a Linux binary outside the live path:

```bash
set -eu
APP_TAG="v10.5.0-mocha"
APP_COMMIT="6013e758d5dceb75827ad191c8d739d7c43cfa04"
case "$(uname -m)" in
  x86_64) ASSET="celestia-app_Linux_x86_64.tar.gz" ;;
  aarch64|arm64) ASSET="celestia-app_Linux_arm64.tar.gz" ;;
  *) printf 'Unsupported architecture\n' >&2; exit 1 ;;
esac
STAGE="$(mktemp -d -p /tmp "celestia-app-${APP_TAG}.XXXXXX")"
BASE_URL="https://github.com/celestiaorg/celestia-app/releases/download/${APP_TAG}"
curl --proto '=https' --tlsv1.2 -fL "${BASE_URL}/${ASSET}" -o "${STAGE}/${ASSET}"
curl --proto '=https' --tlsv1.2 -fL "${BASE_URL}/checksums.txt" -o "${STAGE}/checksums.txt"
(
  cd "$STAGE"
  awk -v file="$ASSET" '$2 == file || $2 == "*" file {print}' checksums.txt > selected-checksum.txt
  test "$(wc -l < selected-checksum.txt)" -eq 1
  sha256sum -c selected-checksum.txt
  mkdir unpacked
  tar -xzf "$ASSET" -C unpacked
)
test -x "$STAGE/unpacked/celestia-appd"
"$STAGE/unpacked/celestia-appd" version --long
printf 'Expected commit: %s\nStaged binary: %s\n' "$APP_COMMIT" "$STAGE/unpacked/celestia-appd"
```

Require reported version `10.5.0-mocha`, the exact commit and `multiplexer`
build tag. Keep the exact previous binary and config available. This staging
example does not install over a live binary or restart a service.

## Configuration preflight

Use the existing dedicated Mocha-5 home and reviewed service arguments, not a
new default home. Verify its genesis and local RPC both identify `mocha-5`.

- Keep `rpc.grpc_laddr` non-empty and loopback-bound; upstream's example is
  `tcp://127.0.0.1:9098`.
- The ABCI client `proxy_app` in `config.toml` must equal the **top-level**
  ABCI server `address` in `app.toml`. The default pair is
  `tcp://127.0.0.1:36658`. For port-prefixed/co-located nodes, explicitly match
  `address` to their existing `proxy_app`; do not put two networks on the same
  default port. Missing `address` falls back to the default and may block v10
  startup. Address mismatch is not a reason to modify the database.
- When Fibre is not operated, keep `priv_validator_grpc_laddr = ""` in
  `config.toml`. v10 exposes `SignRawBytes` on that endpoint; an old non-empty
  setting can become active. Do not expose signer gRPC as an upgrade side effect.
- Upstream recommends `config sync` to add field documentation. Preview only
  with `config sync --dry-run --home <reviewed-home>` and review differences;
  do not blindly apply config synchronization or overwrite existing values.

POSTHUMAN operates app nodes and a Mocha-5 Fibre server, but not Bridge/Light
DA nodes. Preserve the existing Fibre signer link and match its binary to the
reviewed app release; no new escrow transaction or port expansion is implied.

## Safe upgrade and verification order

1. Verify the exact home/service, chain `mocha-5`, effective binary path,
   version/commit/build tags and public consensus identity. Reject any mainnet
   or Mocha-4 home, database, snapshot or signer-state path.
2. Confirm local and independent Mocha-5 RPCs both report app version `10`.
   Height `1082619` is already past; do not send another upgrade signal or
   treat this patch as a new fork.
3. Prove the same consensus key cannot sign from another host, service,
   standby or restored backup. Do not read, copy or move
   `priv_validator_key.json`. Preserve the newest `priv_validator_state.json`
   in place; signing history is monotonic, not a rollback artifact.
4. Record height, active app version, bonded/jailed status, missed-block
   baseline and fresh external signatures. Retain the exact old binary/config
   and establish a verified chain-specific recovery backup through the
   approved procedure without exposing key material.
5. Stage and verify the multiplexer and matching Fibre checksums,
   platform/glibc compatibility, capacity, ABCI address match, and existing
   signer/Fibre transport bindings. Preserve the active Fibre configuration.
6. Upgrade a **non-signing Mocha-5 RPC/app node first**: controlled stop,
   replace only the reviewed binary, restart with the same home/database.
   Verify process binary identity, stable service/restart count, advancing sync
   and committed block/AppHash parity. Only after it passes, stop the existing
   Fibre server and signer, replace both with matching verified binaries, start
   the signer then Fibre, and verify readiness. Never create a second signer.
7. After restart require binary `10.5.0-mocha`, active app version `10`, no
   restart loop, `catching_up=false`, and fresh validator signatures through
   two independent Mocha-5 references.
8. Require advancing height and committed block/AppHash parity at the same
   height. Recheck external signatures, bonded/jailed status, missed-block
   delta, Fibre readiness, service stability and monitoring. Binary version
   alone is not proof that the patch upgrade succeeded.

## Historical v9-to-v10 rollback boundary — no longer available

Mocha-5 is past the v10 activation height. Do not roll a current node back to
v9. Any current v10 patch rollback requires separate compatibility evidence
for the exact database and Fibre release; keep signer state monotonic.

- **Before fork height AND before any v10 app/store migration:** a
  binary/config-only rollback to the exact retained compatible pre-v10
  release (for example previously verified `v9.0.8-mocha`) is possible only
  while local and independent chain state are both pre-activation and the
  database is proven unchanged by migration. Stop the process first; keep the
  same home/data and newest signer state, then verify sync/signing. This is
  temporary: restore the verified v10 multiplexer before activation. This
  condition is historical and cannot apply to the current network height.
- **At/after height `1082619`, after any migration, or with unknown migration
  status:** do **not** downgrade to v9 or restore a pre-fork database. Stop
  signing on an app-hash/consensus mismatch, preserve evidence and use an
  upstream-compatible forward fix or separately reviewed recovery plan. A
  retained old binary alone is not a safe rollback.
- Never roll back, delete, truncate, replace from a snapshot or reset
  `priv_validator_state.json`; never run `unsafe-reset-all` on a signer.
  Never activate a backup host holding the same consensus key. If signer
  fencing or signing-state continuity is uncertain, leave the signer stopped.
- Key movement, snapshot restoration, reset, unjail, funds/signaling actions,
  Fibre/escrow activation and firewall changes are not part of this procedure.

## Alert and recovery evidence

Alert on missing `grpc_laddr`, ABCI client/server mismatch, failure to start an
embedded app, repeated app-version switches, restarts, panic/consensus failure,
unknown migration status, wrong chain identity, stalled height or lost fresh
signatures. v10.5.0 exits when an embedded app fails: verify service-manager
restart behavior and alerting rather than accepting a restart loop as healthy.

Monitor the parent app/CometBFT process, local RPC, logs and independent commits.
Historical v9.0.6 disabled the Prometheus sink inside embedded children to
avoid duplicate collectors; this never meant consensus telemetry was optional.
Do not delete the historical-binary directory to troubleshoot a validator.

## Sources

- [Official v10.5.0-mocha release](https://github.com/celestiaorg/celestia-app/releases/tag/v10.5.0-mocha)
- [Pinned Go module](https://github.com/celestiaorg/celestia-app/blob/6013e758d5dceb75827ad191c8d739d7c43cfa04/go.mod)
- [Pinned embedding constants](https://github.com/celestiaorg/celestia-app/blob/3b77dc2f5b00e1a646a2e9dd98b5c024a0d9ad8a/internal/embedding/data.go)
- [Mocha app v10 activation/signaling](https://mocha.celenium.io/upgrade/10?tab=signals&page=1)
- [Signaling queries and pending-plan gate](validator-signaling.md)
- [Keys and signer boundaries](keys.md)

General multiplexer/configuration background was reviewed from official docs
commit `8fbaa868a323c13d3edae2875d9b27765eb29c45` (consensus installation,
validator and Mocha pages). The release and embedding pins above supersede
that historical documentation's version matrix.
