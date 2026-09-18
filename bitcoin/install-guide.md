# Bitcoin Full Node Installation Guide

## Read this first: Bitcoin has no validators

Bitcoin has no staking, no validator set, no delegation and no slashing. There
is nothing to register and nothing to bond. Two roles exist:

- a **full node** independently verifies every block and transaction against
  consensus rules and relays them. This is what this guide sets up, and it is
  what gives you your own trustless view of the chain.
- a **miner** produces blocks with proof of work. Mining is a hardware and
  energy business — see the **Mining guide** on this card.

Running a full node earns no protocol reward. It buys you verification you do
not have to trust anyone else for, and it is the correct backend for wallets,
explorers, payment processing, Lightning and any service that must not depend
on someone else's RPC.

## Version

| | |
|---|---|
| Current release | **v31.1**, released 2026-07-08 |
| Previous major | v31.0 — upgrade, see below |
| End of life | **v28.x and older receive no updates** |

v31.1 is a bug-fix release over v31.0 and both of its fixes matter to an
operator:

- the chainstate database repeatedly rewrote large parts of itself, producing
  continuous excessive disk reads and writes in normal operation;
- `-privatebroadcast` leaked the node's clear-net IP under some conditions,
  defeating the feature it enables.

Run v31.1, not v31.0.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 2 cores | 4 cores     |
| RAM       | 4 GB    | 8–16 GB     |
| Disk      | 800 GB SSD (full archive) | 1.5 TB NVMe, room to grow |
| Network   | 50 Mbps, unmetered preferred | 1 Gbps |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

The chain grows continuously. Size the disk for at least two years ahead, or
run pruned — see the **Pruning and storage** guide.

`txindex=1` adds roughly 50 GB on top of the block and chainstate data.

## Prepare the host

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install wget gnupg jq ufw
````

Create a dedicated unprivileged user:

````bash
sudo adduser --system --group --home /var/lib/bitcoind bitcoind
````

## Download and verify the release

Never skip verification on Bitcoin Core. Download the binary, the signed
checksum file and the signatures:

````bash
VERSION=31.1
cd /tmp
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS.asc
````

Check the hash of what you downloaded against the signed list:

````bash
sha256sum --ignore-missing --check SHA256SUMS
````

For v31.1 the expected Linux x86-64 digest is:

````
b80d9c3e04da78fb6f0569685673418cf686fadba9042d926d13fb87ff503f9e  bitcoin-31.1-x86_64-linux-gnu.tar.gz
````

Then verify the signatures on `SHA256SUMS` itself. A matching hash proves the
file is intact; only the signature check proves it is the file the project
released. Bitcoin Core is built reproducibly by many independent builders, and
their attestations live in `bitcoin-core/guix.sigs`:

