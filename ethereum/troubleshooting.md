# Ethereum Node Troubleshooting

Ordered by how often each cause turns out to be the answer, not by how
interesting it is.

Before anything else, collect the four facts. Most reports are resolved by them
alone.

````bash
systemctl is-active execution consensus validator
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' http://127.0.0.1:8545
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
timedatectl status | grep -E 'synchronized|NTP'
````

---

## Missed attestations

The symptom that costs money. Work down in order.

**1. Clock.** Drift over a second breaks slot timing and presents as a network
fault. `timedatectl status` must say synchronized. Install `chrony` if it is not
there.

**2. `is_optimistic: true`.** The beacon node is following heads the execution
client has not verified. The validator's attestations are worthless while this
is true. The cause is always on the EL side: not synced, crashed, or the Engine
API connection is broken.

**3. Engine API.** In the CL log, look for `Unauthorized`, `invalid JWT`,
`execution engine offline`, `error connecting to execution client`.

````bash
sudo wc -c /var/lib/ethereum/jwt.hex     # must be exactly 64
sudo ss -tlnp | grep 8551
````

A trailing newline in `jwt.hex` is the single most common cause. So is two
processes reading two different JWT files.

**4. Peers.** Below ~20 CL peers, attestations propagate too slowly to be
included.

````bash
curl -s http://127.0.0.1:5052/eth/v1/node/peer_count | jq
````

Test reachability **from another host**, because the node can always reach
itself:

````bash
nc -vz <public-ip> 30303
nc -vzu <public-ip> 9000
````

If ufw allows the port and it is still unreachable, the block is upstream — the
router, the provider's firewall or a cloud security group.

**5. Disk.** `iostat -x 5`. Sustained `%util` near 100 or await in the tens of
milliseconds means the disk cannot keep up: block import is late, so the
attestation is late, so it is not included. No flag fixes a QLC drive.

**6. Key count.** Compare the number of keys the VC logged at startup against
what you expect. A keystore that failed to decrypt is skipped silently.

**7. Beacon node behind.** Compare head slot against
[beaconcha.in](https://beaconcha.in/).

**Inclusion distance splits the diagnosis.** Attestations landing but late point
at timing, networking or disk. Attestations not landing at all point at the VC
or the beacon node.

---

## Node will not start

| Log line | Cause | Fix |
|---|---|---|
| `Unauthorized` / `invalid JWT` | JWT mismatch or newline | Regenerate, `chmod 640`, both processes on one path |
| `address already in use` | Old process still running, or port conflict | `ss -tlnp | grep <port>` |
| `permission denied` on the data directory | Wrong owner after a manual copy | `chown -R <user>:<user>` the data directory |
| `database contains incompatible genesis` | Data directory belongs to another network | New data directory; do not mix mainnet and testnet |
| Besu/Teku/Lodestar exit immediately, no message | `MemoryDenyWriteExecute=true` in the unit | Set it to `false` — JIT runtimes need it |
| Killed within minutes, nothing in the client log | OOM | Check the kernel log for `oom`; lower `--cache`/`-Xmx` |

---

## Sync problems

**Execution client stuck at a block, CPU idle.** Disk. See above.

**Execution client stuck, CPU busy.** Snap sync healing can sit on the same
block for a long while. Give it hours before intervening; check that the block
number is not actually advancing first.

**Beacon node syncing forever.** You did not use checkpoint sync. Stop, wipe the
beacon data directory, restart with `--checkpoint-sync-url`. Minutes instead of
days. This never touches validator keys.

**`sync_distance` grows steadily.** The node is falling behind, not catching up —
disk or CPU saturation, or a peering problem that stops it receiving blocks.

**Resyncs from scratch after every reboot.** The client was killed before it
flushed. `TimeoutStopSec=300` in the unit, and always stop with
`systemctl stop`.

---

## Database corruption

Symptoms: the client refuses to start with a database or checkpoint error after
an unclean shutdown, or a power loss.

- **Consensus layer:** do not repair it. Wipe the beacon data and checkpoint
  sync. It costs minutes.
- **Execution layer:** a resync costs hours to days. Some clients can recover
  from an earlier checkpoint; read that client's documentation before deleting
  anything.
- **Never** delete anything under the validator data directory while
  troubleshooting the chain database. Keys and the slashing protection database
  are not chain data.

---

## MEV-Boost

| Symptom | Cause |
|---|---|
| Only proposals missed, attestations fine | Relay latency or a dead relay |
| `no bid received` | Normal — the client should build locally; verify it does |
| Proposal missed at the slot | Relay returned a bid and failed to deliver the payload |

Run with `-relay-check`, keep more than one relay, and confirm the beacon node
falls back to a locally built block. A relay problem must never become a missed
slot.

---

## Validator shows as offline on beaconcha.in but the node looks fine

In order: the VC is running but pointed at the wrong beacon node; the keys were
imported into a different data directory than the one the VC reads; the
validator is not activated yet; the public key you are looking at is not the one
loaded.

````bash
curl -s "https://beaconcha.in/api/v1/validator/0xPUBKEY" | jq '.data.status'
````

`pending_queued` means it is waiting for activation and nothing is wrong.

---

## When to stop and ask

Stop, leave the validator **off**, and escalate if:

- you cannot prove the validator keys are running in exactly one place;
- you are about to restore a keystore backup and are unsure of the slashing
  protection database's age;
- a migration was interrupted mid-cutover;
- you are considering starting a validator on a second host "to check".

An offline validator loses a few cents an hour. A double-signing validator loses
ETH and is ejected. The asymmetry is the whole decision.
