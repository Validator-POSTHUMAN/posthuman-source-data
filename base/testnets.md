# Base Sepolia

Base activates every hardfork on Sepolia roughly a week before mainnet. That
week is the only free rehearsal you get, and it is the entire reason to run a
testnet node.

Cobalt is the current example: Sepolia on **23 September 2026**, mainnet on
**30 September 2026**. A Sepolia node running `v1.4.0` on the 23rd tells you
whether your configuration survives the fork, seven days before it matters.

---

## Parameters

| | Base Sepolia |
|---|---|
| Chain ID | `84532` (`0x14a34`) |
| Public RPC | `https://sepolia.base.org` |
| Sequencer | `https://sepolia-sequencer.base.org` |
| Flashblocks WS | `wss://sepolia.flashblocks.base.org/ws` |
| `RETH_CHAIN` | `base-sepolia` |
| `BASE_NODE_NETWORK` | `base-sepolia` |
| Explorer | [sepolia.basescan.org](https://sepolia.basescan.org) |
| Explorer (open source) | [base-sepolia.blockscout.com](https://base-sepolia.blockscout.com) |
| L1 | Ethereum **Sepolia**, not mainnet |

---

## Running it

Identical to mainnet except for the env file:

```bash
NETWORK_ENV=.env.sepolia NODE_TAG=v1.4.0 docker compose up -d
```

Snapshot restore:

```bash
base-reth-node download --minimal --datadir ./reth-data --chain base-sepolia --resumable
```

Verify:

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' \
  http://127.0.0.1:8545
# expect 0x14a34

basectl -c sepolia doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
```

`basectl` takes `-c sepolia` for every command. Using the mainnet preset against
a Sepolia node produces confident comparisons against the wrong reference.

---

## The L1 you point it at

`.env.sepolia` needs **Ethereum Sepolia** endpoints, not Ethereum mainnet:

```bash
BASE_NODE_L1_ETH_RPC=<your-ethereum-sepolia-rpc>
BASE_NODE_L1_BEACON=<your-ethereum-sepolia-beacon>
```

Pointing a Base Sepolia node at an Ethereum mainnet L1 is a configuration error
that produces a node which starts, connects, and never derives a safe head. The
symptom is the frozen-safe-head case from **Troubleshooting**, with an L1 head
that is advancing normally — because it is, on the wrong chain.

`base-reth-node download --chain base-sepolia` and `RETH_CHAIN=base-sepolia`
must agree with each other too. A mismatch gives you a data directory the client
refuses at startup.

---

## What Sepolia is good for

- **Fork rehearsal.** Upgrade it on the Sepolia activation date, watch the safe
  head cross the fork, then do mainnet with a known-good procedure.
- **Testing your own changes.** Compose overrides, reverse-proxy method
  filtering, prune distances, monitoring rules and alert thresholds — all of it
  behaves the same and none of it risks a production consumer.
- **Rehearsing snapshot restore.** The procedure that fails is the one you have
  never run. Sepolia is smaller and faster to redo.
- **Validating a monitoring stack.** Point the prober and the Prometheus rules
  at Sepolia first and confirm the alerts actually fire — an alert that has
  never fired is an untested alert.

## What Sepolia is not good for

- **Capacity planning.** Sepolia's chain is far smaller than mainnet's. Its disk
  and I/O numbers tell you nothing about mainnet sizing. Use the formula in
  **Pruning & Storage** with mainnet figures.
- **Proving an L1 provider plan is large enough.** Sepolia derivation consumes a
  fraction of the L1 requests mainnet does.

---

## Funding a test address

Base Sepolia ETH comes from the testnet faucets listed at
[docs.base.org/get-started/get-funds](https://docs.base.org/get-started/get-funds),
or by bridging Ethereum Sepolia ETH across.

A node operator needs none of this. Running a Base node requires no funded
address, no deposit and no transaction of any kind. Fund something only if you
are testing an application on top of your node.

---

## Related

- **Installation Guide** — the full procedure; this page only lists the deltas
- **Upgrades** — why the Sepolia activation date is the one to diary
