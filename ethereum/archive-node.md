# Running an Ethereum Archive Node

An archive node keeps every historical state, so it can answer "what was this
balance at block 4,000,000" and serve `debug_trace*` over the whole chain. It is
what block explorers, indexers, analytics and MEV research run on.

**Do not run one on a validator host.** Archive workloads are disk-bound and will
compete with attestation timing. Run it on its own machine.

---

## 1. Which client

Archive is the one place where client choice is not about diversity — it is
about whether the thing fits on a disk you can buy.

| Client | Archive size | Notes |
|---|---|---|
| **Erigon** `v3.6.1` | ~2.5 TB+ | The cheapest full archive. Flat-file storage, ships Caplin as an embedded CL. |
| **Reth** `v2.6.0` | ~2.2 TB+ | Comparable size, Rust, strong `debug_trace` performance, static files. |
| Geth | 12 TB+ | Reference behaviour, reference cost. |
| Nethermind | 12 TB+ | |
| Besu | 12 TB+ | |

For a new archive node in 2026 the realistic choice is **Erigon or Reth**. The
others are correct and five times the disk.

---

## 2. Erigon

````bash
ERIGON_VERSION=v3.6.1
cd /tmp
curl -fsSLO https://github.com/erigontech/erigon/releases/download/${ERIGON_VERSION}/erigon_${ERIGON_VERSION}_linux_amd64.tar.gz
tar xzf erigon_${ERIGON_VERSION}_linux_amd64.tar.gz
sudo install -m 0755 erigon /usr/local/bin/erigon
````

Verify the published checksum before installing.

````ini
ExecStart=/usr/local/bin/erigon \
  --chain=mainnet \
  --datadir=/var/lib/erigon \
  --prune.mode=archive \
  --http --http.addr=127.0.0.1 --http.port=8545 \
  --http.api=eth,erigon,web3,net,debug,trace,txpool \
  --authrpc.addr=127.0.0.1 --authrpc.port=8551 \
  --authrpc.jwtsecret=/var/lib/ethereum/jwt.hex \
  --metrics --metrics.addr=127.0.0.1 --metrics.port=6060
````

Erigon still needs a consensus client. Either point an external beacon node at
`8551`, or run the embedded Caplin with `--externalcl=false`.

The `trace` and `debug` namespaces are the reason to run archive at all — but
they are also expensive to serve. Never publish them without rate limiting.

## 3. Reth

````ini
ExecStart=/usr/local/bin/reth node \
  --chain mainnet \
  --datadir /var/lib/reth \
  --http --http.addr 127.0.0.1 --http.port 8545 \
  --http.api eth,net,web3,debug,trace \
  --authrpc.addr 127.0.0.1 --authrpc.port 8551 \
  --authrpc.jwtsecret /var/lib/ethereum/jwt.hex \
  --metrics 127.0.0.1:6060
````

Omit `--full` — that flag is what makes Reth pruned. Nothing else needs to
change.

---

## 4. Hardware

| | Archive |
|---|---|
| CPU | 8+ cores |
| RAM | 64 GB (32 GB works, slowly) |
| Disk | 4 TB NVMe for Erigon/Reth, 16 TB+ for Geth-family |
| Bandwidth | Unmetered |

Initial sync is days, not hours, and it is entirely disk-throughput bound. A
drive that is merely "fast enough for a full node" will roughly double the sync
time.

---

## 5. Verify it is really archive

A pruned node answers historical queries for recent blocks and fails for old
ones, so test against a genuinely old block:

````bash
curl -s -X POST -H 'Content-Type: application/json' --data '{
  "jsonrpc":"2.0","method":"eth_getBalance",
  "params":["0x00000000219ab540356cBB839Cbe05303d7705Fa","0x3D0900"],
  "id":1}' http://127.0.0.1:8545
````

A result is archive. `missing trie node` or `state not available` is not.

````bash
curl -s -X POST -H 'Content-Type: application/json' --data '{
  "jsonrpc":"2.0","method":"trace_block","params":["0x3D0900"],"id":1}' \
  http://127.0.0.1:8545 | head -c 200
````

---

## 6. Serving it

If this node backs an indexer or a public endpoint:

- Terminate TLS at a reverse proxy; do not expose the client directly.
- Allowlist methods. `debug_traceTransaction` over an unbounded range is a
  denial-of-service primitive.
- Rate limit per key, not per IP.
- Keep `admin`, `personal` and `txpool` off the public listener entirely.
- Monitor request latency separately from node sync — an archive node that is
  synced but answering traces in 30 s is down, as far as its users are
  concerned.

## Sources

- [Erigon documentation](https://docs.erigon.tech/)
- [Reth book](https://reth.rs/)
- [ethereum.org — Archive nodes](https://ethereum.org/developers/docs/nodes-and-clients/archive-nodes/)
