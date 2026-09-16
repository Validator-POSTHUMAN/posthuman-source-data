# Starknet full node — installation guide

A Starknet validator is a Starknet **full node** plus an **attestation service**.
This page covers the full node. Two clients are supported by the staking
protocol, and both are documented here:

| Client | Maintainer | Language | Default RPC port | Data layout |
|---|---|---|---|---|
| [Pathfinder](https://github.com/eqlabs/pathfinder) | Equilibrium | Rust | `9545` | single SQLite database |
| [Juno](https://github.com/NethermindEth/juno) | Nethermind | Go + Rust | `6060` | Pebble key-value database |

Either client satisfies the validator requirement. Pick one per host, run it to
a verified synced state, and only then attach the attestation service
([Validator attestation](/networks/starknet/guides/validator-attestation)).

## Hardware

Reference sizing for a mainnet validator node. Starknet state grows
continuously — size disks for at least 12 months of growth, not for today.

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Disk | 1 TB NVMe SSD | 2 TB NVMe SSD |
| Network | 100 Mbit/s | 1 Gbit/s, unmetered |

Notes from production operation:

- NVMe is not optional. Both clients are IO-bound during sync and during
  attestation block-hash lookups; SATA SSD or network storage causes missed
  attestation windows.
- Juno's full mainnet database is significantly larger than Pathfinder's.
  A pruned Juno snapshot is the smaller option if you only need recent state.
- Raise the open-file limit. Under load both clients exceed the default 1024
  descriptors, which surfaces as `Too many open files` and a stalled sync.

## Prerequisites

### 1. Docker

Both clients ship official container images, and Docker is the recommended
runtime for validators. Install it from
[docs.docker.com/get-started/get-docker](https://docs.docker.com/get-started/get-docker/).

### 2. Ethereum WebSocket endpoint (mandatory)

A Starknet full node verifies state against the Starknet core contract on
Ethereum L1. Without a reliable **WebSocket** Ethereum endpoint the node cannot
follow L1 and will stop advancing verified state.

- Starknet Mainnet settles on **Ethereum Mainnet**.
- Starknet Sepolia settles on **Ethereum Sepolia**.
- The URL must be `ws://` or `wss://`, not `http(s)://`.

```bash
export ETHEREUM_URL="wss://<your-ethereum-provider>/ws/v3/<token>"
```

Keep the endpoint credential in an environment file readable only by the node
user (`chmod 600`), never in the compose file, never in shell history, never in
a public repository. Treat an L1 endpoint outage as a validator incident: the
attestation service depends on the node staying current.

### 3. Dedicated system user and file limits

```bash
sudo useradd -m -s /bin/bash starknet
sudo usermod -aG docker starknet

# /etc/security/limits.conf
starknet soft nofile 65536
starknet hard nofile 65536
```

Log out and back in, then verify with `ulimit -n`.

## Option A — Pathfinder

### A.1 Run with Docker

```bash
mkdir -p $HOME/pathfinder/data

docker run -d \
  --name pathfinder \
  --restart unless-stopped \
  -p 9545:9545 \
  -p 9000:9000 \
  --user "$(id -u):$(id -g)" \
  --ulimit nofile=65536:65536 \
  -e RUST_LOG=info \
  -e PATHFINDER_ETHEREUM_API_URL="$ETHEREUM_URL" \
  -v $HOME/pathfinder/data:/usr/share/pathfinder/data \
  eqlabs/pathfinder:latest \
  --network mainnet \
  --monitor-address 0.0.0.0:9000 \
  --rpc.websocket.enabled
```

Pin an exact image tag in production (`eqlabs/pathfinder:vX.Y.Z`) instead of
`latest`, so that a restart never silently changes the client version.

### A.2 Run with Docker Compose (recommended for validators)

Compose is preferred because the node and the attestation service are then one
unit with one restart policy and one upgrade path.

```yaml
# ~/starknet/docker-compose.yml
services:
  pathfinder:
    image: eqlabs/pathfinder:v0.22.7
    container_name: pathfinder
    restart: unless-stopped
    ports:
      - "9545:9545"   # JSON-RPC
      - "9000:9000"   # Prometheus metrics
    volumes:
      - ./data:/usr/share/pathfinder/data
    env_file:
      - .env
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    command:
      - --network
      - mainnet
      - --ethereum.url
      - ${PATHFINDER_ETHEREUM_API_URL}
      - --monitor-address=0.0.0.0:9000
      - --rpc.websocket.enabled
```

```bash
# ~/starknet/.env  (chmod 600)
PATHFINDER_ETHEREUM_API_URL=wss://<your-ethereum-provider>/...
```

```bash
cd ~/starknet
docker compose up -d
docker compose logs -f pathfinder
```

### A.3 Build from source (optional)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

git clone https://github.com/eqlabs/pathfinder.git
cd pathfinder
git checkout v0.22.7
cargo build --release

./target/release/pathfinder \
  --network mainnet \
  --ethereum.url "$ETHEREUM_URL" \
  --data-directory $HOME/pathfinder/data
```

### A.4 Verify Pathfinder

```bash
curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}'

curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_syncing","params":[],"id":1}'
```

`starknet_syncing` returning `false` means the node is at chain head.
While syncing it returns the current and highest known block.

The RPC path carries the RPC version: `/rpc/v0_8`, `/rpc/v0_9`. The attestation
service requires a path it supports — check both sides before wiring them
together, because a version mismatch fails at runtime, not at startup.

## Option B — Juno

### B.1 Run with Docker

```bash
mkdir -p $HOME/juno/juno_mainnet

docker run -d \
  --name juno \
  --restart unless-stopped \
  -p 6060:6060 \
  -p 6061:6061 \
  -p 9090:9090 \
  -v $HOME/juno/juno_mainnet:/var/lib/juno \
  nethermind/juno:latest \
  --http \
  --http-port 6060 \
  --http-host 0.0.0.0 \
  --ws \
  --ws-port 6061 \
  --ws-host 0.0.0.0 \
  --metrics \
  --metrics-host 0.0.0.0 \
  --metrics-port 9090 \
  --db-path /var/lib/juno \
  --eth-node "$ETHEREUM_URL"
```

### B.2 Run with Docker Compose

```yaml
# ~/starknet/docker-compose.yml
services:
  juno:
    image: nethermind/juno:v0.16.0
    container_name: juno
    restart: unless-stopped
    ports:
      - "6060:6060"   # JSON-RPC
      - "6061:6061"   # WebSocket
      - "9090:9090"   # Prometheus metrics
    volumes:
      - ./juno_mainnet:/var/lib/juno
    env_file:
      - .env
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    command:
      - --http
      - --http-port=6060
      - --http-host=0.0.0.0
      - --ws
      - --ws-port=6061
      - --ws-host=0.0.0.0
      - --metrics
      - --metrics-host=0.0.0.0
      - --metrics-port=9090
      - --db-path=/var/lib/juno
      - --eth-node=${JUNO_ETH_NODE}
```

### B.3 Standalone binary

Download the release archive for your platform from
[Juno releases](https://github.com/NethermindEth/juno/releases/latest):

```bash
mkdir -p $HOME/juno/juno_mainnet

./juno \
  --http --http-port 6060 --http-host 0.0.0.0 \
  --db-path $HOME/juno/juno_mainnet \
  --eth-node "$ETHEREUM_URL"
```

### B.4 Build from source (optional)

Requires Go 1.25+, Rust 1.87+, a C compiler and jemalloc.

```bash
sudo apt-get install -y build-essential make libjemalloc-dev libjemalloc2 pkg-config libbz2-dev

git clone https://github.com/NethermindEth/juno
cd juno
git tag -l            # pick an exact release tag
make install-deps
make juno

./build/juno \
  --http --http-port 6060 --http-host 0.0.0.0 \
  --db-path $HOME/juno/juno_mainnet \
  --eth-node "$ETHEREUM_URL"
```

### B.5 Verify Juno

```bash
curl -s -X POST http://127.0.0.1:6060/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}'

curl -s -X POST http://127.0.0.1:6060/v0_9 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_chainId","params":[],"id":1}'
```

Mainnet chain ID is `SN_MAIN` (`0x534e5f4d41494e`), Sepolia is `SN_SEPOLIA`.
Always assert the chain ID before attaching a validator: an attestation service
pointed at the wrong network silently earns nothing.

## Syncing faster

Syncing mainnet from genesis takes days. Use a database snapshot instead —
see [Snapshots](/networks/starknet/guides/snapshots) for the download,
checksum and restore procedure for both clients.

## Choosing between the clients

- Both are accepted by the staking protocol; there is no reward difference.
- Pathfinder pairs with Equilibrium's attestation service, Juno pairs with
  Nethermind's `starknet-staking-v2`. Either attestation service can talk to
  any compliant JSON-RPC node, but the tested combinations are the ones above.
- Running **two different clients** across two hosts is the strongest
  configuration for a validator: a client-specific bug then costs you one node,
  not your attestation record.

## Next steps

1. [Snapshots](/networks/starknet/guides/snapshots) — sync in hours instead of days.
2. [Create validator](/networks/starknet/guides/create-validator) — accounts, stake, commission, delegation pool.
3. [Validator attestation](/networks/starknet/guides/validator-attestation) — the service that earns rewards.
4. [Monitoring](/networks/starknet/guides/monitoring) — what to alert on.
5. [Security](/networks/starknet/guides/security) — address hierarchy and key custody.

## Reference

- Starknet docs — [Running a full node](https://docs.starknet.io/secure/quickstart/running-a-node)
- [Pathfinder repository](https://github.com/eqlabs/pathfinder)
- [Juno documentation](https://juno.nethermind.io/)
