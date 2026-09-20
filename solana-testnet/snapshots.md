# Solana Testnet Snapshots

Same mechanics as mainnet: a validator boots from a full snapshot plus an
incremental and replays forward. What differs on testnet is how often the local
snapshot becomes unusable, and why.

## Layout

````
--ledger    /mnt/ledger
--accounts  /mnt/accounts
--snapshots /mnt/ledger/snapshots
````

Snapshots on the ledger filesystem, never on root. A root filesystem that fills
during snapshot packaging stops replay and voting with
`No space left on device`, and the recovery is a full network fetch. Budget at
least 2× the full snapshot size plus the incremental as free space, and alert on
it.

Testnet full snapshots are smaller than mainnet's, but the ratio and the failure
mode are identical.

## Bootstrap

````
--entrypoint entrypoint.testnet.solana.com:8001
--entrypoint entrypoint2.testnet.solana.com:8001
--entrypoint entrypoint3.testnet.solana.com:8001
--known-validator 5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on
--known-validator dDzy5SR3AXdYWVqbDEkVFdvSPCtS9ihF5kJkHCtXoFs
--known-validator Ft5fbkqNa76vnsjYNwjDZUXoTWpP7VYm3mtsaQckQADN
--known-validator eoKpUABi59aT4rR9HGS3LcMecfut9x7zJyodWWP43YQ
--known-validator 9QxCLckBiJc783jnMvXZubK4wH86Eqqvashtrwvcsgkv
--only-known-rpc
--expected-genesis-hash 4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY
--wal-recovery-mode skip_any_corrupted_record
--limit-ledger-size
````

`--only-known-rpc` together with `--known-validator` is a security control, not
a performance one: without it the node accepts a snapshot from an arbitrary
gossip peer. `--expected-genesis-hash` stops a misconfigured entrypoint putting
you on another cluster — a real risk when you operate both clusters from the
same workstation.

## Generation and retention

````
--full-snapshot-interval-slots 25000
--incremental-snapshot-interval-slots 4000
--maximum-full-snapshots-to-retain 2
--maximum-incremental-snapshots-to-retain 4
````

Keep two full snapshots. You want a known-good one while the next is being
written — especially here, where restarts are frequent.

## What makes testnet different

### Cluster restarts invalidate the local snapshot

After a coordinated restart the shred version changes and the local snapshot is
usually rejected. The node falls back to a network fetch. That is correct; the
failure to watch for is disk, not the fetch.

Make room **before** the fetch:

````bash
ls -lt /mnt/ledger/snapshots | head
df -h /mnt/ledger /mnt/accounts
````

### Ledger resets make the local state worthless

If — and only if — the official announcement says the cluster was reset from a
new genesis, clear the ledger and accounts directories and let the node
bootstrap fresh.

````bash
sudo systemctl stop solana
rm -rf /mnt/ledger/* /mnt/accounts/*
sudo systemctl start solana
````

Keep every keypair. Never run this on a hunch — "my node is behind" is not a
reset, and this command is not recoverable.

### Restart announcements may specify exact arguments

A coordinated restart can require `--wait-for-supermajority`, a specific
`--expected-shred-version`, and hard-fork arguments. Take those values from the
announcement and apply exactly what it says. Do not infer them.

## Restart discipline

1. confirm a recent snapshot pair exists under `--snapshots`;
2. confirm free space on ledger and accounts;
3. hand the identity to the unstaked spare if you have a second host;
4. `stop`, wait for the process to exit, then `start`;
5. watch bank load and replay in the log;
6. confirm externally: gossip peers recovered, not delinquent, vote and root
   advancing.

````bash
solana catchup --our-localhost
solana gossip -ut | wc -l
solana validators -ut | grep <identity-pubkey>
````

## What never gets deleted for space

The ledger, the accounts directory, the tower file, any keypair. If those are
the only things left, the answer is more disk. Safe deletions, in order:
superseded snapshot **pairs**, rotated logs, journald, build trees.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
