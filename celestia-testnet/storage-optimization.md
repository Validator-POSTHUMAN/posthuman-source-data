# Optional ZFS Storage for Celestia DA — Mocha-5

ZFS compression can reduce bridge-store space, but it consumes CPU and can
reduce node performance. It is optional, does not lower the official capacity
requirement, and must be benchmarked. This guide intentionally omits unsafe
production tuning.

## Scope and network boundary

- Consensus chain ID: `mocha-5`; DA P2P network: `mocha`.
- New bridge store: `/srv/celestia-da/.celestia-bridge-mocha-5`.
- New light store: `/srv/celestia-da/.celestia-light-mocha-5`.
- Never reuse a Mocha-4 DA store, consensus data, or signer state.
- No conversion of an in-use filesystem and no live keyring movement.

## Destructive approval gate

Creating a ZFS pool overwrites metadata on the selected disk. The exact device
must receive explicit operator approval after all conditions are proved:

1. It is a whole disk dedicated to the new Mocha-5 pool.
2. It has no partitions, filesystem signatures, mounts, swap, LVM, mdraid,
   existing ZFS membership, or required data.
3. Model, serial, size, and stable by-id path match the approved inventory.
4. Pool topology, failure tolerance, and capacity are documented.
5. Any later data placement has a backup and rollback plan.

Stop on unknown or conflicting evidence. Never rely only on a short kernel
device name.

## Read-only preflight

```bash
lsblk -e 7 -o NAME,PATH,SIZE,MODEL,SERIAL,TYPE,FSTYPE,MOUNTPOINTS
findmnt --real
cat /proc/swaps
sudo pvs
sudo vgs
sudo lvs
cat /proc/mdstat
sudo zpool status
sudo wipefs --no-act /dev/disk/by-id/<approved-disk-id>
```

Any mount, partition, membership, or signature blocks pool creation until it is
reconciled by the operator.

## Approval-gated pool creation

Replace placeholders only after approval. Use the approved stable by-id path.

```bash
sudo zpool create -o ashift=12 \
  <approved-pool-name> /dev/disk/by-id/<approved-empty-disk-id>
sudo zfs create -o mountpoint=/srv/celestia-da \
  <approved-pool-name>/da
sudo zfs set compression=zstd-3 <approved-pool-name>/da
```

This guide does not disable synchronous writes, change prefetch, change
trim policy, or apply speculative record-size tuning. Do not weaken durability
for sync or production operation.

## Initialize a new Mocha-5 store

Verify the archival consensus source reports `mocha-5`, then initialize the
bridge directly at its final store:

```bash
celestia-appd status --node <consensus-rpc-url> | \
  jq -e '.NodeInfo.network == "mocha-5"'
celestia bridge init \
  --node.store /srv/celestia-da/.celestia-bridge-mocha-5 \
  --core.ip <archival-mocha-5-consensus-grpc-host> \
  --core.port <grpc-port> --core.tls --p2p.network mocha
```

For a light node, follow the Mocha-5 light guide and use
`--node.store /srv/celestia-da/.celestia-light-mocha-5`. Key-bearing migration
requires a separate approved procedure. Do not copy any Mocha-4 directory.

Update a service only after initialization, ownership, mount ordering, and
rollback are reviewed.

## Verify

```bash
sudo zpool status <approved-pool-name>
sudo zpool get ashift,autotrim <approved-pool-name>
sudo zfs get mountpoint,compression,compressratio,used,available \
  <approved-pool-name>/da
findmnt /srv/celestia-da
df -h /srv/celestia-da
```

Also verify chain ID `mocha-5`, DA network `mocha`, header freshness, peers,
disk latency, CPU saturation, and write growth under load. Compression savings
do not prove adequate performance.

Alert on pool degradation, device errors, latency growth, low free capacity,
unexpected unmount, wrong network, or service start before mount availability.

## Rollback

Keep the previous service configuration and data location intact until the new
Mocha-5 store is independently healthy. Pool destruction, disk reuse, legacy
data cleanup, and key movement are outside this guide.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/data-availability/storage-optimization`
- `operate/getting-started/hardware-requirements`
- `operate/networks/mocha-testnet`
- `operate/data-availability/bridge-node`
