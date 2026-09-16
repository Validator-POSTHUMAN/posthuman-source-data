# Create a Starknet validator

Starknet staking is entirely **onchain**: there is no validator key file, no
genesis registration and no consensus keypair. You become a validator by
locking STRK in the Staking contract from an account you control, then running
a full node and an attestation service that prove you follow the chain.

> Read [Security](/networks/starknet/guides/security) **before** you send the
> first transaction. The account layout you choose here is the one you will
> live with; changing addresses later costs transactions and, for the staking
> address, is not possible at all.

## Protocol parameters

| Parameter | Mainnet | Sepolia |
|---|---|---|
| Minimum validator stake | 20,000 STRK | 1 STRK |
| Epoch length | 1132 blocks | 231 blocks |
| Epoch duration | ~3600 s | ~1200 s |
| Attestation window | 50 blocks | 30 blocks |
| Unstake lockup | 7 days | 5 minutes |
| Change latency (k) | 1 epoch | 1 epoch |
| BTC weight in staking power (α) | 0.25 | 0.25 |

Rewards are **all-or-nothing per epoch**: attest in the epoch and you receive
the full epoch reward for your staking power; miss it and you receive nothing
for that epoch. There is no slashing of principal in the current phase — the
cost of downtime is forfeited yield, for you and for your delegators.

## Contract addresses

### Mainnet

| Contract | Address |
|---|---|
| Staking | `0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7` |
| Attestation | `0x10398fe631af9ab2311840432d507bf7ef4b959ae967f1507928f5afe888a99` |
| Minting curve | `0x00ca1705e74233131dbcdee7f1b8d2926bf262168c7df339004b3f46015b6984` |
| L2 reward supplier | `0x009035556d1ee136e7722ae4e78f92828553a45eed3bc9b2aba90788ec2ca112` |
| STRK token | `0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d` |

Stakable BTC wrappers on mainnet: WBTC
`0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac`,
SolvBTC `0x0593e034dda23eea82d2ba9a30960ed42cf4a01502cc2351dc9b9881f9931a68`,
tBTC `0x04daa17763b286d1e59b97c283c0b8c949994c361e426a28f743c67bdfe9a32f`,
LBTC `0x036834a40984312f7f7de8d31e3f6305b325389eaeea5b1c0664b2fb936461a4`.

### Sepolia

| Contract | Address |
|---|---|
| Staking | `0x03745ab04a431fc02871a139be6b93d9260b0ff3e779ad9c8b377183b23109f1` |
| Attestation | `0x03f32e152b9637c31bfcf73e434f78591067a01ba070505ff6ee195642c9acfb` |
| STRK token | `0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d` |

