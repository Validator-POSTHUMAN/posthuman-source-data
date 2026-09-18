# Bitcoin Mining Setup Guide

## Mining is a different job from running a node

Running a full node verifies the chain. Mining **produces** blocks with proof of
work and is a hardware, power and heat business. The two are separate: you can
run a node without mining, and you can mine without running a node — though
mining without your own node means trusting someone else's view of the chain,
and it means someone else decides which transactions you work on.

Set up the node first — see the **Installation guide** — then come back here.

## Read the numbers before you buy anything

Live mainnet figures, measured 2026-09-18:

| | |
|---|---|
| Block height | 967,539 |
| Difficulty | 1.2745 × 10¹⁴ |
| Network hash rate | ≈ 954 EH/s (9.5 × 10²⁰ H/s) |
| Next retarget | height 967,680, estimated **+3.76 %** |
| Block subsidy | **3.125 BTC** |
| Next halving | block 1,050,000 — about 82,500 blocks away, roughly early 2028 |

Expected time for a miner to find a block **on its own** is
`difficulty × 2³² ÷ your hash rate`. At the difficulty above that is
5.47 × 10²³ hashes per block:

| Your hardware | Hash rate | Expected time to a solo block |
|---|---|---|
| Bitaxe-class device | 1 TH/s | ~17,300 years |
| One modern ASIC | 100 TH/s | ~173 years |
| Small farm | 1 PH/s | ~17 years |
| Serious operation | 100 PH/s | ~63 days |

A 1 TH/s device has roughly a 1-in-6,300,000 chance of finding a block on any
given day. This is not a reason never to solo mine — it is a lottery with a
real jackpot and people do win it, at these exact odds — but it is the reason
**pool mining** is what nearly everyone does. A pool pays a steady share
proportional to the work you submit instead of a jackpot you will statistically
never see.

Two more facts worth accepting early:

- **CPU and GPU mining is dead on mainnet.** ASICs are roughly a billion times
  faster per watt. CPU miners are useful only on regtest or signet, for
  learning the mechanics — see the **Testnets** guide.
- **Electricity price decides profitability**, not hardware price. Work out
  your cost per kWh and your machine's J/TH before ordering anything.

### The only economics that matter

````
daily revenue = (your TH/s ÷ network TH/s) × 144 blocks × (3.125 BTC + avg fees) × BTC price
daily power   = your TH/s × J/TH × 24 ÷ 1,000,000   kWh
daily cost    = daily power × your price per kWh
````

Run this with your own numbers before every purchase. A machine at 20 J/TH is
profitable at electricity prices where a 30 J/TH machine is not, and the
difference is not marginal. Difficulty has risen in all but a handful of
retargets — assume it keeps rising when you model payback.

Fee income is currently a rounding error: the mempool clears at 1 sat/vB, so
fees add well under 1 % to the subsidy. That is not a constant. After the 2028
halving the subsidy drops to 1.5625 BTC, and fee share becomes the difference
between a viable and a dead machine.

## Path A — pool mining

The simplest working setup. You need no node at all: configure the ASIC's web
interface with the pool's Stratum URL, your worker name and password, and you
are mining.

````
URL:      stratum+tcp://<pool-host>:<port>
Worker:   <account>.<rig-name>
Password: x
````

