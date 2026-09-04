# Celestia Mainnet Bridge Node

A bridge node is the heavy data-availability (DA) role. It imports blocks from
an archival consensus source, validates and erasure-codes them, and serves
shares to the DA network. Current celestia-node DA roles are **bridge** and
**light** only.

## Pinned software

- Network: `celestia`
- celestia-node: `v0.32.1`
- Source commit: `8fc6945a38db8af6277d906c5d313a70db33c444`
- Go: `1.26.5`
- Store: `$HOME/.celestia-bridge`

Verify release announcements before changing these pins. Do not install from an
unpinned branch or pipe a remote script into a shell.

## Capacity and CPU gate

| Profile | CPU | Memory | NVMe | Network |
| --- | ---: | ---: | ---: | ---: |
| Non-archival bridge | 32 cores | 64 GB | 25 TiB | 1 Gbps |
| Archival bridge | 32 cores | 64 GB | 637 TiB | 1 Gbps |

The non-archival figure assumes a conservative 7-day planning window and the
128 MB per 6 seconds maximum-throughput envelope. The archival figure assumes
one year at that envelope. Actual use may be lower, but retain at least one
month of maximum-throughput capacity as free space.

Before provisioning, run the official celestia-app CPU benchmark. Prefer CPUs
with at least 32 cores plus GFNI and SHA-NI support. A core count alone does not
prove the host can sustain the workload.

## Network prerequisites

- Initial bridge sync requires an **archival celestia-app consensus gRPC
  source** with complete historical blocks. A normal pruned public endpoint is
  not sufficient.
- Expose DA P2P port `2121` on both TCP and UDP to the public network.
- Keep DA JSON-RPC port `26658` on loopback. Expose it only through a deliberately
  authenticated, TLS-protected, rate-limited boundary.
- Confirm storage capacity, endpoint retention, firewall policy, and clock sync
  before initialization.

## Build from the pinned source

Install Go `1.26.5` and standard build dependencies through your trusted OS or
Go distribution process, then verify `go version` before building.

```bash
go version
test "$(go env GOVERSION)" = "go1.26.5"

NODE_TAG="v0.32.1"
NODE_COMMIT="8fc6945a38db8af6277d906c5d313a70db33c444"
BUILD_ROOT="$(mktemp -d -p /tmp celestia-node-build.XXXXXX)"

git clone --filter=blob:none --depth 1 --branch "$NODE_TAG" \
  https://github.com/celestiaorg/celestia-node.git "$BUILD_ROOT/src"
test "$(git -C "$BUILD_ROOT/src" rev-parse HEAD)" = "$NODE_COMMIT"

make -C "$BUILD_ROOT/src" build cel-key
install -d "$BUILD_ROOT/stage/bin"
install -m 0755 "$BUILD_ROOT/src/build/celestia" \
  "$BUILD_ROOT/stage/bin/celestia"
install -m 0755 "$BUILD_ROOT/src/cel-key" \
  "$BUILD_ROOT/stage/bin/cel-key"

"$BUILD_ROOT/stage/bin/celestia" version
```

Keep the staging directory until the binary version and commit output have been
reviewed. For a new, non-running node, install the reviewed staged binaries at
`$HOME/.local/bin/`. Replacing a live binary and restarting a service are
separate, approval-controlled operations.

## Initialize

Select and verify an archival consensus gRPC service. For TLS endpoints, add
`--core.tls`; omit it only for a trusted plaintext connection.

```bash
"$HOME/.local/bin/celestia" bridge init \
  --node.store "$HOME/.celestia-bridge" \
  --core.ip <archival-consensus-grpc-host> \
  --core.port <grpc-port> \
  --core.tls \
  --p2p.network celestia
```

Initialization creates the DA store and its local keyring. Follow the separate
[key custody guide](keys.md); never copy secret material into terminal history,
documentation, tickets, or logs.

Review `$HOME/.celestia-bridge/config.toml`, confirm the selected network and
archival source, and verify JSON-RPC remains loopback-bound before starting.

## Service template

Replace only the endpoint placeholders after review. The unit assumes the
binary is installed under the service user's home.

```ini
[Unit]
Description=Celestia mainnet bridge node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<service-user>
ExecStart=%h/.local/bin/celestia bridge start --node.store %h/.celestia-bridge --core.ip <archival-consensus-grpc-host> --core.port <grpc-port> --core.tls --p2p.network celestia
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Do not add `--archival` unless the 637 TiB planning profile, retention intent,
and ongoing capacity alerts have been approved. Decide before the store's first
start: v0.32.1 refuses conversion from a previously pruned store back to
archival mode. If archival retention is later required, provision and verify a
separate new store; do not reset or delete the working store.

## Verify

```bash
systemctl is-active celestia-bridge.service
"$HOME/.local/bin/celestia" header sync-state \
  --node.store "$HOME/.celestia-bridge"
"$HOME/.local/bin/celestia" p2p info \
  --node.store "$HOME/.celestia-bridge"
ss -lntup | grep -E '(:2121|:26658)'
journalctl -u celestia-bridge.service --since "15 minutes ago" --no-pager
```

Healthy means the service is stable, the header height advances toward an
independent mainnet reference, DA peers are present, `2121` is reachable over
TCP and UDP, `26658` is not publicly bound, and disk growth has safe headroom.
A running process alone is not proof of health.

## Upgrade discipline

1. Confirm the announced mainnet tag and commit from official sources.
2. Build in a new staging directory and verify the commit and reported version.
3. Preserve the current binary as the rollback artifact.
4. If crossing from a release before `v0.31.3`, run the role-specific
   `config-update` while the service is stopped and review the merged config.
5. Replace and restart only after approval, then repeat every verification
   above.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/data-availability/bridge-node`
- `operate/data-availability/install-celestia-node`
- `operate/networks/mainnet-beta`
- `operate/maintenance/troubleshooting`
