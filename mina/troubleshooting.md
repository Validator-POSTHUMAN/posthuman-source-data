# Mina Troubleshooting

Ordered by what actually happens to operators, not by subsystem. Every entry
names the check that distinguishes the cause, because most Mina symptoms have
two or three plausible causes and guessing wastes an epoch.

## The node crashes every few minutes

Almost always configuration, not a bug. In order of likelihood:

1. **Key permissions.** `~/keys` must be `700`, the private key `600`. The
   daemon refuses to start otherwise.
2. **Wrong or mangled password.** `MINA_PRIVKEY_PASS` with an unquoted `$` or
   other shell metacharacter is silently altered. Quote it, or escape with `\`.
3. **Peer list not reachable.** Confirm the URL in `PEERS_LIST_URL` or
   `--peer-list-url` resolves and returns content.

The last few lines before the exit say which one it was:

````bash
journalctl --user -u mina -n 100 --no-pager
docker logs --tail 100 mina
````

## The node disappeared after about a week

Not a crash. The daemon **stops itself** after `--stop-time` hours — default
**168** — plus a random 0–9 hours, when no slot was won in the following hour.

- With `Restart=always` (systemd) or `--restart=always` (Docker), this is a
  rolling weekly restart and is expected.
- Without a restart policy, the node is simply gone. Add one.

## I closed my SSH session and the node stopped

A foreground `mina daemon` receives SIGINT on detach. Use the systemd user unit,
Docker with a restart policy, `--background`, or tmux. With the systemd user
unit you also need:

````bash
sudo loginctl enable-linger "$USER"
````

Without lingering, the user manager stops when you log out and takes the node
with it.

## Sync status problems

| Symptom | Meaning | Action |
|---|---|---|
| `Bootstrap` / `Catchup` after start | normal for 5–30 min | wait |
| Block height flat, then jumps | normal catchup behaviour | wait; do not restart |
| Height stuck at 1 for < 1 h | daemon still initialising | wait |
| `Sync status: Offline` | no peer messages for ~24 min | check `8302` inbound, peer list URL |
| Synced, but height ≠ external node | you may be on another chain | compare `Chain id` immediately |

Restarting during catchup restarts catchup. It is the most common self-inflicted
delay on Mina.

Check the height and chain against something that is not your node:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { blockchainLength chainId } }"}' | jq
````

## `Block producers running: 0`

The daemon is synced but is not a producer. Check, in order:

1. Is the key flag actually in effect? `systemctl --user show mina -p ExecStart`
   or `docker inspect mina --format '{{json .Config.Cmd}}'`.
2. Did the password decrypt the key? A wrong password is logged at startup.
3. Permissions again — `600` on the key file.

Note that `mina accounts list` can be empty even on a working producer: passing
`--block-producer-key` does not import the account for *sending transactions*.
Import it separately if you need to send:

````bash
mina accounts import --privkey-path ~/keys/my-wallet
````

## "Nothing changed after I received a delegation"

Correct behaviour. Stake for the current epoch was fixed by a ledger snapshot
taken two epochs ago. New delegations, block rewards and SNARK fees do not
affect your chances this epoch.

Note that official documentation still describes this delay as "~2 weeks" in
places. That figure predates the Mesa upgrade: an epoch is now about **7.44
days** (7140 slots × 90 s). Read the live parameters rather than any prose:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { consensusTimeNow { epoch slot } consensusConfiguration { slotDuration slotsPerEpoch epochDuration } } }"}' | jq
````

## "No blocks won this epoch"

The VRF is deterministic: for a given stake and epoch, the answer does not
change no matter how often you restart. With a small stake, entire epochs
without a won slot are normal. Nothing about your node configuration improves
this — only stake does.

## I won a slot but produced no block

Check the logs for:

````
Internally generated block $state_hash cannot be rebroadcast because it's not a valid time to do so
````

That means the block was not built and gossiped inside the **90-second** slot.
Causes, in order:

1. **Resource contention** — most often a SNARK worker on the same host. Move it,
   or stop it during production windows.
2. **Underpowered CPU.** The official floor of 8 cores / 16 GB is not enough for
   reliable production; experienced operators run 16 cores / 32 GB.
3. **The node was bootstrapping** at the slot time — a restart at the wrong
   moment.

## My block was orphaned

More than one producer can win the same slot; ties are resolved by the VRF
output and one block is dropped. Occasional orphans are normal. **Consistent**
orphans mean you are producing slowly and the network builds on someone else's
block first — treat it as the previous item.

A block produced while in catchup is also orphaned, because it builds at the
wrong height.

## The block had no coinbase, or no transactions

Not a fault. A block producer must buy SNARK work to include transactions. When
no work is available, or it is more expensive than the fees on offer, the block
is produced empty and there may be no coinbase. Rising
`Coda_Transition_frontier_empty_blocks_at_best_tip` is the metric for this.

If you set `--minimum-block-reward`, you asked for this explicitly: blocks below
the threshold are produced empty on purpose.

## My SNARK work is never bought

Workers compete; only the lowest fee for each job reaches the pool. If yours is
never bought:

- lower the fee, or
- change work selection. The default is `rand`; `seq` works jobs in the order
  the scan state needs them and is much more likely to be included promptly,
  `roffset` is the same with a random starting point.

Check what is actually clearing:

````bash
mina advanced snark-pool-list | jq
mina advanced snark-job-list  | jq
````

Disable snarking entirely with `mina client set-snark-worker` (no `--address`).
Community tooling exists to stop the worker around won slots — see the SNARK
stopper approach referenced in Mina's own troubleshooting.

## Transaction stuck as pending

Transactions are included by fee priority, and they are processed in **nonce
order** — one stuck low-fee transaction blocks every later transaction from that
account regardless of their fees.

````bash
mina advanced pooled-user-commands | jq . | grep fee | sort | uniq -c | sort -n
````

Raise the fee, or cancel and resubmit:

````bash
mina client cancel-transaction --id <TRANSACTION_ID>
````

Cancellation submits a higher-fee replacement — it is a race, not a guarantee.
A block holds at most 128 transactions, including the coinbase and the fee
transfers that pay SNARK workers.

## "Specified sender is not in the ledger"

The account has no ledger entry yet, or the node is not synced. An address that
has never received funds does not exist for consensus. Fund it once, then wait
for sync.

## Account shows as "locked"

Expected. Block production does **not** need an unlocked account; sending
transactions does.

````bash
mina accounts unlock --public-key B62q…
mina accounts lock   --public-key B62q…
````

Lock it again afterwards.

## "Abuse message: Netscan detected" from the provider

Known libp2p behaviour, reported most often on Hetzner. Block outbound traffic
to private ranges — the exact `ufw` rules are in **Security hardening**. Review
them against your own private-network dependencies first, or you will cut off
your own coordinator, archive or monitoring.

## "Couldn't determine our IP from the internet"

The daemon's IP auto-detection failed — usually a firewall blocking outbound
HTTP/HTTPS.

````bash
curl ifconfig.me
````

Then start with `--external-ip <your-ip>`. Behind NAT you may also need to
forward `--external-port` (8302) manually.

## `~/.mina-config/daemon.json` missing

A harmless warning. The file is optional; the daemon starts normally. Ignore it
unless you intended to supply one.

## "Prover/verifier killed" messages

Normal. These processes are periodically killed and restarted. Only a resulting
fatal error is an incident.

## `Fatal error: out of memory`

A known failure mode under load. Give the host more RAM, reduce
`--snark-worker-parallelism`, or move SNARK work off the producer. Watch free
memory as a monitored signal, not as a post-mortem check.

## Raspberry Pi / ARM

Not supported, and not fixable. x86-64 only.

## Collecting evidence before you restart

````bash
mina client status --json > status.json
mina client export-logs -tarfile incident-$(date +%Y%m%dT%H%M%SZ)
ls -la ~/.mina-config/         # crash report, if any
````

Only the most recent crash report is kept. Collect it before the next crash
overwrites it.

## Related guides

- **Monitoring** — turning these symptoms into alerts
- **Security hardening** — firewall rules referenced above
- **Block producer** — slot, stake and production semantics
- **Upgrades** — chain ID verification after any version change

## Sources

- [docs.minaprotocol.com — troubleshooting](https://docs.minaprotocol.com/node-operators/troubleshooting)
- [docs.minaprotocol.com — FAQ](https://docs.minaprotocol.com/node-operators/faq)
- [docs.minaprotocol.com — logging](https://docs.minaprotocol.com/node-operators/validator-node/logging)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