| Pool | Notes |
|---|---|
| [Ocean](https://ocean.xyz) | Non-custodial payouts; DATUM lets the miner build its own block templates |
| [Braiins Pool](https://braiins.com/pool) | FPPS, mature tooling, Braiins OS+ firmware integration, Stratum v2 |
| [public-pool](https://github.com/benjamin-wilson/public-pool) | Self-hostable open-source pool; the usual choice for home solo mining against your own node |
| [Solo CKPool](https://solo.ckpool.org) | Solo mining with a shared front end — find a block, keep the block |

Choosing a pool is choosing who constructs the block template — that is, who
decides which transactions get mined with your hash rate. Pools that let the
miner build the template (Ocean's DATUM, Stratum v2 job declaration) move that
decision back to you. For an infrastructure operator that is the interesting
difference between pools, not the fee schedule.

### Payout schemes, one line each

- **FPPS / PPS+** — the pool pays per share at a fixed rate and carries the
  variance. Predictable income, higher fee.
- **PPLNS** — you are paid out of blocks the pool actually finds, weighted by
  recent shares. Lower fee, more variance, penalises hopping.
- **Solo** — nothing until your hardware finds a block, then everything.

## Path B — solo mining against your own node

Solo mining is where a full node stops being optional: you construct the block
template yourself, so you need an unpruned, fully synced node with a healthy
mempool. ASICs speak Stratum and `bitcoind` speaks `getblocktemplate`, so a
Stratum server sits between them.

### Prepare the node

````ini
server=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
txindex=1
maxmempool=1000

# ZMQ so the stratum server hears about new blocks instead of polling
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28333

# v30.0+ defaults, stated explicitly because they decide template contents
blockmintxfee=0.001
datacarriersize=100000
````

`blocksonly=1` is incompatible with mining: an empty mempool means empty blocks
and no fee income.

Stratum servers to use: [public-pool](https://github.com/benjamin-wilson/public-pool)
(modern, web UI, designed for exactly this) or
[ckpool](https://bitbucket.org/ckolivas/ckpool) in solo mode (minimal, C, long
track record). Both point at the node's RPC and ZMQ, both hand your ASIC work
built from your own mempool.

### The IPC mining interface

Since v30.0 Core also exposes an experimental IPC interface intended for
Stratum v2 and similar clients:

````bash
bitcoin -m node -ipcbind=unix   # listen on a unix socket for IPC mining clients
````

v31.0 tightened it: clients must be built against the current `mining.capnp`
schema or `Init.makeMining` fails outright, and `createNewBlock` now waits for
IBD to finish and the tip to catch up before producing templates. Read the
release notes for your exact version before wiring anything to it — this
interface has changed in every release since it appeared.

## Path C — learning and testing

A Bitaxe (open-source, ~1 TH/s, ~15–20 W, silent) mining against your own
`public-pool` instance is the cheapest way to exercise the whole pipeline: node
→ template → stratum → hardware → share → block. On mainnet it is a lottery
ticket; on **signet or regtest** it is a working laboratory where you can mine
blocks on demand and test every downstream system. See the **Testnets** guide.

Hardware and firmware worth knowing:

| | |
|---|---|
| [Bitaxe](https://bitaxe.org) | Open-source single-ASIC miner, ESP32 control board, fully inspectable |
| [Braiins OS+](https://braiins.com/os) | Open firmware for Antminer S19/S21 — autotuning, measurably better J/TH |
| [Stratum v2](https://stratumprotocol.org) | Encrypted, authenticated stratum with miner-built templates |

## Operating a miner

| Signal | Watch for |
|---|---|
| Accepted vs rejected shares | rejection rate > 2 % means stale work, a bad network path, or an unstable overclock |
| Reported hash rate vs nameplate | a sustained shortfall is thermal throttling |
| Chip and intake temperature | dust, failing fans, ambient creep |
| Power draw at the wall | the only honest J/TH measurement |
| Pool-side worker status | a rig can look alive locally and be disconnected from the pool |
| Payout address | verify it after **every** firmware update — replacing it is the standard ASIC malware payload |

Firmware only from the vendor or a project you have verified, never from a
"performance unlock" download. Miners sit on the same LAN as everything else
and ship with weak default credentials: give them their own VLAN, change the
passwords, and never expose a miner's web interface to the internet.

## Sources

- [mempool.space REST API — live difficulty, hash rate, retarget](https://mempool.space/docs/api/rest)
- [bitcoincore.org — v31.0 release notes, IPC mining interface](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes, `bitcoin -m node -ipcbind`](https://bitcoincore.org/en/releases/30.0/)
- [academy.braiins.com — BTC mining setup](https://academy.braiins.com/en/braiins-pool/btc-mining-setup/)
- [bitaxe.org](https://bitaxe.org)
- [stratumprotocol.org — Stratum v2](https://stratumprotocol.org)
- [benjamin-wilson/public-pool](https://github.com/benjamin-wilson/public-pool)
