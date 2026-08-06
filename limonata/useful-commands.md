# Limonata Testnet — Useful Commands

Replace `LIMONATA_HOME` if your node uses a non-default home directory.

```bash
export LIMONATA_HOME="$HOME/.limonatad"
export LIMONATA_RPC="http://127.0.0.1:26657"
export OFFICIAL_RPC="https://cosmos-rpc.limonata.xyz"
```

## Version and service

```bash
limonatad version --long
systemctl is-active limonatad.service
systemctl is-enabled limonatad.service
sudo journalctl -u limonatad.service --since '15 minutes ago' --no-pager
```

## Sync status

```bash
curl -fsS "$LIMONATA_RPC/status" | jq '.result.sync_info | {
  latest_block_height,
  latest_block_time,
  catching_up
}'

curl -fsS "$OFFICIAL_RPC/status" | jq '.result.sync_info | {
  latest_block_height,
  latest_block_time,
  catching_up
}'
```

Compare both heights after 30 seconds. A healthy node advances and eventually
reports `catching_up: false`.

## Peer count

```bash
curl -fsS "$LIMONATA_RPC/net_info" | jq '{n_peers: .result.n_peers}'
```

## Chain identity

```bash
curl -fsS "$LIMONATA_RPC/status" | jq -r '.result.node_info.network'
limonatad status --home "$LIMONATA_HOME" 2>&1 |
  jq '.node_info.network, .sync_info.catching_up'
```

Expected Cosmos chain ID: `limonata_10777-1`. The EVM chain ID is `10777`.

## Validator state

Run this only for a validator you operate:

```bash
limonatad query staking validator <cosmosvaloper...> \
  --node "$OFFICIAL_RPC" --output json |
  jq '.validator // . | {status, jailed, tokens, moniker: .description.moniker}'
```

Do not expose local RPC, REST, gRPC, EVM RPC, metrics, or pprof merely to run
these checks. Loopback access is sufficient.

## Read-only DKG verification

Discover the latest finalized DKG epoch from the indexed official RPC:

```bash
DKG_HEIGHT=$(curl -fsS -G "$OFFICIAL_RPC/block_search" \
  --data-urlencode 'query="encmempool_dkg_finalized.epoch EXISTS"' \
  --data-urlencode 'per_page=1' \
  --data-urlencode 'order_by="desc"' \
  | jq -r '.result.blocks[0].block.header.height')

curl -fsS "$OFFICIAL_RPC/block_results?height=$DKG_HEIGHT" |
  jq '.result.finalize_block_events[] |
    select(.type == "encmempool_dkg_finalized") |
    {type, attributes: (.attributes | from_entries)}'
```

The fixed v0.3.6 milestone proof is epoch `26` at height `1655054`. Expected
values are threshold `186`, QUAL indexes `1..16`, and threshold public key
`02d908f0cd0cabf50ed2901cd195d4185a6c4d41f30e2cf8f0c9324b9c9c38140b`:

```bash
curl -fsS "$OFFICIAL_RPC/block_results?height=1655054" |
  jq '.result.finalize_block_events[] |
    select(.type == "encmempool_dkg_finalized" and
           any(.attributes[]; .key == "epoch" and .value == "26")) |
    .attributes | from_entries'
```

## Read-only encrypted-execution proof

The outer encrypted submit transaction succeeded at height `1655967`. Public
state exposes ciphertext metadata, epoch `26`, sequence `1`, and decrypt
height `1655977`, but not the signed inner EVM transfer:

```bash
OUTER=D60D10216EC9839B2B16025146E63673CD7E8E7C2CC224A46F57A9E096FF62C0
curl -fsS "$OFFICIAL_RPC/tx?hash=0x$OUTER&prove=false" |
  jq '{height: .result.height,
       code: .result.tx_result.code,
       encrypted_events: [.result.tx_result.events[] |
         select(.type == "encmempool_encrypted_submitted") |
         (.attributes | from_entries)]}'
```

At height `1655978`, 256 shares were consumed and the inner transaction was
executed once in BeginBlock:

```bash
curl -fsS "$OFFICIAL_RPC/block_results?height=1655978" |
  jq '[.result.finalize_block_events[] |
    select(.type == "encmempool_dkg_ve_consumed" or
           .type == "encmempool_tx_reinjected") |
    {type, attributes: (.attributes | from_entries)}]'
```

Expected inner hash:
`0x9f20ef9aaa126baaa7fb8b5e123294ffcbfba6817515c7c869a9ad0c69300841`.
It has no ordinary EVM receipt, while the recipient balance changes from zero
to exactly 3 LIMO across the historical block range:

```bash
EVM_RPC=https://rpc.limonata.xyz
INNER=0x9f20ef9aaa126baaa7fb8b5e123294ffcbfba6817515c7c869a9ad0c69300841
RECIPIENT=0xC0FFEE0000000000000000000000000000000042

curl -fsS -H 'content-type: application/json' \
  --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$INNER\"]}" \
  "$EVM_RPC" | jq '.result'

for BLOCK in 0x19449e 0x1944aa; do
  curl -fsS -H 'content-type: application/json' \
    --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBalance\",\"params\":[\"$RECIPIENT\",\"$BLOCK\"]}" \
    "$EVM_RPC" | jq -r --arg block "$BLOCK" '[$block, .result] | @tsv'
done
```

Expected output is `null` for the receipt and balances `0x0` then
`0x29a2241af62c0000`.

## Read-only IBC recovery proof

```bash
OFFICIAL_REST=https://rest.limonata.xyz
curl -fsS "$OFFICIAL_REST/ibc/core/client/v1/client_status/07-tendermint-0" |
  jq '{status}'
curl -fsS "$OFFICIAL_REST/ibc/core/channel/v1/channels/channel-0/ports/transfer" |
  jq '.channel | {state, counterparty}'
```

Expected state is client `Active`, channel `STATE_OPEN`, and counterparty
`channel-11808`. Packet sequence `4` was sent at height `1663139` and received
a successful acknowledgement at `1663143`:

```bash
for HEIGHT in 1663139 1663143; do
  curl -fsS "$OFFICIAL_RPC/block_results?height=$HEIGHT" |
    jq --arg height "$HEIGHT" '[.result.txs_results[]?.events[] |
      select(.type == "send_packet" or .type == "acknowledge_packet") |
      {height: $height, type, attributes: (.attributes | from_entries)}]'
done
```

These commands are verification-only. They do not sign or broadcast an
encrypted transaction.
