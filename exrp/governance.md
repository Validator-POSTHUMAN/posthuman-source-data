# XRPL EVM Mainnet governance

Governance on XRPL EVM does two jobs that are worth separating.

| | Chain governance | Validator-set governance |
|---|---|---|
| What it decides | parameters, upgrades, spending | who is in the validator set |
| Where | `x/gov` proposals on chain | Proof of Authority vote, 7 days |
| Where you watch it | <https://governance.xrplevm.org/proposals> | the same explorer, plus Discord |
| Your obligation | vote on every proposal | respond to questions, stay active |

For a Proof of Authority network, not voting is itself a signal. The advisory
board explicitly counts upgrade voting and governance participation among the
contributions expected from the set, and inactive validators have been removed
before.

## Watching proposals

```bash
exrpd query gov proposals --status voting_period -o json \
  | jq -r '.proposals[] | [.id, .status, (.messages[0]["@type"] // "")] | @tsv'

exrpd query gov proposal <id> -o json | jq
exrpd query gov tally <id> -o json | jq
```

Over REST, with no local node:

```bash
curl -s 'https://rest.exrp.posthuman.digital/cosmos/gov/v1/proposals?proposal_status=2' \
  | jq -r '.proposals[] | [.id, .status, .voting_end_time] | @tsv'
```

`proposal_status=2` is `PROPOSAL_STATUS_VOTING_PERIOD`.

## Upgrade proposals deserve a different reading

A software-upgrade proposal is the only kind that will stop your node if you
ignore it. Read three fields and record them:

- **plan name** — this is the exact directory name Cosmovisor expects under
  `cosmovisor/upgrades/<name>/bin/`. Guessing it is the most common way to
  turn a routine upgrade into an outage.
- **height** — when it happens, in blocks, not in dates.
- **the release it names** — check the tag exists and its checksum, before
  voting rather than after.

```bash
exrpd query upgrade plan          # {} when nothing is scheduled
cat /var/lib/exrpd/.exrpd/data/upgrade-info.json 2>/dev/null
```

Then stage the binary. Voting yes and not staging is worse than voting no.

## Voting

**This broadcasts a transaction from your operator key.** Shown for shape, to
be run deliberately:

```bash
# REVIEW BEFORE RUNNING — broadcasts
# exrpd tx gov vote <proposal_id> yes \
#   --from <key_name> --keyring-backend file \
#   --chain-id xrplevm_1440000-1 \
#   --gas auto --gas-adjustment 1.3 --gas-prices 0.25axrp
```

Options are `yes`, `no`, `abstain`, `no_with_veto`. `no_with_veto` is not a
stronger `no`; it is a claim that the proposal is spam or abusive, and it
carries a deposit penalty for the proposer. Use it accordingly.

Confirm the vote landed rather than assuming the broadcast means it did:

```bash
exrpd query gov vote <proposal_id> <ethm1…> -o json | jq
```

## Parameters

```bash
exrpd query gov params -o json | jq
exrpd query staking params -o json | jq
exrpd query slashing params -o json | jq
```

`slashing params` is the one to read before an upgrade window: it tells you how
many blocks you may miss in the signed-blocks window before jailing, which
turns "how long can this take?" from a guess into a number.

## Keys

The operator key that votes is the same key that controls the validator. It
belongs in `--keyring-backend file` or on hardware, and preferably not on the
validator host at all. A governance vote is a good reason to use a separate
machine with the keyring on it and the node reached over RPC:

```bash
exrpd tx gov vote ... --node https://rpc.exrp.posthuman.digital:443
```
