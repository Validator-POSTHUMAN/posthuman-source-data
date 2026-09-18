# Upgrading Bitcoin Core

Bitcoin has no coordinated upgrade height and no halt: the network does not
stop for you, and a node left behind keeps working until a soft fork activates
rules it does not know. That makes upgrades routine — and makes it easy to
postpone one until the node is running end-of-life software.

## Support window

| Release | Status |
|---|---|
| **v31.1** | current |
| v31.0 | superseded — upgrade, see below |
| v30.x, v29.x | supported |
| **v28.x and older** | **end of life, no updates including security fixes** |

Each new major release moves the EOL line forward by one: v30.0 retired v27.x
and older, v31.0 retired v28.x and older.

v31.1 is a bug-fix release with two fixes an operator should care about:

- the chainstate database repeatedly rewrote large parts of itself, causing
  continuous excessive disk reads and writes in normal operation;
- `-privatebroadcast` leaked the node's clear-net IP under some conditions.

If you run v31.0, this is not optional.

## Before you upgrade

1. **Read the release notes** for every version you are skipping, not only the
   target. Defaults changed materially in v30.0 and v31.0 — see below.
2. Check the current state and write it down:

````bash
bitcoin-cli getblockchaininfo | jq '{blocks, size_on_disk, pruned}'
bitcoin-cli getbestblockhash
bitcoin-cli getnetworkinfo | jq '{version, subversion}'
systemctl show bitcoind -p NRestarts
````

3. Back up `bitcoin.conf`, the systemd unit and any wallet. Keep the **old
   binary** — that is the rollback.
4. Confirm free disk: an index migration or a reindex needs headroom.

## Upgrade

````bash
VERSION=31.1
cd /tmp
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS
wget https://bitcoincore.org/bin/bitcoin-core-${VERSION}/SHA256SUMS.asc
sha256sum --ignore-missing --check SHA256SUMS
gpg --verify SHA256SUMS.asc SHA256SUMS        # against bitcoin-core/guix.sigs builder keys

sudo systemctl stop bitcoind
# wait for a clean exit — "Shutdown: done" in the log. Do not hurry this.
journalctl -u bitcoind -n 20

tar -xzf bitcoin-${VERSION}-x86_64-linux-gnu.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin \
  bitcoin-${VERSION}/bin/bitcoind bitcoin-${VERSION}/bin/bitcoin-cli \
  bitcoin-${VERSION}/bin/bitcoin-util bitcoin-${VERSION}/bin/bitcoin-wallet
sudo systemctl start bitcoind
````

Stopping cleanly is the step that goes wrong. A `bitcoind` killed mid-flush
leaves a corrupt chainstate and costs a multi-hour reindex — which then gets
blamed on the new version.

## Verify

````bash
bitcoin-cli getnetworkinfo | jq '{version, subversion}'
bitcoin-cli getblockchaininfo | jq '{blocks, headers, verificationprogress, initialblockdownload}'
bitcoin-cli getbestblockhash            # compare against mempool.space and blockstream.info
bitcoin-cli getindexinfo                 # indexes present and synced
systemctl show bitcoind -p NRestarts -p ActiveState
journalctl -u bitcoind --since "10 minutes ago" | grep -Ei "error|warning|corrupt"
````

Then verify what depends on the node — ZMQ subscribers, electrs, Lightning —
before calling the upgrade done. The daemon being healthy is not the same as
the stack being healthy.

## Downgrades

Downgrading is **not** generally supported and is the reason to keep the old
binary *and* a data backup:

- Wallet migrations are one-way. A wallet migrated by a newer version may not
  open on the old one.
- Index format changes are one-way. `coinstatsindex` moved to
  `indexes/coinstatsindex/` in v30.0; the old `indexes/coinstats/` is left
  behind precisely so a downgrade remains possible — delete it only once you
  have committed.
- Chainstate written by a newer version may not be readable by an older one; in
  the worst case the recovery is a reindex.

Plan the rollback as "old binary plus a datadir snapshot from before the
upgrade", not "reinstall the old version".

## Defaults that changed — check your config

### v30.0

| Setting | New default | Impact |
|---|---|---|
| `-natpmp` | `1` | node may open its own P2P port through the router |
| `-minrelaytxfee`, `-incrementalrelayfee` | 0.1 sat/vB | change both together or neither |
| `-blockmintxfee` | 0.001 sat/vB | affects block templates if you mine |
| `-datacarriersize` | 100000 | set `83` to restore the previous OP_RETURN limit |
| `-maxorphantx` | **no effect** | remove it — it becomes a startup error in a future release |
| `coinstatsindex` | rebuilt from scratch | plan for the resync time |
| new `bitcoin` wrapper command | — | `bitcoin node`, `bitcoin rpc`, `bitcoin help` |

### v31.0

| Setting | Change | Impact |
|---|---|---|
| `-dbcache` | default 1024 MiB when ≥4096 MiB RAM detected | **set it explicitly in containers** — detected RAM can exceed the cgroup limit and cause OOM kills |
| `-paytxfee`, `settxfee` | **removed** | use `fee_rate` per transaction |
| `onlynet=tor` | **removed** | use `onlynet=onion` |
| `-asmap` | embedded map, no external file | external file now needs an explicit filename |
| mempool | cluster mempool | ancestor/descendant limits gone; clusters capped at 64 tx / 101 kvB; CPFP carve-out removed; stricter RBF |
| `getpeerinfo.startingheight` | hidden | needs `-deprecatedrpc=startingheight`; removed next major |
| fee estimator | 0.1 sat/vB minimum bucket | `fee_estimates.dat` stats reset on first start |

Cluster mempool is the change most likely to surprise custom tooling. If you
parse `getmempoolancestors`/`getmempooldescendants` limits, rely on the CPFP
carve-out, or build packages by hand, test against v31 on signet before
touching production.

## Upgrading the rest of the stack

| Component | Watch for |
|---|---|
| LND / Core Lightning | **never run two instances against one channel state**; check compatibility with the Core version first; channel DB migrations are one-way |
| electrs / Fulcrum | index format changes force a reindex — hours |
| mempool / esplora | schema migrations; keep the database backup |
| Miner firmware | verify the payout address after every update |

Upgrade the node first, confirm it is healthy, then the layers above it — one
at a time, verifying between each.

## Sources

- [bitcoincore.org — v31.1 release notes](https://bitcoincore.org/en/releases/31.1/)
- [bitcoincore.org — v31.0 release notes](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes](https://bitcoincore.org/en/releases/30.0/)
- [bitcoincore.org — announcements list](https://bitcoincore.org/en/list/announcements/join/)
- [bitcoin-core/guix.sigs](https://github.com/bitcoin-core/guix.sigs)
