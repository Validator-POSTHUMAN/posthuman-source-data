# Solana Validator Troubleshooting

Work from evidence, in this order: what does an **external** RPC say, what does
the local RPC say, what does the log say, what does the host say. Do not restart
first. On Solana a restart is a snapshot load, and an unnecessary one turns a
five-minute problem into an hour.

## Triage in four commands

````bash
# 1. what the cluster thinks
solana validators --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>

# 2. what we think
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'

# 3. how far behind
solana catchup --our-localhost

# 4. why
journalctl -u solana --since "30 min ago" | grep -Ei 'panic|error|no space|shred version'
````

---

## Delinquent

`delinquent=true` means the cluster has not counted a recent vote.

| Check | Command | If wrong |
|---|---|---|
| Is the process alive? | `systemctl status solana` | start it, then read the log for why it stopped |
| Is it caught up? | `solana catchup --our-localhost` | see **Falling behind** |
| Is the identity funded? | `solana balance <identity-pubkey>` | top it up; an empty identity cannot pay vote fees |
| Is the vote account funded? | `solana balance <vote-account>` | see **Not admitted** |
| Right shred version? | log line at startup, `solana gossip` peer count | see **Wrong shred version** |
| Tower present? | `ls /mnt/ledger/tower-1_9-*.bin` | never delete it; a missing tower forces a slow, careful restart |

## Not admitted — the silent one

Under Alpenglow the admission ticket is burned from the vote account each epoch.
If the vote account cannot pay, the validator is **not admitted next epoch**. No
crash, no error, no delinquency at first — it simply stops being a validator at
the boundary.

````bash
solana balance <vote-account> --url https://api.mainnet-beta.solana.com
solana vote-account <vote-account> --url https://api.mainnet-beta.solana.com
````

Fund it above rent-exempt minimum plus several tickets, and add the alert if you
do not already have it.

## Falling behind / never catching up

````bash
solana catchup --our-localhost
solana slot --url https://api.mainnet-beta.solana.com
iostat -x 2 5
top -H -p "$(pgrep -f agave-validator)"
````

Usual causes, in order of frequency:

1. **Disk**. Accounts DB on a slow or shared device, or ledger and accounts on
   the same NVMe. Check await and utilisation, not just free space.
2. **CPU contention**. Something else on the box, or PoH sharing a core. Pin PoH
   to a dedicated physical core and keep it free.
3. **Memory pressure**. Without swap a validator under pressure dies; with swap
   it slows and survives. Check `free -h` and `swapon --show`.
4. **Network**. Packet loss on the NIC shows up as missed shreds and rising
   repair traffic. Check `ip -s link` counters and the upstream link.
5. **Genuinely behind after a long outage** — let it catch up; do not restart
   repeatedly, each restart starts the snapshot load again.

## `No space left on device`

The most common real outage. Replay and voting stop at that slot.

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh /mnt/ledger/snapshots/* | sort -h | tail
````

Safe to delete, in this order:

1. superseded snapshot **pairs** — an old full plus every incremental built on
   it, only after a newer pair exists and the node has used it;
2. rotated validator logs;
3. journald (`journalctl --vacuum-size=1G`);
4. build trees and `target/` directories.

**Never** delete to free space: the ledger, the accounts directory, the tower
file, or any keypair. If those are the only things left, the answer is more
disk, not a smaller footprint.

Then fix the cause: move `--snapshots` onto the ledger filesystem, lower
`--maximum-full-snapshots-to-retain`, or add capacity. A root filesystem that
fills during snapshot packaging will do it again.

## Snapshot rejected, node re-downloads on every start

Agave refuses a local snapshot it cannot use and falls back to a network fetch.
Reasons: shred version changed after a cluster restart, corrupt archive, or the
incremental's base full snapshot is gone.

````bash
ls -lt /mnt/ledger/snapshots | head
````

Make room **before** the fetch. Confirm `--known-validator` and
`--only-known-rpc` are set so the fetch comes from a source you chose, and
confirm `--expected-genesis-hash` so a wrong entrypoint cannot put you on
another cluster.

## Wrong shred version

After a cluster-wide restart the shred version changes. A node still carrying
the old value looks completely healthy, peers with nobody and votes on nothing.

````bash
solana gossip | wc -l                       # suspiciously small
journalctl -u solana | grep -i 'shred version'
````

Update `--expected-shred-version` to the current cluster value and restart. If
you pin it, make updating it part of every cluster-restart runbook.

## Skipping leader slots

````bash
solana block-production --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
````

A skip rate above the cluster average is a defect. Look at:

- PoH core contention and overall CPU steal;
- accounts-DB disk latency during your leader window;
- NIC drops and upstream bandwidth — you must be able to fan out shreds;
- client version and scheduler configuration.

SFDP tolerates network average + 5 percentage points. Sustained excess costs
stake, not just rewards.

## Validator will not start

````bash
systemctl status solana
journalctl -u solana -n 200 --no-pager
systemd-analyze verify /etc/systemd/system/solana.service
````

| Symptom | Cause |
|---|---|
| `Unknown argument` / `unexpected argument` | a flag was renamed between releases — read the release notes |
| `Permission denied` on ledger/accounts | ownership or a too-strict `ProtectSystem`/`ReadWritePaths` |
| `Too many open files` | `LimitNOFILE` missing from the unit, or `fs.nr_open` not raised |
| `failed to lock memory` | `LimitMEMLOCK` missing |
| exits immediately, no log | the start script did not use `exec`, or `--log` points somewhere unwritable |
| starts, then restarts in a loop | check `NRestarts`; stop the unit before debugging so it stops fighting you |

## Vote account or identity changes did not take effect

- Vote authority changes take effect at the **next epoch boundary**, and at most
  one change per epoch. Pass `--authorized-voter` twice — old and new — so the
  process keeps voting across the switch.
- BLS public key must be re-published after rotating the vote authority.
- `systemctl start` on an already-active unit is a **no-op**. After replacing a
  key file, always `stop` then `start`, or `restart`. A config change that
  "didn't apply" is usually this.

## Two hosts, one identity

Stop immediately. Determine which host holds the valid tower, shut the other one
down completely, and only then hand the identity over with `--require-tower`.
Never run both "just until the window closes".

## What to capture before restarting

An incident you cannot reconstruct will repeat. Before the restart:

````bash
systemctl show solana -p NRestarts -p ActiveState -p ExecMainStartTimestamp
journalctl -u solana --since "1 hour ago" > /tmp/incident-$(date +%s).log
df -h > /tmp/incident-df.txt; free -h >> /tmp/incident-df.txt
ls -lt /mnt/ledger/snapshots | head >> /tmp/incident-df.txt
````

Keep it. Then restart.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
