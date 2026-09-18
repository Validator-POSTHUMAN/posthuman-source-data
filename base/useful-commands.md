# Base Operator Command Sheet

Every command here is read-only unless the section says otherwise. RPC
endpoints assume the loopback bindings from **Security Hardening**:
EL on `8545`/`8546`, rollup node on `7545`, EL metrics on `7301`, CL metrics on
`7300`.

---

## Service control

```bash
cd /path/to/base

docker compose ps                       # container state
docker compose ps --format 'table {{.Service}}\t{{.State}}\t{{.Ports}}'
docker compose logs -f execution        # base-reth-node
docker compose logs -f node             # base-consensus
docker compose logs --since 30m node
docker compose config | grep -m1 image: # which tag is actually running

docker compose up -d                    # start / apply changes
docker compose restart node             # restart one service
docker compose down                     # stop, keep data
docker stats --no-stream                # CPU / RAM per container
```

systemd equivalents, if you run the binaries directly:

```bash
systemctl status base-reth base-consensus --no-pager
journalctl -u base-reth -f
journalctl -u base-consensus --since '30 min ago'
sudo systemctl restart base-reth base-consensus
```

---

## Health, in the order you should check it

### Is it the right chain?

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' \
  http://127.0.0.1:8545
```

`0x2105` = Base Mainnet (8453). `0x14a34` = Base Sepolia (84532).

### Is the execution layer done syncing?

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_syncing","params":[]}' \
  http://127.0.0.1:8545
```

`false` is healthy. An object means it is still catching up.

### Is derivation from L1 actually working?

```bash
curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H 'Content-Type: application/json' http://127.0.0.1:7545 \
  | jq '{
      unsafe:    .result.unsafe_l2.number,
      safe:      .result.safe_l2.number,
      finalized: .result.finalized_l2.number,
      lag:       (.result.unsafe_l2.number - .result.safe_l2.number),
      l1_head:   .result.head_l1.number,
      age_s:     (now - .result.unsafe_l2.timestamp | floor)
    }'
```

This is the important one. The unsafe head advances even when L1 access is
broken; the safe head does not. See **Monitoring** §1.

### How far behind is the head, in minutes?

```bash
echo Latest synced block behind by: $((($(date +%s)-$( \
  curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H "Content-Type: application/json" http://127.0.0.1:7545 | \
  jq -r .result.unsafe_l2.timestamp))/60)) minutes
```

### Do we agree with the rest of the network?

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  http://127.0.0.1:8545 | jq -r .result

curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  https://mainnet.base.org | jq -r .result
```

Compare the hash too, not just the height — two nodes on different chains can
sit at the same number:

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["safe",false]}' \
  http://127.0.0.1:8545 | jq -r '.result.number + " " + .result.hash'
```

---

## `basectl`

```bash
basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
basectl -c mainnet doctor --json | jq '.summary'
basectl -c mainnet sync-status
basectl -c mainnet sync-status --json | jq '.tipReference'
basectl -c mainnet block latest
basectl -c mainnet block 42417649 --json
basectl -c mainnet p2p info
basectl -c mainnet p2p peers
basectl -c mainnet txpool status
basectl -c mainnet monitor               # TUI
basectl -c mainnet monitor upgrades      # fork countdown and history
basectl -c sepolia doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
```

`basectl doctor` exits `1` if any check fails and `0` when checks only pass,
warn or **skip**. Always pass `--cl-rpc`: the built-in mainnet preset expects
the CL on `9545` while Compose publishes `7545`, and without the flag the
CL-dependent checks are skipped rather than failed.

`basectl p2p add-peer`, `remove-peer`, `ban`, `unban` and the `conductor` and
`sequencer` subcommands mutate state. Nothing on a follower node needs them in
normal operation.

---

## Peers

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"net_peerCount","params":[]}' \
  http://127.0.0.1:8545 | jq -r .result        # hex

basectl -c mainnet p2p info
```

Zero peers with correct ingress rules almost always means blocked **egress** to
`30301/tcp+udp` or `9200/udp` — the Base bootnodes. See the networking table in
the **installation guide**.

---

## Chain queries

```bash
# Latest block, summary
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["latest",false]}' \
  http://127.0.0.1:8545 | jq '{number, hash, timestamp, gasUsed, gasLimit, baseFeePerGas}'

# Gas price
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_gasPrice","params":[]}' \
  http://127.0.0.1:8545 | jq -r .result

# Balance
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0xADDRESS","latest"]}' \
  http://127.0.0.1:8545 | jq -r .result

# Receipt
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":["0xTXHASH"]}' \
  http://127.0.0.1:8545 | jq '{status, blockNumber, gasUsed}'
```

The block tags on Base carry L2 meaning: `latest` is the unsafe head from the
sequencer feed, `safe` is derived from L1, `finalized` follows L1 finality, and
`pending` returns Flashblock data when Flashblocks are enabled.

---

## Flashblocks

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["pending",false],"id":1}' \
  http://127.0.0.1:8545 | jq '{number, timestamp}'

basectl -c mainnet flashblocks | head -3       # NDJSON stream
basectl -c mainnet monitor flashblocks         # TUI
```

If Flashblocks are unavailable the node falls back to the latest block rather
than erroring, so compare the returned number against the head before
concluding the stream is connected.

---

## Metrics

```bash
curl -s http://127.0.0.1:7301/ | head -5          # EL — try / first
curl -s http://127.0.0.1:7301/metrics | head -5   # then /metrics
curl -s http://127.0.0.1:7300/metrics | head -5   # CL
```

An empty reply means the service started without its metrics flag, or the
mapped port is not the one you think.

---

## Exposure check

Run this after every configuration change, not once at install:

```bash
sudo ss -tulpn | grep -E '8545|8546|8551|7545|7300|7301|6060|30303|9222'
docker compose ps --format 'table {{.Service}}\t{{.Ports}}'
```

`127.0.0.1` on every RPC and metrics line; `0.0.0.0` only on `30303` and
`9222`; `8551` nowhere. Then prove it from another host:

```bash
nc -vz -w3 <node-ip> 8545
nc -vz -w3 <node-ip> 7545
```

Both must fail. `ufw status` is not evidence — Docker publishes past it.

---

## Disk and I/O

```bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh ./reth-data
iostat -x 2 5
```

Check **every** mounted filesystem, not just `/`. The data directory is usually
on a separate volume and that is the one that fills.

---

## Snapshot operations

Destructive — `docker compose down` first, and read **Snapshots** before
running any of it.

```bash
docker compose down
rm -rf ./reth-data/*
base-reth-node download --full --datadir ./reth-data --chain base --resumable
docker compose up -d
```

---

## Upgrade

```bash
curl -fsS https://api.github.com/repos/base/base/releases/latest | jq -r .tag_name
docker compose config | grep -m1 image:

export NODE_TAG=v1.4.0
docker compose pull && docker compose up -d
docker compose logs --since 5m node | head -40
```

Then re-run the safe-head check above and watch it advance for ten minutes.
See **Upgrades**.
