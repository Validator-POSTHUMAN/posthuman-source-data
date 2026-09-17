# NEAR Staking Pool: Creation, Ping and Proposals

On NEAR a validator does not "create a validator" with a chain transaction the
way a Cosmos SDK chain does. You deploy a **staking-pool smart contract**
through a factory, point your node at it with `validator_key.json`, and then
re-signal every epoch with `ping`.

| Network | Factory account | Pool name becomes |
|---------|-----------------|-------------------|
| mainnet | `poolv1.near` | `<name>.poolv1.near` |
| testnet | `pool.f863973.m0` | `<name>.pool.f863973.m0` |

Pool creation costs **30 NEAR** attached deposit (contract storage) plus gas.
That deposit is not a stake; it stays with the pool account.

## Prerequisites

1. `neard` fully synced — `syncing=false` and local height tracking a public
   endpoint. A proposal from an unsynced node produces missed chunks the moment
   the seat activates.
2. A NEAR account you control (the **pool owner**), funded with 30 NEAR plus
   gas plus the stake you intend to self-bond.
3. `near-cli-rs` and the validator extension installed.

```bash
npm install -g near-cli-rs@latest
npm install -g near-validator
near --version
```

## 1. Generate the staking key pair

The staking key is the key `neard` uses to sign as the pool. Generate it
offline; it never needs to be a full-access key on any account.

```bash
near generate-keypair save-to-file ~/near-staking-key.json
```

Keep the file `0600` and back it up outside the host. See the **Keys &
custody** guide before you continue.

## 2. Deploy the staking pool

`reward_fee_fraction` is your commission. `7/100` is 7%.

```bash
export OWNER=<owner-account>.near
export POOL=<pool-name>            # becomes <pool-name>.poolv1.near
export STAKE_PUBKEY=ed25519:<public-key-from-step-1>

near contract call-function as-transaction poolv1.near create_staking_pool \
  json-args "{\"staking_pool_id\": \"$POOL\",
              \"owner_id\": \"$OWNER\",
              \"stake_public_key\": \"$STAKE_PUBKEY\",
              \"reward_fee_fraction\": {\"numerator\": 7, \"denominator\": 100}}" \
  prepaid-gas '300.0 Tgas' \
  attached-deposit '30 NEAR' \
  sign-as "$OWNER" \
  network-config mainnet \
  sign-with-keychain \
  send
```

The call succeeds when the receipt outcome returns `true`. Confirm the pool
exists before moving on:

```bash
near contract call-function as-read-only "$POOL.poolv1.near" get_owner_id \
  json-args '{}' network-config mainnet now
```

## 3. Install `validator_key.json`

`neard` reads `~/.near/validator_key.json` at startup. The `account_id` must be
the **full pool account**, not the owner account, and the field is `secret_key`
— not `private_key`.

```json
{
  "account_id": "<pool-name>.poolv1.near",
  "public_key": "ed25519:<public-key>",
  "secret_key": "ed25519:<secret-key>"
}
```

```bash
install -m 0600 /dev/null ~/.near/validator_key.json
# write the JSON above into it, then:
sudo systemctl restart neard
```

A running `neard` does not pick up a new or changed `validator_key.json`.
`systemctl start` on an already-active unit is a no-op — use `restart`, then
confirm the key was loaded:

```bash
journalctl -u neard -n 50 --no-pager | grep -i 'validator\|signer'
```

## 4. Deposit and stake

Any account can delegate. This is the self-bond from the owner:

```bash
near contract call-function as-transaction "$POOL.poolv1.near" deposit_and_stake \
  json-args '{}' \
  prepaid-gas '300.0 Tgas' \
  attached-deposit '<amount> NEAR' \
  sign-as "$OWNER" \
  network-config mainnet \
  sign-with-keychain \
  send
```

## 5. Ping every epoch

`ping` does two things: it re-submits the staking proposal, and it updates
delegator reward accounting on the pool contract. Skip it and reported
delegator rewards go stale and your seat is not re-proposed.

```bash
near contract call-function as-transaction "$POOL.poolv1.near" ping \
  json-args '{}' \
  prepaid-gas '300.0 Tgas' \
  attached-deposit '0 NEAR' \
  sign-as "$OWNER" \
  network-config mainnet \
  sign-with-keychain \
  send
```

