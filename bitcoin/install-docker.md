# Bitcoin Core in Docker

## There is no official image

Bitcoin Core publishes **signed binaries, not container images**. Every popular
`bitcoind` image on Docker Hub is maintained by a third party, and pulling one
means trusting whoever built it with the thing your node exists to avoid
trusting. Some are well maintained (`btcpayserver/bitcoin`, `lncm/bitcoind`);
several widely-linked ones have been unmaintained for years.

The safe pattern is a three-line Dockerfile that verifies the official release
itself. You keep container ergonomics and lose nothing.

## Build the image

````dockerfile
# Dockerfile
FROM debian:bookworm-slim AS build
ARG VERSION=31.1
ARG SHA256=b80d9c3e04da78fb6f0569685673418cf686fadba9042d926d13fb87ff503f9e
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget \
 && wget -q https://bitcoincore.org/bin/bitcoin-core-${VERSION}/bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz \
 && echo "${SHA256}  bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz" | sha256sum -c - \
 && tar -xzf bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz \
 && install -m 0755 -t /usr/local/bin \
      bitcoin-${VERSION}/bin/bitcoind \
      bitcoin-${VERSION}/bin/bitcoin-cli \
      bitcoin-${VERSION}/bin/bitcoin-util \
      bitcoin-${VERSION}/bin/bitcoin-wallet

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -g 10000 bitcoin && useradd -u 10000 -g 10000 -m -d /data bitcoin
COPY --from=build /usr/local/bin/bitcoin* /usr/local/bin/
USER bitcoin
VOLUME /data
EXPOSE 8333
ENTRYPOINT ["bitcoind", "-datadir=/data"]
````

````bash
docker build --build-arg VERSION=31.1 -t posthuman/bitcoind:31.1 .
docker run --rm posthuman/bitcoind:31.1 -version
````

Pin the digest, never a floating tag, in anything that deploys automatically.
The `SHA256` build argument is the value from the release `SHA256SUMS` — verify
that file's GPG signature once, by hand, as described in the installation
guide, and then the digest carries that trust into every rebuild.

## Compose

````yaml
# docker-compose.yml
services:
  bitcoind:
    image: posthuman/bitcoind:31.1
    container_name: bitcoind
    restart: unless-stopped
    stop_grace_period: 20m
    user: "10000:10000"
    volumes:
      - /srv/bitcoin:/data
    ports:
      - "8333:8333"          # P2P, public
      - "127.0.0.1:8332:8332" # RPC, loopback only
      - "127.0.0.1:28332-28334:28332-28334" # ZMQ, loopback only
    mem_limit: 12g
    command:
      - -datadir=/data
      - -conf=/data/bitcoin.conf
      - -printtoconsole
````

Three details that are specific to containers and cause real damage when
missed:

- **`stop_grace_period: 20m`.** Docker's default is 10 seconds, then `SIGKILL`.
  A `bitcoind` killed mid-flush corrupts the chainstate and costs a multi-hour
  reindex. This is the most common way containerised nodes break.
- **`dbcache` must be explicit.** Core reads the host's RAM, not the cgroup
  limit, so on a 128 GB host with `mem_limit: 12g` it will size the cache for
  128 GB and get OOM-killed. Put `dbcache=4096` in `bitcoin.conf` and keep it
  well under `mem_limit`.
- **Bind RPC and ZMQ to `127.0.0.1` in the port mapping.** `- "8332:8332"`
  publishes RPC on every interface and, on many hosts, punches straight through
  `ufw`, because Docker writes its own iptables rules. Verify from outside:
  `nc -vz <public-ip> 8332` must fail.

`bitcoin.conf` for the container is the same file as the systemd install, with
`rpcbind=0.0.0.0` and `rpcallowip=127.0.0.1/32` — inside the container the
loopback is not the host's, so RPC binds to the container interface and the
port mapping is what restricts it.

## Operating it

````bash
docker exec -u bitcoin bitcoind bitcoin-cli -datadir=/data getblockchaininfo | jq '{blocks,headers,verificationprogress,initialblockdownload}'
docker logs -f --tail 100 bitcoind
docker compose stop bitcoind && docker compose start bitcoind   # respects stop_grace_period
````

Upgrade = rebuild with a new `VERSION`/`SHA256`, then `docker compose up -d`.
Everything in the **Upgrades** guide about downgrade limits applies identically;
the container does not protect the on-disk data from a version that migrated it.

## When a prebuilt image is the better answer

If you are deploying a full node-plus-Lightning-plus-explorer stack rather than
a single daemon, use a distribution that assembles and pins the whole set:

| Stack | What it is |
|---|---|
| [btcpayserver/btcpayserver-docker](https://github.com/btcpayserver/btcpayserver-docker) | Bitcoin Core, NBXplorer, LND/CLN, BTCPay, Compose-orchestrated |
| [nix-bitcoin](https://github.com/fort-nix/nix-bitcoin) | NixOS modules, security-focused, Core + CLN + hardening by default |
| [Cyphernode](https://github.com/SatoshiPortal/cyphernode) | Modular node backend for commercial use, optional indexers |
| [Umbrel](https://umbrel.com) / [Start9](https://start9.com) | Appliance-style home node distributions |

These are worth reading even if you deploy by hand — their Compose files are a
compact record of which ports, volumes and ZMQ topics a real stack needs.

## Sources

- [bitcoincore.org — download and `SHA256SUMS`](https://bitcoincore.org/en/download/)
- [bitcoincore.org — v31.0 release notes, `-dbcache` default](https://bitcoincore.org/en/releases/31.0/)
- [btcpayserver/btcpayserver-docker](https://github.com/btcpayserver/btcpayserver-docker)
- [fort-nix/nix-bitcoin](https://github.com/fort-nix/nix-bitcoin)
