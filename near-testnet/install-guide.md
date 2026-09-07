# NEAR Testnet Validator Installation Guide

## About NEAR testnet

NEAR testnet mirrors mainnet's mechanics: `neard` runs the node, validators are
selected each epoch by a **stake auction**, and a validator that misses the
seat price simply does not validate that epoch. Testnet is the right place to
learn that rhythm, because the seat price moves and being dropped from the
validator set is a normal event rather than an incident.

Differences from mainnet:

- test NEAR comes from the faucet, and the seat price is far lower;
- the staking-pool factory and the chain suffix differ — pools are created under
  the testnet factory and validator accounts end in `.testnet`;
- epochs are the same length in blocks, so the feedback loop for "did my change
  work" is still measured in hours, not minutes.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 8 cores | 8+ cores, high clock |
| RAM       | 20 GB   | 32 GB       |
| Disk      | 500 GB SSD | 1 TB NVMe |
| Network   | 1 Gbps  | 1 Gbps      |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

## Prepare the host

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install build-essential pkg-config libssl-dev clang llvm jq curl unzip
````

## Install neard

Build the release tag that testnet is currently running, or use the official
binary for that tag. Record the exact version — `neard --version` is the first
thing anyone will ask when a node misbehaves:

````bash
neard --version
````

## Initialise for testnet

````bash
neard --home ~/.near init --chain-id testnet --download-genesis --download-config
````

The chain ID is what decides which network you joined. Confirm it in
`~/.near/genesis.json` and `~/.near/config.json` before starting — a node
initialised with the wrong chain ID will run perfectly and be on the wrong
network.

## Sync from a snapshot

Syncing testnet from genesis is impractical. Use an official or reputable
community snapshot for the **testnet** chain, and move any existing `data`
directory aside instead of deleting it, so a bad snapshot is a rollback rather
than a restart:

````bash
mv ~/.near/data ~/.near/data.pre-snapshot-$(date -u +%Y%m%dT%H%M%SZ)
````

## Run as a service

````bash
sudo tee /etc/systemd/system/neard.service > /dev/null <<'EOF'
[Unit]
Description=NEAR testnet node
After=network-online.target
Wants=network-online.target

[Service]
User=near
Type=simple
ExecStart=/usr/local/bin/neard --home /home/near/.near run
Restart=on-failure
RestartSec=30
KillSignal=SIGINT
TimeoutStopSec=45
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now neard
````

## Open the P2P port

````bash
sudo ufw allow 22/tcp
sudo ufw allow 24567/tcp
sudo ufw enable
````

Keep the RPC port (`3030`) bound locally.

## Verify

````bash
curl -s http://127.0.0.1:3030/status | jq '{chain_id, sync_info: {latest_block_height: .sync_info.latest_block_height, syncing: .sync_info.syncing}, version}'
````

Compare your height against a public testnet RPC:

````bash
curl -s -X POST https://rpc.testnet.near.org -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' | jq -r .result.sync_info.latest_block_height
````

## Create the validator key and staking pool

1. Generate the validator key so that its account ID is your pool account:

````bash
neard --home ~/.near init --account-id <your-pool>.pool.f863973.m0 --chain-id testnet
````

2. Fund a testnet account from the faucet.
3. Deploy a staking pool through the testnet staking-pool factory, setting your
   commission.
4. Put the validator public key into `~/.near/validator_key.json` and restart.
5. Stake, then wait: you validate from the epoch in which your stake clears the
   seat price, not from the moment you stake.

## Verify you are actually in the set

````bash
curl -s -X POST https://rpc.testnet.near.org -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq '.result.current_validators[] | select(.account_id=="<your-pool>") | {stake, num_produced_blocks, num_expected_blocks}'
````

`num_produced_blocks` close to `num_expected_blocks` is the real health signal.
A validator in the set that produces far fewer blocks than expected is being
penalised on its reward, and the cause is usually the host, not the chain.

## Monitoring

Watch: service state and restart count, block height against a public RPC, chain
ID, whether you are in the current validator set, produced versus expected
blocks, seat price against your stake, and disk free.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
