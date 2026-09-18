# Ethereum Node Installation — Execution + Consensus, Any Client Pair

An Ethereum node is **two processes**, not one. An execution layer (EL) client
holds state and executes transactions; a consensus layer (CL) client runs
proof-of-stake and drives the EL over the Engine API. Neither works alone, and
they authenticate to each other with a shared JWT secret.

A third process, the **validator client (VC)**, is optional and only needed if
you are staking. It is covered in the *Create validator* guide, not here.

```
                 +-------------------+   Engine API :8551   +------------------+
  P2P :30303 --- | Execution client  | <------------------> | Consensus client | --- P2P :9000
                 |  Geth / Nethermind|    JWT-authenticated |  Lighthouse /    |
                 |  Besu / Reth      |                      |  Teku / Nimbus…  |
                 +-------------------+                      +--------+---------+
                       JSON-RPC :8545                                 | Beacon API :5052
                                                             +--------+---------+
                                                             | Validator client | (staking only)
                                                             +------------------+
```

Verified against client releases published as of **2026-09-18**. Mainnet runs
the **Fusaka** fork (activated 2025-12-03, epoch 411392); **Glamsterdam** is the
next upgrade and has no confirmed mainnet date.

---

## 1. Pick your two clients — this is a real decision

Ethereum has no "default" client, and picking the popular one is the one choice
that can cost you money. Consensus is reached by 2/3 of stake. If a client with
more than 1/3 share has a bug, the chain stops finalising. If a client with more
than 2/3 share forks, the fork finalises and the validators on it **cannot come
back without being slashed** — the full 32 ETH.

