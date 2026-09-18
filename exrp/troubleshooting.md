# XRPL EVM Mainnet troubleshooting

Ordered by how often each one is the actual cause, not by how dramatic it
looks.

## App hash mismatch on a fresh node

```
ERR  wrong Block.Header.AppHash  expected=... got=...
panic: Failed to process committed block
```

**Check `client.toml` before anything else.**

```bash
grep chain-id /var/lib/exrpd/.exrpd/config/client.toml
```

`xrplevm_144000-1` — six digits — produces deterministic app-hash divergence
during bootstrap even when the genesis file and the binary are both correct.
The correct value is `xrplevm_1440000-1`, seven digits. Leaving the field unset
also works. This has cost real hours; it is the first thing to rule out.

Second cause: `evm-chain-id` unset or wrong in `app.toml`. It must be
`1440000` on mainnet, and it has been mandatory since v10.

Third cause: the wrong binary for the height being replayed. Check the upgrade
table and the version your peers report.

## Node is "running" but the height does not move

```bash
curl -s http://127.0.0.1:26657/net_info | jq -r .result.n_peers
```

- **0–2 peers**: the address book is stale or `persistent_peers` is empty.
  Stop, delete `config/addrbook.json`, refresh peers from `peers.txt`, start.
- **Normal peer count, height still flat**: compare your app hash against an
  independent RPC. If it differs you are on a different chain and no amount of
  waiting fixes it — restore from a snapshot.
- **Disk full.** Check every mount, not `/`.

## `catching_up` never becomes false

Normal for a genesis sync; it can take days. If you did not intend a genesis
sync, you probably have no snapshot restored, or state sync silently fell back
to block sync. Check the first few hundred lines of the log after start.

## Cosmovisor exits immediately

```
panic: ... no such file or directory .../cosmovisor/upgrades/<name>/bin/exrpd
```

The restored `data/upgrade-info.json` names an upgrade whose binary you have
not staged. Create the directory, put the correct binary in it, `chown` it to
the service user, start.

Also check you are running `cosmovisor run start`, not `cosmovisor start`. The
second is a different command.

## Validator shows `voting_power: 0`

In order of likelihood:

1. **The service was `start`ed while already active.** `systemctl start` on a
   running unit succeeds and does nothing. After replacing
   `priv_validator_key.json`, always `restart`, or `stop` then `start`.
2. The node is syncing — voting power appears once it is caught up.
3. The validator is jailed. Check `jailed_until` in the slashing module.
4. The wrong key is in place. Compare `exrpd tendermint show-validator`
   against the consensus public key the chain has recorded for your operator.

## Jailed

```bash
curl -s https://rest.exrp.posthuman.digital/cosmos/slashing/v1beta1/signing_infos \
  | jq -r '.info[] | select(.address=="<ethmvalcons…>")'
```

- `jailed_until` in the future — wait for it, fix the cause, then unjail.
  Unjailing is a broadcast transaction and a deliberate operator decision.
- `tombstoned: true` — permanent. The validator cannot return with that
  consensus key. This is the double-sign outcome.

**Do not unjail before you know why you were jailed.** Unjailing a node that is
still missing blocks just schedules the next jail.

## EVM JSON-RPC returns nothing or the wrong chain

```bash
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

- Empty: the JSON-RPC server is disabled. In `app.toml`, `[json-rpc] enable =
  true` and check `address`.
- Wrong chain ID: `evm-chain-id` under `[evm]` is unset or wrong.
- `eth_getTransactionByHash` returns null for a transaction you know exists:
  `indexer = "null"` in `config.toml`. That is correct on a signer and wrong on
  an RPC node.

## `exrpd` will not start after an upgrade

```bash
sudo journalctl -u exrpd --since "10 min ago" | head -50
```

- `unknown flag` or `unknown command`: the new version changed the CLI; check
  the unit's `ExecStart`.
- Database version error: the binary is *older* than the data. Put the previous
  binary back; do not delete data.
- Nothing in the journal at all: the unit user cannot read the node home.
  `ls -la` the home and check ownership.

## State sync aborted

Covered in the State Sync tab. Short version: move `trust_height` closer to the
head, use two genuinely independent `rpc_servers`, and re-derive `trust_hash`
from the same RPC that gave you the height.

## Everything looks fine and the validator still misses blocks

Check, in this order:

1. presence in `last_commit` (see Monitoring) — the only direct evidence;
2. clock skew — `timedatectl`, and NTP actually synchronised;
3. peer latency to the rest of the set;
4. disk write latency during block commit;
5. a second process on another host holding the same key. If this is the
   answer, stop and treat it as an incident: two signers is the scenario the
   whole discipline exists to prevent.

## What not to do

- `exrpd tendermint unsafe-reset-all` on a signer home.
- Restoring `priv_validator_state.json` from a backup or a snapshot.
- Starting "a second copy just to catch up" while the first is live.
- Trusting `systemctl is-active` as proof the node is healthy, or a single
  external source as proof it agrees with the network.
