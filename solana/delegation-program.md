# Solana Delegation: SFDP and Stake Pools

A validator with no delegated stake earns nothing and still pays roughly 1 SOL a
day in vote fees plus the per-epoch admission ticket. Getting stake is therefore
not marketing — it is what makes the node viable. There are two realistic
sources: the **Solana Foundation Delegation Program** and **stake pools**.

## Solana Foundation Delegation Program (SFDP)

SFDP is the usual first stake for a new operator. It is also the strictest, and
its criteria are published and machine-checked every epoch.

### You must run testnet as well

A mainnet-beta delegation requires a **testnet node** meeting the same baseline.
The testnet node must pass all baseline criteria in **at least 5 of the last 10
testnet epochs**. Testnet participation is not optional and not a formality: it
is where onboarding position is earned.

### Criteria that decide eligibility

| Criterion | Requirement | Applies to |
|---|---|---|
| Vote credits | no more than **3% below the cluster average** for the epoch | mainnet + testnet |
| Commission | **≤ 5%** | mainnet only (no cap on testnet) |
| Skip rate | at most **network average + 5 percentage points** | mainnet + testnet |
| Total stake | **< 1,000,000 SOL** from all sources | mainnet only |
| Software version | at or above the enforced minimum, which moves 48 h after the supermajority adopts it | both, values differ per cluster |
| Metric reporting | continuous reporting to the Solana metrics server | enforced for nodes reporting as Agave; recognised Firedancer versions are exempt; **no reported version is not exempt** |
| Data-centre concentration | provider must hold **≤ 15%** of total staked network | mainnet, since 2026-05-01 |
| ASN / company concentration | ASN and hosting provider must hold **< 25%** of network stake | mainnet, since 2026-05-01 |
| Earned stake | must not go **10+ epochs** without receiving Foundation stake | mainnet: rejection; testnet: loss of onboarding number |

Concentration is tracked from `validators.app` data-centre and ASN views. When a
provider crosses the threshold, the Foundation removes delegations by
**seniority score** — lowest first — so the newest validator at a crowded
provider is the first to lose stake. Check the provider's existing concentration
**before** you sign a hosting contract; it is the one criterion you cannot fix
afterwards without moving the node.

### What this means operationally

- Keep commission at or below 5% on mainnet, and do not drift.
- Set `SOLANA_METRICS_CONFIG` on every Agave node on every cluster. Missing
  metrics is a silent eligibility failure.
- Track vote credits against the cluster average every epoch, not just
  delinquency. You can be non-delinquent and still fail the 3% rule.
- Upgrade promptly. The minimum version moves 48 hours after supermajority
  adoption, and testnet usually runs ahead of mainnet.
- Choose hosting for ASN diversity, not only for price.

Apply and track status through the Solana Foundation delegation programme pages;
the criteria page is the authoritative and frequently updated source.

## Stake pools

Pools allocate delegated SOL algorithmically across validators, and between them
they control a large share of staked supply. Each publishes its own scoring, and
the scores do **not** agree with each other or with SFDP.

| Pool | Token | Character |
|---|---|---|
| Jito | JitoSOL | MEV-oriented; scoring rewards MEV participation and performance |
| Marinade | mSOL + native staking | published Stake Auction Marketplace (SAM) bidding and a scored delegation strategy |
| BlazeStake | bSOL | permissionless-leaning allocation |
| jpool | jSOL | DAO-governed validator set |
| Sanctum-hosted LSTs | many | infrastructure for a long tail of pool tokens |

Common levers across pools: commission (both inflation and MEV), skip rate, vote
credits, version currency, self-stake, geographic and ASN diversity, and time in
the set. Several pools additionally run bidding or auction mechanics, where the
validator effectively quotes what it will pay for stake.

Two warnings worth stating plainly:

- **Optimising for a pool's score is a business decision, not an operational
  one.** Bidding for stake can be revenue-negative; read the mechanics before
  opting in.
- **Pool governance changes.** Validator sets and scoring are governed by DAOs
  or committees, and criteria have been changed with modest notice. Do not build
  a revenue plan on one pool's current formula.

## Self-stake and private delegation

Self-stake improves credibility and satisfies some pool scores, but it does not
change block-production odds beyond its weight. Private delegation — a treasury,
a DAO, a partner — is negotiated, not scored, and is the most stable stake a
validator can hold.

## Delegating to a validator

For a delegator, stake goes to the **vote account**, not to the identity:

````bash
solana create-stake-account stake-keypair.json <amount>
solana delegate-stake stake-keypair.json <vote-account-pubkey>
solana stake-account <stake-account-pubkey>
````

Stake activates at the next epoch boundary and deactivates the same way, with a
cooldown. Rewards are paid in the first block of the following epoch and are
proportional to vote credits earned.

````bash
solana stakes <vote-account-pubkey>          # who is delegated to this validator
solana inflation rewards <vote-account-pubkey> --rewards-epoch <epoch>
````

## Practical priority for a new validator

1. Get the **testnet** node clean and keep it clean — that is the SFDP gate.
2. Set commission ≤ 5% and publish metrics on both clusters.
3. Pick hosting with low ASN and data-centre concentration.
4. Apply to SFDP; track the criteria dashboard every epoch.
5. Only then look at pools, and read each one's scoring before changing
   anything about the node to satisfy it.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