Share of the network as reported by [clientdiversity.org](https://clientdiversity.org/)
on 2026-09-18. Consensus figures come from Miga Labs crawls and are updated
daily; execution figures are self-reported to supermajority.info, cover about
59% of the network, and are stale in places — treat them as an order of
magnitude, not a measurement.

| Execution client | Share | Language | Notes |
|---|---|---|---|
| [Nethermind](https://github.com/NethermindEth/nethermind) `1.39.3` | ~43% | C#/.NET | Snap sync, good pruning story, solid metrics. |
| [Geth](https://github.com/ethereum/go-ethereum) `v1.17.5` | ~43% | Go | Reference implementation, most documentation, most tooling assumes it. |
| [Besu](https://github.com/hyperledger/besu) `26.8.1` | ~8% | Java | Minority client. Enterprise features, higher RAM. |
| [Reth](https://github.com/paradigmxyz/reth) `v2.6.0` | ~3% | Rust | Minority client. No snap sync; fast staged full sync, strong archive story. |
| [Erigon](https://github.com/erigontech/erigon) `v3.6.1` | ~3% | Go | Minority client. No snap sync; the cheapest archive node. Ships its own CL (Caplin). |

| Consensus client | Share | Language | Notes |
|---|---|---|---|
| [Lighthouse](https://github.com/sigp/lighthouse) `v8.2.2` | ~51.6% | Rust | **Over the 33% danger line.** Avoid for a new node unless you have a specific reason. |
| [Prysm](https://github.com/OffchainLabs/prysm) `v7.1.8` | ~19.9% | Go | Large share, extensive docs. |
| [Nimbus](https://github.com/status-im/nimbus-eth2) `v26.8.0` | ~10.7% | Nim | Minority. Lowest resource footprint; one binary runs beacon + validator. |
| [Teku](https://github.com/Consensys/teku) `26.9.0` | ~7.4% | Java | Minority. Beacon and validator in one process if you want it. |
| [Lodestar](https://github.com/ChainSafe/lodestar) `v1.48.0` | ~3.0% | TypeScript | Minority. |
| [Grandine](https://github.com/grandinetech/grandine) `2.0.6` | ~1.6% | Rust | Minority, newest of the set. |

**POSTHUMAN recommendation for a new node: a minority client on at least one
side, and preferably both.** Nethermind + Nimbus, Besu + Teku and Reth + Lodestar
are all production-viable pairs. The instructions below are written so that any
EL pairs with any CL — the Engine API contract is identical.

---

## 2. Hardware

Current guidance is [EIP-7870](https://eips.ethereum.org/EIPS/eip-7870), which
is the number to quote when someone asks why the box costs what it costs.

| | Minimum | Recommended (full node) | Validating |
|---|---|---|---|
| CPU | 2+ cores | 4+ cores | 8+ cores |
| RAM | 16 GB | 32 GB | 64 GB |
| Disk | 2 TB NVMe SSD | 4 TB NVMe SSD | 4 TB NVMe SSD |
| Bandwidth | 25 Mbit/s | 50 down / 15 up | 50 down / 25+ up |

Hard rules learned the expensive way:

- **NVMe SSD, not SATA, and never a hard disk.** Sync is IOPS-bound. A node on
  spinning rust will never catch the head.
- **No DRAM-less and no QLC drives.** They pass a benchmark and then fall behind
  under sustained random writes. Yorick Downe's
  [SSD list](https://gist.github.com/yorickdowne/f3a3e79a573bf35767cd002cc977b038)
  is the reference the staking community actually uses.
- **Unmetered connection.** Since Fusaka the node also gossips blob data columns
  (PeerDAS), and blob throughput is raised further by BPO forks. Budget upward,
  not downward.
- **2 TB is already tight in 2026 and is expected to be insufficient by 2027.**
  Buy 4 TB if you intend to leave the node alone.

Approximate execution-layer disk, from ethereum.org:

| Client | Snap/fast sync | Full archive |
|---|---|---|
| Geth | 500 GB+ | 12 TB+ |
| Nethermind | 500 GB+ | 12 TB+ |
| Besu | 800 GB+ | 12 TB+ |
| Erigon | n/a (full prune ~2 TB) | 2.5 TB+ |
| Reth | n/a (full prune ~1.2 TB) | 2.2 TB+ |

Consensus layer adds roughly 100–200 GB for a pruned beacon node.

---

## 3. Base system

````bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git jq unzip ufw chrony
````

`chrony` is not optional on a staking node. Attestations are slot-bound; a clock
that drifts by more than a second turns into missed duties that look like a
networking fault.

````bash
timedatectl status | grep -E 'synchronized|NTP'
````

### Firewall

Only P2P belongs on the public internet. RPC, Engine API, metrics and the
beacon API stay local.

````bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'ssh'
sudo ufw allow 30303/tcp comment 'EL p2p'
sudo ufw allow 30303/udp comment 'EL discovery'
sudo ufw allow 9000/tcp comment 'CL p2p'
sudo ufw allow 9000/udp comment 'CL discovery'
sudo ufw allow 9001/udp comment 'CL quic'
sudo ufw enable
sudo ufw status numbered
````

Ports that must **never** be opened: `8545` (JSON-RPC), `8546` (WS),
`8551` (Engine API), `5052` (Beacon API), `5054`/`6060`/`8008` (metrics).
Opening `8545` to the internet on a node that also holds keys is the single
most common way staking setups get drained.

If the clients run in Docker, note that Docker publishes ports **past** ufw.
Bind explicitly to `127.0.0.1` in the Compose file; do not rely on the firewall.

### Dedicated users

Separate users so one client cannot read the other's data directory.

````bash
sudo useradd --no-create-home --shell /bin/false execution
sudo useradd --no-create-home --shell /bin/false consensus
sudo mkdir -p /var/lib/execution /var/lib/consensus
sudo chown -R execution:execution /var/lib/execution
sudo chown -R consensus:consensus /var/lib/consensus
````

### JWT secret

The Engine API is authenticated with a 32-byte hex secret shared by exactly the
two local processes. It is not a wallet key, but anyone who holds it can drive
your execution client.

````bash
sudo mkdir -p /var/lib/ethereum
sudo openssl rand -hex 32 | tr -d '\n' | sudo tee /var/lib/ethereum/jwt.hex > /dev/null
sudo groupadd -f ethereum
sudo usermod -aG ethereum execution
sudo usermod -aG ethereum consensus
sudo chown root:ethereum /var/lib/ethereum/jwt.hex
sudo chmod 640 /var/lib/ethereum/jwt.hex
````

Verify it is exactly 64 hex characters with no trailing newline — a newline is a
classic cause of `Unauthorized` on the Engine API:

````bash
sudo wc -c /var/lib/ethereum/jwt.hex   # must print 64
````

---

## 4. Execution client

Install exactly one. Every unit below writes to `/var/lib/execution`, listens on
`8551` for the Engine API and `8545` on loopback only.

### Geth

The release tarball filename embeds a build commit, so take the exact URL from
the [downloads page](https://geth.ethereum.org/downloads) and verify the
published checksum, or use the PPA:

````bash
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt update && sudo apt install -y geth
geth version
````

````ini
# /etc/systemd/system/execution.service
[Unit]
Description=Geth execution client
After=network-online.target
Wants=network-online.target

[Service]
User=execution
Group=execution
Type=simple
Restart=always
RestartSec=5
TimeoutStopSec=300
ExecStart=/usr/bin/geth \
  --mainnet \
  --datadir /var/lib/execution \
  --syncmode snap \
  --http --http.addr 127.0.0.1 --http.port 8545 --http.api eth,net,web3 \
  --authrpc.addr 127.0.0.1 --authrpc.port 8551 \
  --authrpc.jwtsecret /var/lib/ethereum/jwt.hex \
  --metrics --metrics.addr 127.0.0.1 --metrics.port 6060 \
  --cache 8192 \
  --maxpeers 100

[Install]
WantedBy=multi-user.target
````

`TimeoutStopSec=300` matters: an execution client killed mid-write can corrupt
its database and cost you a full resync.

### Nethermind

````bash
NM_VERSION=1.39.3
cd /tmp
curl -fsSLO https://github.com/NethermindEth/nethermind/releases/download/${NM_VERSION}/nethermind-${NM_VERSION}-linux-x64.zip
unzip -q nethermind-${NM_VERSION}-linux-x64.zip -d nethermind
sudo mv nethermind /usr/local/share/nethermind
sudo ln -sf /usr/local/share/nethermind/nethermind /usr/local/bin/nethermind
````

Check the checksum published on the release page before moving the binary into
place.

Replace the `ExecStart` block of `execution.service` with:

````ini
ExecStart=/usr/local/bin/nethermind \
  --config mainnet \
  --datadir /var/lib/execution \
  --JsonRpc.Enabled true \
  --JsonRpc.Host 127.0.0.1 --JsonRpc.Port 8545 \
  --JsonRpc.EngineHost 127.0.0.1 --JsonRpc.EnginePort 8551 \
  --JsonRpc.JwtSecretFile /var/lib/ethereum/jwt.hex \
  --Metrics.Enabled true --Metrics.ExposePort 6060 \
  --Sync.SnapSync true
````

### Besu

Besu needs a JRE (Java 21+).

````bash
sudo apt install -y openjdk-21-jre-headless
BESU_VERSION=26.8.1
cd /tmp
curl -fsSLO https://github.com/hyperledger/besu/releases/download/${BESU_VERSION}/besu-${BESU_VERSION}.tar.gz
tar xzf besu-${BESU_VERSION}.tar.gz
sudo mv besu-${BESU_VERSION} /usr/local/share/besu
sudo ln -sf /usr/local/share/besu/bin/besu /usr/local/bin/besu
````

````ini
ExecStart=/usr/local/bin/besu \
  --network=mainnet \
  --data-path=/var/lib/execution \
  --sync-mode=SNAP \
  --data-storage-format=BONSAI \
  --rpc-http-enabled=true --rpc-http-host=127.0.0.1 --rpc-http-port=8545 \
  --engine-rpc-enabled=true --engine-rpc-port=8551 \
  --engine-jwt-secret=/var/lib/ethereum/jwt.hex \
  --metrics-enabled=true --metrics-host=127.0.0.1 --metrics-port=6060
````

### Reth

````bash
RETH_VERSION=v2.6.0
cd /tmp
curl -fsSLO https://github.com/paradigmxyz/reth/releases/download/${RETH_VERSION}/reth-${RETH_VERSION}-x86_64-unknown-linux-gnu.tar.gz
tar xzf reth-${RETH_VERSION}-x86_64-unknown-linux-gnu.tar.gz
sudo install -m 0755 reth /usr/local/bin/reth
````

````ini
ExecStart=/usr/local/bin/reth node \
  --chain mainnet \
  --datadir /var/lib/execution \
  --http --http.addr 127.0.0.1 --http.port 8545 --http.api eth,net,web3 \
  --authrpc.addr 127.0.0.1 --authrpc.port 8551 \
  --authrpc.jwtsecret /var/lib/ethereum/jwt.hex \
  --metrics 127.0.0.1:6060 \
  --full
````

Drop `--full` for an archive node. Reth has no snap sync: it does a staged full
sync, which is fast but writes far more than snap sync does.

### Start it

````bash
sudo systemctl daemon-reload
sudo systemctl enable --now execution
sudo journalctl -fu execution
````

---

## 5. Consensus client

### Checkpoint sync — use it

Syncing the beacon chain from genesis takes days. Checkpoint sync pulls a
finalised state from a trusted provider and starts from there, in minutes. Every
client supports it and every client should use it.

This is a **trust assumption for one state root**. Verify the checkpoint against
a second source before you rely on the node; the community provider list is at
[eth-clients/checkpoint-sync-endpoints](https://github.com/eth-clients/checkpoint-sync-endpoints).

### Lighthouse

````bash
LH_VERSION=v8.2.2
cd /tmp
curl -fsSLO https://github.com/sigp/lighthouse/releases/download/${LH_VERSION}/lighthouse-${LH_VERSION}-x86_64-unknown-linux-gnu.tar.gz
tar xzf lighthouse-${LH_VERSION}-x86_64-unknown-linux-gnu.tar.gz
sudo install -m 0755 lighthouse /usr/local/bin/lighthouse
````

````ini
# /etc/systemd/system/consensus.service
[Unit]
Description=Lighthouse beacon node
After=network-online.target execution.service
Wants=network-online.target

[Service]
User=consensus
Group=consensus
Type=simple
Restart=always
RestartSec=5
ExecStart=/usr/local/bin/lighthouse bn \
  --network mainnet \
  --datadir /var/lib/consensus \
  --execution-endpoint http://127.0.0.1:8551 \
  --execution-jwt /var/lib/ethereum/jwt.hex \
  --checkpoint-sync-url https://mainnet.checkpoint.sigp.io \
  --http --http-address 127.0.0.1 --http-port 5052 \
  --metrics --metrics-address 127.0.0.1 --metrics-port 5054 \
  --disable-upnp

[Install]
WantedBy=multi-user.target
````

### Prysm

````bash
sudo curl -fsSL https://raw.githubusercontent.com/OffchainLabs/prysm/master/prysm.sh -o /usr/local/bin/prysm.sh
sudo chmod +x /usr/local/bin/prysm.sh
````

````ini
ExecStart=/usr/local/bin/prysm.sh beacon-chain \
  --mainnet \
  --datadir /var/lib/consensus \
  --execution-endpoint http://127.0.0.1:8551 \
  --jwt-secret /var/lib/ethereum/jwt.hex \
  --checkpoint-sync-url https://beaconstate.info \
  --genesis-beacon-api-url https://beaconstate.info \
  --grpc-gateway-host 127.0.0.1 --grpc-gateway-port 5052 \
  --monitoring-host 127.0.0.1 --monitoring-port 8080 \
  --accept-terms-of-use
````

`prysm.sh` downloads the binary on first run and on every version bump. On a
locked-down host, fetch the release binary directly instead and pin it.

### Teku

````bash
sudo apt install -y openjdk-21-jre-headless
````

Download the release from the
[Teku releases page](https://github.com/Consensys/teku/releases), verify its
checksum, unpack to `/usr/local/share/teku` and symlink `bin/teku` into
`/usr/local/bin`.

````ini
Environment="JAVA_OPTS=-Xmx5g"
ExecStart=/usr/local/bin/teku \
  --network=mainnet \
  --data-base-path=/var/lib/consensus \
  --ee-endpoint=http://127.0.0.1:8551 \
  --ee-jwt-secret-file=/var/lib/ethereum/jwt.hex \
  --initial-state=https://beaconstate.info/eth/v2/debug/beacon/states/finalized \
  --rest-api-enabled=true --rest-api-interface=127.0.0.1 --rest-api-port=5052 \
  --metrics-enabled=true --metrics-interface=127.0.0.1 --metrics-port=8008
````

### Nimbus

One binary runs the beacon node and, optionally, the validator in the same
process — the lowest-footprint option on this list.

Download the `nimbus-eth2_Linux_amd64_*` tarball from the
[releases page](https://github.com/status-im/nimbus-eth2/releases), verify the
checksum, and install `build/nimbus_beacon_node` into `/usr/local/bin`.

Trusted-node sync is a one-off command before first start:

````bash
sudo -u consensus /usr/local/bin/nimbus_beacon_node trustedNodeSync \
  --network=mainnet \
  --data-dir=/var/lib/consensus \
  --trusted-node-url=https://beaconstate.info \
  --backfill=false
````

````ini
ExecStart=/usr/local/bin/nimbus_beacon_node \
  --network=mainnet \
  --data-dir=/var/lib/consensus \
  --web3-url=http://127.0.0.1:8551 \
  --jwt-secret=/var/lib/ethereum/jwt.hex \
  --rest --rest-address=127.0.0.1 --rest-port=5052 \
  --metrics --metrics-address=127.0.0.1 --metrics-port=8008
````

### Lodestar

Needs Node.js 22+. Download the release tarball from the
[Lodestar releases page](https://github.com/ChainSafe/lodestar/releases) and
verify its checksum.

````ini
ExecStart=/usr/local/bin/lodestar beacon \
  --network mainnet \
  --dataDir /var/lib/consensus \
  --execution.urls http://127.0.0.1:8551 \
  --jwtSecret /var/lib/ethereum/jwt.hex \
  --checkpointSyncUrl https://beaconstate.info \
  --rest --rest.address 127.0.0.1 --rest.port 5052 \
  --metrics --metrics.address 127.0.0.1 --metrics.port 8008
````

### Start it

````bash
sudo systemctl daemon-reload
sudo systemctl enable --now consensus
sudo journalctl -fu consensus
````

---

## 6. Verify — four checks, in this order

A node that starts is not a node that works. Run all four.

**1. Execution client answers and knows its chain**

````bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
  http://127.0.0.1:8545
````

Expect `{"jsonrpc":"2.0","id":1,"result":"0x1"}`. `0x1` is mainnet.

**2. Execution client has finished syncing**

````bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' \
  http://127.0.0.1:8545
````

`false` means synced. An object means it is still catching up — read
`currentBlock` against `highestBlock`.

**3. Consensus client is synced and talking to the EL**

````bash
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
````

Expect `is_syncing: false`, `is_optimistic: false` and a small
`sync_distance`. **`is_optimistic: true` is the failure people miss**: the
beacon node is following heads it has not had the EL verify, usually because the
Engine API connection is broken. A validator on an optimistic node attests to
nothing useful.

**4. The head is the real head**

````bash
curl -s http://127.0.0.1:5052/eth/v1/beacon/headers/head | jq '.data.header.message.slot'
````

Compare against [beaconcha.in](https://beaconcha.in/). More than a couple of
slots behind and something is wrong.

Peer counts, for completeness:

````bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}' http://127.0.0.1:8545
curl -s http://127.0.0.1:5052/eth/v1/node/peer_count | jq
````

Fewer than 10 EL peers or fewer than 20 CL peers usually means the P2P ports are
not actually reachable from outside. Check from another host, not from the node.

---

## 7. First-run mistakes

| Symptom | Cause | Fix |
|---|---|---|
| CL logs `Unauthorized` / `invalid JWT` | Trailing newline in `jwt.hex`, or the two processes read different files | `wc -c` must print 64; point both at the same path |
| `is_optimistic: true` forever | EL not synced, or Engine API unreachable | Check `eth_syncing` and that the EL listens on `8551` |
| EL stuck at a block, CPU idle | Disk cannot keep up — QLC or SATA | Replace the disk; no flag fixes this |
| Very few peers, no inbound | ufw allows the port but the router or provider does not | Test `nc -vz <public-ip> 30303` from elsewhere |
| CL restarts every few minutes | OOM | Check the kernel log for `oom`; lower `--cache`/`-Xmx` or add RAM |
| Sync restarts from scratch after reboot | Client killed before it flushed | Set `TimeoutStopSec=300` and stop with `systemctl stop`, never `kill -9` |
| Everything looks fine, attestations missed | Clock drift | `timedatectl status`; install and enable `chrony` |

---

## 8. Where to go next

- Staking on top of this node: **Create validator**.
- Containerised alternative to all of the above: **Docker installation**
  (eth-docker).
- Dashboards and alerts: **Monitoring & Security**.
- Disk, pruning and archive modes: **Pruning & Storage**.
- Testing before mainnet: **Testnets** — Hoodi is the staking testnet.

## Sources

- [ethereum.org — Nodes and clients](https://ethereum.org/developers/docs/nodes-and-clients/)
- [ethereum.org — Spin up your own Ethereum node](https://ethereum.org/developers/docs/nodes-and-clients/run-a-node/)
- [EIP-7870 — Hardware recommendations](https://eips.ethereum.org/EIPS/eip-7870)
- [clientdiversity.org](https://clientdiversity.org/)
- Client release pages, versions as published 2026-09-18
