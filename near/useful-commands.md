# NEAR Operator Command Sheet

`POOL` is the full pool account (`<name>.poolv1.near`), `OWNER` is the pool
owner account. Set them once:

```bash
export POOL=<name>.poolv1.near
export OWNER=<owner>.near
export RPC=http://127.0.0.1:3030
```

## Service

```bash
sudo systemctl status neard --no-pager
sudo systemctl restart neard          # required after any validator_key.json change
journalctl -u neard -f
journalctl -u neard -n 500 --no-pager | grep -iE 'error|panic|fatal'
neard --version
```

`systemctl start` on an already-active unit is a no-op. After replacing
`validator_key.json`, always `restart`.

## Node status

```bash
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{version: .result.version.version,
         protocol: .result.protocol_version,
         height: .result.sync_info.latest_block_height,
         syncing: .result.sync_info.syncing}'

# peers
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"network_info","params":[]}' \
  | jq '{active: (.result.active_peers | length), num: .result.num_active_peers}'

# gas price
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"gas_price","params":[null]}' \
  | jq '.result.gas_price'
```

## Validator state

```bash
near-validator validators network-config mainnet now
near-validator validators network-config mainnet next
near-validator proposals network-config mainnet
```

Raw RPC, current epoch, your pool only:

```bash
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq --arg p "$POOL" '
      {epoch_start: .result.epoch_start_height,
       seat_price_candidates: (.result.current_proposals | length),
       me: (.result.current_validators[] | select(.account_id==$p) |
            {stake, is_slashed,
             blocks: "\(.num_produced_blocks)/\(.num_expected_blocks)",
             chunks: "\(.num_produced_chunks)/\(.num_expected_chunks)",
             endorsements: "\(.num_produced_endorsements)/\(.num_expected_endorsements)"})}'
```

Kickout reasons for the previous epoch:

```bash
curl -s -X POST "$RPC" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq '.result.prev_epoch_kickout'
```

## Pool contract — read only

```bash
near contract call-function as-read-only "$POOL" get_total_staked_balance json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL" get_reward_fee_fraction   json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL" get_staking_key           json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL" get_owner_id              json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL" get_number_of_accounts    json-args '{}' network-config mainnet now
near contract call-function as-read-only "$POOL" get_account json-args "{\"account_id\": \"$OWNER\"}" network-config mainnet now
```

## Pool contract — transactions

Every one of these signs with the owner key. Read **Keys & custody** first.

```bash
# ping — every epoch
near contract call-function as-transaction "$POOL" ping json-args '{}' \
  prepaid-gas '300.0 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER" network-config mainnet sign-with-keychain send

# self-bond
near contract call-function as-transaction "$POOL" deposit_and_stake json-args '{}' \
  prepaid-gas '300.0 Tgas' attached-deposit '<amount> NEAR' \
  sign-as "$OWNER" network-config mainnet sign-with-keychain send

# commission change
near contract call-function as-transaction "$POOL" update_reward_fee_fraction \
  json-args '{"reward_fee_fraction": {"numerator": 5, "denominator": 100}}' \
  prepaid-gas '300.0 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER" network-config mainnet sign-with-keychain send

# unstake / withdraw (4-epoch unbonding between them)
near contract call-function as-transaction "$POOL" unstake_all json-args '{}' \
  prepaid-gas '300.0 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER" network-config mainnet sign-with-keychain send

near contract call-function as-transaction "$POOL" withdraw_all json-args '{}' \
  prepaid-gas '300.0 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER" network-config mainnet sign-with-keychain send
```

## Accounts and keys

```bash
near account view-account-summary "$OWNER" network-config mainnet now
near account list-keys "$OWNER" network-config mainnet now
near generate-keypair save-to-file ~/new-key.json
near account delete-key "$OWNER" ed25519:<public-key> network-config mainnet sign-with-keychain send
```

## Capacity

```bash
df -h | grep -v 'tmpfs\|udev\|loop'     # check every mount, not just /
free -h
du -sh ~/.near/data
```

## Config

```bash
jq '{archive, save_trie_changes, rpc: .rpc.addr, store: .store.path,
     cold_store: .cold_store.path, boot_nodes: (.network.boot_nodes | length)}' \
  ~/.near/config.json
```

Back up `config.json` before editing it, and restart `neard` afterwards.
