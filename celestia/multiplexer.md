# Celestia Mainnet Multiplexer

The Celestia multiplexer is a `celestia-appd` consensus-node feature. It is not
a `celestia-node` DA role and does not replace bridge or light nodes.

The multiplexer keeps one CometBFT instance while selecting an embedded legacy
application for historical app versions or the native current application. It
observes `AppVersion` changes and switches application execution without a
whole-binary swap at the upgrade boundary. The normal operator entry point
remains `celestia-appd start`; there is no separate multiplexer service.

## Current official pin

| Item | Mainnet value |
| --- | --- |
| Chain ID | `celestia` |
| Release tag | `v9.0.6` |
| Git commit | `6f4b596e47f80683adb1a161ca7cb640dcd9d206` |
| Source module | `github.com/celestiaorg/celestia-app/v9` |
| Source-build Go version | `1.26.5` |
| Linux runtime floor | glibc `2.38` or later; Ubuntu 24.04 or equivalent |
| Supported release architectures | Linux and macOS, `amd64` and `arm64` |

The official mainnet and Mocha release tags point to the same commit, but use
the network-specific tag and chain identity. Do not substitute the Mocha tag
for a mainnet release procedure.

At the pinned commit, the multiplexer build embeds these historical app
binaries:

- app version 3: `v3.12.0`
- app version 4: `v4.1.0`
- app version 5: `v5.0.12`
- app version 6: `v6.4.4`
- app version 7: `v7.0.2-mocha`
- app version 8: `v8.0.8`

The `v7.0.2-mocha` label is the exact upstream embedding constant in v9.0.6.
Do not silently replace an embedded asset based on its name.

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

This stages a release without replacing a live binary. Select only an official
multiplexer archive, validate it against the release checksum file, and inspect
its metadata before activation.

```bash
set -eu

APP_TAG="v9.0.6"
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

Confirm the reported version is `9.0.6`, the commit is the pinned commit, and
the build tags include `multiplexer`. Keep the staged artifact until review is
complete. Installing it into the active binary path and restarting the node are
separate, approval-controlled operations.

For a source build, pin both tag and commit and use Go `1.26.5`. At this source
revision, the standard multiplexer target downloads the six historical release
archives before embedding them. Review that dependency path and verify the
historical assets before treating a locally built binary as production-ready.

## Configuration contract

Set `CELESTIA_HOME` to the reviewed mainnet consensus home. Before activation,
inspect the effective service arguments and configuration:

```bash
CELESTIA_HOME="$HOME/.celestia-app"

test -f "$CELESTIA_HOME/config/genesis.json"
test "$(jq -r '.chain_id // .genesis.chain_id' \
  "$CELESTIA_HOME/config/genesis.json")" = "celestia"

grep -E '^[[:space:]]*proxy_app[[:space:]]*=' \
  "$CELESTIA_HOME/config/config.toml"
grep -E '^[[:space:]]*grpc_laddr[[:space:]]*=' \
  "$CELESTIA_HOME/config/config.toml"
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

Before changing an existing validator:

1. Verify the exact mainnet home, service, current binary path, version, commit,
   build tags, and chain ID.
2. Confirm active upgrade instructions and network signaling state.
3. Preserve configuration, the consensus signer, and the newest
   `priv_validator_state.json` through the approved backup process.
4. Prove the same consensus key cannot sign from another host or service.
5. Check glibc compatibility before selecting the multiplexer artifact.
6. Review `rpc.grpc_laddr`, `proxy_app`, and `address` before activation.
7. Stage the binary and define a rollback artifact; do not change node data to
   solve a binary or configuration error.
8. Activate once, then verify process stability, sync, external commits, and
   validator signatures.

The multiplexer can sync from genesis with embedded applications, but this is
not permission to discard a recoverable database or signer state. Never lower,
regenerate, or replace signer state during a binary-only upgrade.

## Verification and alert contract

Healthy operation requires all of the following:

- `celestia-appd version --long` reports the pinned version, commit, and
  `multiplexer` build tag;
- the service remains active without a restart loop;
- logs show multiplexer initialization without embedded-app startup failure;
- local RPC reports network `celestia`, advancing height, fresh block time, and
  `catching_up=false` after synchronization;
- external fresh commits include the expected validator consensus address when
  the node is meant to sign.

Alert immediately on:

- `App cannot be started without CometBFT when using the multiplexer`;
- missing `grpc_laddr`;
- ABCI client/server address mismatch;
- failure to decompress or start an embedded application;
- repeated app-version switching, process restarts, stale height, or lost
  validator signatures.

The v9.0.6 source disables the Prometheus sink only in an embedded child app to
avoid duplicate collector registration. This does not mean consensus telemetry
is unavailable: monitor the parent process, CometBFT RPC, service state, logs,
and external commits.

If an old embedded artifact is suspected, preserve and inventory the current
historical-binary directory, then stage a verified replacement set. Do not
apply a broad deletion instruction from troubleshooting material to a
production validator.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `constants/mainnet_versions.json`
- `app/operate/consensus-validators/install-celestia-app/page.mdx`
- `app/operate/consensus-validators/validator-node/page.mdx`

Evidence reviewed from official celestia-app tag `v9.0.6`, commit
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
