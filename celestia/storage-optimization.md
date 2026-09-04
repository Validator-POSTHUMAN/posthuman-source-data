# Optional ZFS Storage for Celestia DA — Mainnet

ZFS compression can reduce bridge-store space, but compression consumes CPU
and can reduce node performance. It is optional, does not reduce the official
capacity requirement, and must be benchmarked against the operator's workload.
This guide intentionally omits unsafe production tuning.

## Scope

- Intended for a new Celestia DA store on dedicated bare-metal storage.
- Mainnet bridge store example: `/srv/celestia-da/.celestia-bridge`
- Mainnet light store example: `/srv/celestia-da/.celestia-light`
- Does not convert an in-use filesystem or move a live keyring.
- Does not change consensus storage.

## Destructive approval gate

Creating a ZFS pool overwrites storage metadata on the selected disk. Do not run
the pool-creation step until all conditions below are evidenced and the exact
disk device has explicit operator approval:

1. The device is a whole physical disk dedicated to this new pool.
2. It has no partitions, filesystem signatures, mounts, swap, LVM, mdraid,
   existing ZFS membership, or required data.
3. The device identity was verified by model, serial, size, and stable by-id
   path, not only by a short kernel name.
4. The expected pool topology and failure tolerance are documented.
5. Backups and rollback are defined for any data that will later be placed on
   the pool.

If any check is unknown, stop. An “empty-looking” disk is not sufficient.

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

Match every result to the approved device record. Do not continue on a mounted,
partitioned, member, or signature-bearing device.

## Approval-gated pool creation

Replace placeholders only after the destructive gate is approved. Use the
stable by-id path from the approved record.

```bash
sudo zpool create -o ashift=12 \
  <approved-pool-name> /dev/disk/by-id/<approved-empty-disk-id>
sudo zfs create -o mountpoint=/srv/celestia-da \
  <approved-pool-name>/da
sudo zfs set compression=zstd-3 <approved-pool-name>/da
```

This deliberately avoids `sync=disabled`, prefetch changes, auto-trim changes,
and speculative record-size tuning. Do not weaken durability for initial sync
or production operation.

## Configure a new DA store

Initialize the chosen role directly at its final path rather than moving a live
store:

```bash
celestia bridge init \
  --node.store /srv/celestia-da/.celestia-bridge \
  --core.ip <archival-consensus-grpc-host> \
  --core.port <grpc-port> --core.tls --p2p.network celestia
```

For a light node, use the current light-node guide and
`--node.store /srv/celestia-da/.celestia-light`. Any key-bearing migration
requires the separate key procedure and approval.

Update the service only after initialization, ownership, mounts, and rollback
are reviewed. Ensure the service starts after the ZFS mount is available.

## Verify

```bash
sudo zpool status <approved-pool-name>
sudo zpool get ashift,autotrim <approved-pool-name>
sudo zfs get mountpoint,compression,compressratio,used,available \
  <approved-pool-name>/da
findmnt /srv/celestia-da
df -h /srv/celestia-da
```

Then verify the DA service, header freshness, peer connectivity, disk latency,
CPU saturation, and write growth under real load. Compare these measurements
with an uncompressed baseline when possible. A positive compression ratio does
not prove the node can sustain required throughput.

Alert on pool degradation, device errors, latency growth, low free capacity,
unexpected unmount, or service start before the dataset is mounted.

## Rollback

Stop before activation if the pool, mount, capacity, ownership, or performance
checks fail. Keep the original service configuration and data location intact
until the new store is independently healthy. Pool destruction, disk reuse,
and key-bearing data movement are intentionally outside this guide.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/data-availability/storage-optimization`
- `operate/getting-started/hardware-requirements`
- `operate/data-availability/bridge-node`
