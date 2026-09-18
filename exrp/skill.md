# XRPL EVM AI Operations Skill

This tab links the XRPL EVM–specific AI-agent skill for node operations. The
skill is operator-neutral: it names no production host, no credential and no
private endpoint.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/xrplevm
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/xrplevm/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/xrplevm/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/xrplevm/scripts/xrplevm-healthcheck.sh

## Read this first: what XRPL EVM is

A Cosmos SDK chain with an EVM execution layer, run by one binary, `exrpd`,
under CometBFT consensus in **Proof of Authority**. A validator holds a
consensus key, signs blocks, can be jailed, and can be **tombstoned** for
double-signing — permanently, with no vote to reverse it.

So every Ethereum-follower reflex is wrong here. Restarting is not free.
Deleting the data directory is not free if the home holds a signer key.
"Start a second copy to catch up" is the single most dangerous sentence on this
network.

## The failures this skill exists for

**Six digits instead of seven.** A `chain-id = "xrplevm_144000-1"` in
`client.toml` causes deterministic app-hash divergence during bootstrap while
the genesis file and the binary are both correct. It does not present as a
configuration error. The correct value is `xrplevm_1440000-1`.

**The documentation table lags the fleet.** The official Networks page lists
the last consensus-breaking version. Patch releases never appear there and
never produce an on-chain plan, so `exrpd query upgrade plan` returning `{}` is
not evidence there is nothing to do. Verified 2026-09-18: the table said
`v10.1.0` while the official RPC reported `10.2.1` and an independent node
reported `10.2.0` — same height, same app hash.

**`systemctl start` on a live unit is a no-op.** After replacing a binary or a
`priv_validator_key.json`, `start` returns success and changes nothing.
Symptoms: `voting_power=0`, height stuck, `valcons` absent from `last_commit`.

**A healthy-looking node on the wrong chain.** `active (running)` plus
`catching_up=false` is compatible with following a different chain entirely.
The only check that settles it is an app-hash comparison at a common height
against an independent RPC.

## What it helps agents do

- Verify a node in the right order: `/status`, `/abci_info`, then app-hash
  agreement against two independent RPCs — by hash, not by height.
- Distinguish a consensus-breaking upgrade at a block height from a patch
  release with no gate, and drive each to the correct verification.
- Restore a snapshot in the order that works: download, verify the archive,
  *then* stop the node — never the other way round — while preserving
  `priv_validator_state.json`.
- Run the anti-double-sign check before any migration, restore or service
  action, across every host that has ever held the key, and treat an inactive
  unit with a live listener as a running node.
- Read `voting_power: 0` through its four real causes rather than guessing.
- Separate the two chain IDs — Cosmos `xrplevm_1440000-1` and EVM `1440000` —
  and the two address representations of one account, `ethm1…` and `0x…`,
  without ever adding the balances together.
- Read `indexer = "null"` as the reason `eth_getTransactionByHash` returns null
  on a validator, and know that changing it does not backfill.
- Recognise `tombstoned: true` as terminal and stop, rather than attempting
  recovery.

## Operational scope

- Cosmos chain ID `xrplevm_1440000-1`; EVM chain ID `1440000` / `0x15f900`.
  Testnet `xrplevm_1449000-1` / `1449000`; devnet `xrplevm_1449900-1`.
- Binary `exrpd`; CometBFT `0.38.19`; Cosmos SDK `v0.53.x-xrplevm`; denom
  `axrp`, 18 decimals.
- `evm-chain-id` under `[evm]` in `app.toml` has been mandatory since v10.
- Ports: `26656` P2P public; `26657`, `1317`, `9090`, `8545`, `8546`, `26660`
  loopback or behind a reviewed proxy.
- Admission is a seven-day Proof of Authority vote, not a staking transaction.
- The `v11.x` release line is testnet and devnet, not mainnet.

## Safety boundaries

Read-only by default. The skill broadcasts no transaction, moves no funds and
handles no key material. Explicit operator approval is required before any
service stop or restart on a signer, any snapshot restore or data replacement,
any binary change, any `unsafe-reset-all`, any firewall change, and any
transaction — `create-validator`, `unjail`, `vote`, or a transfer.

`xrplevm-healthcheck.sh` is read-only and prints no credential. A passing check
is evidence, not proof.

## Related guides

The full operator set for this network is on the other tabs of this page:
installation, bootstrap files, peers, snapshots, state sync, RPC and indexes,
upgrades, monitoring, security hardening, governance, becoming a validator,
command sheet, troubleshooting, test networks, operator toolbox and endpoints.