An epoch is ~12 h. Automate it on a timer that runs more often than that —
every 6 h is a safe cadence, and a duplicate ping is harmless.

```ini
# /etc/systemd/system/near-ping.service
[Unit]
Description=Ping NEAR staking pool

[Service]
Type=oneshot
User=near
ExecStart=/usr/local/bin/near-ping.sh
```

```ini
# /etc/systemd/system/near-ping.timer
[Unit]
Description=Ping NEAR staking pool every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:05:00
Persistent=true

[Install]
WantedBy=timers.target
```

Give the ping signer its own **function-call access key** restricted to the
pool contract, not a full-access key. See **Keys & custody**.

## 6. Verify the proposal

Proposals apply two epochs out: signal now, seat in ~3 epochs.

```bash
near-validator proposals network-config mainnet
near-validator validators network-config mainnet now
near-validator validators network-config mainnet next
```

Your pool should appear with `Proposal(Accepted)`, then in `next`, then in
`now`. Cross-check on
[nearblocks.io/node-explorer](https://nearblocks.io/node-explorer) and
[near-staking.com/stats](https://near-staking.com/stats).

Raw RPC, no CLI required:

```bash
curl -s -X POST https://rpc.mainnet.near.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq --arg p "$POOL.poolv1.near" '
      {epoch_height: .result.epoch_height,
       me: (.result.current_validators[] | select(.account_id==$p)
            | {stake: .stake, is_slashed: .is_slashed,
               blocks: "\(.num_produced_blocks)/\(.num_expected_blocks)",
               chunks: "\(.num_produced_chunks)/\(.num_expected_chunks)",
               endorsements: "\(.num_produced_endorsements)/\(.num_expected_endorsements)"})}'
```

## Commission changes

```bash
near contract call-function as-transaction "$POOL.poolv1.near" update_reward_fee_fraction \
  json-args '{"reward_fee_fraction": {"numerator": 5, "denominator": 100}}' \
  prepaid-gas '300.0 Tgas' \
  attached-deposit '0 NEAR' \
  sign-as "$OWNER" \
  network-config mainnet \
  sign-with-keychain \
  send
```

Fee increases on the standard staking-pool contract take effect after a delay
and are visible on-chain to delegators. Announce them before you send the
transaction.

## Rotating the staking key

A staking key rotation is a two-step change and both steps must land, in order:

1. `update_staking_key` on the pool with the new public key.
2. Replace `validator_key.json` on the node and `restart neard`.

Doing only step 1 leaves the node signing with a key the pool no longer
recognises. Doing only step 2 leaves the node signing for a key the pool never
accepted. Either way you stop producing. Do this at the start of an epoch, not
near its boundary, and verify with `validators ... now` before the next epoch.

## Reward and fee withdrawal

The pool's commission is not paid out automatically. In the standard
staking-pool contract it accrues as owner stake inside the pool and compounds
until the owner explicitly unstakes and withdraws it:

```bash
# owner's own balance inside the pool
near contract call-function as-read-only "$POOL.poolv1.near" get_account \
  json-args "{\"account_id\": \"$OWNER\"}" network-config mainnet now
```

Unstaking enters a 4-epoch (~2 day) unbonding period before `withdraw` works.
Confirm which account actually holds the withdraw authority before sending
anything — it is not necessarily the node host's key.

## Read-only pool queries

```bash
near contract call-function as-read-only "$POOL.poolv1.near" get_total_staked_balance json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL.poolv1.near" get_reward_fee_fraction   json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL.poolv1.near" get_staking_key           json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL.poolv1.near" get_number_of_accounts    json-args '{}' network-config mainnet now
```

## Sources

- [near-nodes.io — compile and run a node](https://near-nodes.io/validator/compile-and-run-a-node)
- [docs.near.org — validator staking](https://docs.near.org/protocol/network/staking)
- [docs.near.org — NEAR CLI](https://docs.near.org/tools/cli)
- [near/core-contracts — staking-pool](https://github.com/near/core-contracts/tree/master/staking-pool)
