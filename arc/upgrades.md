# Arc Network mainnet — upgrades

**Arc hardforks activate on a wall-clock timestamp, not a block height.** There
is no on-chain plan to query, no height to watch approaching, and no signal in
your logs the day before. A missed upgrade is a node that stops being on the
canonical chain at a moment someone else decided months ago.

That makes the calendar the primary control here, which is unusual and is the
single thing to carry away from this page.

## Known activations

| Network | Fork | Timestamp | Wall clock | Required |
|---|---|---|---|---|
| Arc Testnet | Zero8 | `1788447600` | 2026-09-03 15:00 UTC | `v0.8.0` |
| Arc mainnet | Zero7 + Zero8 | `1789052400` | 2026-09-10 15:00 UTC | `v0.8.0` |

Source: Circle's run-a-node page. Both deadlines have passed, so **`v0.8.0` is
mandatory on mainnet today**, not recommended. Earlier versions are not
supported after those timestamps.

Confirmed against the network rather than the documentation: `arc_getVersion`
on `rpc.mainnet.arc.io` returned `v0.8.0` (commit `5abb64c1…`) on 2026-09-18.

## Where the truth is

Circle's `node-requirements` **Versions** table is the nominal source, and as
of 2026-09-18 it still lists only Arc Testnet — mainnet has no row. So use
three sources, in this order:

1. `arc_getVersion` against the official mainnet RPC — what the fleet runs;
2. <https://github.com/circlefin/arc-node/releases> — what exists;
3. <https://docs.arc.io/arc/references/node-requirements#versions> — what
   Circle says, when it says it.

```sh
curl -s -X POST https://rpc.mainnet.arc.io -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'

curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'
```

If those two disagree, you are the one who is behind.

## Read the breaking changes first, not after

Every release links two documents, and `v0.8.0` has content in both:

- <https://github.com/circlefin/arc-node/blob/main/CHANGELOG.md>
- <https://github.com/circlefin/arc-node/blob/main/BREAKING_CHANGES.md>

`v0.8.0` specifics worth knowing before you run `arcup`:

- **Snapshots moved to Reth V2 storage format.** A fresh install from a v0.8.0
  snapshot needs no migration. A node restored from an older **V1** snapshot
  does — that is the migration `BREAKING_CHANGES.md#v080` describes.
- **The RPC transport between EL and CL is deprecated** and will be removed in
  `v0.9.0`. If your layers run on separate hosts, plan the move to a single
  host with IPC now rather than at the `v0.9.0` deadline.

Flag defaults have also moved across recent releases, and a default that
changes silently is worse than a flag that is removed loudly:

| Flag | Changed | From → to |
|---|---|---|
| `--rpc.max-connections` | `v0.7.1` | `500` → `250` |
| `--rpc.max-subscriptions-per-connection` | `v0.7.1` | `1024` → `32` |
| EL prune block interval under `--full` | `v0.7.3` | `5000` → `128` |

## Upgrading

```sh
. ~/.arc_env

# what you are on
arc-node-execution --version
arc-node-consensus --version

# stop the consensus layer first, execution second
sudo systemctl stop arc-consensus
sudo systemctl stop arc-execution

arcup --install v0.8.0

arc-node-execution --version
arc-node-consensus --version

# start execution first, consensus second
sudo systemctl start arc-execution
sudo systemctl start arc-consensus
```

**Order matters in both directions.** The CL connects to the EL's sockets at
startup and fails if they are absent, so the EL always starts first. Stopping
in the reverse order avoids the CL logging connection failures at a moment you
are trying to read the logs.

`arcup` verifies each archive against its `.sha256`. GPG verification is
disabled until Circle publishes the release signing key.

To upgrade `arcup` itself: `arcup --self-update`. Plain `arcup` updates the
binaries to the latest release — which is convenient and is also how a node
ends up on a version nobody chose. Pin with `--install <tag>` on anything you
care about.

### Docker

```sh
export ARC_VERSION=0.8.0
docker pull docker.cloudsmith.io/circle/arc-network/arc-execution:$ARC_VERSION
docker pull docker.cloudsmith.io/circle/arc-network/arc-consensus:$ARC_VERSION
docker compose up -d
```

Remember that `docker compose up` re-runs the init containers, and if a newer
snapshot has been published it will restore that instead — a second full
download, and the node moves back to the snapshot's block. See the Docker tab.

## Verify the upgrade

Not "the service is up". Four things:

```sh
systemctl is-active arc-execution arc-consensus
arc-node-execution --version

# version as the node reports it over RPC
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'

# height advancing, twice
cast block-number --rpc-url http://127.0.0.1:8545
sleep 30
cast block-number --rpc-url http://127.0.0.1:8545

# and agreeing with the network, by hash
```

A node that restarts cleanly on a new binary and then sits at a fixed height is
the exact failure this network produces. Check the second sample.

## Rollback

There is no signer state and no slashing risk, so rollback is ordinary:
reinstall the previous tag with `arcup --install <tag>`, start EL then CL. The
only thing that must survive is the consensus-layer private key in
`$ARC_CONSENSUS`.

A downgrade across the V1→V2 storage boundary is not a rollback, though —
older binaries cannot read V2 data. Below `v0.8.0` the recovery path is a fresh
snapshot restore, not a binary swap.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
