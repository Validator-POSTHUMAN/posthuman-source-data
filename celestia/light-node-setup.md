# Celestia Mainnet Light Node

A light node follows extended headers and performs data availability sampling
(DAS) without downloading every block. Current celestia-node DA roles are
**bridge** and **light** only.

## Pinned software

- Network: `celestia`
- celestia-node: `v0.32.1`
- Source commit: `8fc6945a38db8af6277d906c5d313a70db33c444`
- Go: `1.26.5`
- Store: `$HOME/.celestia-light`

Do not install from an unpinned branch or pipe a remote script into a shell.

## Capacity

| Profile | CPU | Memory | Disk | Network |
| --- | ---: | ---: | ---: | ---: |
| Pruned light node | 1 core | 500 MB | 20 GB SSD | 56 Kbps |
| Unpruned-header light node | 1 core | 500 MB | 7 TiB NVMe | 56 Kbps |

The 20 GB profile is for normal pruned operation. The 7 TiB figure is a
one-year planning estimate for retaining unpruned headers at the 128 MB per
6 seconds throughput envelope; actual use may be lower. Monitor real growth and
keep capacity headroom.

## Build from the pinned source

Install Go `1.26.5` and build dependencies through trusted distribution
channels, then verify the toolchain.

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

Keep the staging directory until the version and commit have been reviewed. For
a new, non-running node, install the reviewed staged binaries at
`$HOME/.local/bin/`. Binary activation and service restart are separate
approval-controlled steps.

## Initialize

A light node uses a consensus gRPC endpoint for state access. Verify the endpoint
serves mainnet before using it. Add `--core.tls` only when the endpoint provides
TLS.

```bash
"$HOME/.local/bin/celestia" light init \
  --node.store "$HOME/.celestia-light" \
  --core.ip <consensus-grpc-host> \
  --core.port <grpc-port> \
  --core.tls \
  --p2p.network celestia
```

Initialization creates the DA store and local keyring. Follow [Keys and signer
boundaries](keys.md) for custody rules.

Keep JSON-RPC `26658` on loopback unless an authenticated, TLS-protected,
rate-limited access layer is intentionally designed and reviewed.

## Service template

```ini
[Unit]
Description=Celestia mainnet light node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<service-user>
ExecStart=%h/.local/bin/celestia light start --node.store %h/.celestia-light --core.ip <consensus-grpc-host> --core.port <grpc-port> --core.tls --p2p.network celestia
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

This guide does not submit blobs or other transactions. Fund and transaction
work requires a separate reviewed procedure.

## Verify

```bash
systemctl is-active celestia-light.service
"$HOME/.local/bin/celestia" header sync-state \
  --node.store "$HOME/.celestia-light"
"$HOME/.local/bin/celestia" p2p info \
  --node.store "$HOME/.celestia-light"
"$HOME/.local/bin/celestia" state account-address \
  --node.store "$HOME/.celestia-light"
ss -lntp | grep ':26658'
journalctl -u celestia-light.service --since "15 minutes ago" --no-pager
```

Healthy means the service remains stable, headers advance toward an independent
mainnet reference, sampling continues without persistent errors, peers are
present, RPC stays loopback-bound, and disk has headroom. Treat stale or unknown
header freshness as degraded rather than healthy.

## Upgrade discipline

Build every replacement in a new staging directory, verify the announced tag
and commit, retain the current binary for rollback, and restart only after
review. When upgrading from a release earlier than `v0.31.3`, run
`celestia light config-update --p2p.network celestia` while stopped and inspect
the merged configuration before activation.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/data-availability/light-node/quickstart`
- `operate/data-availability/light-node/advanced`
- `operate/data-availability/install-celestia-node`
- `operate/maintenance/troubleshooting`
