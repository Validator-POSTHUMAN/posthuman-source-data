# Bitcoin Node Troubleshooting

Work in this order: **is it the right chain → is it progressing → is it
reachable → is it the host.** Most time is lost by starting at the bottom.

## Node will not start

````bash
systemctl status bitcoind
journalctl -u bitcoind -n 50 --no-pager
````

| Log line | Cause | Fix |
|---|---|---|
| `Cannot obtain a lock on data directory` | another `bitcoind` is running on the same datadir | find it (`ss -tlnp`, `ps aux | grep bitcoind`), stop it. Never run two on one datadir |
| `Corrupted block database detected` | unclean shutdown | `bitcoind -reindex-chainstate`; `-reindex` only if block files are suspect |
| `Error: Cannot write to data directory` | ownership/permissions | datadir owned by the service user, `0700` |
| `Config file … specified in the datadir …` | `-conf` inside `-datadir` recursion | give `-conf` an absolute path outside the loop |
| `Invalid or missing settings.json` | interrupted write | remove `settings.json`; it is regenerated |
| `Error: Unknown option -maxorphantx` | removed option still in config | delete it (no effect since v30.0, error in a future release) |
| Immediate OOM kill in a container | `dbcache` sized from host RAM, not the cgroup | set `dbcache` explicitly well under `mem_limit` |

## Stuck sync

````bash
bitcoin-cli getblockchaininfo | jq '{blocks, headers, verificationprogress, initialblockdownload}'
bitcoin-cli getpeerinfo | jq 'length'
bitcoin-cli getchaintips
````

| Symptom | Meaning |
|---|---|
| `headers` climbing, `blocks` frozen | block download stalled — peers, bandwidth or disk |
| both frozen, peers > 0 | check `getchaintips` for a `headers-only` tip with more work: you may be on a minority branch |
| both frozen, peers = 0 | network, DNS seeds or firewall; see below |
| `verificationprogress` crawling | disk-bound. Raise `dbcache`, move to NVMe |
| progress, then rollback | reorg. Normal for 1–2 blocks; deeper needs investigation |

Force fresh peers:

````bash
bitcoin-cli setnetworkactive false && sleep 5 && bitcoin-cli setnetworkactive true
bitcoin-cli addnode "<known-good-node>:8333" onetry
````

## No peers

````bash
bitcoin-cli getnetworkinfo | jq '{networkactive, connections_in, connections_out, networks: [.networks[] | {name, reachable, proxy}]}'
````

- `networkactive: false` — someone disabled P2P; re-enable it.
- `connections_out: 0` and DNS failing — the host cannot resolve the DNS seeds.
- `onlynet=onion` with Tor down — the node is deliberately isolated and Tor is
  the fault. Check `systemctl status tor` and the control port.
- `connections_in: 0` only — inbound is closed. Fine for a private backend; if
  you meant to serve peers, check `ufw`, the provider firewall and NAT.

Note `-natpmp=1` is the default since v30.0: a node may be reachable through a
router without your having opened anything.

## Wrong chain

The serious one. Same height, different hash:

````bash
bitcoin-cli getbestblockhash
curl -s https://mempool.space/api/blocks/tip/hash
curl -s https://blockstream.info/api/blocks/tip/hash
bitcoin-cli getchaintips | jq '.[] | select(.status != "active")'
bitcoin-cli getdeploymentinfo | jq '.deployments'
````

If your tip disagrees with two independent sources for more than a few minutes:
stop everything that consumes this node, do not credit payments from it, and
investigate before restarting. Causes worth checking: a stale binary that does
not enforce a newer soft fork (`Warning: unknown new rules activated`), a
manually set `assumevalid`, or a datadir seeded from an untrusted copy.

## RPC problems

| Symptom | Cause | Fix |
|---|---|---|
| `Could not connect to the server` | not running, or `-datadir` mismatch so the cookie is not found | pass the same `-datadir`, check the service |
| `Authorization failed` | wrong `rpcauth`/cookie, or the cookie was regenerated at restart | re-read the cookie; do not cache it |
| `Work queue depth exceeded` | RPC saturated by an indexer | raise `rpcworkqueue=64`, `rpcthreads=16`, throttle the caller |
| `Method not found` | method not in that user's `rpcwhitelist`, or removed in this version | check the whitelist, then the release notes |
| `Loading block index…` for a long time | normal on start; minutes on a large node | wait; watch the log |
| `-rpcclienttimeout` expiry on `dumptxoutset`/`gettxoutsetinfo` | long-running RPC | `-rpcclienttimeout=0` |

