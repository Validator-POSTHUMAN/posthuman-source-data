# XRPL EVM Mainnet — becoming a validator

XRPL EVM is **Proof of Authority**. You do not buy your way into the set with
stake. The existing validators vote you in, over seven days, and they can vote
you out. That makes admission a process with a social half and a technical
half, and the technical half is the part you can finish before you ask.

## What the process actually is

1. Run a healthy, synced node on mainnet and keep it that way long enough to
   point at.
2. Join the [XRPL EVM Discord](https://discord.gg/xrplevm), pick the validator
   role in `#roles`.
3. Introduce yourself in `#become-a-validator`: who you are, what you already
   run, and what you intend to contribute long term.
4. Supply three identifiers — moniker, `ethmvaloper` operator address,
   consensus public key.
5. A proposal is opened and voted on for **seven days**. Expect public and
   private questions during that window.
6. Watch it at <https://governance.xrplevm.org/proposals>.

The official guidance names demonstrated interest in the project, recognised
community participation and a commitment to long-term governance as the
selection signals. A synced node is table stakes, not an argument.

## Prepare the three identifiers

### Operator key

```bash
exrpd keys add <key_name> --key-type eth_secp256k1 --keyring-backend file
```

`--key-type eth_secp256k1` is required — this is an EVM chain and the default
Cosmos curve produces an account the EVM side cannot use.

Back up the mnemonic offline, before you do anything else with the key. Not in
chat, not in a password manager note you have not tested restoring from.

### Operator address

```bash
exrpd keys show <key_name> --keyring-backend file --bech val
# ethmvaloper1...
```

### Consensus public key

```bash
exrpd tendermint show-validator
# {"@type":"/cosmos.crypto.ed25519.PubKey","key":"..."}
```

This is derived from `config/priv_validator_key.json`. Publishing the **public**
key is exactly right; the file it comes from never leaves the host.

### Moniker

Set in `config.toml`, and it is what the network will call you. Changing it
later is a transaction, so pick the name you want on the validator list.

## Before you ask to be admitted

Prove all of these to yourself first. Each one is something the set can check.

- [ ] Node synced, `catching_up=false`, and the app hash matches **two**
      independent RPCs at a common height.
- [ ] Version equal to the fleet patch level, not just to the docs table.
- [ ] Monitoring that alerts on divergence and on missing commits, not on the
      process being up.
- [ ] `priv_validator_key.json` and `node_key.json` backed up offline, and the
      restore tested.
- [ ] Exactly one host can sign with the key, proven and not assumed.
- [ ] Firewall: P2P public, everything else loopback or behind a reviewed
      proxy.
- [ ] A sentry topology, or a documented reason you do not need one.
- [ ] A rollback plan for an upgrade, written down.
- [ ] A commitment you can keep: 24-hour incident response, upgrade voting,
      and maintained public infrastructure are the contributions the advisory
      board asks for.

## Creating the validator object

Once the set has voted you in, the validator object is created with an ordinary
staking transaction. **This broadcasts and it involves your keys.** It is shown
here so the shape is familiar, not so it can be pasted:

```bash
# REVIEW BEFORE RUNNING — broadcasts a transaction
# exrpd tx staking create-validator \
#   --amount=<amount>axrp \
#   --pubkey=$(exrpd tendermint show-validator) \
#   --moniker="<moniker>" \
#   --chain-id=xrplevm_1440000-1 \
#   --commission-rate=... --commission-max-rate=... --commission-max-change-rate=... \
#   --min-self-delegation=1 \
#   --from=<key_name> --keyring-backend=file \
#   --gas=auto --gas-adjustment=1.3 --gas-prices=0.25axrp
```

Check the current parameters and what other validators use before choosing
commission values — they are visible and they are harder to change than to set:

```bash
exrpd query staking params -o json | jq
exrpd query staking validators --limit 200 -o json \
  | jq -r '.validators[] | [.description.moniker, .commission.commission_rates.rate] | @tsv'
```

## After admission

The first block you sign is the moment the double-sign rule starts to matter.
From then on, every migration, restore, upgrade or "let me just start the other
one to check" passes through the anti-double-sign check first. `tombstoned:
true` is permanent and no vote reverses it.

Read the Security tab before the first signed block, not after.

## Removal

The same majority that admits validators removes inactive ones. Advisory-board
notes from 2026-07 record inactive validators being dropped from both testnet
and mainnet sets. Being admitted is not the end of the process — uptime,
upgrade participation and governance voting are the continuation of it.
