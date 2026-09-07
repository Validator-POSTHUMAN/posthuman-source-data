# Avalanche Validator Installation Guide

## About Avalanche

Avalanche is an EVM-compatible Layer 1 built from three chains that share one
validator set: the **P-Chain** (staking and coordination), the **X-Chain**
(asset transfers) and the **C-Chain** (EVM contracts). One `avalanchego`
process serves all three, plus any subnets you choose to track.

**Validator facts that shape the setup:**
- Staking is non-custodial and time-boxed: you lock AVAX for a fixed period
  with a start and end time, and the stake unlocks when that period ends.
- Rewards depend on measured **uptime**, and uptime is measured by your peers,
  not by your own node. A node that cannot accept inbound connections looks
  offline to the network even while its own health endpoint is happy.
- There is no slashing for downtime, but a validator below the uptime
  threshold at the end of its staking period earns nothing for that period.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 8 cores | 16 cores    |
| RAM       | 16 GB   | 32 GB       |
| Disk      | 1 TB SSD| 2 TB NVMe   |
| Network   | 1 Gbps  | 1 Gbps, static IP |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

Minimum self-stake to become a primary-network validator is 2,000 AVAX.

## Update the system

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install curl wget jq ufw
````

## Open the P2P port — do this before you start

This is the single step most often skipped, and it fails in a way that looks
like success. `avalanchego` will sync, report peers and serve RPC while
**only** making outbound connections. The network then measures your uptime as
near zero because no peer can dial you back, and the node's own health check
eventually reports `primary network validator has no inbound connections`.

````bash
sudo ufw allow 22/tcp
sudo ufw allow 9651/tcp
sudo ufw enable
sudo ufw status verbose
````

Port `9651/tcp` must be reachable **inbound** from the public internet. Port
`9650` is the API and must stay local — never expose it.

Verify from another machine, not from the node itself:

````bash
nc -vz <your-public-ip> 9651
````

If your provider has its own firewall or security group in front of the host,
open `9651/tcp` there as well.

## Install the node

The official installer builds or fetches the release, creates the systemd unit
and generates the staking keys on first run:

````bash
wget -nd -m https://raw.githubusercontent.com/ava-labs/avalanche-docs/master/scripts/avalanchego-installer.sh
chmod 700 avalanchego-installer.sh
./avalanchego-installer.sh
````

Answer the prompts:
- **RPC access**: private (localhost only).
- **State sync**: enabled — it brings the C-Chain up in hours rather than days.
- **Public IP**: your static IP, or dynamic resolution if the host's IP changes.

The installer places the binary under `~/avalanche-node/avalanchego`, the data
directory at `~/.avalanchego/`, and installs `avalanchego.service`.

## Recommended configuration

Pruned C-Chain with state sync keeps disk growth manageable. Create
`~/.avalanchego/configs/chains/C/config.json`:

````json
{
  "state-sync-enabled": true,
  "pruning-enabled": true
}
````

Restart after changing chain configuration:

````bash
sudo systemctl restart avalanchego
````

## Start and follow the node

````bash
sudo systemctl enable --now avalanchego
sudo systemctl status avalanchego
sudo journalctl -u avalanchego -f -o cat
````

## Verify bootstrap

Each chain bootstraps separately. All three must return `true` before you
register as a validator:

````bash
for chain in P X C; do
  printf '%s: ' "$chain"
  curl -s -X POST --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"info.isBootstrapped\",\"params\":{\"chain\":\"$chain\"}}" \
    -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq -r .result.isBootstrapped
done
````

Check health and peer count:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"health.health"}' \
  -H 'content-type:application/json' http://127.0.0.1:9650/ext/health | jq .result.healthy

curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"info.peers"}' \
  -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq -r .result.numPeers
````

## Get your NodeID and BLS identity

Registration needs the NodeID together with the BLS public key and its proof of
possession. All three come from one call:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"info.getNodeID"}' \
  -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq .result
````

Keep `~/.avalanchego/staking/` safe. It holds `staker.crt`, `staker.key` and
`signer.key` — these are your node's identity. Back the directory up before any
migration, and never run two nodes with the same staking keys at the same time.

## Register as a validator

Use the Core wallet or the Avalanche CLI to add the validator on the P-Chain
with your NodeID, BLS key, proof of possession, stake amount, and start and end
times. Registration is a P-Chain transaction and needs a funded P-Chain
address; the node itself never holds your funds.

## Verify from outside your own node

Your own node is not a witness to your uptime. After the staking period starts,
check what the network sees:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"platform.getCurrentValidators","params":{"nodeIDs":["NodeID-..."]}}' \
  -H 'content-type:application/json' https://api.avax.network/ext/bc/P | jq '.result.validators[0] | {connected, uptime, validationRewardOwner}'
````

If `connected` is `false` or the uptime is far below your local reading, the
cause is almost always inbound reachability on `9651/tcp`, not the node.

You can also confirm on the public explorer:
`https://avascan.info/staking/validator/<your-node-id>`

## Upgrade

````bash
./avalanchego-installer.sh --upgrade
sudo systemctl restart avalanchego
````

After every upgrade re-check bootstrap, health, version and the external
`connected` flag before considering the upgrade finished.

## Monitoring

Watch at minimum:
- `avalanchego.service` active and restart count stable;
- all three chains bootstrapped;
- peer count in a normal range for the network;
- **external** `connected=true` and uptime for your NodeID;
- free space on the data filesystem;
- the staking period end date — an expired validator simply stops validating.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
