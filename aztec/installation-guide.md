# Aztec Sequencer Installation Guide
## Requirements
Linux or MacOS
CPU: 8 cores
RAM: 16 GB
SSD: 1 TB
Stable internet connection (≥ 25 Mbps)
Installation
Install Docker:
Docker installation guide

## Install Aztec tools:

````bash
bash -i <(curl -s https://install.aztec.network)
````

Update Aztec to the latest test version:

````bash
aztec-up -v latest
````

## Quick Start

Set environment variables:


export ETHEREUM_HOSTS=<Ethereum RPC URL>
export L1_CONSENSUS_HOST_URLS=<Consensus RPC URL>
export VALIDATOR_PRIVATE_KEY="0x<your private key>"
export COINBASE="0x<your reward address>"
export P2P_IP="<your public IP>"
Start the sequencer and archiver:


aztec start --node --archiver --sequencer --network alpha-testnet
Or with parameters:


aztec start --node --archiver --sequencer \
  --network alpha-testnet \
  --l1-rpc-urls $ETHEREUM_HOSTS \
  --l1-consensus-host-urls $L1_CONSENSUS_HOST_URLS \
  --sequencer.validatorPrivateKey $VALIDATOR_PRIVATE_KEY \
  --sequencer.coinbase $COINBASE \
  --p2p.p2pIp $P2P_IP
Register as a Validator
After your node is synced, run:


aztec add-l1-validator \
  --staking-asset-handler=0xF739D03e98e23A7B65940848aBA8921fF3bAc4b2 \
  --l1-rpc-urls $ETHEREUM_HOSTS \
  --l1-chain-id 11155111 \
  --private-key "0x<your private key>" \
  --attester "0x<your address>" \
  --proposer-eoa "0x<your address>"

  
Full guide: docs.aztec.network
Support: Aztec Discord
