# SFDP on Testnet

Testnet is not a rehearsal for the Solana Foundation Delegation Program — it is
half of it. A mainnet-beta delegation is contingent on a **testnet node** that
meets the baseline criteria, and the testnet node is where your position in the
onboarding queue is earned and lost.

## The gate

Your testnet node must meet **all baseline criteria in at least 5 of the latest
10 testnet epochs** for the mainnet node to receive a delegation.

## Criteria, and how testnet differs from mainnet

| Criterion | Testnet | Mainnet |
|---|---|---|
| Vote credits | no more than **3% below cluster average** | same |
| Skip rate | at most **network average + 5 pp** | same |
| Software version | enforced minimum — **usually newer than mainnet** | enforced minimum |
| Metric reporting | required (Agave-reporting nodes; recognised Firedancer versions exempt; unreported version is **not** exempt) | same |
| Commission | **no cap** | ≤ 5% |
| Total stake | **no cap** | < 1,000,000 SOL |
| Data-centre / ASN concentration | not enforced | enforced (≤15% DC, <25% ASN) |
| Earned stake | 10+ epochs without stake → **lose your onboarding number**, go to the bottom of the queue | 10+ epochs without stake → rejected from the programme |

The consequence asymmetry is the thing to internalise: on mainnet inattention
gets you removed, on testnet it sends you to the back of a queue you may have
spent months climbing.

## Why testnet is harder than it looks

- **Testnet runs newer software.** The minimum enforced version moves 48 hours
  after the supermajority adopts it, and testnet adopts first. An upgrade
  cadence that is comfortable on mainnet will fail here.
- **Testnet is stress-tested deliberately.** Synthetic load is sometimes heavier
  than mainnet. Vote credits and skip rate are graded against the cluster
  average, so a slow host is visible immediately.
- **Cluster restarts and ledger resets happen.** Following a restart
  announcement promptly — new shred version, sometimes a new snapshot — is part
  of the job. A node left on the old shred version scores nothing and looks
  healthy while doing it.
- **Metrics are a silent failure.** The testnet `SOLANA_METRICS_CONFIG` differs
  from mainnet's. Setting the wrong one fails the criterion without any local
  symptom.

## Client consistency

The client you run on testnet is expected to match the client you run on
mainnet. This matters if you are evaluating a fork or an orderflow stack: you
cannot pilot it on the existing SFDP testnet validator. A pilot needs a
**separate, non-staked** testnet validator with its own identity.

## Running the testnet node well

- Fund the identity from the faucet before it runs dry — voting costs fees here
  too, and an unfunded identity stops voting.
- Alert on the same signals as mainnet: delinquency, slot distance, vote credits
  versus cluster average, skip rate, identity balance, disk.
- Keep the upgrade turnaround short. Track the feature-gate schedule and upgrade
  ahead of activation epochs, not after them.
- Do not reuse the mainnet identity keypair. One identity, one running process,
  per cluster.
- Watch your standing every epoch rather than monthly; the 5-of-10 window is
  short enough that two bad epochs matter.

## Where to check status

- Criteria — <https://solana.org/delegation-criteria>
- Testnet validator view — <https://www.validators.app/?network=testnet>
- Feature-gate schedule — <https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule>

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
