# Mina Archive Node

A Mina node is succinct: it verifies the whole chain without storing it, and it
keeps only the last `k` = 290 blocks in its transition frontier. That is the
point of the protocol, and it means a plain node cannot answer "what happened
last month".

An archive node fixes that. It is an ordinary `mina` daemon plus a separate
`mina-archive` process that writes every block it is handed into PostgreSQL.

Run one if you need: historical block or transaction lookup, zkApp events and
actions, exchange or accounting integrations, or your own payout and delegation
analytics instead of an explorer's.

## Requirements

- 8-core CPU, 32 GB RAM, x86-64
- 64 GB for the node, **plus** database growth — budget separately. A compressed
  mainnet dump is about 1.6 GB today; restored and indexed it is substantially
  larger and grows continuously.
- Working knowledge of running PostgreSQL. This is the part that breaks.

## Install

````bash
sudo apt-get install --yes --allow-downgrades mina-archive=4.0.0-6850301
sudo apt-get install --yes postgresql postgresql-contrib
````

Docker: `minaprotocol/mina-archive:4.0.0-6850301-CODENAME-mainnet`.

Keep the archive package version identical to the daemon version. A schema from
one release and a daemon from another is a slow, confusing failure.

## Create the database

````bash
sudo -u postgres createdb archive
sudo -u postgres psql -c "ALTER DATABASE archive SET DEFAULT_TRANSACTION_ISOLATION TO SERIALIZABLE;"
````

Set the isolation level **before** any archive process connects. Multiple
archive processes writing concurrently to one database can produce
inconsistencies otherwise — this is a known issue, not a theoretical one.

Load the schema for the exact release you run:

