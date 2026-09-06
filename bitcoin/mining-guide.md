# Bitcoin Mining Setup Guide

## Mining is a different job from running a node

Running a full node verifies the chain. Mining **produces** blocks with proof of
work and is a hardware, power and heat business. The two are separate: you can
run a node without mining, and you can mine without running a node — though
mining without your own node means trusting someone else's view of the chain.

Set up the node first — see the full node guide on this card — then come back
here.

## Read the numbers before you buy anything

These are live mainnet figures, not illustrations:

- network hash rate: **≈ 1,038 EH/s** (1.04 × 10²¹ hashes per second)
- difficulty: **≈ 1.27 × 10¹⁴**

Expected time for a miner to find a block **on its own** is
`difficulty × 2³² ÷ your hash rate`. At the difficulty above that is about
5.47 × 10²⁶ hashes per block, which works out to:

| Your hardware | Hash rate | Expected time to a solo block |
|---|---|---|
| Bitaxe-class device | 1 TH/s | ~17 million years |
| One modern ASIC | 100 TH/s | ~170,000 years |
| Small farm | 1 PH/s | ~17,000 years |
| Serious operation | 100 PH/s | ~170 years |

This is not a reason never to solo mine — it is a lottery with a real jackpot
and people do win it — but it is the reason **pool mining** is what nearly
everyone does. A pool pays you a steady share proportional to the work you
submit instead of a jackpot you will statistically never see.

Two more facts worth accepting early:

- **CPU and GPU mining is dead on mainnet.** ASICs are roughly a billion times
  faster per watt. CPU miners are useful only on regtest or testnet, for
  learning the mechanics.
- **Electricity price decides profitability**, not hardware price. Work out
  your cost per kWh and your machine's J/TH before ordering anything.

## Path A — pool mining

The simplest working setup. You need no node at all: configure the ASIC's web
interface with the pool's Stratum URL, your worker name and password, and you
are mining.

````
Pool URL:  stratum+tcp://<pool-host>:<port>
Worker:    <your-account>.<machine-name>
Password:  x
````

Choose a pool on payout scheme (PPS vs PPLNS), fee, minimum payout and — worth
weighing — how centralising it is. If you already run a node, prefer a pool that
lets you supply your own block template.

## Path B — solo mining against your own node

Here your node builds the block templates, so you decide what goes into the
blocks you try to mine. You need a Stratum server between the ASIC and
`bitcoind`, because ASICs speak Stratum and `bitcoind` speaks
`getblocktemplate`.

### Prepare the node

Mining needs ZMQ notifications so the Stratum server learns about new blocks
immediately rather than by polling. Add to `bitcoin.conf`:

````
# ZMQ notifications for the stratum server, local only
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28333

# RPC for the stratum server, local only
server=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
````

Generate the RPC credential with the official helper and keep the password in
your secret store, never in a config you commit or a message you send:

````bash
python3 <(curl -sS https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py) miner
````

Restart and confirm the node is fully synced before mining — a node behind the
tip will hand out templates for a chain nobody else is on:

````bash
sudo systemctl restart bitcoind
bitcoin-cli getblockchaininfo | jq '{blocks, headers, initialblockdownload}'
bitcoin-cli getmininginfo
````

### Run a solo Stratum server

**CKPool in solo mode** is the standard choice:
`https://bitbucket.org/ckolivas/ckpool`

Build it, then write a config that points at your node and pays to **your**
address:

````json
{
  "btcd": [
    {
      "url": "127.0.0.1:8332",
      "auth": "miner",
      "pass": "<rpc-password-from-your-secret-store>",
      "notify": true
    }
  ],
  "btcaddress": "<your-bitcoin-address>",
  "btcsig": "/your-tag/",
  "serverurl": ["0.0.0.0:3333"],
  "mindiff": 1,
  "startdiff": 1000,
  "logdir": "/var/log/ckpool"
}
````

`btcaddress` is where the block reward goes if you win. Check it twice — a typo
here is the most expensive typo in this guide.

For Bitaxe-class hardware, **public-pool**
(`https://github.com/benjamin-wilson/public-pool`) is a friendlier
self-hosted alternative with a web dashboard, and it talks to the same node.

### Firewall

````bash
sudo ufw allow 3333/tcp   # only from your miners' network
````

Restrict `3333/tcp` to the LAN your ASICs are on. Your RPC port `8332` stays
closed to everything except localhost — the Stratum server is the only thing
that should touch it.

### Point the miner at your server

````
Pool URL:  stratum+tcp://<your-server-ip>:3333
Worker:    <your-bitcoin-address>.<machine-name>
Password:  x
````

## Verify it is really mining

On the Stratum server, watch for accepted shares from each worker. Shares are
the proof your hardware is doing real work against your templates — an ASIC
that connects but submits nothing is misconfigured, not unlucky.

On the node:

````bash
bitcoin-cli getmininginfo
bitcoin-cli getblocktemplate '{"rules":["segwit"]}' | jq '{height, previousblockhash, curtime}'
````

The template height must be the current tip plus one. If it is not, the node is
not synced and everything downstream is wasted work.

## Rehearse on regtest first

Before pointing real hardware anywhere, run the whole flow locally where blocks
are free and instant:

````bash
bitcoind -regtest -daemon
bitcoin-cli -regtest createwallet miner
ADDR=$(bitcoin-cli -regtest getnewaddress)
bitcoin-cli -regtest generatetoaddress 101 "$ADDR"
bitcoin-cli -regtest getbalance
````

This teaches you templates, coinbase maturity (100 blocks before a reward is
spendable) and reorgs in minutes, at zero cost.

## Operational care

- **Heat and power** are the real failure modes. One ASIC is a 3 kW space
  heater on a dedicated circuit; plan airflow, breakers and noise before
  delivery, not after.
- **Firmware**: run vendor firmware or a reputable alternative. Third-party
  firmware from unverified sources has repeatedly shipped hidden fee
  redirection — your hashrate silently paying someone else.
- **Payout address**: verify it on the device and in the pool account. Prefer
  an address whose keys you hold offline.
- **Monitoring**: hash rate per worker, accepted versus rejected shares, chip
  temperatures, fan health, power draw, and node sync state. A rising reject
  rate usually means network or overclock problems, not bad luck.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
