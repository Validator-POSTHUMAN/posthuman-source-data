# Celestia Mocha-5 Multiplexer

The Celestia multiplexer is a `celestia-appd` consensus-node feature. It is not
a `celestia-node` DA role and does not replace bridge or light nodes.

The multiplexer keeps one CometBFT instance while selecting an embedded legacy
application for historical app versions or the native current application. It
observes `AppVersion` changes and switches application execution without a
whole-binary swap at the upgrade boundary. The normal operator entry point
remains `celestia-appd start`; there is no separate multiplexer service.

Mocha-5 is a new chain from height 1. Never reuse Mocha-4 consensus data,
signer state, home directories, snapshots, or service arguments for Mocha-5.

## Current official pin

| Item | Mocha-5 value |
| --- | --- |
| Chain ID | `mocha-5` |
| Release tag | `v9.0.6-mocha` |
| Git commit | `6f4b596e47f80683adb1a161ca7cb640dcd9d206` |
| Source module | `github.com/celestiaorg/celestia-app/v9` |
| Source-build Go version | `1.26.5` |
| Linux runtime floor | glibc `2.38` or later; Ubuntu 24.04 or equivalent |
| Supported release architectures | Linux and macOS, `amd64` and `arm64` |

The official `v9.0.6-mocha` and `v9.0.6` tags point to the same commit. Keep
the Mocha release label and chain identity explicit; a shared commit does not
make mainnet and testnet state interchangeable.

At the pinned commit, the multiplexer build embeds these historical app
binaries:

- app version 3: `v3.12.0`
- app version 4: `v4.1.0`
- app version 5: `v5.0.12`
- app version 6: `v6.4.4`
- app version 7: `v7.0.2-mocha`
- app version 8: `v8.0.8`

These are exact upstream embedding constants. Do not substitute historical
assets or import a Mocha-4 binary directory into a Mocha-5 home.

## Deployment model and boundaries

- The default upstream `make build` and `make install` targets use build tags
  `ledger,multiplexer`. `make install-standalone` omits multiplexer support.
- Official release archives named `celestia-app_<OS>_<arch>.tar.gz` are
  multiplexer builds. Archives containing `standalone` omit it.
- A multiplexer binary must run with CometBFT. Starting its application without
  CometBFT fails closed.
- The multiplexer supports the historical ABCI 1.0 and ABCI 2.0 boundaries used
  by the embedded applications.
- Multiplexer is an alternative to whole-binary switching. Do not layer an
  unreviewed second automatic binary-switch mechanism around it.
- It does not relax consensus-key custody, signer-state continuity, backup, or
  one-live-signer requirements.

## Stage and verify an official release

This stages the Mocha release without replacing a live binary. Select only an
official multiplexer archive, validate it against the release checksum file,
and inspect its metadata before activation.

```bash
set -eu

APP_TAG="v9.0.6-mocha"
APP_COMMIT="6f4b596e47f80683adb1a161ca7cb640dcd9d206"

case "$(uname -m)" in
  x86_64) ASSET="celestia-app_Linux_x86_64.tar.gz" ;;
  aarch64|arm64) ASSET="celestia-app_Linux_arm64.tar.gz" ;;
  *) printf 'Unsupported architecture: %s\n' "$(uname -m)" >&2; exit 1 ;;
esac

STAGE="$(mktemp -d -p /tmp "celestia-app-${APP_TAG}.XXXXXX")"
BASE_URL="https://github.com/celestiaorg/celestia-app/releases/download/${APP_TAG}"

curl --proto '=https' --tlsv1.2 -fL \
  "${BASE_URL}/${ASSET}" -o "${STAGE}/${ASSET}"
curl --proto '=https' --tlsv1.2 -fL \
  "${BASE_URL}/checksums.txt" -o "${STAGE}/checksums.txt"

(
  cd "$STAGE"
  awk -v file="$ASSET" '$2 == file || $2 == "*" file {print}' \
    checksums.txt > selected-checksum.txt
  test "$(wc -l < selected-checksum.txt)" -eq 1
  sha256sum -c selected-checksum.txt
  mkdir unpacked
  tar -xzf "$ASSET" -C unpacked
)

test -x "$STAGE/unpacked/celestia-appd"
"$STAGE/unpacked/celestia-appd" version --long
printf 'Expected commit: %s\n' "$APP_COMMIT"
printf 'Staged binary: %s\n' "$STAGE/unpacked/celestia-appd"
```

Confirm the reported version is `9.0.6-mocha`, the commit is the pinned commit,
and the build tags include `multiplexer`. Keep the staged artifact until review
is complete. Installing it into the active binary path and restarting the node
are separate, approval-controlled operations.

