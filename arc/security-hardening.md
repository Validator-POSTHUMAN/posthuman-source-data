# Arc Network mainnet — security hardening

An Arc node is a follower. It holds no consensus stake, signs no blocks and
cannot be slashed, so there is no double-sign rule here and no key-uniqueness
proof to run. Restarting is safe; replacing the data directory is safe.

That inverts the usual priorities. What costs you on Arc is publishing
something you did not mean to publish, or serving wrong answers with
confidence.

## Ports

| Port | Service | Follow node | RPC provider node |
|---|---|---|---|
| `8545` | EL JSON-RPC | loopback | public, behind a proxy |
| `8546` | EL WebSocket | loopback | public, behind a proxy |
| `8551` | EL Engine API (authrpc) | **never exposed** | **never exposed** |
| `9001` | EL Prometheus | loopback | loopback |
| `29000` | CL Prometheus | loopback | loopback |
| `31000` | CL RPC | **never exposed** | **never exposed** |
| `30303` | EL P2P (devp2p) | not used | public |
| `27000` | CL P2P (libp2p) | not used | restricted to onboarding peer IPs |

A follow node needs **no inbound ports at all**. It reaches the network through
outbound HTTPS and WebSocket to the relay endpoints. If your follow node has
anything open inbound, that is a decision you should be able to justify.

The Engine API controls block import. Never expose it. On a colocated
deployment it does not exist as a TCP listener at all — IPC has no port, which
is one of the reasons IPC is the supported mode.

```sh
ss -ltnp | grep -vE '127\.0\.0\.1|\[::1\]'
```

Anything in that output is public. `ufw status` is not evidence: Docker writes
its iptables rules ahead of `ufw`, so a container published with a bare
`host:container` mapping is reachable on a host whose firewall reads as
correct. Bind explicitly — `127.0.0.1:8545:8545`.

## IPC versus RPC between the layers

Use IPC. Keep both processes on one host.

The RPC transport between EL and CL is **deprecated as of `v0.8.0` and will be
removed in `v0.9.0`**. The CL logs a startup warning when any RPC option is
set. Separated hosts require:

- rebinding the EL's eth JSON-RPC off loopback so the CL can reach it;
- exposing the Engine API on `8551` on `0.0.0.0`;
- a shared JWT secret, generated once and copied between hosts;
- and, if backpressure is enabled, a WebSocket server on `8546` exposing the
  `reth` namespace.

That is four things bound to non-loopback addresses instead of two sockets in a
directory. If you must do it, restrict every one of those ports to the other
host's address at the firewall, and treat `8551` as the one that must never be
wrong.

```sh
openssl rand -hex 32 | tr -d "\n" > "$ARC_HOME/jwtsecret"
chmod 600 "$ARC_HOME/jwtsecret"
```

Never print the JWT. Never commit it. It is not a shared constant on Arc, and
it should not become one on your fleet.

## RPC namespaces are a security setting

Circle's quickstart uses `--http.api eth,net,web3,txpool,trace,debug`. On
loopback that is convenient. On anything reachable it publishes
`debug_traceTransaction`, which is a one-line remote denial of service, and
pending-transaction visibility, which is an MEV surface.

For anything public: `eth,net,web3,rpc` and `--public-api`, verified with
`rpc_modules`. See the RPC tab.

## Rate limiting is not optional

The node enforces no per-client request limit. A public endpoint needs a
reverse proxy or load balancer in front of `8545` and `8546` doing rate
limiting, request-size limits and connection throttling. Without it a single
client saturates the interface.

The load balancer must allow `arc_getCertificate` through to `8545`, or the
`arc` namespace stops working for everyone.

## The keys that exist

There is exactly one, and it is not a signing key:

| File | What it is | If lost |
|---|---|---|
| `$ARC_CONSENSUS/` private key | the node's **network identity**, written by `arc-node-consensus init` | permanently gone; re-run `init` for a new identity |

`docker compose down -v` plus `rm -rf ~/.arc` deletes it. So does clearing
`$ARC_CONSENSUS` before re-running a snapshot download — which the
troubleshooting guidance explicitly warns about, because the obvious fix for a
half-extracted snapshot is the thing that destroys it.

Back it up, or accept that recovery means a new identity.

## Supply chain

`arcup` verifies each downloaded archive against its `.sha256` file. **GPG
signature verification is disabled until Circle publishes the release signing
key**, which Circle states in its own installation documentation.

So the integrity control on this path is a checksum served from the same origin
as the artifact. For a production node, prefer building from a tagged source
checkout, or pin and verify the Docker image digest rather than the tag.

`curl … | bash` installs a script that configures a node you will be
responsible for at three in the morning. Read it first.

## Host

- SSH keys only, `PermitRootLogin no`, `PasswordAuthentication no`.
- Unattended security updates.
- Run the node as a dedicated non-root user; under systemd use
  `RuntimeDirectory=arc`, `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem`.
- The Docker init container runs as root deliberately, to set ownership for the
  main services at UID 999. That is expected; no manual `chown` is needed.
- glibc 2.39 or newer. Running the binaries on an older distribution does not
  half-work, it fails to start.

## What an incident looks like here

Not a slashing event. The realistic failures are:

1. **Your node stopped following and nobody noticed.** The process is up,
   `eth_blockNumber` answers, and the number is old. Alert on block-number
   progress *and* on divergence from an independent RPC. See Monitoring.
2. **You published an RPC someone built on.** Now their outage is your outage.
   Decide deliberately whether you are an endpoint provider.
3. **You missed a hardfork timestamp.** Arc's activations are wall-clock, not
   block heights. See Upgrades.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
