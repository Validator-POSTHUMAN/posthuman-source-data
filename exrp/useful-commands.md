# XRPL EVM Mainnet — command sheet

Assumes `HOME=/var/lib/exrpd` and `--home /var/lib/exrpd/.exrpd`. Commands that
would sign, broadcast or move funds are marked and are **not** meant to be
pasted without review.

## Node state

```bash
exrpd version
exrpd status 2>&1 | jq '.sync_info'
curl -s http://127.0.0.1:26657/status  | jq '.result.sync_info'
curl -s http://127.0.0.1:26657/abci_info | jq -r '.result.response.version'
curl -s http://127.0.0.1:26657/net_info | jq -r '.result.n_peers'
```

## Agreement with the network

```bash
LOCAL=http://127.0.0.1:26657
REMOTE=https://cosmos-rpc.xrplevm.org
H=$(curl -s "$LOCAL/status" | jq -r .result.sync_info.latest_block_height)
curl -s "$LOCAL/block?height=$H"  | jq -r .result.block.header.app_hash
curl -s "$REMOTE/block?height=$H" | jq -r .result.block.header.app_hash
```

## Signing

```bash
# our consensus identity as the node itself reports it
curl -s "$LOCAL/status" | jq -r '.result.validator_info | {address, voting_power}'

# present in the latest commit?
ADDR=$(curl -s "$LOCAL/status" | jq -r .result.validator_info.address)
curl -s "$LOCAL/commit" \
  | jq -r --arg a "$ADDR" '[.result.signed_header.commit.signatures[].validator_address] | index($a) // "absent"'

# slashing view
curl -s https://rest.exrp.posthuman.digital/cosmos/slashing/v1beta1/signing_infos \
  | jq -r '.info[] | select(.address=="<ethmvalcons…>")'
```

## Validator set

```bash
exrpd query staking validators --limit 200 -o json \
  | jq -r '.validators[] | [.description.moniker, .status, .tokens] | @tsv'

exrpd query staking validator <ethmvaloper…> -o json | jq
curl -s "$LOCAL/validators?per_page=100" | jq -r '.result.total'
```

## Governance

```bash
exrpd query gov proposals --status voting_period -o json \
  | jq -r '.proposals[] | [.id, .status, (.messages[0]["@type"] // "")] | @tsv'
exrpd query gov proposal <id> -o json | jq
exrpd query gov tally <id> -o json | jq
```

Voting is a broadcast. See the Governance tab before running it.

## Upgrades

```bash
exrpd query upgrade plan          # {} means no plan scheduled
exrpd query upgrade applied <name>
ls -la /var/lib/exrpd/.exrpd/cosmovisor/upgrades/
cat /var/lib/exrpd/.exrpd/data/upgrade-info.json 2>/dev/null
```

## EVM side

Both of these speak to the same node.

```bash
EVM=https://rpc.exrp.posthuman.digital/evm

curl -s -X POST "$EVM" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# 0x15f900 = 1440000

curl -s -X POST "$EVM" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

curl -s -X POST "$EVM" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}'
```

The EVM block number and the CometBFT height are the same chain counted the
same way. If they disagree by more than a block, the EVM indexer is behind and
that is worth investigating.

## Address conversion

An account has one key and two representations: `ethm1…` on the Cosmos side and
`0x…` on the EVM side.

```bash
exrpd debug addr <ethm1…>
exrpd keys parse <ethm1…>
```

## Service control

```bash
sudo systemctl status exrpd --no-pager
sudo journalctl -u exrpd -f
sudo journalctl -u exrpd --since "10 min ago" | grep -iE 'err|panic|wrong|mismatch'
sudo systemctl restart exrpd     # restart, not start — start on a live unit is a no-op
```

## Keys — read-only

```bash
exrpd keys list --keyring-backend file
exrpd tendermint show-validator     # consensus public key
exrpd tendermint show-address       # ethmvalcons…
exrpd tendermint show-node-id
```

`exrpd keys export` and `exrpd keys add` write or reveal key material. Neither
belongs in a runbook paste.

## Disk

```bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh /var/lib/exrpd/.exrpd/data
du -sh /var/lib/exrpd/.exrpd/data/* | sort -h | tail
```

Check **all** mounts, not just `/`. A node home on a separate large volume
makes a full `/` look like a chain problem and vice versa.

## Commands that change state — review first

```bash
# BROADCASTS. Do not run from a runbook.
# exrpd tx staking create-validator ...
# exrpd tx gov vote <id> yes --from <key>
# exrpd tx slashing unjail --from <key>

# DESTRUCTIVE. Never on a signer home.
# exrpd tendermint unsafe-reset-all
```
