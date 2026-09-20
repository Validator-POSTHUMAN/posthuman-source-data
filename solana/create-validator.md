# Create a Solana Validator

On Solana there is no `create-validator` transaction. What makes a node a
validator is a **vote account** that points at your identity, plus a running
process that votes with that identity. This page covers the on-chain half.

Do every step here from a trusted workstation, not from the validator host. The
withdrawer keypair must never touch the server.

## 1. Fund the identity

The identity pays a fee for every vote transaction it sends — on the order of
**1.0–1.1 SOL per day** at current parameters. Treat it as a hot wallet: keep
weeks of runway on it, not years, and top it up from a cold wallet.

````bash
solana config set --url https://api.mainnet-beta.solana.com
solana config set --keypair ./validator-keypair.json
solana balance
````

## 2. Create the vote account

````bash
solana create-vote-account \
  --fee-payer ./validator-keypair.json \
  ./vote-account-keypair.json \
  ./validator-keypair.json \
  ./authorized-withdrawer-keypair.json
````

Argument order is vote account, then validator identity, then authorized
withdrawer. The withdrawer **must not** be the same key as the identity or the
vote authority; the CLI enforces this.

Add `--commission <percent>` to set commission at creation. Without it you get
the CLI default, which is almost certainly not what you want to advertise.

Read it back before doing anything else:

````bash
solana vote-account <vote-account-pubkey>
````

Move the withdrawer keypair to its permanent offline home now, while you still
remember where it is.

## 3. Set the BLS public key (SIMD-0387)

Voting validators must publish the BLS public key derived from their authorized
voter. Without it the validator cannot vote once the feature is active on the
cluster. Requires Solana CLI **4.1.0 or newer**.

Find the current authorized voter — for almost everyone it is the validator
identity:

````bash
solana vote-account <vote-account-pubkey> | grep "Vote Authority"
````

Inspect the BLS key the keypair derives locally, then publish it:

````bash
solana-keygen bls_pubkey ./validator-keypair.json

solana vote-authorize-voter-checked \
  <vote-account-pubkey> \
  ./validator-keypair.json \
  ./validator-keypair.json
````

Passing the same keypair twice does not rotate the voter; it fills in the BLS
public key for the voter you already have. Confirm:

````bash
solana vote-account <vote-account-pubkey> | grep "BLS Public Key"
````

No `BLS Public Key` line means it is not set. Do this **before** starting the
validator, and re-do it whenever you rotate the vote authority.

## 4. Keep the vote account funded — the admission ticket

Under Alpenglow the **Validator Admission Ticket (VAT)** is burned from the vote
account once per epoch. The ticket for epoch *E* is charged at the start of
epoch *E*, and it buys admission for epoch *E+1*. An underfunded vote account is
simply not admitted to vote or produce blocks in the next epoch.

The vote account must hold the rent-exempt minimum **plus** the next ticket:

| Target slot time | Approx. epoch | VAT per epoch |
|---|---|---|
| 400 ms (baseline) | 48 h | 1.6 SOL |
| 350 ms | 42 h | 1.4 SOL |
| 300 ms (current on mainnet-beta) | 36 h | 1.2 SOL |
| 250 ms (planned) | 30 h | 1.0 SOL |
| 200 ms (planned) | 24 h | 0.8 SOL |

Slot-time feature activations are delayed by one epoch, so the ticket charged at
a transition boundary still uses the previous stage's amount.

Commission revenue can refill the ticket, but it is **not** a guarantee: rewards
that arrive at an epoch boundary cannot rescue an account that was already short
when admission was evaluated. Pre-fund the first ticket, then alert on the vote
account balance like you alert on disk.

### Route commission to the vote account (SIMD-0232)

Inflation rewards already default to the vote account. Block revenue defaults to
the identity; pointing it at the vote account instead is what makes the VAT
self-funding. Both require the **authorized withdrawer** to sign:

````bash
solana vote-update-commission-collector \
  <vote-account-pubkey> block-revenue \
  <vote-account-pubkey> ./authorized-withdrawer-keypair.json

solana vote-update-commission-collector \
  <vote-account-pubkey> inflation-rewards \
  <vote-account-pubkey> ./authorized-withdrawer-keypair.json
````

Block-revenue changes made in epoch *E* take effect in *E+2*; inflation-rewards
changes in *E+1*. Verify with `solana vote-account`.

## 5. Start voting and confirm the network agrees

Start the validator (see the installation guide), then check what the cluster
sees — not what your host says:

````bash
solana gossip | grep <identity-pubkey>
solana validators | grep <identity-pubkey>
solana vote-account <vote-account-pubkey>
solana catchup <identity-pubkey>
````

The node is genuinely working only when all four hold:

- it appears in gossip;
- `delinquent` is **false**;
- `lastVote` and `rootSlot` advance between two samples taken a minute apart;
- `solana catchup` reports it caught up rather than an ever-growing gap.

## 6. Attract stake

A new validator with no delegation earns nothing and still pays vote fees. The
two normal routes:

- **Solana Foundation Delegation Program** — see the delegation programme page.
  It has explicit testnet and mainnet criteria and it is the usual first stake.
- **Stake pools** — Jito, Marinade, jpool, BlazeStake and others allocate stake
  algorithmically from published scoring. Read each pool's criteria before
  optimising for it; the metrics differ.

Self-stake helps credibility but does not change block production odds beyond
its weight.

## Common mistakes

| Mistake | Consequence |
|---|---|
| Withdrawer stored on the validator | one host compromise = permanent loss of the vote account |
| Withdrawer equals identity | rejected at creation; if worked around, no separation of duties at all |
| BLS public key never set | validator cannot vote once SIMD-0387 is active |
| Vote account funded to the rent minimum only | not admitted next epoch, silently |
| Commission changed without notice | delegators leave, and the change is public and permanent in history |
| Vote authority rotated without `--authorized-voter` overlap | missed votes across the epoch boundary |

Vote authority can change at most once per epoch and takes effect at the next
epoch boundary. Pass `--authorized-voter` twice — old and new — so the process
keeps voting across the switch.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
