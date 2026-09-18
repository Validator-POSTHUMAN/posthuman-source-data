# Lightning Node

## Read this first: Lightning state is not replicable

A Lightning node's channel database is the only record of the current channel
state. Two consequences that have no equivalent on the Bitcoin layer:

- **Never run two instances against the same channel state.** Publishing an old
  commitment transaction lets your counterparty take the channel balance
  through a justice transaction. Restoring a stale copy of `channel.db` is the
  standard way people lose funds. It is the same failure class as double
  signing on a proof-of-stake validator, and it deserves the same discipline:
  one live instance, fenced, ever.
- **A file-level backup of a running channel database is worse than useless.**
  The only safe backup is the **Static Channel Backup** (SCB), which cannot
  restore balances by itself — it triggers cooperative or force closes so funds
  return on-chain.

Treat the seed and the SCB as key material. Everything in **Backup and
recovery** applies.

## Prerequisites

A Bitcoin Core node with ZMQ enabled, ideally archival:

````ini
server=1
txindex=1
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
rpcauth=lightning:<salt>$<hash>
````

A pruned node works but is a liability: a force close needing a block below the
prune horizon fails at the moment you most need it to succeed. Keep at least
`prune=50000` if you must prune.

## Which implementation

| | [LND](https://github.com/lightningnetwork/lnd) **v0.21.3-beta** | [Core Lightning](https://github.com/ElementsProject/lightning) **v26.06.7** |
|---|---|---|
| Language | Go | C |
| Interface | gRPC + REST, macaroon auth | JSON-RPC over a Unix socket |
| Channel DB | bbolt, or Postgres/etcd | SQLite, or Postgres |
| Extensibility | subservers, `lnd` plugins ecosystem | first-class plugin system |
| Ecosystem | largest: Loop, Pool, LNDhub, RTL, Zeus, BTCPay | CLN plugins, BTCPay, Greenlight |
| Best fit | product integration, routing at scale | operators who want a small auditable daemon |

Both are production software. LND has the larger integration surface; CLN has
the smaller attack surface and a cleaner plugin model.

## LND

### Install

````bash
VERSION=v0.21.3-beta
cd /tmp
wget https://github.com/lightningnetwork/lnd/releases/download/${VERSION}/lnd-linux-amd64-${VERSION}.tar.gz
wget https://github.com/lightningnetwork/lnd/releases/download/${VERSION}/manifest-${VERSION}.txt
wget https://github.com/lightningnetwork/lnd/releases/download/${VERSION}/manifest-roasbeef-${VERSION}.sig
sha256sum --check manifest-${VERSION}.txt --ignore-missing
gpg --verify manifest-roasbeef-${VERSION}.sig manifest-${VERSION}.txt
tar -xzf lnd-linux-amd64-${VERSION}.tar.gz
sudo install -m 0755 -t /usr/local/bin lnd-linux-amd64-${VERSION}/lnd lnd-linux-amd64-${VERSION}/lncli
lnd --version
````

The release is signed by the maintainer; import the key from the
[lnd repository](https://github.com/lightningnetwork/lnd/tree/master/scripts/keys)
and verify before you install. Verification is the same discipline as for Core.

### Configure

````ini
# /var/lib/lnd/lnd.conf
[Application Options]
alias=POSTHUMAN
color=#2d2d2d
listen=0.0.0.0:9735
rpclisten=127.0.0.1:10009
restlisten=127.0.0.1:8080
maxpendingchannels=5
accept-keysend=true

[Bitcoin]
bitcoin.mainnet=true
bitcoin.node=bitcoind
bitcoin.defaultchanconfs=3

[Bitcoind]
bitcoind.rpchost=127.0.0.1:8332
bitcoind.rpcuser=lightning
bitcoind.rpcpass=<from secret store>
bitcoind.zmqpubrawblock=tcp://127.0.0.1:28332
bitcoind.zmqpubrawtx=tcp://127.0.0.1:28333

[wtclient]
wtclient.active=true

[watchtower]
watchtower.active=true
````

`bitcoind.rpcpass` is the one place a plaintext RPC password is unavoidable.
Keep `lnd.conf` mode `0600`, owned by the daemon user, and out of git.

### First start

````bash
sudo systemctl start lnd
lncli create           # interactive: seed passphrase, wallet password
````

`lncli create` prints a **24-word aezeed** exactly once. Write it down offline.
It recovers on-chain funds and, with an SCB, initiates channel recovery — it
does not by itself restore channel balances.

The wallet is encrypted at rest and must be unlocked after every restart:

````bash
lncli unlock
````

For unattended restarts, either use `wallet-unlock-password-file` with a
root-only file, or systemd credentials. Do not put the password in the unit's
environment where it lands in `systemctl show` output.

### Operate

````bash
lncli getinfo | jq '{version, synced_to_chain, synced_to_graph, num_active_channels, block_height}'
lncli walletbalance
lncli channelbalance
lncli listchannels | jq '.channels[] | {remote_pubkey, capacity, local_balance, active}'
lncli openchannel --node_key=<pubkey> --local_amt=1000000 --sat_per_vbyte=5
lncli closechannel --funding_txid=<txid> --output_index=0
lncli describegraph | jq '.nodes | length'
````

`synced_to_chain: false` after a restart is normal; `false` for more than a few
minutes means the ZMQ feed or the backing node is broken. `synced_to_graph`
matters for routing — a node that is not graph-synced cannot build paths.

### Static Channel Backup

`channel.backup` lives in the data directory and is **rewritten on every
channel open and close**. Ship it off-host on every change:

````bash
# one-shot copy
scp /var/lib/lnd/data/chain/bitcoin/mainnet/channel.backup backup-host:/srv/lnd-scb/

# continuous, via inotify
inotifywait -m -e close_write /var/lib/lnd/data/chain/bitcoin/mainnet/channel.backup \
  | while read -r _; do rsync -a channel.backup backup-host:/srv/lnd-scb/; done
````

Recovery, on a **new** node with the same seed:

````bash
lncli create                       # choose "restore from seed"
lncli restorechanbackup --multi_file=/srv/lnd-scb/channel.backup
````

This asks every counterparty to force-close, and your balances return on-chain
after the timelocks. Expect on-chain fees and a delay. Never point a restored
node at channels that a still-running instance also has.

### Watchtowers

A watchtower publishes the justice transaction if a counterparty broadcasts an
old state while your node is offline. `wtclient.active=true` is the client
side; add a tower:

````bash
lncli wtclient add <tower-pubkey>@<host>:9911
lncli wtclient towers
````

Run your own tower (`watchtower.active=true` above) for other nodes you
operate, and register at least one independent tower for the ones that hold
real balances.

## Core Lightning

### Install

````bash
sudo apt -y install lightningd    # Debian/Ubuntu package, or build from source
lightningd --version
````

Release tarballs and signatures are published on the
[releases page](https://github.com/ElementsProject/lightning/releases); verify
them before installing, as with everything else here.

### Configure

````ini
# /var/lib/lightningd/config
network=bitcoin
alias=POSTHUMAN
rgb=2d2d2d
bind-addr=0.0.0.0:9735
log-level=info
bitcoin-rpcconnect=127.0.0.1
bitcoin-rpcport=8332
bitcoin-rpcuser=lightning
bitcoin-rpcpassword=<from secret store>
````

### Operate

````bash
lightning-cli getinfo
lightning-cli listfunds
lightning-cli listpeerchannels
lightning-cli connect <pubkey>@<host>:9735
lightning-cli fundchannel <pubkey> 1000000
lightning-cli close <channel-id>
````

### Key material and backup

`hsm_secret` in the network directory **is** the node identity and the
on-chain key. Back it up offline, encrypted, once — it does not change.
Channel state lives in `lightningd.sqlite3`; the supported continuous backup is
the [`backup` plugin](https://github.com/lightningd/plugins/tree/master/backup),
which maintains a consistent replica instead of copying a live database file.

`emergency.recover` and `lightning-cli emergencyrecover` provide the CLN
equivalent of SCB recovery. As with LND: it recovers funds by closing channels,
not by resuming them.

## Monitoring

Minimum set for a node with real balances:

| Signal | Alert when |
|---|---|
| `getinfo.synced_to_chain` | false for > 5 min |
| `getinfo.synced_to_graph` (LND) | false for > 15 min |
| active vs total channels | any channel inactive > 15 min |
| peer count | 0, or a sustained drop |
| on-chain wallet balance | below the fee reserve needed to force-close every channel |
| SCB file age vs last channel event | backup older than the last open/close |
| watchtower session count | 0 |
| backing `bitcoind` | anything in the **Monitoring** guide |

A Lightning node is the one component here where "the process is up" is
actively misleading: a node that is running, unlocked and not graph-synced
routes nothing and earns nothing while looking healthy.

## Sources

- [lightningnetwork/lnd — releases](https://github.com/lightningnetwork/lnd/releases)
- [docs.lightning.engineering — operational guides](https://docs.lightning.engineering/)
- [ElementsProject/lightning — releases](https://github.com/ElementsProject/lightning/releases)
- [docs.corelightning.org](https://docs.corelightning.org/)
- [lightningd/plugins — `backup`](https://github.com/lightningd/plugins/tree/master/backup)
- [lightningdevkit.org](https://lightningdevkit.org/)
