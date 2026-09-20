# Solana RPC Node

An RPC node runs the same software as a validator with voting turned off. It
earns nothing from consensus, costs more in hardware, and exists to answer
queries. Do not try to make one machine do both jobs on mainnet: RPC load and
leader-slot performance compete for exactly the resources that decide your skip
rate.

## What changes versus a validator

| | Validator | RPC node |
|---|---|---|
| Votes | yes | **no** (`--no-voting`) |
| Vote account | required | none |
| Identity | hot, funded | any keypair, unfunded |
| CPU | 12c/24t minimum | 16c/32t or more |
| RAM | 256 GB+ | 512 GB+ if you enable all account indexes |
| Disk | accounts + ledger on separate NVMe | accounts and ledger **must not** share a disk |
| RPC port | closed | that is the whole point |

## Startup flags

````bash
exec agave-validator \
  --identity /home/sol/rpc-identity.json \
  --no-voting \
  --ledger /mnt/ledger \
  --accounts /mnt/accounts \
  --snapshots /mnt/ledger/snapshots \
  --log /home/sol/agave-validator.log \
  --rpc-port 8899 \
  --rpc-bind-address 127.0.0.1 \
  --full-rpc-api \
  --dynamic-port-range 8000-8050 \
  --entrypoint entrypoint.mainnet-beta.solana.com:8001 \
  --entrypoint entrypoint2.mainnet-beta.solana.com:8001 \
  --entrypoint entrypoint3.mainnet-beta.solana.com:8001 \
  --known-validator 7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2 \
  --known-validator GdnSyH3YtwcxFvQrVVJMm1JhTS4QVX7MFsX56uJLUfiZ \
  --only-known-rpc \
  --expected-genesis-hash 5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d \
  --wal-recovery-mode skip_any_corrupted_record \
  --limit-ledger-size
````

Bind RPC to loopback and put a reverse proxy in front of it. Exposing
`agave-validator`'s RPC directly to the internet gives you no rate limiting, no
TLS, no per-method policy and no useful access log.

## Transaction history

By default an RPC node answers only about data still in its ledger.

````
--enable-rpc-transaction-history
--enable-extended-tx-metadata-storage     # inner instructions, token balances
````

`--enable-rpc-transaction-history` stores extra block and transaction metadata
and **will** blow past the `--limit-ledger-size` target of roughly 500 GB. Size
the ledger disk for the history depth you actually need; "all of it" is an
archive node and a different capacity plan.

`--limit-ledger-size <shreds>` controls retention. The default aims at ~500 GB
of blockstore, excluding accounts data, account index and snapshots — which all
live in the same directory tree unless you move them.

## Account indexes

Scanning RPC methods — `getProgramAccounts`, the SPL-token lookups — are slow
without an index and can be pathological on a busy cluster.

````
--account-index program-id
--account-index spl-token-mint
--account-index spl-token-owner
````

| Index | Serves |
|---|---|
| `program-id` | `getProgramAccounts` |
| `spl-token-mint` | `getTokenAccountsByDelegate`, `getTokenLargestAccounts` |
| `spl-token-owner` | `getTokenAccountsByOwner`, `getProgramAccounts` with an owner filter |

Each index is held in memory. Enabling all three is the reason the RPC RAM
recommendation is 512 GB rather than 256 GB. Enable only what your callers use.

You can exclude the worst offenders:

````
--account-index-exclude-key <pubkey>
````

## Geyser plugins

For streaming account, slot, block and transaction updates out of the node in
real time, use a Geyser plugin rather than polling RPC:

````
--geyser-plugin-config /home/sol/geyser-config.json
````

This is how indexers, gRPC streaming services and data pipelines are built on
Solana. A misbehaving plugin runs inside the validator process — treat plugin
selection and upgrades with the same care as the client itself, and never run an
unpinned or unattributed plugin build.

## In front of the node

- **Reverse proxy** (nginx, Caddy, HAProxy) for TLS, rate limiting, request size
  caps and method allowlisting.
- **Method policy.** Block or heavily limit `getProgramAccounts` and
  `getBlock`-range scans from untrusted callers; they are the cheap way to take
  your node down.
- **Health checks.** `getHealth` plus a slot-distance check against a public
  RPC; drop a lagging node out of the pool rather than serving stale state.
- **More than one node.** A single RPC node is a single point of failure and
  cannot be restarted without an outage.

## Monitoring specifics

Everything in the validator monitoring guide applies except the consensus layer.
Add:

- request rate and latency per method;
- error rate, especially `-32005` (node behind) and timeouts;
- slot distance to the cluster — an RPC node serving stale data is worse than
  one that is down;
- account-index memory footprint;
- open file descriptors and connection counts.

## Cost reality

An RPC node is more expensive than a validator and earns nothing directly. Run
one if you need private, unthrottled, low-latency access — for your own
validator tooling, an indexer, or a product. If you need occasional queries, a
commercial provider is cheaper than the hardware.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
