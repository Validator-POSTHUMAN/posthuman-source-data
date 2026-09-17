# Mina Delegation Program and Delegator Payouts

Mina pays block rewards to the **producer**, not to delegators. There is no
on-chain distribution, no commission field and no automatic split. Every payout
on Mina is an off-chain obligation that someone has to execute and be trusted to
execute correctly.

Two things are covered here, and they are not the same:

1. The **Mina Foundation Delegation Program** — the Foundation delegates its
   tokens to selected block producers, who must return most of the rewards
   under specific rules.
2. **Ordinary delegator payouts** — what you owe the people who chose you.

There is also a separate o1Labs delegation program with its own policy. The
rules below are the Foundation's.

## Foundation program: how it works

The Foundation delegates to a set of block producers. You keep **8%** of the
staking rewards attributable to that delegation and return the rest. Selection
happens quarterly — a *delegation cycle* — based on your Performance Score and
the published policy.

### Step 1 — apply

Review the Mina Foundation Delegation Policy and complete the application form.
You submit the public key that would receive the delegation.

### Step 2 — run the uptime tracking system

This is the part that is operational rather than administrative, and the part
people get wrong.

The sidecar tracker was **discontinued on 14 June 2024**. Anything describing a
separate uptime sidecar container is obsolete. The current system is
SNARK-work-based and built into the daemon (3.0.0+): no keypair import, just
flags.

`~/.mina-env`:

````
EXTRA_FLAGS="--block-producer-key /home/YOUR_USER/keys/my-wallet \
             --uptime-submitter-key /home/YOUR_USER/keys/my-wallet \
             --uptime-url https://uptime-backend.minaprotocol.com/v1/submit"
UPTIME_PRIVKEY_PASS="your-key-password"
MINA_PRIVKEY_PASS="your-key-password"
LOG_LEVEL=Info
FILE_LOG_LEVEL=Debug
````

````bash
systemctl --user restart mina
````

Under Docker, pass the same three flags on the daemon command line and set both
password variables in the container environment.

`UPTIME_PRIVKEY_PASS` must be **its own line**, not folded into `EXTRA_FLAGS`.
That single mistake produces a node that looks perfectly healthy and scores
zero.

`--uptime-submitter-key` takes a private key path exactly like
`--block-producer-key`; most operators point both at the same key, so
submissions are attributed to the producer's public key.

### Step 3 — KYC/AML

Only if you are selected. You are contacted with instructions; you cannot
complete this step in advance.

## Performance Score

- Uptime is measured in **20-minute windows**. Online at any point in a window
  counts as online for the whole window.
- The score is the percentage of all windows over a rolling **90 days**.
- You may run **more than one node on the same block producer key** to improve
  your odds of staying online. Mina has no double-signing penalty, so this is an
  explicitly sanctioned strategy.

Track it:

- Official: <https://uptime.minaprotocol.com>
- Community: <https://minataur.net/uptime>

Treat a falling score as an incident. It is a lagging indicator over 90 days, so
by the time the number looks bad the damage is already several weeks old.

## Payout obligation

If you receive a Foundation delegation:

- **Tooling is mandatory.** Use the latest
  [`jrwashburn/mina-pool-payout`](https://github.com/jrwashburn/mina-pool-payout)
  script. It handles the return-address mapping, the calculation and the memo
  format.
- **Addresses** come from the published Mina Delegation Program Return Addresses
  mapping document. Do not invent a destination.
- **Memo**: every payment's memo must carry the **MD5 hash of your block
  producer public key**. This is how payments are attributed; an unmarked
  payment is how you get flagged delinquent while having actually paid.
- **Frequency**: at least once per epoch.
- **Deadline**: rewards for epoch *N* must be **accepted in a block** — not
  merely broadcast — by **slot 3,500 of epoch N+1**. Since the Mesa upgrade a
  slot is 90 seconds, so slot 3,500 is roughly **3.6 days** into the next epoch,
  about half of the ~7.44-day epoch. Older material describing this as "about
  half a week" was written when slots were three minutes. Compute the wall-clock
  deadline from live consensus parameters each time.
- The canonical chain for this purpose is taken as **12 blocks behind the tip**
  at slot 3,500.

### How the amount is computed

Per epoch:

1. Total stake delegated to your account for the epoch.
2. `provider_share = provider_delegation / total_stake` (between 0 and 1).
3. For each block you produced on the canonical chain with a non-zero block
   reward, the calculation is based on a **360 MINA** coinbase.
4. `payout = provider_share * 0.92 * 360` per such block — the 0.92 being your
   8% fee retained.
5. Send to the mapped address with the MD5 memo; where applicable also send the
   correct amount to the burn address.

Transaction fees are yours. You may keep them or split them with the pool — that
is your published policy, not a program rule.

The authoritative implementation is
`PayoutCalculatorIsolateSuperCharge.ts` in the payout repository. When your
spreadsheet and the script disagree, the script is right.

## Paying ordinary delegators

Nothing above applies to delegators who simply chose you. What applies instead:

- **Publish your terms before accepting delegation**: fee percentage, payout
  cadence, what happens to transaction and SNARK fees, and what happens if you
  miss a block. Delegators cannot be slashed and cannot be locked in — your only
  retention mechanism is being predictable.
- **Compute from the staking ledger**, not from an explorer. Export it from your
  own synced node:

````bash
mina ledger export staking-epoch-ledger > staking-ledger.json
jq --arg pk "$YOUR_PUBLIC_KEY" '
  [ .[] | select(.delegate == $pk) | (.balance | tonumber) ] | add
' staking-ledger.json
````

  Each delegator's share is their balance in that ledger divided by the total.
  The ledger is fixed for the epoch, so the denominator does not move under you.
- **Remember the two-epoch delay.** A delegator who joined this epoch was not in
  the ledger that determined this epoch's rewards and is owed nothing for it.
  Say so in your published terms or you will have the argument once per month.
- **Treat every batch as an operation.** Fresh preflight, explicit confirmation
  of the exact epochs being paid, and a dry run before broadcasting. An
  automated payout loop with an unlocked key is a standing risk that is hard to
  bound — POSTHUMAN deliberately keeps Mina payouts manual and gated for this
  reason.
- **Keep the evidence.** Epoch, ledger hash, per-delegator amounts and
  transaction hashes. Payout disputes are settled with records, not memory.

Community tooling worth knowing: `mina-pool-payout` for the calculation,
public payout simulators for delegator-facing comparisons, and an archive node
if you want your own reward history rather than an explorer's — see
**Archive node**.

## Related guides

- **Block producer** — stake latency and proving production
- **Monitoring** — treating the uptime score as a monitored signal
- **Keys** — why the uptime submitter key matters
- **Archive node** — building your own reward history

## Sources

- [docs.minaprotocol.com — delegation program](https://docs.minaprotocol.com/node-operators/delegation-program)
- [docs.minaprotocol.com — Foundation delegation program](https://docs.minaprotocol.com/node-operators/delegation-program/foundation-delegation-program)
- [docs.minaprotocol.com — uptime tracking system](https://docs.minaprotocol.com/node-operators/delegation-program/uptime-tracking-system)
- [minaprotocol.com — Mina Foundation Delegation Policy](https://minaprotocol.com/blog/mina-foundation-delegation-policy)
- [github.com/jrwashburn/mina-pool-payout](https://github.com/jrwashburn/mina-pool-payout)
