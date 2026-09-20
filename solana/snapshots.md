# Solana Snapshots and Bootstrap

A Solana validator never syncs from genesis in practice. It loads a **snapshot**
— a full account state at some slot, plus an incremental on top — and replays
forward from there. Snapshots are therefore not an optimisation on Solana; they
are the boot path, and every restart goes through them.

## The two archives

| Archive | What it is | Typical size (mainnet-beta) |
|---|---|---|
| `snapshot-<slot>-<hash>.tar.zst` | full account state at `<slot>` | 70–110 GB |
| `incremental-snapshot-<base>-<slot>-<hash>.tar.zst` | delta since the full snapshot's base slot | 1–10 GB |

An incremental is only usable with the full snapshot whose base slot it names.
Deleting the full archive orphans every incremental built on it.

## Where they live — and the mistake to avoid

`--snapshots <dir>` decides where archives are written. If you do not pass it,
they land inside the ledger directory.

**Put snapshots on the ledger filesystem, never on root.** Snapshot packaging
needs headroom for a temporary copy of the archive it is writing. A root
filesystem that fills during packaging does not degrade — replay and voting stop
at that slot with `No space left on device`, and the recovery is a full network
snapshot fetch that costs far more downtime than the disk would have cost.

````
--ledger    /mnt/ledger
--accounts  /mnt/accounts
--snapshots /mnt/ledger/snapshots
````

Budget at least **2× the full snapshot size plus the incremental** as free space
on the snapshot filesystem, and alert on it.

## Snapshot generation flags

````
--full-snapshot-interval-slots 25000
--incremental-snapshot-interval-slots 4000
--maximum-full-snapshots-to-retain 2
--maximum-incremental-snapshots-to-retain 4
````

Higher intervals mean fewer, cheaper packaging events but a longer replay after
a restart. Retention is the knob that actually controls disk: two full snapshots
is the sane minimum, because you want a known-good one while the next is being
written.

An RPC node that serves no other validators can add `--no-snapshot-fetch` once
it has local state, and a node that should never publish snapshots to peers can
run with `--no-untrusted-rpc`-style restrictions plus a closed firewall.

## Bootstrapping a fresh node

On first start the validator fetches genesis and a snapshot from its entrypoints
and known validators:

````
--entrypoint entrypoint.mainnet-beta.solana.com:8001
--entrypoint entrypoint2.mainnet-beta.solana.com:8001
--entrypoint entrypoint3.mainnet-beta.solana.com:8001
--known-validator 7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2
--known-validator GdnSyH3YtwcxFvQrVVJMm1JhTS4QVX7MFsX56uJLUfiZ
--known-validator DE1bawNcRJB9rVm3buyMVfr8mBEoyyu73NBovf2oXJsJ
--known-validator CakcnaRDHka2gXyfbEd2d3xsvkJkqsLw2akB3zsN1D2S
--only-known-rpc
--expected-genesis-hash 5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d
--wal-recovery-mode skip_any_corrupted_record
--limit-ledger-size
````

`--only-known-rpc` is a security control, not a performance one: without it the
node will accept a snapshot from an arbitrary gossip peer. Always set it
together with `--known-validator`, and always set `--expected-genesis-hash` so a
misconfigured entrypoint cannot quietly put you on the wrong cluster.

Expect the first boot to take **one to several hours**: download, untar,
rebuild the bank, then replay to the tip.

## Restart discipline

A restart is a snapshot load. Do it in this order, every time:

1. **Confirm a fresh snapshot exists.** Check the newest full and incremental
   under `--snapshots` and how many slots behind the tip they are. Restarting
   with a stale pair turns a two-minute restart into a network fetch.
2. **Confirm free space** on ledger, accounts and snapshots filesystems.
3. **Hand the identity to the spare** if this is a voting validator and you have
   a second host — see the keys guide.
4. Stop the service and wait for the process to exit fully. `systemctl start` on
   an already-active unit is a no-op; use `stop` then `start`, or `restart`.
5. Watch the log through bank load and replay.
6. Confirm from an **external** RPC that the validator is current and not
   delinquent before calling the restart done.

````bash
ls -lt /mnt/ledger/snapshots | head
df -h /mnt/ledger /mnt/accounts
solana catchup --our-localhost
solana validators --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
````

## Recovering when the local snapshot is rejected

Agave will refuse a local snapshot it cannot use — wrong shred version after a
cluster restart, corrupted archive, or a base slot too far behind — and fall
back to a network fetch. That is the designed behaviour, and the failure mode to
watch for is disk, not the fetch itself:

- make room **before** the fetch, not during it;
- delete only snapshot archives, and only pairs you have replaced;
- never delete the ledger, the accounts directory, the tower file or any keypair
  to free space.

If you must free space under pressure, the safe order is: old snapshot pairs,
then rotated logs, then journald, then build trees. Everything else needs a
decision, not a `rm`.

## Third-party snapshot services

Public snapshot mirrors can cut a bootstrap from hours to tens of minutes, and
several large operators publish them. Two rules:

- verify the source. A snapshot is account state; a malicious one is a
  compromised node. Prefer sources you can attribute to a known operator, and
  prefer `--known-validator` + `--only-known-rpc` over any HTTP mirror.
- verify the shred version and genesis hash after load, before you let the node
  vote.

## Verification after any snapshot operation

````bash
# local
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'

# external truth
solana vote-account <vote-account-pubkey> --url https://api.mainnet-beta.solana.com
solana validators --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
````

Local health alone proves nothing about voting. Take two external samples a
minute apart and require `lastVote` and `rootSlot` to advance in both.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
