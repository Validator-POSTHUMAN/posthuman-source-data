# NEAR Mainnet Validator Installation Guide

NEAR is not a Cosmos SDK chain. There is no `gaiad`-style daemon, no
Tendermint `priv_validator_key.json`, no Cosmovisor, no genesis/addrbook
bootstrap pair and no IBC. Everything below is NEAR-native.

## Network facts

| Parameter | Value |
|-----------|-------|
| Network | NEAR Mainnet |
| Chain ID | `mainnet` |
| Binary | `neard` (from [`near/nearcore`](https://github.com/near/nearcore)) |
| Latest stable release | `2.13.4` |
| Protocol version | `86` |
| Token | `NEAR` |
| Block time | ~1.1 s |
| Epoch length | 43,200 blocks (~12 h) |
| Unbonding | 4 epochs (~2 days) |
| P2P port | `24567` |
| RPC / metrics port | `3030` |
| Staking-pool factory | `poolv1.near` |
| Explorer | [nearblocks.io](https://nearblocks.io/node-explorer) |
| POSTHUMAN pool | [`posthuman.poolv1.near`](https://nearblocks.io/node-explorer/posthuman.poolv1.near) |

Always confirm the current stable tag on the
[nearcore releases page](https://github.com/near/nearcore/releases) before you
build. Mainnet runs the latest **stable** release; testnet runs the latest
**release candidate**.

## Validator roles

NEAR has two validator roles with different hardware and stake requirements:

- **Block / chunk producers** — the top 100 validators by stake. They track a
  shard, produce blocks and chunks, and carry the heaviest hardware cost.
- **Chunk validators** — everyone below the top 100. They do not track shards;
  they validate and endorse chunks. Lower RAM and storage, same 2.5% minimum
  annual reward target.

A seat requires more stake than the 300th largest staking proposal, with an
absolute floor of 25,500 NEAR. The live seat price is published on
[nearblocks.io/node-explorer](https://nearblocks.io/node-explorer) and
[near-staking.com/stats](https://near-staking.com/stats).

## Hardware

Source: [near-nodes.io hardware requirements](https://near-nodes.io/validator/hardware-validator).

| Role | CPU | RAM | Storage |
|------|-----|-----|---------|
| Chunk/block producer (recommended) | 8+ physical cores, x86_64 | 48 GB | 3 TB NVMe |
| Chunk validator (recommended) | 8+ physical cores, x86_64 | 16 GB | 2 TB NVMe |
| Chunk validator (minimum) | 8+ physical cores, x86_64 | 8 GB | 1 TB SSD, 15k IOPS |

Required CPU features: `CMPXCHG16B`, `POPCNT`, `SSE4.1`, `SSE4.2`, `AVX`,
`SHA-NI`. Verify before provisioning:

```bash
lscpu | grep -o -E 'cx16|popcnt|sse4_1|sse4_2|avx|sha_ni' | sort -u
```

Provision at least 8 GiB of RAM headroom above steady-state usage, or swap.
`neard` memory use spikes during state transitions, and an OOM kill during
your assigned chunk production costs endorsements directly.

## 1. System preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl jq build-essential pkg-config libssl-dev \
  clang cmake protobuf-compiler llvm gcc g++ make python3 \
  libcurl4-openssl-dev zlib1g-dev libdw-dev binutils-dev libiberty-dev

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
rustc --version
```

## 2. Network tuning

```bash
sudo tee /etc/sysctl.d/local.conf > /dev/null << 'EOF'
net.core.rmem_max = 8388608
net.core.wmem_max = 8388608
net.ipv4.tcp_rmem = 4096 87380 8388608
net.ipv4.tcp_wmem = 4096 16384 8388608
net.ipv4.tcp_slow_start_after_idle = 0
EOF
sudo sysctl --system
```

## 3. Build `neard`

```bash
git clone https://github.com/near/nearcore
cd nearcore
git fetch origin --tags
git tag -l --sort=-v:refname | head -5

git checkout tags/2.13.4 -b node-2.13.4   # replace with the current stable tag
make neard
./target/release/neard --version
```

The build needs roughly 1 GB of RAM per parallel job. If jobs are killed,
reduce them: `CARGO_BUILD_JOBS=8 make neard`.

Install the binary where systemd will find it:

```bash
sudo install -m 0755 target/release/neard /usr/local/bin/neard
neard --version
```

## 4. Initialise the working directory

```bash
neard --home ~/.near init --chain-id mainnet --download-genesis --download-config validator
```

This writes:

| File | Purpose |
|------|---------|
| `config.json` | node configuration |
| `genesis.json` | mainnet genesis state (large; the download runs for a while with no progress output) |
| `node_key.json` | P2P identity of the host — **not** the staking key |
| `data/` | chain state |

`--download-config` takes a profile name. Pick it deliberately:

| Profile | Use for | Notes |
|---------|---------|-------|
| `validator` | validator nodes | heavily optimised, does not keep full state, **cannot serve RPC queries** |
| `rpc` | public/internal RPC nodes | keeps recent data for all shards, serves roughly the last 5 epochs |
| `archival` | archive nodes | full history from genesis, large storage — see the Archive & Indexing guide |

Run the validator on the `validator` profile and run RPC on a **separate**
host. Do not turn a validator into a public RPC endpoint.

## 5. Sync to the chain tip

Epoch Sync is the current recommended bootstrap: it syncs from genesis without
downloading a state snapshot. It needs a fresh boot-node list.

```bash
BOOT_NODES=$(curl -s -X POST https://rpc.mainnet.near.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"network_info","params":[],"id":"dontcare"}' \
  | jq -r '.result.active_peers as $active | .result.known_producers as $known |
      $active[] as $peer | $known[] | select(.peer_id == $peer.id) |
      "\(.peer_id)@\($peer.addr)"' | paste -sd "," -)

cp ~/.near/config.json ~/.near/config.json.backup
jq --arg newBootNodes "$BOOT_NODES" '.network.boot_nodes = $newBootNodes' \
  ~/.near/config.json > ~/.near/config.tmp && mv ~/.near/config.tmp ~/.near/config.json
```

Third-party snapshots remain an option for a faster cold start; see the
Snapshot guide.

## 6. Firewall

```bash
sudo ufw allow 24567/tcp comment "NEAR P2P"
sudo ufw enable
```

Port `24567` must be reachable. Port `3030` carries both JSON-RPC and
Prometheus metrics: keep it on loopback or a private interface on a validator
and scrape it from there. Publishing `3030` from a validator host is a
deliberate exposure decision, not a default — see the Security guide.

## 7. systemd unit

```bash
sudo tee /etc/systemd/system/neard.service > /dev/null << 'EOF'
[Unit]
Description=NEAR node
Documentation=https://near-nodes.io
After=network-online.target
Wants=network-online.target

[Service]
User=near
Group=near
Type=simple
ExecStart=/usr/local/bin/neard --home /home/near/.near run
Restart=on-failure
RestartSec=30
LimitNOFILE=65535
Environment=RUST_LOG=info
Environment=RUST_BACKTRACE=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now neard
journalctl -u neard -f
```

## 8. Verify sync

```bash
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{version: .result.version.version,
         chain_id: .result.chain_id,
         protocol: .result.protocol_version,
         height: .result.sync_info.latest_block_height,
         syncing: .result.sync_info.syncing}'
```

Compare `latest_block_height` against an independent endpoint before you call
the node synced:

```bash
curl -s -X POST https://rpc.mainnet.near.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '.result.sync_info.latest_block_height'
```

`syncing` must be `false` and the local height must track the public height
within a few blocks. Never submit a staking proposal before this holds.

Use `127.0.0.1` rather than `localhost` in any high-frequency check. On a
dual-stack host `localhost` resolves to `::1` first, and a service bound to
`0.0.0.0` only answers after the IPv6 attempt times out.

## 9. Become a validator

The node itself does not stake. On NEAR, stake lives in a **staking-pool smart
contract** deployed through the `poolv1.near` factory, and the node signs for
that pool through `validator_key.json`.

Follow the **Create validator** guide for the full sequence: create the
account and access keys, deploy the pool, write `validator_key.json`, restart
`neard`, deposit stake, then `ping` every epoch.

Read the **Keys & custody** guide first. The node key, the staking key and the
pool owner's full-access key are three different things with three different
blast radii.

## Related guides

- **Create validator** — pool creation, `ping`, proposals, commission
- **Keys & custody** — `validator_key.json`, `node_key.json`, access keys
- **Security** — host hardening, RPC exposure, backups
- **Monitoring** — Prometheus exporters, endorsement ratio, alerting
- **Archive & Indexing** — archival node, split storage, indexers
- **Endpoints** — public RPC endpoints and health checks
- **Useful commands** — `near-cli-rs` and `near-validator` cheat sheet
- **Upgrades** — `neard` release upgrade procedure
- **NEAR Testnet** — the same flow against `pool.f863973.m0`

## Sources

- [near-nodes.io — compile and run a node](https://near-nodes.io/validator/compile-and-run-a-node)
- [near-nodes.io — hardware requirements](https://near-nodes.io/validator/hardware-validator)
- [near-nodes.io — epoch sync](https://near-nodes.io/intro/node-epoch-sync)
- [docs.near.org — validators](https://docs.near.org/protocol/network/validators)
- [github.com/near/nearcore](https://github.com/near/nearcore)
