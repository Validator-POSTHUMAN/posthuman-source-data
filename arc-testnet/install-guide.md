# Arc Network Testnet — Full Node Installation Guide

POSTHUMAN supports Arc by publishing tested, operator-focused infrastructure
documentation. This guide installs a non-signing Arc testnet follow node. It
does not configure a validator or imply a partnership or endorsement by Arc
or Circle.

Tested release: `v0.7.2` (2026-07-17). Always review the official changelog
and breaking changes before installation or upgrade.

## Requirements

- Ubuntu 24.04 or another Linux distribution with glibc 2.39+
- x86_64/amd64 or aarch64/arm64
- 64 GB+ RAM
- 1 TB+ TLC NVMe storage
- stable 24 Mbps+ network connection
- `curl`, `tar`, and `sha256sum`

The node consists of an Execution Layer (EL) and Consensus Layer (CL). The CL
retrieves finalized blocks from Arc relay endpoints, verifies certificates,
and sends blocks to the EL for execution.

## 1. Install verified binaries

The example below uses the official x86_64 Linux release and verifies the
release-provided checksum before installation.

```bash
ARC_VERSION=v0.7.2
ARC_ARCHIVE=arc-node-v0.7.2-x86_64-unknown-linux-gnu.tar.gz
ARC_TMP=$(mktemp -d)

mkdir -p "$HOME/.arc/bin"

curl -fL --retry 3 \
  -o "$ARC_TMP/$ARC_ARCHIVE" \
  "https://github.com/circlefin/arc-node/releases/download/$ARC_VERSION/$ARC_ARCHIVE"

curl -fL --retry 3 \
  -o "$ARC_TMP/$ARC_ARCHIVE.sha256" \
  "https://github.com/circlefin/arc-node/releases/download/$ARC_VERSION/$ARC_ARCHIVE.sha256"

(cd "$ARC_TMP" && sha256sum -c "$ARC_ARCHIVE.sha256")
tar -xzf "$ARC_TMP/$ARC_ARCHIVE" -C "$HOME/.arc/bin"
chmod 0755 "$HOME/.arc/bin/arc-node-execution" \
  "$HOME/.arc/bin/arc-node-consensus" \
  "$HOME/.arc/bin/arc-snapshots"
```

Verify all binaries:

```bash
$HOME/.arc/bin/arc-node-execution --version
$HOME/.arc/bin/arc-node-consensus --version
$HOME/.arc/bin/arc-snapshots --version
```

All three must report `v0.7.2` and commit
`a85368c0b0a7924e4c74035d195f96deb0291622`.

## 2. Download snapshots

Arc does not currently support syncing a new node from genesis. Bootstrap
both layers from the official snapshot service:

```bash
mkdir -p "$HOME/.arc/execution" "$HOME/.arc/consensus"

$HOME/.arc/bin/arc-snapshots download \
  --chain arc-testnet \
  --execution-path "$HOME/.arc/execution" \
  --consensus-path "$HOME/.arc/consensus"
```

Do not use `--force` on an existing node unless you intentionally approved a
destructive replacement and backed up required identity/config files.

## 3. Initialize the consensus identity

Run this once on a new node:

```bash
$HOME/.arc/bin/arc-node-consensus init \
  --home "$HOME/.arc/consensus"
```

Back up `$HOME/.arc/consensus/config/` securely. Never publish or print the
private identity material.

## 4. Create systemd services

Replace `YOUR_USERNAME` in both unit files. The recommended same-host setup
uses local IPC between EL and CL. RPC and metrics stay on loopback.

Create `/etc/systemd/system/arc-execution.service`:

```ini
[Unit]
Description=Arc Node - Execution Layer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
RuntimeDirectory=arc
Environment=RUST_LOG=info
WorkingDirectory=/home/YOUR_USERNAME/.arc
ExecStart=/home/YOUR_USERNAME/.arc/bin/arc-node-execution node \
  --chain arc-testnet \
  --datadir /home/YOUR_USERNAME/.arc/execution \
  --full \
  --disable-discovery \
  --ipcpath /run/arc/reth.ipc \
  --auth-ipc \
  --auth-ipc.path /run/arc/auth.ipc \
  --http \
  --http.addr 127.0.0.1 \
  --http.port 8545 \
  --http.api eth,net,web3,txpool,trace,debug \
  --metrics 127.0.0.1:9001 \
  --enable-arc-rpc \
  --rpc.forwarder https://rpc.quicknode.testnet.arc.network/
Restart=always
RestartSec=10
KillSignal=SIGTERM
TimeoutStopSec=300
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/arc-consensus.service`:

