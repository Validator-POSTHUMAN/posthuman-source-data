# Backup and Recovery

## What is worth backing up, and what is not

| Data | Back it up? | Why |
|---|---|---|
| `wallet.dat` / wallet directory | **yes, offline** | irreplaceable key material |
| Wallet descriptors (`listdescriptors`) | **yes** | reconstructs the whole wallet from the seed |
| LND `channel.backup` (SCB) | **yes, on every change** | only supported channel backup |
| LND aezeed / CLN `hsm_secret` | **yes, offline, once** | node identity and on-chain funds |
| `bitcoin.conf`, systemd units | yes | cheap, saves an hour |
| `blocks/` | no | re-downloadable, 856 GB |
| `chainstate/` | no | rebuildable, and a stale copy is dangerous |
| `indexes/` | no | rebuilt from blocks |
| LND `channel.db` / CLN `lightningd.sqlite3` | **no — restoring a stale copy loses funds** | see below |

The rule: **back up keys and the things that cannot be recomputed. Never back
up consensus or channel state as a file you might one day restore.**

## Bitcoin Core wallets

Since v23 wallets are descriptor wallets, and the descriptors plus the seed are
the complete backup:

````bash
bitcoin-cli -rpcwallet=<name> listdescriptors true > /secure/descriptors-<name>.json   # includes private keys
bitcoin-cli -rpcwallet=<name> backupwallet /secure/wallet-<name>-$(date +%F).dat
````

`listdescriptors true` prints **private keys**. Treat that file exactly like a
seed phrase: encrypted storage, offline, never in git, never in a chat.

Restore:

````bash
bitcoin-cli createwallet "<name>" false false "" true true    # blank, descriptor wallet
bitcoin-cli -rpcwallet=<name> importdescriptors '<contents of the descriptors file>'
# or simply place the backed-up wallet directory in the datadir and load it
bitcoin-cli loadwallet "<name>"
````

After import, rescan from the wallet's birthday:

````bash
bitcoin-cli -rpcwallet=<name> rescanblockchain 700000
````

A rescan needs the blocks. **A pruned node cannot rescan below its prune
horizon** — if the backup you may one day restore has an old birthday, the node
you restore onto must be archival.

Verify a restored wallet before trusting it:

````bash
bitcoin-cli -rpcwallet=<name> getwalletinfo | jq '{walletname, descriptors, private_keys_enabled, keypoolsize}'
bitcoin-cli -rpcwallet=<name> getbalances
bitcoin-cli -rpcwallet=<name> listunspent | jq 'length'
````

An untested backup is not a backup. Restore into a throwaway datadir on signet
or against a watch-only copy at least once, and record that you did.

## Lightning

This is where file-level backups actively destroy funds.

### Static Channel Backup — the only safe channel backup

`channel.backup` is rewritten on every channel open and close. Ship it off-host
on every change:

````bash
inotifywait -m -e close_write /var/lib/lnd/data/chain/bitcoin/mainnet/channel.backup |
  while read -r _; do
    rsync -a /var/lib/lnd/data/chain/bitcoin/mainnet/channel.backup backup-host:/srv/lnd-scb/
  done
````

An SCB does **not** restore channel balances. It tells your counterparties to
close, and funds return on-chain after the timelocks — with on-chain fees and a
delay. That is the intended behaviour, and it is the safe one.

### Never restore a channel database

Restoring a stale `channel.db` (LND) or `lightningd.sqlite3` (CLN) makes your
node broadcast an outdated commitment. The counterparty takes the whole channel
balance through a justice transaction, correctly and irreversibly. The same
applies to a filesystem snapshot, a VM snapshot, or a second instance started
against a copy of the data directory.

One live Lightning instance per channel state. Ever. Fence the old host before
starting a new one — stop the service, disable it, mask it, and confirm no
process holds the data directory.

### Seeds and identity

| | LND | Core Lightning |
|---|---|---|
| Seed | 24-word aezeed, shown once at `lncli create` | `hsm_secret` file |
| Recovers | on-chain funds; with SCB, initiates channel recovery | on-chain funds and node identity |
| Backup | offline, written down, never digital | offline, encrypted, once — it does not change |

CLN's supported continuous backup is the
[`backup` plugin](https://github.com/lightningd/plugins/tree/master/backup),
which maintains a consistent replica rather than copying a live database.
`lightning-cli emergencyrecover` plus `emergency.recover` is the CLN equivalent
of SCB recovery: it recovers funds by closing channels, not by resuming them.

## Node recovery scenarios

| Scenario | Action | Cost |
|---|---|---|
| Unclean shutdown, corrupt chainstate | `-reindex-chainstate` | hours |
| Block files suspect, or `txindex`/`prune` changed | `-reindex` | hours to days |
| Disk failure, keys safe | rebuild host, resync (use assumeutxo) | hours |
| Disk failure, wallet on that disk and no backup | funds are gone | — |
| Host compromise | rebuild from scratch; treat every key on it as burned | — |

Recovering the chain is always possible and never urgent. Recovering keys is
impossible and always urgent. Budget your effort accordingly.

Fast rebuild path, in order: fresh host → verified binary → config from backup
→ `loadtxoutset` with a signed snapshot → let the background chainstate
validate → restore wallet descriptors last, onto a node you have verified is on
the right chain.

## Off-host discipline

- At least one copy outside the machine's failure domain, and outside its RAID
  set — RAID is not a backup.
- Checksum after every copy; verify the checksum on the destination, not the
  source.
- Encrypt anything containing key material at rest.
- Restore-test on a schedule. A backup that has never been restored is a
  hypothesis.
- Record where each backup lives and who can reach it. A backup nobody can find
  during an incident does not exist.

## Sources

- [developer.bitcoin.org — `listdescriptors`, `importdescriptors`, `backupwallet`](https://developer.bitcoin.org/reference/rpc/)
- [docs.lightning.engineering — recovering funds and SCB](https://docs.lightning.engineering/lightning-network-tools/lnd/recovery)
- [lightningd/plugins — `backup`](https://github.com/lightningd/plugins/tree/master/backup)
- [bitcoin/bitcoin — `doc/managing-wallets.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/managing-wallets.md)
