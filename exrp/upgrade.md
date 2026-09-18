# XRPL EVM Mainnet upgrades

Two different things are called an upgrade here, and conflating them is the
main source of mistakes.

| | Consensus-breaking upgrade | Patch release |
|---|---|---|
| Example | `v10.1` at height `6856000` | `v10.2.0` → `v10.2.1` |
| Gate | an on-chain plan at a block height | none |
| Coordination | the whole validator set switches at the same block | roll whenever you like |
| Where it is announced | Networks table, governance proposal | GitHub releases only |
| Missing it | your node halts or forks | you run an older patch than everyone else |

## Mainnet upgrade history

| Upgrade | Height | Date | Version |
|---|---|---|---|
| Genesis | 0 | 2025-04-25 | `v7.0.0` |
| v8 | 497000 | 2025-05-28 | `v8.0.2` |
| v9 | 4688681 | 2026-02-26 | `v9.0.3` |
| v10 | 4749000 | 2026-03-02 | `v10.0.2` |
| v10.1 | 6856000 | 2026-07-20 | `v10.1.0` |

Source: <https://docs.xrplevm.org/pages/operators/resources/networks>

## The Networks table lags patches

Verified 2026-09-18: that table names `v10.1.0` as the current mainnet version,
while `cosmos-rpc.xrplevm.org` reports `10.2.1` and an independent ITRocket node
reports `10.2.0` — at the same height and the same app hash. `v10.2.0` and
`v10.2.1` are `cosmos/evm` dependency bumps, not forks, so no plan and no table
row ever appeared for them.

Consequence: **read the fleet, not only the table.**

```bash
curl -s https://cosmos-rpc.xrplevm.org/abci_info | jq -r .result.response.version
curl -s https://xrplevm-mainnet-rpc.itrocket.net/abci_info | jq -r .result.response.version
curl -s http://127.0.0.1:26657/abci_info | jq -r .result.response.version
```

If the first two agree with each other and disagree with yours, you are behind
a patch. That is not an emergency, but a `cosmos/evm` hotfix line is exactly
where you do not want to be the last node running the old code.

## The v11 line is not mainnet

`v11.x` tags exist and run on devnet and testnet. Do not install them on
mainnet before the mainnet upgrade proposal passes and the Networks table gains
its row. A testnet schedule is not a mainnet schedule.

## Check for a pending on-chain plan

```bash
exrpd query upgrade plan --node http://127.0.0.1:26657
```

`{}` means no plan is scheduled. It does **not** mean there is nothing to do —
patch releases never appear here.

## Validator-safe sequence

1. Verify the release and its checksum at
   <https://github.com/xrplevm/node/releases>. Never install an artifact whose
   `checksums.txt` line you have not checked.
2. Record the current height, the running version and signer state.
3. Download and checksum the target artifact **while the node is online**.
4. Prove no second process and no second host can sign with the same
   `priv_validator_key.json`. This is the anti-double-sign check and it comes
   before any service action.
5. Stage the binary:
   - Cosmovisor: `cosmovisor/upgrades/<exact-plan-name>/bin/exrpd`, the name
     taken from the on-chain plan, not guessed;
   - plain systemd: install the new binary and keep the old one for rollback.
6. For a consensus-breaking upgrade, let the node reach the height and switch;
   for a patch, `stop` then `start` at a time you choose.
7. Verify: version, chain ID, height advancing, peers connected, and the
   validator present in `last_commit`.

```bash
exrpd version
curl -s http://127.0.0.1:26657/status | jq '.result.sync_info, .result.validator_info'
```

## `systemctl start` on an already-active service is a no-op

After replacing a binary or a `priv_validator_key.json`, use `restart`, or
`stop` followed by `start`. A `start` against a running unit returns success
and changes nothing. Symptoms of getting this wrong: `voting_power=0`, a
height that does not move, and your `valcons` address absent from
`last_commit`.

## Rollback

Keep the previous binary and the pre-upgrade `data/` until the node has signed
for a sustained period on the new version. Never restore
`priv_validator_state.json` from a snapshot or an older backup — rolling that
file backwards is how a double-sign happens.
