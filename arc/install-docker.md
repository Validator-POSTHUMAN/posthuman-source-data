# Arc Network mainnet — Docker deployment

The Docker path avoids the glibc 2.39 requirement that blocks the pre-built
binaries on older distributions. It runs the same two processes.

## Prerequisites

- Docker Engine 24+ with BuildKit
- Docker Compose v2
- 1 TB+ NVMe SSD

## Images

```sh
export ARC_VERSION=0.8.0
export ARC_HOME=~/.arc

docker pull docker.cloudsmith.io/circle/arc-network/arc-execution:$ARC_VERSION
docker pull docker.cloudsmith.io/circle/arc-network/arc-consensus:$ARC_VERSION

export ARC_EXECUTION_IMAGE=docker.cloudsmith.io/circle/arc-network/arc-execution:$ARC_VERSION
export ARC_CONSENSUS_IMAGE=docker.cloudsmith.io/circle/arc-network/arc-consensus:$ARC_VERSION
```

`v0.8.0` is mandatory on mainnet: Circle's run-a-node page requires it before
timestamp `1789052400` (2026-09-10 15:00 UTC), when Zero7 and Zero8 activate.
That deadline has passed, and `arc_getVersion` against the official mainnet RPC
confirms the fleet is on `v0.8.0`.

### Or build them

```sh
git clone https://github.com/circlefin/arc-node.git && cd arc-node
git checkout v$ARC_VERSION
docker buildx bake \
  --set "*.args.GIT_COMMIT_HASH=$(git rev-parse v$ARC_VERSION^{commit})" \
  --set "*.args.GIT_VERSION=v$ARC_VERSION" \
  --set "*.args.GIT_SHORT_HASH=$(git rev-parse --short v$ARC_VERSION^{commit})" \
  --set "arc-execution.tags=arc-execution:$ARC_VERSION" \
  --set "arc-consensus.tags=arc-consensus:$ARC_VERSION"
```

## Prepare the data directory first

```sh
mkdir -p "${ARC_HOME:-$HOME/.arc}"
```

Skip this and Docker creates it as root, and the `arc-snapshots` container
fails with permission errors.

## Compose file

```sh
curl -O https://raw.githubusercontent.com/circlefin/arc-node/v${ARC_VERSION}/deployments/docker-compose.yml
```

**Read it before running it, and change the chain.** Circle's published file
targets `arc-testnet`. For mainnet, the `arc-snapshots` service command needs
`--chain=arc-mainnet`, and the EL and CL need `--chain arc-mainnet` and mainnet
`--follow.endpoint` values:

```
https://rpc.mainnet.arc.io,wss=rpc.mainnet.arc.io
https://rpc.drpc.mainnet.arc.io,wss=rpc.drpc.mainnet.arc.io
https://rpc.blockdaemon.mainnet.arc.io,wss=rpc.blockdaemon.mainnet.arc.io/websocket
```

All three verified reachable on 2026-09-18, each answering chain `0x13b2`.

Also review the port mappings. A bare `host:container` mapping binds `0.0.0.0`,
and Docker writes its iptables rules ahead of `ufw` — so a host whose firewall
reads as correct can be serving JSON-RPC to the internet. Bind explicitly:

```yaml
    ports:
      - "127.0.0.1:8545:8545"
```

## Start

```sh
docker compose up -d
docker compose logs -f arc-snapshots
```

On the first run, init containers download the snapshot pair, initialise the CL
private key and prepare the shared IPC socket volume.

## Two things that make `up` expensive

The init containers run on **every** `docker compose up`. Normally they finish
in seconds. Two cases are not normal:

**A newer snapshot has been published.** With no explicit URLs, the service
asks the API for the latest snapshot on every run, and a newer one usually
exists within hours. It restores that one instead — a second full download, and
the node moves *back* to the snapshot's block, discarding everything it synced
since. Pin explicit URLs if this matters to you.

**A previous restore did not finish.** A layer is marked restored only after
download and extraction both complete, so an interrupted run leaves unmarked
data behind. On the next run the service cannot distinguish that from a
directory you filled yourself, so it stops rather than delete someone else's
data. Nothing else starts either, because the rest of the stack waits on it.

Add `--force` to the command, bring the stack up once, then take the flag out:

```yaml
    command:
      - download
      - --chain=arc-mainnet
      - --el-profile=full
      - --force
      - --execution-path=/data/execution
      - --consensus-path=/data/consensus
```

`FORCE_SNAPSHOT_RESTORE=true` has no effect. `arc-snapshots` does not read it.

## Verify

```sh
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Then against the network:

```sh
cast block-number --rpc-url https://rpc.mainnet.arc.io
```

Metrics are exposed on the host at `localhost:9001/metrics` (EL) and
`localhost:29000/metrics` (CL).

## Stop

```sh
docker compose down
```

Data persists in `~/.arc`. **`docker compose down -v` plus `rm -rf ~/.arc`
permanently deletes the consensus-layer private key** — your node's network
identity. It cannot be recovered.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
