# Arc Network mainnet — troubleshooting

Ordered by how often each is the real cause.

## Block number stays at `0x0`

The classic new-node symptom. Four causes, in order:

**IPC sockets missing.** The EL writes `$ARC_RUN/reth.ipc` and
`$ARC_RUN/auth.ipc` within about 30 seconds of starting.

```sh
ls -l "$ARC_RUN"
```

If they are absent, the EL did not start. Read its output for a panic or a
configuration error — not the CL's.

**The CL started before the EL.** The CL connects to those sockets at startup
and fails if they are not there. Restart the CL. Always start the EL first.

**Snapshot extraction was interrupted.** `arc-snapshots download` extracts
silently, so an interrupted run leaves a partly populated directory that looks
finished. Re-run the download.

> Do **not** clear `$ARC_CONSENSUS` first. It holds the CL private key written
> by `arc-node-consensus init` — your node's network identity, unrecoverable.
> If you have already cleared it, re-run `init` before starting.

**`$ARC_RUN` differs between shells.** Re-source `~/.arc_env` in every terminal
that lost its environment. Under systemd, `RuntimeDirectory=arc` makes this
impossible to get wrong, which is a good reason to move to units early.

## `GLIBC_2.38 not found` / `GLIBC_2.39 not found`

The pre-built binaries are dynamically linked against glibc **2.39 or newer**.
Ubuntu 24.04 works; Debian 12 does not. Use a newer distribution, the Docker
images, or build from source. There is no flag for this.

## The node runs and the height does not move

The process is up, `eth_blockNumber` answers, the number is old. This is the
characteristic Arc failure and nothing logs it as an error.

```sh
cast block-number --rpc-url http://127.0.0.1:8545
sleep 30
cast block-number --rpc-url http://127.0.0.1:8545
cast block-number --rpc-url https://rpc.mainnet.arc.io
```

A follow node depends entirely on its relay endpoints. Check, in order:

1. **Relay endpoints reachable from the node host** — not from your laptop.
   Outbound HTTPS and WebSocket to `rpc.mainnet.arc.io` and the provider
   endpoints.
2. **CL logs** for follow-endpoint errors. Rate-limit and fetch warnings are
   normal in isolation; they are actionable when the height stops.
3. **All three endpoints configured?** One is a single point of failure.
4. **Backpressure.** If the EL is memory-starved or the disk is slow, execution
   throttles. See Pruning & storage.

## Wrong chain

Compare the block **hash**, not the number:

```sh
H=$(cast block-number --rpc-url http://127.0.0.1:8545)
cast block --rpc-url http://127.0.0.1:8545      "$H" --json | jq -r .hash
cast block --rpc-url https://rpc.mainnet.arc.io "$H" --json | jq -r .hash
```

If they differ, check `--chain`. `arc-mainnet` is `5042`; `arc-testnet` is
`5042002`.

```sh
cast chain-id --rpc-url http://127.0.0.1:8545
```

Circle's published `docker-compose.yml` and every quickstart example target
`arc-testnet`. A mainnet deployment built by copying one of them and changing
the RPC URLs but not `--chain` is a testnet node pointed at mainnet relays.

## `arc-snapshots` stops and asks for `--force`

Expected behaviour, not a bug. A layer is marked restored only after download
*and* extraction finish, so an interrupted run leaves unmarked data. The tool
cannot distinguish that from a directory you populated yourself, so it refuses
rather than delete it.

Add `--force`, bring it up once, remove the flag. `FORCE_SNAPSHOT_RESTORE=true`
does nothing — `arc-snapshots` does not read it.

## Automatic snapshot resolution fails

Automatic resolution requires the API to publish a **storage v2 listing** for
the chain. There is **no fallback to any other listing**. The failure is the
answer: that chain has no published v2 pair right now.

Options: an explicit `--execution-url` and `--consensus-url` pair from Circle,
or wait. Genesis sync is not supported, so there is no third option.

Never pass a **presigned** manifest URL by hand — reth derives component URLs
by string concatenation, so the query string ends up between the path and the
filename and every component 404s.

## `Address already in use` on the consensus layer

The CL's local RPC and the EL's P2P listener have collided on a port. Set
`--rpc.addr 127.0.0.1:31000` explicitly on the CL. Follow-mode catch-up
continues through the relay endpoints while this is broken, so the node looks
healthy and `arc_getCertificate` silently does not work.

## Memory climbing during startup or catch-up

Documented behaviour on some hardware: execution runs ahead of persistence and
the difference lives in RAM.

```sh
--execution-persistence-backpressure
--execution-persistence-backpressure-threshold=16
```

Lower the threshold if it persists. On separated hosts, backpressure also needs
the EL to serve WebSocket with the `reth` namespace on `8546`, or it is
silently inactive.

## `MaxConnections` / `TooManySubscriptions`

Client-side errors against a busy public node. Defaults are `250` and `32`,
lowered from `500` and `1024` in `v0.7.1` to bound WebSocket log-fanout memory.
Raise them; do not lower them. And put a rate-limiting proxy in front, because
the node enforces no per-client limit.

## `rpc_modules` shows namespaces you did not want

`--http.api` is additive and Circle's quickstart uses
`eth,net,web3,txpool,trace,debug`. For anything public: `eth,net,web3,rpc` plus
`--public-api`. Then re-check — and confirm
`eth_newPendingTransactionFilter` returns error `-32001` rather than a filter
id.

## The node was fine and is now on the wrong side of a fork

Arc activations are **wall-clock timestamps**, not block heights. There is no
on-chain plan, no approaching height, and no warning in your logs. If the node
diverged at a moment you cannot explain, check the timestamp against the fork
schedule and the version against `arc_getVersion` on the official RPC.

Recovery is a version upgrade and, if the divergence is deep, a fresh snapshot.
There is no signer state at stake — an Arc node is a follower, so a resync
costs time and nothing else.

## Docker: `up` triggers a full re-download

The init containers run on every `docker compose up`, and with no explicit URLs
they ask the API for the *latest* snapshot. A newer one usually exists within
hours, so the layer is replaced — a second full download, and the node moves
back to that snapshot's block. Pin explicit URLs if this matters.

## Docker: permission errors from `arc-snapshots`

`$ARC_HOME` did not exist before `docker compose up`, so Docker created it as
root. Create it first:

```sh
mkdir -p "${ARC_HOME:-$HOME/.arc}"
```

The init container running as root is intentional — it sets ownership for the
main services at UID 999. No manual `chown` is needed.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
