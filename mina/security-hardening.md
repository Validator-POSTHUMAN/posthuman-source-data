# Mina Security Hardening

Mina's threat model is unusual and it drives everything below: there is **no
slashing**, so the chain will not punish you for a mistake — but the block
producer's private key is an ordinary spending key that must sit unlocked on an
internet-connected machine. You cannot lose stake to a consensus fault. You can
lose every coin in the producer account to a compromised host.

So: protect the host, keep the stake somewhere else, and expose exactly one
port.

## Port model

| Port | Purpose | Exposure |
|---|---|---|
| `8302/tcp` | libp2p P2P (gossip and RPC) | **public** — the only one |
| `8301/tcp` | client RPC **and** SNARK coordinator ↔ worker | loopback or private network, never public |
| `3085/tcp` | full GraphQL / REST | loopback only |
| `3086/tcp` | archive process server port | private network only |
| `6060`, `6061` | Prometheus daemon and libp2p metrics | loopback or private network |

````bash
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 8302/tcp
sudo ufw enable
sudo ufw status numbered
````

A block producer that cannot be dialled on `8302` still syncs, but it gossips
poorly and can lose its own slots. It is the one port that must be open, and
opening any of the others is how nodes get taken.

### Port 8301 has no authentication

The client RPC and the coordinator↔worker protocol share `8301` and the protocol
is explicitly not secure. Anyone who can reach it can talk to your daemon. Keep
coordinator and workers on the same private network, VPN or Docker network.

The daemon restricts which sources may use that port via a client trustlist:

````bash
mina advanced client-trustlist list
mina advanced client-trustlist add    --cidr 10.0.0.0/8
mina advanced client-trustlist remove --cidr 10.0.0.0/8
````

`MINA_CLIENT_TRUSTLIST` sets it at startup. The official SNARK compose example
uses `0.0.0.0/0` — that is safe **only** because the port is never published
outside the Docker network. Copying that value onto a host with `-p 8301:8301`
is a full compromise.

### Port 3086 writes to your archive

The archive server port has no authentication either: anyone who can reach it
can insert blocks into your archive database. Only the daemons feeding the
archive should reach it. In Kubernetes, add a NetworkPolicy; on a plain host,
keep both processes on localhost or a private interface.

## GraphQL exposure

Two flags open the REST/GraphQL server beyond localhost, and they are not
equivalent:

| Flag | Opens | Verdict |
|---|---|---|
| `--insecure-rest-server` | **full** API, including mutations | avoid on a producer |
| `--open-limited-graphql-port --limited-graphql-port N` | read-only limited API | acceptable, still firewalled |

The full API includes `sendPayment`, `sendDelegation`, `exportLogs` and the
SNARK-worker setters. Combined with an account the operator has unlocked with
`mina accounts unlock`, an exposed full endpoint is a direct path to moving
funds — no host compromise required.

Under Docker the daemon's server listens on localhost *inside the container*, so
a `-p` mapping alone reaches nothing. Use the limited port and bind the host
side to loopback:

````
-p 127.0.0.1:3085:3086
--open-limited-graphql-port --limited-graphql-port 3086
````

If a dashboard needs the endpoint from another machine, put it behind a
reverse proxy with TLS and authentication, or reach it over a VPN. Do not widen
the daemon flag.

## Key and secret handling

- `~/keys` mode `700`; private key mode `600`. The daemon refuses to start
  otherwise, which is a feature.
- `~/.mina-env` mode `600`. It contains `MINA_PRIVKEY_PASS` in plaintext — that
  is unavoidable for an unattended node, so treat the file as key material and
  keep it out of backups that are not encrypted.
- **Never** pass the password on the command line. `--block-producer-password`
  exists, and the daemon's own help warns it will land in your shell history and
  in `ps` output for every local user.
- Mount key directories read-only into containers (`-v ~/mina/keys:/keys:ro`).
- Keep the stake in a cold wallet delegated to the hot producer key. See
  **Keys**. This is the single control that bounds the damage of a host
  compromise.

## Hetzner and "netscan detected"

Mina's libp2p module triggers abuse warnings at some providers — Hetzner in
particular. The fix documented by Mina is to block outbound traffic to private
ranges:

````bash
sudo ufw allow 22
sudo ufw allow 8302
sudo ufw enable

sudo ufw deny out from any to 10.0.0.0/8
sudo ufw deny out from any to 172.16.0.0/12
sudo ufw deny out from any to 192.168.0.0/16
sudo ufw deny out from any to 100.64.0.0/10
sudo ufw deny out from any to 198.18.0.0/15
sudo ufw deny out from any to 169.254.0.0/16
````

Apply this **before** first start on such a provider. Check it against your own
topology first: if your coordinator, workers, archive or monitoring live on a
private network, these rules will cut them off and you need explicit allow rules
for those destinations above the denies.

## Host baseline

- SSH: key-only authentication, no root login, non-default handling of failed
  attempts (fail2ban or equivalent).
- Run the daemon as a dedicated non-root user. The package's systemd unit is a
  **user** unit for exactly this reason; do not "fix" it into a root service.
- Unattended security updates for the OS — but **pin the Mina package**. An
  automatic `mina-mainnet` upgrade can move a node across a fork boundary
  unattended. Pin the exact version and upgrade deliberately; see **Upgrades**.
- Time sync (NTP/chrony) running and monitored.
- Docker hosts: do not add untrusted users to the `docker` group; membership is
  equivalent to root.

## Redundancy is allowed — use it correctly

Mina has no double-sign penalty, and the delegation program explicitly permits
running more than one node on the same block producer key. Standby producers are
therefore a legitimate availability strategy, not a slashing risk.

What still bites:

- **Never** share a libp2p key between two live nodes. Duplicate peer IDs
  degrade connectivity in ways that are hard to diagnose.
- Every copy of the producer key is another host whose compromise costs you the
  account. Two hosts, two attack surfaces — harden both or run one.

## Backup and recovery

Back up, encrypted and off-host:

- the encrypted private key and its public key file;
- the password, stored separately from the key;
- the libp2p key, if you pinned one;
- your `~/.mina-env` / compose file, as configuration-with-secrets.

`~/.mina-config` chain data is disposable — it re-syncs in about 30 minutes.
Restoring a node from key plus config is fast; restoring a lost key is not
possible at all.

## Related guides

- **Keys** — custody, hot/cold, rotation reality
- **SNARK worker** — why `8301` stays private
- **Archive node** — why `3086` stays private
- **Monitoring** — metrics ports and what to alert on
- **Upgrades** — pinning and deliberate version moves

## Sources

- [docs.minaprotocol.com — requirements (networking)](https://docs.minaprotocol.com/node-operators/validator-node/requirements)
- [docs.minaprotocol.com — troubleshooting (ports, Hetzner)](https://docs.minaprotocol.com/node-operators/troubleshooting)
- [docs.minaprotocol.com — querying data](https://docs.minaprotocol.com/node-operators/validator-node/querying-data)
- [docs.minaprotocol.com — archive node getting started](https://docs.minaprotocol.com/node-operators/archive-node/getting-started)
- [docs.minaprotocol.com — SNARK workers getting started](https://docs.minaprotocol.com/node-operators/snark-workers/getting-started)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
