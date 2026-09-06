# Espresso Decaf Testnet Node Installation Guide

## About Decaf

Decaf is the Espresso testnet. A node runs the Espresso `sequencer` and takes
part in consensus; validators register on an Ethereum contract, receive
delegation, and enter the active set only if they rank in the **top 100 by
stake**. Registration alone does not make you active — that is the single most
common surprise on this network.

Two roles exist. This guide covers the **regular (non-DA) node**, which is what
most operators run.

## The two things that decide whether this works

**The genesis file is the network.** The sequencer is started against a genesis
TOML for the exact network and release. Take it from the official repository,
pin the release, and record its SHA-256. A node started against the wrong or a
drifted genesis will look like it is running and will not be on Decaf.

**The L1 endpoint must serve archive log requests.** The sequencer reads
Ethereum Sepolia, including historical logs. Free endpoints commonly answer
`403 Archive requests require a personal token` for exactly those calls, and the
failure surfaces as a node that starts and then makes no progress. Verify the
endpoint answers historical `eth_getLogs` before you deploy, and configure both
the HTTP and WebSocket forms.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8 cores     |
| RAM       | 8 GB    | 16 GB       |
| Disk      | 200 GB SSD | 500 GB NVMe |
| Network   | 100 Mbps, public IP | 1 Gbps, static IP |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

## Prepare the host

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install docker.io jq curl
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
````

Espresso's documentation asks for TCP tuning; BBR and enlarged socket buffers
are the relevant part:

````bash
sudo tee /etc/sysctl.d/99-espresso.conf > /dev/null <<'EOF'
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
EOF
sudo sysctl -p /etc/sysctl.d/99-espresso.conf
````

## Open the ports

````bash
sudo ufw allow 22/tcp
sudo ufw allow 9977/tcp
sudo ufw enable
````

`9977/tcp` is Cliquenet, the peer-to-peer transport, and must be reachable
inbound. The address you advertise must be the address peers can actually reach
— bind `0.0.0.0:9977` and advertise your public `IP:9977`. The API port
(`8770/tcp` by default) is for you, not for the internet; leave it closed or
behind a proxy.

## Fetch and pin the genesis

````bash
mkdir -p ~/espresso-decaf/{store,keys,genesis}
cd ~/espresso-decaf
# take decaf.toml from EspressoSystems/espresso-network at the release tag you run
sha256sum genesis/decaf.toml
````

Record that hash next to the image tag you deploy. Those two values together are
what let you prove later which network and which release you were actually on.

## Create the keys

The sequencer uses a BLS consensus key and an x25519 network key. Generate them
with the same image you will run, write them to a key file, and lock it down:

````bash
chmod 600 ~/espresso-decaf/keys/0.env
````

The x25519 private key must persist across restarts — a node that regenerates it
loses its registered network identity and peers stop recognising it.

## Run the sequencer

Put the full `docker run` invocation in a `run.sh` next to the data rather than
typing it each time. Restarts and upgrades then reuse the exact same arguments,
which is what keeps a node reproducible:

````bash
cd ~/espresso-decaf
cat run.sh
./run.sh
docker logs -f espresso-decaf
````

The container mounts `store/` for consensus state, `keys/0.env` read-write only
as needed, and `genesis/decaf.toml` read-only.

## Verify

````bash
curl -s http://127.0.0.1:8770/status/block-height
curl -s http://127.0.0.1:8770/status/success-rate
docker inspect --format='{{.State.Health.Status}}' espresso-decaf
````

Block height must advance and the chain ID must be Decaf's. If height is flat,
check the L1 endpoint before anything else.

## Register as a validator

Registration is an Ethereum transaction against the Espresso staking contract:
it publishes your BLS key, your x25519 key and your commission. After
registration you must also publish your reachable P2P address in the network
config, or peers cannot dial you.

Then wait. You are active only once delegated stake puts you inside the top 100.
Until then a correct, healthy, registered node simply does not participate, and
nothing about the node needs fixing.

## Upgrade

Pull the announced image tag, stop the container, start it with the same
`run.sh`, the same volumes and the genesis for that release, then re-verify
height, health and that your keys are still the registered ones.

## Monitoring

Watch: container health and restart count, block height advancing, L1 endpoint
health, inbound reachability on `9977/tcp`, your position relative to the active
set, and disk free on the store volume.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
