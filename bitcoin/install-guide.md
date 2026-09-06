# Bitcoin Full Node Installation Guide

## Read this first: Bitcoin has no validators

Bitcoin has no staking, no validator set, no delegation and no slashing. There
is nothing to register and nothing to bond. Two roles exist:

- a **full node** independently verifies every block and transaction against
  consensus rules and relays them. This is what this guide sets up, and it is
  what gives you your own trustless view of the chain.
- a **miner** produces blocks with proof of work. Mining is a hardware and
  energy business, not a node-operations one, and is out of scope here.

Running a full node earns no protocol reward. It buys you verification you do
not have to trust anyone else for, and it is the correct backend for wallets,
explorers, payment processing and any service that must not depend on someone
else's RPC.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 2 cores | 4 cores     |
| RAM       | 4 GB    | 8–16 GB     |
| Disk      | 800 GB SSD (full archive) | 1.5 TB NVMe, room to grow |
| Network   | 50 Mbps, unmetered preferred | 1 Gbps |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

The chain grows continuously. Size the disk for at least two years ahead, or
run pruned — see below.

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
VERSION=28.0
cd /tmp
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS.asc
````

Check the hash of what you downloaded against the signed list:

````bash
sha256sum --ignore-missing --check SHA256SUMS
````

Then verify the signatures on `SHA256SUMS` itself against the Bitcoin Core
builder keys published at
`https://github.com/bitcoin-core/guix.sigs`. A matching hash proves the file is
intact; only the signature check proves it is the file the project released.

Install:

````bash
tar -xzf bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin bitcoin-${VERSION}/bin/bitcoind bitcoin-${VERSION}/bin/bitcoin-cli
bitcoind --version
````

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

To run pruned instead of archival, replace `txindex=1` with `prune=550000`
(about 550 GB retained). **`prune` and `txindex` are mutually exclusive**, and
switching between them later requires a full reindex — decide before the first
sync, not after.

Generate an RPC credential with the official helper rather than putting a
password in the config file:

````bash
python3 <(curl -sS https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py) myservice
````

Add the resulting `rpcauth=` line to `bitcoin.conf` and keep the generated
password in your secret store — never in the repository, a command line or a
chat message.

## Open the P2P port

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8333/tcp
sudo ufw enable
````

`8333/tcp` inbound lets other nodes connect to you. Port `8332` is RPC and must
stay closed to the internet.

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
TimeoutStopSec=600
User=bitcoind
Group=bitcoind
RuntimeDirectory=bitcoind
StateDirectory=bitcoind
PrivateTmp=true
ProtectSystem=full
NoNewPrivileges=true
PrivateDevices=true
MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now bitcoind
````

`TimeoutStartSec=infinity` is deliberate: the initial block download takes many
hours and systemd must not kill it partway.

## Verify

````bash
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getblockchaininfo | jq '{chain, blocks, headers, verificationprogress, pruned, initialblockdownload: .initialblockdownload}'
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getnetworkinfo | jq '{version, subversion, connections, connections_in, connections_out}'
````

The node is fully synced when `blocks` equals `headers`, `verificationprogress`
is essentially `1`, and `initialblockdownload` is `false`. Compare the tip
against an independent source before you trust it:

````bash
sudo -u bitcoind bitcoin-cli -datadir=/var/lib/bitcoind getbestblockhash
curl -s https://blockstream.info/api/blocks/tip/hash
````

Both hashes must match. Equal block heights with different hashes means you are
on a different chain than the rest of the network, which matters far more than
being a few blocks behind.

`connections_in` greater than zero confirms `8333/tcp` is genuinely reachable.

## Upgrade

Stop the service, verify the new release's signatures exactly as above, replace
the binaries, start the service, then re-check version, sync state and the tip
hash against an independent source. Bitcoin Core supports downgrades poorly
across major versions — keep the previous binary and a data backup until the
new version has been running cleanly.

## Monitoring

Watch: service state and restart count, `blocks` versus `headers`, tip hash
against an independent source, peer counts in and out, disk free and its growth
rate, and mempool size. For a pruned node also watch that pruning is actually
keeping up with your disk budget.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
