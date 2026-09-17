# Mina Block Producer

A block producer is a synced daemon that has been given a private key. There is
no registration transaction, no bond, no validator object on chain and no
minimum stake — your chance of winning a slot is simply your share of the stake
that delegates to your public key.

There is also no slashing and no jailing. Missing a slot costs you that block's
reward and nothing else. What it does cost, over time, is delegators.

## Enable block production

**systemd** — add to `EXTRA_FLAGS` in `~/.mina-env`:

````
EXTRA_FLAGS="--block-producer-key /home/YOUR_USER/keys/my-wallet"
MINA_PRIVKEY_PASS="your-key-password"
````

````bash
systemctl --user restart mina
````

**Docker** — add to the daemon command:

````
--block-producer-key /keys/my-wallet
````

with `MINA_PRIVKEY_PASS` in the container environment.

`--block-producer-key` is deprecated in favour of the `MINA_BP_PRIVKEY`
environment variable, which takes the same path. Both work on 4.0.0. Never pass
both `--block-producer-key` and `--block-producer-pubkey` — the daemon refuses
to start.

### Send rewards somewhere else

````
--coinbase-receiver $COLD_PUBLIC_KEY
````

Without it, coinbase goes to the producing key — your hot wallet. With it,
rewards accumulate directly in cold storage and the hot wallet stays at a
minimal balance, which is the entire point of the hot/cold split. Transaction
fees and SNARK fees are unaffected by this flag.

## Verify it is actually producing

````bash
mina client status
````

````
Block producers running:        1 (B62q...)
Coinbase receiver:              Block producer
Next block will be produced in: in 7.077h for slot: ...
````

- `Block producers running: 0` on a synced node means the key was not loaded —
  check the password and the file permissions, in that order.
- `Next block will be produced in:` is the VRF's answer for the current epoch.
  If it is absent, you have no won slots this epoch. With a small stake that is
  normal and not a fault.

Your own node's opinion is not proof that a block landed. Confirm from outside:

- `https://minascan.io/mainnet/validator/<YOUR_PUBLIC_KEY>/delegations`
- `https://minataur.net/account/<YOUR_PUBLIC_KEY>`

## Stake latency — the thing that confuses everyone

Mina decides the current epoch's stake from a ledger snapshot taken **two
epochs earlier**. Concretely:

- A new delegation to you changes nothing today. It does not change your block
  production this epoch, and usually not the next one either.
- Docs describe the delay as 1–2 epochs for a delegation change and 2–4 weeks
  in wall-clock terms. Since the Mesa upgrade an epoch is about **7.44 days**
  (7140 slots × 90 s), so the wall-clock figure in older material is roughly
  double the current reality. Always compute it from live parameters rather
  than quoting a blog post.
- Nothing is wrong with your node when a fresh delegation produces no change.

Read the current parameters and epoch position from any node:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { consensusTimeNow { epoch slot globalSlot } consensusConfiguration { slotDuration slotsPerEpoch epochDuration } } }"}' | jq
````

## Know your real stake

The explorer's view is convenient and occasionally behind. The authoritative
number is in the staking ledger your own node holds:

````bash
mina ledger export staking-epoch-ledger > staking-ledger.json
````

Sum the balances of every account whose `delegate` is your public key:

````bash
jq --arg pk "$YOUR_PUBLIC_KEY" '
  [ .[] | select(.delegate == $pk) | (.balance | tonumber) ] | add
' staking-ledger.json
````

`next-epoch-ledger` is the same export for the epoch that is about to become
active — that is where a recent delegation shows up first.

## Redundancy

Running two nodes with the same block producer key is **safe on Mina**. There is
no equivocation penalty, and the delegation program states outright that you may
run more than one node on the same key to improve your odds of staying online.
Both nodes will independently win the same slots and produce the same block;
the network accepts one.

This is the opposite of the Cosmos rule, and it is the single most important
difference to internalise if you operate both. What it does not excuse:

- two nodes on the same **libp2p** key — that genuinely breaks connectivity;
- assuming the spare is healthy. An unmonitored standby is not redundancy.

## Empty blocks and the reward floor

````
--minimum-block-reward AMOUNT
````

When a won slot's available transactions and SNARK work would leave a reward
below `AMOUNT`, the daemon produces an **empty** block instead of paying for
SNARK work it cannot recover. Default is no threshold. Setting it is a
deliberate economic choice: it protects against loss-making blocks, and it also
removes those blocks' transaction throughput from the network. Decide, record the
decision, and keep the value consistent across your fleet — a divergent value on
one host makes block-by-block comparisons meaningless.

## Delegator payouts

Mina pays block rewards to the producer, not to delegators. There is no on-chain
distribution. If you accept delegation you have taken on a manual, off-chain
payout obligation. Publish your fee and schedule *before* accepting delegation,
and treat each batch as an operation with a fresh preflight — an automated
payout loop signing from an unlocked key is a standing risk that is hard to
bound. See the **Delegation program** guide for the Foundation's specific rules,
deadlines and required tooling.

## Related guides

- **Keys** — hot/cold split, what the producer key can do
- **Monitoring** — proving production rather than assuming it
- **Delegation program** — uptime scoring and payout obligations
- **SNARK worker** — the second earning role, independent of block production

## Sources

- [docs.minaprotocol.com — block producers](https://docs.minaprotocol.com/node-operators/block-producer-node)
- [docs.minaprotocol.com — block producer getting started](https://docs.minaprotocol.com/node-operators/block-producer-node/getting-started)
- [docs.minaprotocol.com — hot and cold block production](https://docs.minaprotocol.com/node-operators/block-producer-node/hot-cold-block-production)
- [docs.minaprotocol.com — staking and snarking](https://docs.minaprotocol.com/node-operators/validator-node/staking-and-snarking)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
