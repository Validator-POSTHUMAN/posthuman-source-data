# XRP Ledger Validator Installation Guide

> **This tab is about a different network from the rest of this card.** The card
> is XRPL EVM — a Cosmos SDK sidechain running `exrpd`, with delegated
> proof-of-stake, `xrplevm_1440000-1` and everything else on the other tabs.
> This tab is the **XRP Ledger itself**, run with `rippled`: a different binary,
> a different consensus model, and no staking at all.
>
> They are published together because operators reach for one while thinking of
> the other. If you came here for node setup on the chain this card is named
> after, use the **installation guide** tab instead.

## Read this first: XRPL validators are not paid

The XRP Ledger has **no staking, no delegation, no block rewards and no
slashing**. Running a validator earns you nothing directly, and there is no
stake to bond or lose.

What decides whether your validator matters is completely different from a
proof-of-stake network: your influence comes only from other operators listing
your validating key in their **UNL** (Unique Node List). Most servers follow a
default list published by a trusted list publisher. A validator nobody lists is
a fully correct server that has no effect whatsoever on consensus.

So the real work of becoming a validator here is: run a reliable, well-behaved
server for a long time, publish who you are, and earn a place on published
lists. The installation below is the easy part.

## Two server roles

- **Stock server** (also called a tracking server): follows the ledger, answers
  API requests, relays transactions. This is what most operators actually need,
  and what you should run first.
- **Validator**: additionally signs proposals and validations with a validating
  key. A validator should not be the machine that serves your public API.

The recommended shape is a validator that peers through your own stock servers
rather than directly to the open internet. The stock servers absorb the public
traffic; the validator keeps a small, known peer set.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 8 cores | 8+ cores, high clock |
| RAM       | 16 GB   | 32 GB       |
| Disk      | 500 GB NVMe | 1 TB NVMe |
| Network   | 1 Gbps  | 1 Gbps, static IP |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

Disk is about history, not about the ledger being large today. A server with
default online deletion keeps a rolling window and stays in the hundreds of GB.
**Full history is multiple terabytes and keeps growing** — do not enable it
unless you specifically intend to run a history server.

## Install rippled

Install from the official repository so upgrades are ordinary package upgrades:

````bash
sudo apt -y update && sudo apt -y install apt-transport-https ca-certificates wget gnupg jq
wget -q -O - https://repos.ripple.com/repos/api/gpg/key/public | gpg --dearmor | sudo tee /usr/share/keyrings/ripple-key.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/ripple-key.gpg] https://repos.ripple.com/repos/rippled-deb $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/ripple.list
sudo apt -y update && sudo apt -y install rippled
rippled --version
````

At the time of writing the current release line is **3.3.0**. Check the version
you installed against what the network is actually running before going further
— see the verification section.

## Configure

The package installs `/opt/ripple/etc/rippled.cfg`. The parts that matter:

````ini
[server]
port_rpc_admin_local
port_peer
port_ws_admin_local

[port_rpc_admin_local]
port = 51234
ip = 127.0.0.1
admin = 127.0.0.1
protocol = http

[port_peer]
port = 51235
ip = 0.0.0.0
protocol = peer

[port_ws_admin_local]
port = 6006
ip = 127.0.0.1
admin = 127.0.0.1
protocol = ws

[node_size]
huge

[node_db]
type=NuDB
path=/var/lib/rippled/db/nudb
online_delete=2000
advisory_delete=0

[ledger_history]
2000
````

The validator list your server trusts is what defines "the network" for it, so
set it explicitly rather than relying on whatever a package default happens to
be. The mainnet publisher and its key, verified against the live list:

````ini
[validator_list_sites]
https://vl.ripple.com

[validator_list_keys]
ED2677ABFFD1B33AC6FBC3062B71F1E8397C1505E1C42C64D11AD1B28FF73F4734
````

Fetch `https://vl.ripple.com` yourself and compare the `public_key` field with
the value above before trusting either. A validator list key copied from a
forum post is a supply-chain decision, not a configuration detail.

`online_delete` and `ledger_history` together define your retention window.
Setting `ledger_history` to `full` is what turns a 500 GB server into a
multi-terabyte one.

Only `51235/tcp` faces the network. RPC and WebSocket admin ports stay on
`127.0.0.1`.

````bash
sudo ufw allow 22/tcp
sudo ufw allow 51235/tcp
sudo ufw enable
````

## Start and verify as a stock server

````bash
sudo systemctl enable --now rippled
rippled server_info | jq '.result.info | {build_version, server_state, complete_ledgers, peers, amendment_blocked}'
````

What to look for:
- `server_state`: `full` or `proposing`. Anything else means it is still
  syncing or has lost sync.
- `complete_ledgers`: an advancing range, not a stalled one.
- `peers`: a healthy double-digit count.
- `amendment_blocked`: **must be `false`**. See below.

Compare against a public server so you know your view matches the network:

````bash
curl -s -X POST https://xrplcluster.com/ -H 'content-type: application/json' \
  -d '{"method":"server_info","params":[{}]}' | jq '.result.info | {build_version, complete_ledgers}'
````

## Amendments: the failure that stops your server dead

XRPL upgrades through **amendments** that validators vote on. When an amendment
gains support and activates, servers too old to understand it become
`amendment_blocked` — they stop processing the ledger entirely. This is not a
degraded state, it is a stopped one.

Practical consequence: track amendment votes and upgrade **before** activation,
not after. Check regularly:

````bash
rippled feature | jq '.result.features | to_entries[] | select(.value.enabled==false and .value.supported==true) | {name: .value.name, vetoed: .value.vetoed}'
````

## Become a validator

The validating key is generated and kept **offline**. The server never holds the
master key — it holds a token derived from it. This is the most important
operational detail on this network.

On an **offline** machine, using the `validator-keys` tool:

````bash
validator-keys create_keys          # writes validator-keys.json - keep this OFFLINE
validator-keys create_token --keyfile validator-keys.json
````

`create_token` prints a `[validator_token]` block. Copy **only that block** into
`rippled.cfg` on the server and restart:

````ini
[validator_token]
eyJ2YWxpZGF0aW9uX3NlY3...
````

````bash
sudo systemctl restart rippled
rippled server_info | jq -r '.result.info.pubkey_validator, .result.info.server_state'
````

`server_state` should reach `proposing`. Keep `validator-keys.json` offline and
backed up: it is what lets you rotate the token if the server is ever
compromised, and rotating is the whole point of the token design.

## Publish who you are, then get listed

1. Set your domain in `rippled.cfg` and publish a `xrp-ledger.toml` at
   `https://<your-domain>/.well-known/xrp-ledger.toml` that claims your
   validating public key.
2. Verify the claim is visible on public validator registries.
3. Build a track record: high agreement with the consensus ledger, no missed
   validations, prompt amendment upgrades.
4. Then approach list publishers about inclusion.

Steps 3 and 4 are the ones that take months. Steps 1 and 2 take an afternoon.

## Monitoring

Watch: `server_state` staying `proposing`, `amendment_blocked` false, ledger
range advancing, peer count, agreement with the network's consensus ledger,
disk usage against your retention window, and — separately from the machine —
whether your key is present on the published lists you expect.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
