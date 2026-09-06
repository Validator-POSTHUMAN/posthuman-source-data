# Avalanche Fuji Testnet Validator Installation Guide

## About Fuji

Fuji is the Avalanche testnet. It runs the same `avalanchego` binary, the same
three chains and the same staking mechanics as mainnet, which makes it the
correct place to rehearse the whole validator lifecycle before committing real
AVAX.

Differences that matter:

- minimum self-stake is **1 AVAX** on Fuji against 2,000 AVAX on mainnet;
- test AVAX comes from the official faucet, and the faucet usually wants a
  mainnet-funded address as an anti-abuse check;
- the same uptime rule applies. Fuji measures your uptime from your peers, so a
  node that cannot accept inbound connections looks offline here exactly as it
  would on mainnet — which is precisely the failure worth rehearsing.

Everything else — hardware, install, configuration, monitoring — follows the
Avalanche mainnet guide. This page states only the deltas.

## Requirements

Fuji is lighter than mainnet, but not by as much as people expect:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8 cores     |
| RAM       | 8 GB    | 16 GB       |
| Disk      | 300 GB SSD | 500 GB NVMe |
| Network   | 100 Mbps | 1 Gbps, static IP |

## Install

Use the same official installer and choose the Fuji network when prompted:

````bash
wget -nd -m https://raw.githubusercontent.com/ava-labs/avalanche-docs/master/scripts/avalanchego-installer.sh
chmod 700 avalanchego-installer.sh
./avalanchego-installer.sh --fuji
````

If you configure the node by hand instead, the network is selected with:

````
--network-id=fuji
````

Data lives under `~/.avalanchego/` and the staking identity under
`~/.avalanchego/staking/` exactly as on mainnet. **Never reuse the same staking
keys on Fuji and mainnet** — they are the node's identity, and a duplicate
identity on two running nodes is a problem you do not want to create for
yourself while testing.

## Open the P2P port

````bash
sudo ufw allow 22/tcp
sudo ufw allow 9651/tcp
sudo ufw enable
````

Verify inbound reachability from another machine:

````bash
nc -vz <your-public-ip> 9651
````

## Verify bootstrap

````bash
for chain in P X C; do
  printf '%s: ' "$chain"
  curl -s -X POST --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"info.isBootstrapped\",\"params\":{\"chain\":\"$chain\"}}" \
    -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq -r .result.isBootstrapped
done
````

Confirm the node really is on Fuji rather than mainnet:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"info.getNetworkName"}' \
  -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq -r .result.networkName
````

## Fund and register

1. Get test AVAX from the official Avalanche faucet.
2. Move it to your P-Chain address.
3. Read the NodeID, BLS public key and proof of possession:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"info.getNodeID"}' \
  -H 'content-type:application/json' http://127.0.0.1:9650/ext/info | jq .result
````

4. Add the validator on the P-Chain with your stake amount and a start and end
   time.

## Verify from outside

Use the public Fuji API rather than your own node:

````bash
curl -s -X POST --data '{"jsonrpc":"2.0","id":1,"method":"platform.getCurrentValidators","params":{"nodeIDs":["NodeID-..."]}}' \
  -H 'content-type:application/json' https://api.avax-test.network/ext/bc/P | jq '.result.validators[0] | {connected, uptime}'
````

`connected: false` here means the same thing it means on mainnet: inbound
`9651/tcp` is not actually reachable. Fixing it on Fuji is free; fixing it on
mainnet costs a staking period of rewards.

## Monitoring

Same as mainnet: service state, all three chains bootstrapped, peer count,
external `connected` and uptime, disk free, and the staking period end date.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
