# Base Node Troubleshooting

Work down this page in order. Most Base node problems are one of four things:
the L1 endpoint, the disk, egress to the bootnodes, or a flag that changed in
the last release.

---

## Start here

```bash
docker compose ps                       # is anything restarting or exited?
docker compose logs --since 15m node    # rollup node first — it fails louder
docker compose logs --since 15m execution
df -h | grep -v 'tmpfs\|udev\|loop'     # every mount, not just /
basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
```

`basectl doctor` answers most of the rest of this page in one command. Pass
`--cl-rpc` explicitly or the CL checks are **skipped**, not failed, and the exit
code will be `0` while half the diagnosis never ran.

---

## The container exits immediately

### Exit code 8, log says `Could not retrieve public IP`

`consensus-entrypoint` resolves the public IP at every start by querying
`ifconfig.me`, `api.ipify.org`, `ipecho.net` and `v4.ident.me` over plain HTTP,
and exits `8` if all four fail. The node never starts and there is no
rollup-node log at all.

- Allow outbound HTTP to at least one of those hosts, **or**
- run the binaries under systemd and set `BASE_NODE_P2P_ADVERTISE_IP` yourself —
  see **Binaries & systemd**. The Compose path overwrites that variable
  unconditionally, so you cannot fix it in the env file.

### Log names an unknown or unexpected argument

A flag was removed in the release you just pinned. `v1.4.0` deprecated
`--rollup.disable-tx-pool-gossip` on `base-reth-node`; if it is still in your
entrypoint, `ADDITIONAL_ARGS` or a systemd unit, remove it.

Read the release notes for the tag you moved to. This is the most common
post-upgrade failure and the log line names the flag.

### `expected RETH_CHAIN to be set` / `expected BASE_NODE_NETWORK to be set`

The env file was not loaded. Check `NETWORK_ENV`, check you are in the directory
containing `docker-compose.yml`, and check the file exists and is readable.

### Permission errors on `./reth-data`

The directory was created by `sudo docker compose` and is owned by root.

```bash
docker compose down
sudo chown -R "$USER":"$USER" ./reth-data
docker compose up -d
```

Then stop using `sudo` for compose. Add your user to the `docker` group
instead.

---

## It runs but does not sync

### Height is not increasing at all

Check, in this order:

1. **L1 endpoints.** From the node host, not from your laptop:

   ```bash
   curl -s -X POST -H 'Content-Type: application/json' \
     --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
     "$BASE_NODE_L1_ETH_RPC"
   curl -s "$BASE_NODE_L1_BEACON/eth/v1/node/syncing" | jq
   ```

   A 401, 403 or 429 is a credential or quota problem, not a node problem.

2. **Is your L1 node synced?** Base cannot finish syncing behind an L1 node that
   has not.

3. **Engine API.** Look in the EL log for authentication failures against
   `8551`. If both services do not read the same
   `BASE_NODE_L2_ENGINE_AUTH_RAW`, the rollup node cannot drive the execution
   client.

4. **Clock.** `chronyc tracking` or `timedatectl`. Drift above a second breaks
   P2P in ways that look like everything else.

### The unsafe head advances but the safe head is frozen

This is the important failure and it looks completely healthy from outside.

```bash
curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H 'Content-Type: application/json' http://127.0.0.1:7545 \
  | jq '{unsafe: .result.unsafe_l2.number, safe: .result.safe_l2.number, l1: .result.head_l1.number}'
```

The unsafe head comes from the sequencer feed and keeps moving regardless. The
safe head only advances when the node reads batches back from Ethereum. Frozen
safe head means **L1 derivation has stopped**:

| Cause | Check |
|---|---|
| L1 execution RPC failing or rate-limited | provider dashboard; rollup node log for `429`, timeouts |
| Beacon endpoint pruned past the blob retention window | rollup node log for blob-sidecar fetch failures |
| Beacon endpoint does not serve blob sidecars at all | `curl "$BASE_NODE_L1_BEACON/eth/v1/beacon/blob_sidecars/head"` |
| L1 node itself behind | `head_l1` in `syncStatus` against a public L1 |

Nothing in `docker compose ps`, in the process list, or in a height-based
monitor will show this. Alert on `unsafe − safe`.

### Syncing, but far too slowly

Almost always disk.

```bash
iostat -x 2 5      # %util near 100 and high await = the bottleneck
```

- Locally attached NVMe, ext4, `noatime`. Networked storage does not keep up;
  EBS needs `io2` Block Express at minimum.
- Restore from a snapshot instead of syncing from genesis. Days become hours.
- A slow or rate-limited L1 endpoint throttles L2 sync just as effectively as a
  slow disk. Check both before replacing hardware.

