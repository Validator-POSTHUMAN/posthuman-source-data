# XRP Ledger Testnet Node Installation Guide

> **Not to be confused with XRPL EVM testnet.** This card is the XRP Ledger
> Testnet, run with `rippled`. XRPL EVM testnet is a separate Cosmos-based
> sidechain with its own card and its own binary.

## About the XRPL Testnet

The Testnet (also called Altnet) runs the same `rippled` software as mainnet
with worthless test XRP from a faucet. It is the right place to:

- rehearse the validator setup, including the offline key and token flow;
- test an application against real ledger semantics;
- see how an amendment behaves before it reaches mainnet — testnet and devnet
  get amendments first, which is exactly why they are worth watching.

The install is the mainnet procedure. This page states the deltas.

## Requirements

Testnet is lighter than mainnet because its history is far shorter:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8 cores     |
| RAM       | 8 GB    | 16 GB       |
| Disk      | 200 GB NVMe | 500 GB NVMe |
| Network   | 100 Mbps | 1 Gbps     |

## Install

Identical to mainnet — the same package, the same binary:

````bash
sudo apt -y install rippled
rippled --version
````

At the time of writing Testnet runs the **3.3.0** release line, the same as
mainnet, while Devnet runs a newer release candidate. Confirm before you deploy:

````bash
curl -s -X POST https://s.altnet.rippletest.net:51234/ -H 'content-type: application/json' \
  -d '{"method":"server_info","params":[{}]}' | jq -r '.result.info.build_version'
````

## Point the config at the Testnet

This is the only change that decides which network you join. Replace the
mainnet hub and validator list in `rippled.cfg`:

````ini
[ips]
s.altnet.rippletest.net 51235

[network_id]
testnet

# Testnet validator list publisher - not the mainnet one
[validator_list_sites]
https://vl.altnet.rippletest.net

[validator_list_keys]
ED264807102805220DA0F312E71FC2C69E1552C9C5790F6C25E3729DEB573D5860
````

Using the mainnet `[ips]` or the mainnet validator list on a testnet server is
the classic mistake here: the server starts, syncs nothing useful, and looks
merely slow rather than misconfigured.

Start and confirm the network:

````bash
sudo systemctl restart rippled
rippled server_info | jq '.result.info | {build_version, server_state, complete_ledgers, peers, network_id}'
````

Cross-check your ledger range against the public Testnet server:

````bash
curl -s -X POST https://s.altnet.rippletest.net:51234/ -H 'content-type: application/json' \
  -d '{"method":"server_info","params":[{}]}' | jq -r '.result.info.complete_ledgers'
````

The Testnet ledger index is in the tens of millions and starts well above zero,
because the network has been reset in the past. A range that starts at your own
sync point is normal; a range that does not advance is not.

## Get test XRP

The official Testnet faucet funds an account with test XRP. You need a funded
account before you can send anything, because XRPL requires a **reserve** —
accounts do not exist until funded, and that trips up first-time users far more
often than any node problem.

## Rehearse the validator flow

Do the whole offline-key exercise here before you do it on mainnet:

````bash
validator-keys create_keys
validator-keys create_token --keyfile validator-keys.json
````

Put only the `[validator_token]` block on the server, restart, and confirm:

````bash
rippled server_info | jq -r '.result.info.pubkey_validator, .result.info.server_state'
````

Then practise the part that actually matters in an incident: **rotate the
token** from the offline key file and confirm the server picks up the new
identity. A rotation you have never performed is not a recovery plan.

## Note on validator lists

Testnet has its own list publisher, and being on it says nothing about mainnet.
Testnet is for proving your operational process, not for building mainnet
reputation.

## Monitoring

Same signals as mainnet: `server_state`, `amendment_blocked`, advancing ledger
range, peers, disk against the retention window. On testnet, also watch for
amendments arriving here first — that is the early warning for what mainnet will
require of you next.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
