# Celestia Mocha-5 Bridge Node

A bridge node is the heavy data-availability (DA) role. It imports blocks from
an archival consensus source, validates and erasure-codes them, and serves
shares to the DA network. Current celestia-node DA roles are **bridge** and
**light** only.

## Network and software pins

- Consensus chain ID: `mocha-5`
- DA P2P network: `mocha`
- celestia-node: `v0.32.1-mocha`
- Source commit: `8fc6945a38db8af6277d906c5d313a70db33c444`
- Go: `1.26.5`
- Store: `$HOME/.celestia-bridge-mocha-5`

Mocha-5 started from height 1 and is not an in-place upgrade from Mocha-4.
Never reuse a Mocha-4 DA store, consensus data directory, or signer-state file.
Do not install from an unpinned branch or pipe a remote script into a shell.

## Capacity and CPU gate

| Profile | CPU | Memory | NVMe | Network |
| --- | ---: | ---: | ---: | ---: |
| Non-archival bridge | 32 cores | 64 GB | 25 TiB | 1 Gbps |
| Archival bridge | 32 cores | 64 GB | 637 TiB | 1 Gbps |

These official planning profiles use a conservative 7-day window for
non-archival operation and one year for archival operation, both at the
128 MB per 6 seconds maximum-throughput envelope. Actual use may be lower.
Maintain at least one month of maximum-throughput capacity as free space.

Run the official celestia-app CPU benchmark before provisioning. Prefer at
least 32 cores with GFNI and SHA-NI support; core count alone is not proof of
sufficient throughput.

## Network prerequisites

- Initial bridge sync requires an **archival Mocha-5 celestia-app consensus
  gRPC source** with complete history from height 1. A pruned endpoint and any
  Mocha-4 endpoint are invalid.
- Expose DA P2P port `2121` on TCP and UDP.
- Keep DA JSON-RPC `26658` on loopback unless it is deliberately protected by
  authentication, TLS, and rate limits.
- Verify the endpoint chain ID, archival retention, firewall policy, storage,
  and clock synchronization before initialization.

## Build from the pinned source

Install Go `1.26.5` and build dependencies from trusted distribution channels,
then verify the toolchain.

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

First verify the proposed consensus source is on `mocha-5` and retains every
block required for initial sync.

```bash
celestia-appd status --node <consensus-rpc-url> | \
  jq -e '.NodeInfo.network == "mocha-5"'

"$HOME/.local/bin/celestia" bridge init \
  --node.store "$HOME/.celestia-bridge-mocha-5" \
  --core.ip <archival-mocha-5-consensus-grpc-host> \
  --core.port <grpc-port> \
  --core.tls \
  --p2p.network mocha
```

Add `--core.tls` only for a TLS endpoint. Initialization creates the new DA
store and local keyring. Do not copy any Mocha-4 directory into this store.
Follow [Keys and signer boundaries](keys.md) for custody rules.

Review the generated config and confirm `mocha`, the Mocha-5 upstream, and the
loopback JSON-RPC bind before starting.

## Service template

```ini
[Unit]
Description=Celestia Mocha-5 bridge node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<service-user>
ExecStart=%h/.local/bin/celestia bridge start --node.store %h/.celestia-bridge-mocha-5 --core.ip <archival-mocha-5-consensus-grpc-host> --core.port <grpc-port> --core.tls --p2p.network mocha
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Do not add `--archival` until the 637 TiB profile, retention objective, and
capacity alerting have been approved. Decide before the store's first start:
v0.32.1 refuses conversion from a previously pruned store back to archival
mode. If archival retention is later required, provision and verify a separate
new Mocha-5 store; do not reset or delete the working store.

## Verify

```bash
systemctl is-active celestia-bridge-mocha-5.service
"$HOME/.local/bin/celestia" header sync-state \
  --node.store "$HOME/.celestia-bridge-mocha-5"
"$HOME/.local/bin/celestia" p2p info \
  --node.store "$HOME/.celestia-bridge-mocha-5"
ss -lntup | grep -E '(:2121|:26658)'
journalctl -u celestia-bridge-mocha-5.service \
  --since "15 minutes ago" --no-pager
```

Healthy means the service is stable, headers advance toward an independent
Mocha-5 reference, peers are present, `2121` is reachable on TCP and UDP,
`26658` is not public, and disk has headroom. Any Mocha-4 chain identity is a
hard failure.

## Upgrade discipline

Verify the announced Mocha tag and commit, build in a new staging directory,
retain rollback, and activate only after review. When crossing from a release
before `v0.31.3`, run
`celestia bridge config-update --p2p.network mocha --node.store "$HOME/.celestia-bridge-mocha-5"`
while stopped, inspect the merged configuration, then restart and repeat all
checks.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/getting-started/hardware-requirements`
- `operate/data-availability/bridge-node`
- `operate/data-availability/install-celestia-node`
- `operate/networks/mocha-testnet`
- `operate/maintenance/troubleshooting`