### `Error: nonce has already been used` when sending a transaction

The node is not at the head yet. It is a symptom, not a bug. Wait for
`optimism_syncStatus` to show a recent unsafe head.

---

## Zero peers

Ingress rules are usually fine and the problem is **egress**.

| Direction | Port | Protocol | Purpose |
|---|---|---|---|
| Ingress | `30303` | TCP + UDP | EL P2P |
| Ingress | `9222` | TCP + UDP | CL P2P |
| Egress | `30301` | TCP + UDP | **Base bootnodes** |
| Egress | `9200` | UDP | **Base bootnodes** |

If outbound `30301` or `9200` is blocked, the node reaches no bootnode and
finds zero peers however open your ingress is.

With stateless network ACLs rather than a stateful firewall, also allow outbound
ephemeral ports `32768–60999` (TCP + UDP) — peer replies are dropped silently
without them.

Behind NAT, the advertised address matters. In Compose it is resolved
automatically and may be wrong; under systemd set
`BASE_NODE_P2P_ADVERTISE_IP`, or pass `--nat=extip:<your-ip>` through
`ADDITIONAL_ARGS`.

```bash
basectl -c mainnet p2p info
basectl -c mainnet p2p reachability enode://...   # independent external probe
```

---

## Snapshot restore problems

| Symptom | Cause | Fix |
|---|---|---|
| `Archive extracted, but output verification failed` | a newer snapshot was published mid-download | interrupt and re-run; the download is idempotent |
| Node starts a fresh sync after restore | data nested in `./reth-data/reth/` | move the contents up one level |
| Database errors or missing files at start | the node was running while the data changed | `docker compose down`, clear the contents, restore again |
| Out of disk mid-extract | the `2 ×` term in the sizing formula was skipped | provision more, or use `--minimal` |
| Restored `--full` but history queries fail | `--full` keeps only 10,064 blocks — hours on Base | restore the archive snapshot and set your own prune distances |

The last one is not a failure, it is the node type working as designed. See
**Pruning & Storage**.

---

## RPC problems

### Connection refused on `127.0.0.1:8545`

```bash
docker compose ps
sudo ss -tulpn | grep 8545
docker compose logs execution | grep -i rpc
```

Check the container is running, the port mapping exists, and the RPC server
actually started.

### Port conflicts at startup

```bash
sudo ss -tulpn | grep LISTEN
```

Defaults in use: `8545`, `8546`, `8551`, `7545`, `7300`, `7301`, `6060`,
`30303`, `9222`. Stop the conflicting service or remap in
`docker-compose.override.yml`.

### `method not found` for `debug_*` or `trace_*`

The namespace is not enabled. The stock entrypoint enables
`web3,debug,eth,net,txpool,miner` on HTTP; the hardened systemd unit in
**Binaries & systemd** deliberately does not. Enable it temporarily on a
loopback listener, never on a published one.

### `eth_getLogs` returns nothing for older blocks

Not an error. Your node is pruned past that range. See **Pruning & Storage**.

### Flashblocks `pending` returns the same as `latest`

The WebSocket stream is not connected. The node falls back silently rather than
erroring.

```bash
docker compose logs execution | grep -i flashblock
```

`Running in vanilla node mode` in the startup log means `RETH_FB_WEBSOCKET_URL`
was not set in the environment the container actually received.

---

## After a fork

If the safe head stopped near a known activation time, you missed the fork.

1. Upgrade to the required release immediately — do not investigate first.
2. Watch the safe head for 30 minutes. It usually recovers on its own by
   re-deriving from L1.
3. If it does not, the local database followed the wrong chain past the fork.
   Restore from a current snapshot.
4. Tell downstream consumers. They cached wrong answers with full confidence.

There is no penalty and no slashing. The cost is entirely in what you served
while it was wrong. See **Upgrades**.

---

## Collecting evidence before you ask for help

```bash
docker compose ps
docker compose logs --no-color --since 2h > /tmp/base-logs.txt
docker compose config | grep -v -i 'RPC\|BEACON\|AUTH'   # redact credentials
basectl -c mainnet doctor --json > /tmp/base-doctor.json
sudo ss -tulpn | grep -E '8545|7545|30303|9222'
df -h; iostat -x 1 3; chronyc tracking
```

**Redact before sharing.** `BASE_NODE_L1_ETH_RPC` and `BASE_NODE_L1_BEACON`
usually contain a provider API key in the URL path, and
`BASE_NODE_L2_ENGINE_AUTH_RAW` is a secret — even though the committed default
is public, yours should not be.

Then: the `🛠｜node-operators` channel in the
[Base Discord](https://discord.gg/buildonbase), or
[base/base issues](https://github.com/base/base/issues).