````bash
psql -h localhost -p 5432 -d archive \
  -f <(curl -Ls https://raw.githubusercontent.com/MinaProtocol/mina/4.0.0-mainnet-mesa/src/app/archive/create_schema.sql)
````

## Run

````bash
mina-archive run \
  --postgres-uri postgres://localhost:5432/archive \
  --server-port 3086
````

Point the daemon at it:

````
EXTRA_FLAGS="--block-producer-key … --archive-address 3086"
````

For a remote archive use `--archive-address <ip>:3086`, and only across a
trusted private network.

### Do not expose port 3086

The archive server port has **no authentication**. Anyone who can reach it can
write blocks into your database. Keep the daemon and archive on localhost, a
private network, a Docker network or one Kubernetes cluster — with a
NetworkPolicy if the cluster is shared.

### About `--config`

`mina-archive` accepts `--config` to insert genesis accounts, which prevents
gaps in account balances because the archive stores only incremental changes.
It is slow and expensive. **Do not use it on mainnet or devnet.** Seed from an
existing archive dump instead; `--config` is for a brand-new network.

## Docker Compose

Added to the compose project from the **Install (Docker)** guide:

````yaml
services:
  postgres:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: archive
      POSTGRES_USER: mina
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - './pgdata:/var/lib/postgresql/data'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mina -d archive"]
      interval: 10s
      retries: 30

  mina_archive:
    image: minaprotocol/mina-archive:4.0.0-6850301-bookworm-mainnet
    restart: always
    command: >
      mina-archive run
        --postgres-uri postgres://mina:${POSTGRES_PASSWORD}@postgres:5432/archive
        --server-port 3086
    depends_on:
      postgres:
        condition: service_healthy
````

No `ports:` entry on either service — they talk over the compose network. Add
`--archive-address mina_archive:3086` to the daemon service's command. Keep
`POSTGRES_PASSWORD` in a mode-`600` `.env` file.

## Seed from a public dump

Replaying the whole chain into an empty archive takes a very long time. Start
from a dump instead. o1Labs publishes public dumps of its own archives —
**hourly**, roughly 1.6 GB compressed for mainnet:

````bash
curl -O https://storage.googleapis.com/mina-archive-dumps/mainnet-archive-dump-2026-09-17_1100.sql.tar.gz
tar -xzf mainnet-archive-dump-2026-09-17_1100.sql.tar.gz
psql -h localhost -U mina -d archive -f mainnet-archive-dump-2026-09-17_1100.sql
````

List what is actually available rather than guessing a filename:

````bash
curl -s "https://storage.googleapis.com/storage/v1/b/mina-archive-dumps/o?prefix=mainnet-archive-dump-$(date -u +%F)&fields=items(name,size,updated)" | jq -r '.items[].name'
````

Swap `mainnet` for `devnet` on testnet. This bucket is a convenience from one
provider, not a guarantee: mirror the dumps you depend on, and keep your own
`pg_dump` schedule.

## Redundancy

Gaps appear when the feeding daemon or the archive process misses blocks. The
defences, cheapest first:

1. **Multiple daemons, one archive.** Point several daemons at the same
   `--archive-address`. Removes the single-daemon dependency.
2. **Multiple archive processes, one database.** Same `--postgres-uri`. Requires
   the `SERIALIZABLE` isolation set above.
3. **Precomputed blocks.** `--upload-blocks-to-gcloud` (with `GCLOUD_KEYFILE`,
   `NETWORK_NAME`, `GCLOUD_BLOCK_UPLOAD_BUCKET`) writes one JSON file per block
   to object storage. `-log-precomputed-blocks` puts the same data in
   `mina.log`, which you can ship to any log service.
4. **Extensional blocks.** `mina-extract-blocks --archive-uri … --end-state-hash
   … [--all-blocks]` regenerates per-block JSON from a healthy database. These
   contain only what the database holds — enough to repair another archive, not
   enough to reconstruct a full block.
5. **`pg_dump`.** Nightly at minimum:

````bash
pg_dump -U mina -Fp archive | gzip > archive-$(date +%F).sql.gz
````

## Detect gaps

The query that matters — blocks whose parent is missing:

````sql
SELECT height
FROM blocks
WHERE parent_id IS NULL AND height > 1
ORDER BY height;
````

Make it a monitored check, not something you run after someone complains. A
silently incomplete archive is worse than no archive: it answers questions
wrongly instead of failing.

Latest block, as a freshness probe:

````sql
SELECT height, state_hash,
       to_timestamp(CAST("timestamp" AS bigint)/1000) AT TIME ZONE 'UTC' AS datetime
FROM blocks
WHERE id = (SELECT MAX(id) FROM blocks);
````

## Useful queries

Blocks produced by a public key:

````sql
SELECT b.height, b.state_hash
FROM blocks b
JOIN public_keys pk ON b.creator_id = pk.id
WHERE pk.value = 'B62q…'
ORDER BY b.height DESC
LIMIT 50;
````

Payments received by a public key:

````sql
SELECT uc.*
FROM user_commands uc
JOIN blocks_user_commands buc ON uc.id = buc.user_command_id
JOIN public_keys pk ON uc.receiver_id = pk.id
WHERE pk.value = 'B62q…' AND uc.command_type = 'payment';
````

Block counts by producer:

````sql
SELECT pk.value, COUNT(*) AS blocks
FROM blocks b
JOIN public_keys pk ON b.creator_id = pk.id
GROUP BY pk.value
ORDER BY blocks DESC
LIMIT 25;
````

The schema is about 45 tables; `\dt` lists them and `\d <table>` shows one. The
canonical definition lives in `src/app/archive/create_schema.sql` at the tag you
installed.

## Related guides

- **Install (Docker)** — the daemon service these blocks extend
- **Security hardening** — why `3086` stays private
- **Monitoring** — adding archive freshness and gap checks to alerting
- **Delegation program** — what payout tooling needs from an archive

## Sources

- [docs.minaprotocol.com — archive node](https://docs.minaprotocol.com/node-operators/archive-node)
- [docs.minaprotocol.com — archive node getting started](https://docs.minaprotocol.com/node-operators/archive-node/getting-started)
- [docs.minaprotocol.com — archive redundancy](https://docs.minaprotocol.com/node-operators/archive-node/archive-redundancy)
- [MinaProtocol/mina — `create_schema.sql`](https://github.com/MinaProtocol/mina/blob/4.0.0-mainnet-mesa/src/app/archive/create_schema.sql)