For a source build, pin both tag and commit and use Go `1.26.5`. At this source
revision, the standard multiplexer target downloads the six historical release
archives before embedding them. Review that dependency path and verify the
historical assets before treating a locally built binary as production-ready.

## Mocha-5 configuration contract

Use a dedicated home ending in `-mocha-5`; this guide uses
`$HOME/.celestia-app-mocha-5`. Before activation, inspect the effective service
arguments and configuration:

```bash
MOCHA_5_HOME="$HOME/.celestia-app-mocha-5"

test -f "$MOCHA_5_HOME/config/genesis.json"
test "$(jq -r '.chain_id // .genesis.chain_id' \
  "$MOCHA_5_HOME/config/genesis.json")" = "mocha-5"

grep -E '^[[:space:]]*proxy_app[[:space:]]*=' \
  "$MOCHA_5_HOME/config/config.toml"
grep -E '^[[:space:]]*grpc_laddr[[:space:]]*=' \
  "$MOCHA_5_HOME/config/config.toml"
```

The effective configuration must satisfy both conditions:

1. `rpc.grpc_laddr` is non-empty. Upstream documents
   `tcp://127.0.0.1:9098` as the loopback example.
2. The ABCI client `proxy_app` and ABCI server `address` values match. Upstream
   documents `tcp://127.0.0.1:36658` as the multiplexer default pair.

Keep these internal endpoints on loopback unless an explicit protected design
requires otherwise. A mismatch is a startup blocker, not a reason to alter
consensus data.

## Upgrade and recovery gate

Before changing an existing Mocha-5 validator:

1. Verify chain ID `mocha-5`, dedicated home, service, current binary path,
   version, commit, build tags, and public consensus identity.
2. Reject any home, snapshot, database, or signer-state path inherited from
   Mocha-4.
3. Confirm active Mocha upgrade instructions and signaling state.
4. Preserve configuration, the Mocha-5 consensus signer, and the newest
   Mocha-5 `priv_validator_state.json` through the approved backup process.
5. Prove the same consensus key cannot sign from another host or service.
6. Check glibc compatibility before selecting the multiplexer artifact.
7. Review `rpc.grpc_laddr`, `proxy_app`, and `address` before activation.
8. Stage the binary and define a rollback artifact; do not change node data to
   solve a binary or configuration error.
9. Activate once, then verify process stability, sync, external Mocha-5
   commits, and validator signatures.

The multiplexer can sync from genesis with embedded applications, but this is
not permission to reuse Mocha-4 data or signer state. Create new Mocha-5 state
and preserve its signing history after activation.

## Verification and alert contract

Healthy operation requires all of the following:

- `celestia-appd version --long` reports the pinned Mocha version, commit, and
  `multiplexer` build tag;
- the service uses only the dedicated `-mocha-5` home and remains active
  without a restart loop;
- logs show multiplexer initialization without embedded-app startup failure;
- local RPC reports network `mocha-5`, advancing height, fresh block time, and
  `catching_up=false` after synchronization;
- external fresh Mocha-5 commits include the expected validator consensus
  address when the node is meant to sign.

Alert immediately on:

- `App cannot be started without CometBFT when using the multiplexer`;
- missing `grpc_laddr`;
- ABCI client/server address mismatch;
- any Mocha-4 chain ID, home, snapshot, database, or signer-state reference;
- failure to decompress or start an embedded application;
- repeated app-version switching, process restarts, stale height, or lost
  validator signatures.

The v9.0.6 source disables the Prometheus sink only in an embedded child app to
avoid duplicate collector registration. This does not mean consensus telemetry
is unavailable: monitor the parent process, CometBFT RPC, service state, logs,
and external commits.

If an old embedded artifact is suspected, preserve and inventory the current
historical-binary directory, then stage a verified Mocha-5 replacement set. Do
not apply a broad deletion instruction from troubleshooting material to a
validator.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `constants/mocha_versions.json`
- `app/operate/networks/mocha-testnet/page.mdx`
- `app/operate/consensus-validators/install-celestia-app/page.mdx`
- `app/operate/consensus-validators/validator-node/page.mdx`

Evidence reviewed from official celestia-app tag `v9.0.6-mocha`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`:

- `go.mod`
- `Makefile`
- `.goreleaser.yaml`
- `multiplexer/README.md`
- `multiplexer/cmd/start.go`
- `multiplexer/abci/multiplexer.go`
- `multiplexer/appd/run.go`
- `cmd/celestia-appd/cmd/modify_root_command_multiplexer.go`
- `internal/embedding/data.go`
- `docs/release-notes/release-notes.md`
