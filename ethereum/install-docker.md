# Ethereum with eth-docker

[eth-docker](https://github.com/ethstaker/eth-docker) (`v26.9.0`) is the
community-maintained Docker Compose stack for Ethereum staking. It runs every
mainnet client pair, wires the JWT and the Engine API for you, ships Prometheus
and Grafana, and updates clients with one command.

**When to use it instead of systemd:** almost always, for a first node, and for
any operator running more than one machine. It removes the entire class of
mistakes this documentation set spends pages warning about — wrong JWT
permissions, a client bound to `0.0.0.0`, a missing fee recipient, a mismatched
metrics port.

**When not to:** when you need the node to fit an existing systemd-based
configuration management estate, or when a policy forbids Docker on the host.
The systemd path is in **Installation**.

---

## 1. Prerequisites

Ubuntu LTS or Debian stable. Docker Engine with the Compose plugin — **not** the
Ubuntu snap package, which has caused complete data loss on upgrade:

````bash
sudo snap remove --purge docker   # only if the snap is installed
````

eth-docker can install the prerequisites itself:

````bash
git clone https://github.com/ethstaker/eth-docker.git && cd eth-docker
./ethd install
````

Log out and back in afterwards so the docker group membership applies.

### Put chain data on the right disk

Docker stores everything under `/var/lib/docker` by default. If the operating
system lives on a small drive and the chain data belongs on a large NVMe, set
this **before** the first sync:

````json
// /etc/docker/daemon.json
{
  "data-root": "/mnt/nvme/docker"
}
````

````bash
sudo systemctl stop docker
sudo cp -rp /var/lib/docker /mnt/nvme/
sudo systemctl start docker
````

Moving it after a 1 TB sync is a long, avoidable afternoon.

---

## 2. Configure

````bash
./ethd config
````

The wizard asks for, in order:

| Prompt | What to answer |
|---|---|
| Network | `mainnet`, or `hoodi` for testing |
| Execution client | Prefer a minority client — Nethermind, Besu or Reth |
| Consensus client | Prefer a minority client — Nimbus, Teku, Lodestar or Grandine |
| Validator | Only if this host will stake |
| Fee recipient | An address you control. Required. |
| MEV-Boost | Optional; see **Create validator** for the tradeoff |
| Grafana | Yes |

The wizard writes `.env`. Everything it asked is editable there afterwards, and
`.env` is the file to back up — it is the whole configuration of the node.

Checkpoint sync is on by default and uses a public provider. Verify the head
against a second source once the node is up.

---

## 3. Run

````bash
./ethd up
./ethd logs -f execution
./ethd logs -f consensus
````

Common commands:

| Command | Does |
|---|---|
| `./ethd up` | Start everything |
| `./ethd down` | Stop everything |
| `./ethd update` | Pull new client images (does not restart) |
| `./ethd up` after `update` | Apply the new images |
| `./ethd logs -f <service>` | Follow one service |
| `./ethd version` | Show running client versions |
| `./ethd terminate` | **Deletes chain data.** Read the prompt. |

`./ethd update && ./ethd up` is the entire client upgrade procedure. On a
validator host, still read the release notes first — see **Upgrades**.

---

## 4. Ports and exposure

eth-docker binds RPC, the Beacon API and metrics to `127.0.0.1` by default and
publishes only the P2P ports. Do not change that on a staking host.

The thing to remember: **Docker writes iptables rules in front of ufw**, so a
port published as `8545:8545` is reachable from the internet even though
`ufw status` says otherwise. If you edit a Compose override, keep the
`127.0.0.1:` prefix.

Verify what is actually listening:

````bash
sudo ss -tlnp | grep -vE '127\.0\.0\.1|\[::1\]'
````

---

## 5. Validator keys

````bash
./ethd keyimport
````

Point it at the `validator_keys/` directory produced by the deposit CLI. Key
generation itself belongs on an offline machine — see **Create validator**.

The slashing protection database lives in the validator container's volume.
Before moving keys to another host:

````bash
./ethd keyexport            # exports keys
# stop the validator on the old host FIRST, then import on the new one
````

Never run the same keys on two hosts. eth-docker does not prevent it.

---

## 6. Monitoring

Grafana is at `http://127.0.0.1:3000` — reach it over an SSH tunnel, not by
publishing the port:

````bash
ssh -L 3000:127.0.0.1:3000 <operator>@<host>
````

The bundled dashboards cover sync status, peers, attestation effectiveness and
resource use. Alerting setup and what to alert on are in **Monitoring &
Security**.

---

## 7. Verify

Same four checks as the systemd path:

````bash
docker exec -it eth-docker-execution-1 true 2>/dev/null || ./ethd version
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' http://127.0.0.1:8545
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
curl -s http://127.0.0.1:5052/eth/v1/beacon/headers/head | jq '.data.header.message.slot'
````

`is_optimistic` must be `false`, and the head slot must match
[beaconcha.in](https://beaconcha.in/).

## Sources

- [ethdocker.com](https://ethdocker.com/)
- [ethstaker/eth-docker](https://github.com/ethstaker/eth-docker) — `v26.9.0`