## Mempool and fee surprises after v31.0

Cluster mempool replaced ancestor/descendant limits. Symptoms of tooling that
has not caught up:

- transactions rejected with cluster-limit errors instead of the old
  ancestor/descendant messages — a cluster is capped at 64 transactions and
  101 kvB;
- RBF replacements that used to be accepted now rejected — the replacement must
  strictly improve the mempool feerate diagram;
- packages relying on the **CPFP carve-out** failing — it was removed; use TRUC
  transactions and sibling eviction.

Inspect with `getmempoolcluster <txid>` and `getmempoolfeeratediagram`.

Also: `-paytxfee` and `settxfee` were removed in v31.0. Scripts that call them
now fail — pass `fee_rate` per transaction.

## Disk

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh /var/lib/bitcoind/{blocks,chainstate,indexes}
bitcoin-cli getblockchaininfo | jq '{size_on_disk, pruned, prune_target_size}'
````

Check **every** mount, not just `/`. A datadir on a separate volume fills
independently of the root filesystem, and a full datadir volume is how nodes
corrupt themselves.

Out of space on an archive node: prune (requires `-reindex` if `txindex=1` is
set), move the datadir to a larger volume, or grow the volume. Out of space on
a pruned node means pruning is not keeping up — lower `prune=`.

## ZMQ silently dead

`bitcoind` reports nothing when a ZMQ subscriber stops receiving, and the
dependent service — Lightning, electrs, mempool — simply stops learning about
blocks while looking healthy.

````bash
ss -tlnp | grep 2833
python3 - <<'EOF'
import zmq
c = zmq.Context(); s = c.socket(zmq.SUB)
s.connect("tcp://127.0.0.1:28332"); s.setsockopt(zmq.SUBSCRIBE, b"")
s.setsockopt(zmq.RCVTIMEO, 900000)   # a block can take a while
print(s.recv_multipart()[0])
EOF
````

Monitor the age of the last ZMQ message as a first-class metric — see
**Monitoring**.

## Lightning

| Symptom | Check |
|---|---|
| `synced_to_chain: false` persists | backing node health, ZMQ, `bitcoind.rpc*` credentials |
| `synced_to_graph: false` persists | peer connectivity; the node routes nothing until this is true |
| channels inactive | peer offline, or your node unreachable on 9735 |
| force-close fails on a pruned node | a required block is below the prune horizon — the reason to run archival |
| wallet locked after restart | `lncli unlock`, or configure an unlock password file |

Before restarting or restoring anything Lightning: **confirm no second instance
exists against the same channel state.** Restoring a stale channel database
loses the channel balance to a justice transaction.

## Performance

| Symptom | Likely cause |
|---|---|
| Slow IBD | `dbcache` too small, or a SATA/spinning disk |
| High CPU after sync | script verification on new blocks — normal; `par=` to cap |
| High RAM | `dbcache` plus `maxmempool` plus peers. Budget all three |
| Slow RPC | disk saturated, or work queue exhausted |
| Disk I/O constant on v31.0 | the chainstate rewrite bug — **upgrade to v31.1** |

## Escalation

Stop and get a second operator before:

- deleting any datadir content,
- restoring a Lightning channel database or starting a second Lightning
  instance,
- restoring a wallet backup onto a host whose cleanliness you are unsure of,
- acting on a chain divergence you cannot explain.

Everything else here is recoverable. Those four are not.

## Sources

- [bitcoincore.org — v31.1 release notes](https://bitcoincore.org/en/releases/31.1/)
- [bitcoincore.org — v31.0 release notes, cluster mempool](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes](https://bitcoincore.org/en/releases/30.0/)
- [bitcoin/bitcoin — `doc/reduce-memory.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/reduce-memory.md)
- [developer.bitcoin.org — RPC reference](https://developer.bitcoin.org/reference/rpc/)
