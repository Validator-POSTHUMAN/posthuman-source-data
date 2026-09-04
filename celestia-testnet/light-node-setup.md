# Celestia Mocha-5 Light Node

A light node follows extended headers and performs data availability sampling
(DAS) without downloading every block. Current celestia-node DA roles are
**bridge** and **light** only.

## Network and software pins

- Consensus chain ID: `mocha-5`
- DA P2P network: `mocha`
- celestia-node: `v0.32.1-mocha`
- Source commit: `8fc6945a38db8af6277d906c5d313a70db33c444`
- Go: `1.26.5`
- Store: `$HOME/.celestia-light-mocha-5`

Mocha-5 is a new chain from height 1. Never reuse a Mocha-4 DA store,
consensus data directory, or signer-state file. Do not install from an unpinned
branch or pipe a remote script into a shell.

## Capacity

| Profile | CPU | Memory | Disk | Network |
| --- | ---: | ---: | ---: | ---: |
| Pruned light node | 1 core | 500 MB | 20 GB SSD | 56 Kbps |
| Unpruned-header light node | 1 core | 500 MB | 7 TiB NVMe | 56 Kbps |

The 20 GB profile is for normal pruned operation. The 7 TiB figure is a
one-year planning estimate for unpruned headers at the 128 MB per 6 seconds
maximum-throughput envelope. Monitor actual growth and keep capacity headroom.

## Build from the pinned source

Install Go `1.26.5` and build dependencies through trusted distribution
channels, then verify the toolchain.

```bash
go version
test "$(go env GOVERSION)" = "go1.26.5"

NODE_TAG="v0.32.1-mocha"
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

Keep staging until the reported version and commit are reviewed. For a new,
non-running node, install the reviewed staged binaries at `$HOME/.local/bin/`.
Binary activation and service restart are separate approval-controlled steps.

## Initialize a new Mocha-5 store

Verify the proposed consensus endpoint reports `mocha-5`. Add `--core.tls` only
when the endpoint supports TLS.

```bash
celestia-appd status --node <consensus-rpc-url> | \
  jq -e '.NodeInfo.network == "mocha-5"'

"$HOME/.local/bin/celestia" light init \
  --node.store "$HOME/.celestia-light-mocha-5" \
  --core.ip <mocha-5-consensus-grpc-host> \
  --core.port <grpc-port> \
  --core.tls \
  --p2p.network mocha
```

Initialization creates a new DA store and local keyring. Do not copy a
Mocha-4 directory into it. Follow [Keys and signer boundaries](keys.md).

Keep JSON-RPC `26658` on loopback unless an authenticated, TLS-protected,
rate-limited access layer is explicitly designed and reviewed.

## Service template

```ini
[Unit]
Description=Celestia Mocha-5 light node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<service-user>
ExecStart=%h/.local/bin/celestia light start --node.store %h/.celestia-light-mocha-5 --core.ip <mocha-5-consensus-grpc-host> --core.port <grpc-port> --core.tls --p2p.network mocha
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

This guide does not submit blobs or other transactions.

## Verify

```bash
systemctl is-active celestia-light-mocha-5.service
"$HOME/.local/bin/celestia" header sync-state \
  --node.store "$HOME/.celestia-light-mocha-5"
"$HOME/.local/bin/celestia" p2p info \
  --node.store "$HOME/.celestia-light-mocha-5"
"$HOME/.local/bin/celestia" state account-address \
  --node.store "$HOME/.celestia-light-mocha-5"
ss -lntp | grep ':26658'
journalctl -u celestia-light-mocha-5.service \
  --since "15 minutes ago" --no-pager
```

Healthy means the service remains stable, headers advance toward an independent
Mocha-5 reference, sampling has no persistent errors, peers are present, RPC is
loopback-bound, and disk has headroom. Any Mocha-4 chain identity is a hard
failure; stale or unknown freshness is degraded.

## Upgrade discipline

Build replacements in a new staging directory, verify the announced Mocha tag
and commit, retain rollback, and activate only after review. When upgrading
from before `v0.31.3`, run
`celestia light config-update --p2p.network mocha --node.store "$HOME/.celestia-light-mocha-5"`
while stopped and inspect the merged configuration before activation.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/data-availability/light-node/quickstart`
- `operate/data-availability/light-node/advanced`
- `operate/data-availability/install-celestia-node`
- `operate/networks/mocha-testnet`