```ini
[Unit]
Description=Arc Node - Consensus Layer
After=arc-execution.service
Requires=arc-execution.service

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
Environment=RUST_LOG=info
WorkingDirectory=/home/YOUR_USERNAME/.arc
ExecStart=/home/YOUR_USERNAME/.arc/bin/arc-node-consensus start \
  --home /home/YOUR_USERNAME/.arc/consensus \
  --full \
  --eth-socket /run/arc/reth.ipc \
  --execution-socket /run/arc/auth.ipc \
  --rpc.addr 127.0.0.1:31000 \
  --follow \
  --follow.endpoint https://rpc.drpc.testnet.arc.network,wss=rpc.drpc.testnet.arc.network \
  --follow.endpoint https://rpc.quicknode.testnet.arc.network,wss=rpc.quicknode.testnet.arc.network \
  --follow.endpoint https://rpc.blockdaemon.testnet.arc.network,wss=rpc.blockdaemon.testnet.arc.network/websocket \
  --execution-persistence-backpressure \
  --execution-persistence-backpressure-threshold=50 \
  --metrics 127.0.0.1:29000
Restart=always
RestartSec=10
KillSignal=SIGTERM
TimeoutStopSec=300
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
```

Review the generated paths before starting:

```bash
sudo systemd-analyze verify \
  /etc/systemd/system/arc-execution.service \
  /etc/systemd/system/arc-consensus.service

sudo systemctl daemon-reload
sudo systemctl enable arc-execution arc-consensus
sudo systemctl start arc-execution
sudo systemctl start arc-consensus
```

## 5. Verify against external truth

Service state alone is not sufficient. Confirm the local height advances and
compare it with an independent Arc RPC.

```bash
systemctl is-active arc-execution arc-consensus

LOCAL_HEX=$(curl -fsS -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://127.0.0.1:8545 | jq -r .result)

REMOTE_HEX=$(curl -fsS -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://rpc.testnet.arc.network | jq -r .result)

printf 'local=%d remote=%d lag=%d\n' \
  "$LOCAL_HEX" "$REMOTE_HEX" "$((REMOTE_HEX-LOCAL_HEX))"

curl -fsS http://127.0.0.1:31000/ready
```

Repeat the height check after 30 seconds. The local height must increase.
`eth_syncing=false` by itself is not proof that the node is current.

Inspect recent logs:

```bash
sudo journalctl -u arc-execution -u arc-consensus \
  --since '10 minutes ago' --no-pager
```

## Security notes

- Keep JSON-RPC (`8545`), CL RPC (`31000`), and metrics (`9001`, `29000`) on
  `127.0.0.1` for a normal follow node.
- Do not expose `debug`, `trace`, or `txpool` namespaces publicly.
- Do not expose the Engine API. The same-host configuration above uses IPC.
- A public RPC provider requires Arc's separate hardened RPC-node profile,
  trusted peers, restricted namespaces, firewall review, and onboarding.
- Preserve the previous binaries and unit files before every upgrade.

## Official resources

- Arc: https://www.arc.io/
- Documentation: https://docs.arc.network/
- Node repository: https://github.com/circlefin/arc-node
- Release: https://github.com/circlefin/arc-node/releases/tag/v0.7.2
- Changelog: https://github.com/circlefin/arc-node/blob/main/CHANGELOG.md
- Breaking changes: https://github.com/circlefin/arc-node/blob/main/BREAKING_CHANGES.md
- Snapshots: https://snapshots.arc.network/
- Explorer: https://testnet.arcscan.app/
- Partner guidelines: https://www.arc.io/brand-guidelines-and-partner-toolkit

Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.