````bash
git clone --depth 1 https://github.com/bitcoin-core/guix.sigs /tmp/guix.sigs
gpg --import /tmp/guix.sigs/builder-keys/*.gpg
gpg --verify SHA256SUMS.asc SHA256SUMS
````

You want several **good** signatures from keys you have decided to trust. A
`Good signature` line with `WARNING: This key is not certified with a trusted
signature` means the maths checks out but you have not personally vouched for
that key — which is normal on a first install and the reason multiple
independent builders signing the same hash is the actual security property.

Install:

````bash
tar -xzf bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin \
  bitcoin-${VERSION}/bin/bitcoind \
  bitcoin-${VERSION}/bin/bitcoin-cli \
  bitcoin-${VERSION}/bin/bitcoin-util \
  bitcoin-${VERSION}/bin/bitcoin-wallet
bitcoind --version
````

Since v30.0 the tarball also ships a `bitcoin` wrapper command: `bitcoin node`
is `bitcoind`, `bitcoin rpc` is `bitcoin-cli -named`, `bitcoin help` lists the
rest. It adds no functionality of its own and nothing is deprecated by it — the
direct commands below work unchanged.

## Configure

````bash
sudo -u bitcoind mkdir -p /var/lib/bitcoind
sudo tee /var/lib/bitcoind/bitcoin.conf > /dev/null <<'EOF'
# Network
listen=1
maxconnections=64

# Local RPC only. Never expose 8332 to the internet.
server=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1

# Index everything a service backend usually needs.
txindex=1

# Resource limits
dbcache=4096
par=4
EOF
sudo chown bitcoind:bitcoind /var/lib/bitcoind/bitcoin.conf
sudo chmod 600 /var/lib/bitcoind/bitcoin.conf
````

Field-by-field reference, including the settings this minimal file leaves out,
is in the **Configuration** guide. Two decisions are worth making before the
first sync, because changing them later costs a full reindex:

- **`prune` and `txindex` are mutually exclusive.** To run pruned, drop
  `txindex=1` and set `prune=550000` (≈550 GB retained).
- Additional indexes (`blockfilterindex`, `coinstatsindex`, `txospenderindex`)
  are cheap to add later but are built by a rescan that takes hours.

`dbcache=4096` is an explicit choice, not the default. Since v31.0 the default
is 1024 MiB on hosts where at least 4096 MiB of RAM is detected — and in a
container the detected RAM can exceed what the cgroup actually allows, which
turns into an OOM kill. Set `dbcache` explicitly on any containerised node.

### RPC credentials

The default and safest scheme is the **cookie**: `bitcoind` writes
`/var/lib/bitcoind/.cookie` at startup, mode `0600`, and any process that can
read it as the `bitcoind` user authenticates with no shared secret anywhere.
Use it for local administration.

Only when a separate service account needs RPC, add a hashed credential. Fetch
the official helper, read it, then run it:

````bash
wget -O /tmp/rpcauth.py https://raw.githubusercontent.com/bitcoin/bitcoin/v31.1/share/rpcauth/rpcauth.py
less /tmp/rpcauth.py
python3 /tmp/rpcauth.py myservice
````

Add the resulting `rpcauth=` line to `bitcoin.conf`. That line contains only a
salted hash and is safe to store. The generated password is not: put it in your
secret store, never in the repository, a command line, a log or a chat message.

## Open the P2P port

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8333/tcp
sudo ufw enable
````

`8333/tcp` inbound lets other nodes connect to you. Port `8332` is RPC and must
stay closed to the internet — see **Security hardening** for the full policy.

Note that `-natpmp` defaults to `1` since v30.0, so a node behind a
NAT-PMP/PCP-capable router may become reachable without you opening anything.
If that is not what you want, set `natpmp=0` explicitly.

## systemd unit

````bash
sudo tee /etc/systemd/system/bitcoind.service > /dev/null <<'EOF'
[Unit]
Description=Bitcoin Core daemon
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/bitcoind -datadir=/var/lib/bitcoind -conf=/var/lib/bitcoind/bitcoin.conf -pid=/run/bitcoind/bitcoind.pid
Type=notify
NotifyAccess=all
PIDFile=/run/bitcoind/bitcoind.pid
Restart=on-failure
TimeoutStartSec=infinity
TimeoutStopSec=1200
User=bitcoind
Group=bitcoind
RuntimeDirectory=bitcoind
StateDirectory=bitcoind
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
NoNewPrivileges=true
PrivateDevices=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now bitcoind
````

`TimeoutStartSec=infinity` is deliberate: the initial block download takes many
hours and systemd must not kill it partway. `TimeoutStopSec=1200` is equally
deliberate — **a `bitcoind` killed mid-flush corrupts the chainstate** and costs
a multi-hour reindex. Give it time to shut down cleanly.

## Initial block download

IBD is the long part: expect roughly 4–12 hours on an NVMe host with a fast
link, far longer on spinning disks or a small `dbcache`. Watch progress:

````bash
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getblockchaininfo \
  | jq '{blocks, headers, verificationprogress, size_on_disk}'
sudo journalctl -u bitcoind -f
````

Two ways to shorten it, both covered in **Pruning and storage**:

- `assumeutxo` — load a signed UTXO snapshot with `loadtxoutset`, get a usable
  node in minutes while the historical blocks validate in the background;
- raising `dbcache` for the duration of IBD (8–16 GB if the RAM is there), then
  lowering it again.

Never copy a `blocks/` or `chainstate/` directory from an untrusted source. A
node that trusts someone else's chainstate has given up the only thing it was
built to do.

## Verify

````bash
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getblockchaininfo | jq '{chain, blocks, headers, verificationprogress, pruned, initialblockdownload}'
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getnetworkinfo | jq '{version, subversion, connections, connections_in, connections_out}'
````

The node is fully synced when `blocks` equals `headers`, `verificationprogress`
is essentially `1`, and `initialblockdownload` is `false`. Compare the tip
against an independent source before you trust it:

````bash
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getbestblockhash
curl -s https://blockstream.info/api/blocks/tip/hash
curl -s https://mempool.space/api/blocks/tip/hash
````

All hashes must match. Equal block heights with different hashes means you are
on a different chain than the rest of the network, which matters far more than
being a few blocks behind.

`connections_in` greater than zero confirms `8333/tcp` is genuinely reachable.
A node with `connections_in: 0` and healthy `connections_out` is not broken —
it verifies the chain exactly as well — it simply does not serve peers. That is
a reasonable choice for a node that exists only as a backend for your own
services, and a poor one if you meant to contribute capacity to the network.
Decide which of the two you are running, and set the firewall to match.

## Next

| You want | Read |
|---|---|
| every `bitcoin.conf` option that matters | **Configuration** |
| containers instead of systemd | **Docker install** |
| a smaller disk, or a faster first sync | **Pruning and storage** |
| Electrum/Esplora/mempool backends on top | **RPC, indexes and APIs** |
| a Lightning node | **Lightning node** |
| metrics and alerts | **Monitoring** |
| Tor, firewall, key custody | **Security hardening** |
| to move to the next release safely | **Upgrades** |

## Sources

- [bitcoincore.org — v31.1 release notes](https://bitcoincore.org/en/releases/31.1/)
- [bitcoincore.org — v31.0 release notes](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes](https://bitcoincore.org/en/releases/30.0/)
- [bitcoin.org — running a full node](https://bitcoin.org/en/full-node)
- [bitcoin-core/guix.sigs — builder attestations](https://github.com/bitcoin-core/guix.sigs)
- [bitcoin/bitcoin — `doc/reduce-memory.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/reduce-memory.md)