The authoritative list, including the current set of BTC wrappers, is the
Staking contract's `get_active_tokens` function and the
[Starknet chain information](https://docs.starknet.io/learn/cheatsheets/chain-info#staking)
page. Verify addresses against it before every mainnet transaction.

## Account layout

The protocol deliberately separates three validator addresses. Use three
distinct accounts — this is the single most important security decision in the
whole procedure.

| Address | Used for | Custody |
|---|---|---|
| **Staking** | `stake`, `increase_stake`, `unstake_intent`, `unstake_action`, commission and pool settings | Cold. Holds the whole stake. Hardware wallet or multisig. |
| **Rewards** | receives `claim_rewards` payouts | Cold. Never used by any service. |
| **Operational** | signs `attest` transactions every epoch | Hot. Lives on the validator host. Keep only gas in it. |

Consequences worth internalising:

- The operational key is online 24/7 by design. If it leaks, an attacker cannot
  move your stake, but they can stop your attestations and burn your gas —
  rotate it with `change_operational_address`.
- If the operational account uses **local signing**, it must be a deployed and
  **unprotected** account: no Ready Wallet Guardian, no Braavos hardware
  signer. Those protections block the automated attestation signature.
  Use a remote signer if you need protected custody.
- The staking address cannot be changed. Choose it once, correctly.

## Prerequisites

1. A synced full node — [Installation guide](/networks/starknet/guides/installation-guide).
2. `sncast` from [Starknet Foundry](https://foundry-rs.github.io/starknet-foundry/starknet/sncast-overview.html),
   or [Starkli](https://book.starkli.rs/), or a wallet-driven block explorer.
3. Three deployed accounts as above, the staking account funded with at least
   the minimum stake plus fees.

```bash
export STAKING_ADDRESS=<your staking account address>
export REWARDS_ADDRESS=<your rewards account address>
export OPERATIONAL_ADDRESS=<your operational account address>
export STAKING_CONTRACT=0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7
export STRK=0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d
```

The examples below use `--network mainnet`; swap in `--network sepolia` and the
Sepolia addresses to rehearse the whole flow on testnet first. Rehearse it.

## Step 1 — Approve the STRK transfer

The Staking contract pulls STRK from your staking account, so it needs an
allowance first. STRK has 18 decimals: 20,000 STRK is
`20000000000000000000000`.

```bash
sncast --account=staker invoke \
  --contract-address=$STRK \
  --function=approve \
  --arguments=$STAKING_CONTRACT,20000000000000000000000 \
  --network=mainnet
```

## Step 2 — Stake

`stake` takes the rewards address, the operational address and the amount.
The amount must match the approved allowance.

```bash
sncast --account=staker invoke \
  --contract-address=$STAKING_CONTRACT \
  --function=stake \
  --arguments=$REWARDS_ADDRESS,$OPERATIONAL_ADDRESS,20000000000000000000000 \
  --network=mainnet
```

Check both addresses character by character before broadcasting. A typo in the
rewards address sends every future payout to an account you do not control.

## Step 3 — Set commission

Commission is expressed with a precision of 10,000 = 100%. `100` is 1%,
`500` is 5%.

```bash
sncast --account=staker invoke \
  --contract-address=$STAKING_CONTRACT \
  --function=set_commission \
  --arguments=500 \
  --network=mainnet
```

To raise commission later you must first publish a ceiling and an expiry epoch
with `set_commission_commitment`. Until that commitment expires you may move
freely inside `[0, M]` but never above `M`. Delegators read this as your
commission policy — set the commitment deliberately, not as an afterthought.

## Step 4 — Open a delegation pool

A separate pool contract is deployed per stakable token. Call
`set_open_for_delegation` once per token you want to accept.

```bash
# STRK pool
sncast --account=staker invoke \
  --contract-address=$STAKING_CONTRACT \
  --function=set_open_for_delegation \
  --arguments=$STRK \
  --network=mainnet

# Example: WBTC pool
sncast --account=staker invoke \
  --contract-address=$STAKING_CONTRACT \
  --function=set_open_for_delegation \
  --arguments=0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac \
  --network=mainnet
```

BTC delegation carries weight α = 0.25 in staking power and is paid in STRK.
Opening BTC pools widens your delegator base beyond STRK holders; it does not
require any change to your node or attestation setup.

## Step 5 — Verify

```bash
sncast call \
  --contract-address=$STAKING_CONTRACT \
  --function=get_staker_info_v1 \
  --arguments=$STAKING_ADDRESS \
  --network=mainnet
```

The response contains, in order: a success flag, rewards address, operational
address, stake, validator index, unclaimed rewards, pool flag, pool stake,
pool unclaimed rewards, pool commission (`0x64` = 100 = 1%).

Confirm three things before you consider registration done:

1. The stake is the amount you intended, in FRI (wei-equivalent) units.
2. The rewards and operational addresses are exactly the accounts you control.
3. The commission matches your published policy.

## Step 6 — Start attesting

Registration alone earns nothing. Bring up the attestation service against
your synced node — [Validator attestation](/networks/starknet/guides/validator-attestation) —
and confirm a confirmed attestation in the current epoch before you consider
the validator live. Then wire the alerts from
[Monitoring](/networks/starknet/guides/monitoring).

Because of the `k = 1` epoch latency, your stake becomes effective in the
epoch **after** the one in which you staked. Rewards begin from that epoch.

## Ongoing operations

| Operation | Function | Called from | Notes |
|---|---|---|---|
| Claim validator rewards | `claim_rewards` | staking or rewards address | Paid to the rewards address. No lockup. |
| Add stake | `increase_stake` | staking address | Needs a fresh `approve` first. |
| Change rewards address | `change_reward_address` | staking address | Takes effect immediately. |
| Change operational address | `declare_operational_address` then `change_operational_address` | new operational address, then staking address | Two-step by design. Restart the attestation service with the new key. |
| Raise commission ceiling | `set_commission_commitment` | staking address | Publishes max commission and expiry epoch. |
| Open another pool | `set_open_for_delegation` | staking address | One call per token. |
| Signal exit | `unstake_intent` | staking address | Starts the 7-day lockup. Rewards stop. |
| Complete exit | `unstake_action` | staking address | Only after the lockup elapses. |

### Rotating the operational key

1. Deploy the new operational account and fund it with gas.
2. From the **new** operational address, call `declare_operational_address`
   with your staking address.
3. From the **staking** address, call `change_operational_address` with the new
   operational address.
4. Restart the attestation service with the new private key.
5. Verify a confirmed attestation in the next epoch before deleting the old key.

Do not skip step 5. A rotation that silently breaks signing is indistinguishable
from a healthy service until the epoch reward does not arrive.

### Exiting

`unstake_intent` stops rewards immediately and starts a 7-day lockup; funds are
only withdrawable with `unstake_action` afterwards. Announce the exit to your
delegators first — their funds follow their own pool exit procedure and their
rewards also stop.

## Reference

- Starknet docs — [Becoming a validator](https://docs.starknet.io/secure/quickstart/becoming-a-validator)
- Starknet docs — [Staking protocol](https://docs.starknet.io/learn/protocol/staking)
- [`starknet-staking` contracts and spec](https://github.com/starkware-libs/starknet-staking/blob/main/docs/spec.md)
- [SNIP 28 — Staking V2](https://community.starknet.io/t/snip-28-staking-v2-proposal/115250)
- [SNIP 31 — Bitcoin staking on Starknet](https://community.starknet.io/t/bitcoin-staking-on-starknet/115696)
