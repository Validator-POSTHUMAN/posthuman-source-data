# Starknet Sepolia Node and Attestor Installation Guide

## About Starknet on Sepolia

Starknet Sepolia is the public testnet. It is the right place to rehearse the
validator flow, because on Sepolia the minimum validator stake is **1 STRK**
against **20,000 STRK** on mainnet — the whole staking and attestation
lifecycle can be exercised for a nominal amount.

A Starknet validator is two processes:

- a **full node** (Pathfinder) that follows Starknet and answers RPC;
- an **attestor** that watches for the blocks your validator is assigned and
  submits attestation transactions. Rewards depend on attestations landing, not
  on the node merely being up.

## The dependency people miss

Pathfinder does not stand alone. It follows Starknet by reading Ethereum, so it
needs an **Ethereum Sepolia WebSocket** endpoint for the whole time it runs —
not just during sync. Choose this endpoint deliberately:

- it must be a WebSocket URL (`wss://`), not plain HTTPS;
- free public Sepolia endpoints will emit repeated PubSub backend errors while
  block import quietly continues. If catch-up stalls rather than merely
  logging, the endpoint is the first thing to replace, not Pathfinder;
- some providers refuse archive log requests without an account. Confirm your
  endpoint answers historical log queries before committing to it.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8 cores     |
| RAM       | 8 GB    | 16 GB       |
| Disk      | 250 GB SSD | 500 GB NVMe |
| Network   | 100 Mbps | 1 Gbps     |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

## Prepare the host

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install docker.io docker-compose-v2 jq curl
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
````

## Run Pathfinder

Create `~/starknet-sepolia/docker-compose.yml`:

````yaml
services:
  pathfinder:
    image: eqlabs/pathfinder:v0.22.7
    container_name: pathfinder-testnet
    restart: unless-stopped
    ports:
      - "127.0.0.1:9545:9545"
      - "127.0.0.1:9000:9000"
    volumes:
      - ./data:/usr/share/pathfinder/data
    command:
      - --network=sepolia-testnet
      - --ethereum.url=wss://<your-ethereum-sepolia-ws-endpoint>
      - --http-rpc=0.0.0.0:9545
      - --monitor-address=0.0.0.0:9000
````

````bash
mkdir -p ~/starknet-sepolia/data && cd ~/starknet-sepolia
docker compose up -d
docker compose logs -f pathfinder
````

Pin the image to an explicit tag as shown. Bind the RPC and metrics ports to
`127.0.0.1` unless you intend to publish them, and put a reverse proxy in front
if you do.

## Use the official snapshot

Syncing Sepolia from genesis takes days. Restore the official Pathfinder
`testnet-sepolia` snapshot instead, then let the node catch up the remainder.
Before replacing anything, move the existing database aside rather than
deleting it:

````bash
docker compose down
mv ~/starknet-sepolia/data ~/starknet-sepolia/data.pre-snapshot-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p ~/starknet-sepolia/data
# download and extract the official snapshot into ./data, then:
docker compose up -d
````

Keeping the previous directory is what makes a bad snapshot a five-minute
rollback instead of a fresh multi-day sync.

## Verify

````bash
curl -s -X POST http://127.0.0.1:9545/rpc/v0_7 \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"starknet_blockNumber","params":[]}' | jq

curl -s -X POST http://127.0.0.1:9545/rpc/v0_7 \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"starknet_chainId","params":[]}' | jq
````

Compare your block number with a public Sepolia explorer. A node that is
importing but far behind is normal during catch-up; a node whose height stops
advancing is almost always the Ethereum endpoint, not Pathfinder.

## Prepare the validator account

1. Create and fund a Starknet Sepolia account (a public faucet provides test
   STRK/ETH). Keep the keystore at mode `0600` and never print or copy the
   private key.
2. Deploy the account with Starkli once it holds funds — an undeployed account
   cannot send transactions.
3. Register as a validator with the minimum Sepolia stake (1 STRK) and set your
   commission.
4. Run the attestor against your own Pathfinder RPC and confirm attestations are
   landing on-chain. Attestation transactions cost fees, so the attestor account
   needs a working balance and monitoring on that balance.

## Monitoring

Watch: container state and restart count, block height advancing versus a public
explorer, the Ethereum Sepolia endpoint's health, attestations actually landing
in each assigned window, attestor account balance, and disk free.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
