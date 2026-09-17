# Mina SNARK Coordinator and SNARK Workers

SNARK work is Mina's second operator role and it is economically independent of
block production. Workers generate zk-SNARK proofs of transactions; block
producers must buy completed work to include transactions in a block. That
purchase is what keeps the chain 22 kB instead of growing forever.

You do not need to understand zk-SNARKs to run a worker. You do need to
understand that this is a **marketplace**: you post a fee, producers buy the
cheapest acceptable work, and a fee nobody accepts earns nothing.

## Choose a mode

| Mode | What runs | Use when |
|---|---|---|
| Embedded worker | one worker thread pool inside the daemon | single machine, minimal setup |
| Coordinator + external workers | daemon distributes work to separate worker processes | scaling across cores or machines |

In both modes the daemon is still a full network participant and can still
produce blocks.

**Do not co-locate a SNARK worker with a block producer you care about.** Proving
is CPU- and RAM-hungry, and the resource it competes for is exactly the resource
the producer needs to build a blockchain SNARK inside its 90-second slot. Run
SNARK work on separate hosts, or accept that you are trading block reliability
for SNARK fees.

## Embedded worker

**systemd** — in `~/.mina-env`:

````
EXTRA_FLAGS="--run-snark-worker $SNARK_WORKER_PUBLICKEY \
             --snark-worker-fee 0.001 \
             --snark-worker-parallelism 4 \
             --work-selection seq"
````

````bash
systemctl --user restart mina
````

**Docker** — same flags appended to the daemon command.

| Flag | Meaning |
|---|---|
| `--run-snark-worker PUBLICKEY` | public key that receives SNARK fees |
| `--snark-worker-fee FEE` | fee in MINA per proof (daemon default `100000000` nanomina = 0.1 MINA) |
| `--snark-worker-parallelism NUM` | threads for proving; equivalent to `OMP_NUM_THREADS`, does not affect block production |
| `--work-selection seq \| rand \| roffset` | how work is picked from the pool (default `rand`) |

Only the public key is configured. No private key is needed for SNARK work, so
this role carries no key-custody risk.

## Coordinator with external workers

### Coordinator

**systemd** — in `~/.mina-env`:

````
EXTRA_FLAGS="--run-snark-coordinator $SNARK_WORKER_PUBLICKEY \
             --snark-worker-fee 0.001 \
             --work-selection seq"
````

The coordinator distributes work, propagates finished proofs to the network, and
sets the key that collects fees from its workers. `--run-snark-coordinator` is
ignored if `--run-snark-worker` is also set.

### Workers

On each worker machine:

````bash
mina internal snark-worker \
  --proof-level full \
  --shutdown-on-disconnect false \
  --daemon-address <COORDINATOR_IP>:8301 \
  --snark-worker-parallelism 8
````

`--shutdown-on-disconnect false` keeps the worker alive across coordinator
restarts. Without it, one coordinator restart silently leaves you with a pool of
dead workers.

A minimal unit for a worker host — `/etc/systemd/system/mina-snark-worker.service`:

````ini
[Unit]
Description=Mina SNARK Worker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mina
ExecStart=/usr/local/bin/mina internal snark-worker \
  --proof-level full \
  --shutdown-on-disconnect false \
  --daemon-address COORDINATOR_IP:8301 \
  --snark-worker-parallelism 8
Restart=always
RestartSec=30
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
````

````bash
sudo systemctl daemon-reload
sudo systemctl enable --now mina-snark-worker
````

### The coordinator port is unauthenticated

Port `8301` carries both the local client RPC and the coordinator↔worker
protocol, and it has **no authentication**. Anyone who can reach it can talk to
your daemon. Keep coordinator and workers on the same private network, VPN or
Docker network, and never expose `8301` to the internet. See **Security
hardening**.

## Docker Compose: coordinator plus worker

````yaml
services:
  mina_snark_coordinator:
    image: minaprotocol/mina-daemon:4.0.0-6850301-bullseye-mainnet
    restart: always
    environment:
      MINA_PRIVKEY_PASS: ${MINA_PRIVKEY_PASS}
      MINA_CLIENT_TRUSTLIST: "0.0.0.0/0"
    healthcheck:
      test: ["CMD-SHELL", "mina client status"]
      interval: 60s
      timeout: 10s
      retries: 100
    entrypoint: []
    command: >
      bash -c '
        mina daemon
          --peer-list-url https://bootnodes.minaprotocol.com/networks/mainnet.txt
          --run-snark-coordinator $$(cat /root/.mina-config/keys/wallet-key.pub)
          --snark-worker-fee 0.001
          --work-selection rand
      '
    volumes:
      - './node/mina-config:/root/.mina-config'
    ports:
      - '8302:8302'

  mina_snark_worker:
    image: minaprotocol/mina-daemon:4.0.0-6850301-bullseye-mainnet
    restart: always
    entrypoint: []
    command: >
      bash -c '
        mina internal snark-worker
          --daemon-address mina_snark_coordinator:8301
          --proof-level full
          --shutdown-on-disconnect false
      '
    volumes:
      - './node/mina-config:/root/.mina-config'
    depends_on:
      mina_snark_coordinator:
        condition: service_healthy
````

`MINA_CLIENT_TRUSTLIST: "0.0.0.0/0"` is what lets the worker container reach the
coordinator's `8301` across the Docker network. It is safe **only** because that
port is never published to the host. If you add `ports: - '8301:8301'` to the
coordinator, you have handed your daemon to the internet. Scale workers with
`docker compose up -d --scale mina_snark_worker=N`, sized to physical cores, not
threads.

## Change fees at runtime

No restart needed:

````bash
mina client set-snark-work-fee 0.001
mina client set-snark-worker --address $SNARK_WORKER_PUBLICKEY
mina client set-snark-worker                # omit --address to stop snarking
````

## Tuning and economics

- **Fee.** Too high and no producer buys your work; too low and you prove for
  nothing. Watch what is actually clearing in the snark pool and treat the fee
  as a periodically reviewed setting, not a one-time decision.
- **Work selection.** `seq` makes workers deterministic and easy to reason about;
  `rand` (the default) reduces duplicated effort when many independent workers
  compete for the same pool. `roffset` is the compromise.
- **Parallelism.** Per the requirements, budget 4 cores / 8 threads *per worker*
  and 32 GB RAM on the worker host. Over-subscribing threads slows every proof
  rather than producing more of them.
- **Duplicated work earns nothing.** Two of your own workers proving the same
  job is pure waste; that is what the coordinator exists to prevent.

## Verify

````bash
mina client status
````

Look for the SNARK worker key and fee in the output, and for a non-zero
`Snark pool size`. On the worker hosts, confirm the process is connected rather
than merely running:

````bash
systemctl status mina-snark-worker
journalctl -u mina-snark-worker -n 100 --no-pager
````

A worker that logs repeated connection attempts to the coordinator is not
earning, no matter how busy its CPU looks.

## Related guides

- **Security hardening** — why `8301` is never public
- **Monitoring** — proving that work is being sold, not just produced
- **Install (Docker)** — the daemon service these compose blocks extend

## Sources

- [docs.minaprotocol.com — SNARK workers](https://docs.minaprotocol.com/node-operators/snark-workers)
- [docs.minaprotocol.com — SNARK workers getting started](https://docs.minaprotocol.com/node-operators/snark-workers/getting-started)
- [docs.minaprotocol.com — SNARK workers Docker Compose example](https://docs.minaprotocol.com/node-operators/snark-workers/docker-compose)
- [docs.minaprotocol.com — requirements](https://docs.minaprotocol.com/node-operators/validator-node/requirements)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
