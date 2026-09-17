# Axelar testnet (`axelar-testnet-lisbon-3`) validator setup

An Axelar validator is not a single daemon. It is `axelard` for consensus,
`vald` for protocol events and external-chain voting, a dedicated `tofnd` for
threshold signing, and a broadcaster account — the same stack on testnet as on
mainnet. That is why Axelar does not use the shared generated installation
guide for the validator role: the generated guide describes a plain full node
and stops, which on Axelar is an incomplete setup rather than a finished one.

**The procedure is the mainnet procedure.** Rather than duplicate it here,
where the copy would drift, follow the Axelar **mainnet** Node Ops guides and
substitute the testnet values in the table below:

- *Validator setup* — topology, build, `vald` and `tofnd`, external chains,
  verification.
- *Broadcaster proxy* — broadcaster account and registration.
- *Amplifier Verifier* — the separate verifier plane. Keep it off the classic
  validator host on testnet too.

They are published under the Axelar mainnet network, not here, because the
steps are identical and one reviewed copy is better than two that drift.

## What differs on testnet

| | Testnet | Mainnet |
| --- | --- | --- |
| Chain ID | `axelar-testnet-lisbon-3` | `axelar-dojo-1` |
| Genesis | `resources/testnet/genesis.json` in `axelarnetwork/axelarate-community` | mainnet resources |
| Seeds | `resources/testnet/seeds.txt` in the same repository | mainnet seeds |
| Node home | `$HOME/.axelar` | `$HOME/.axelar` |
| External chains | testnet RPC for every enabled chain | mainnet RPC |

The node home is the binary default and is **the same string on both
networks**. Running mainnet and testnet on one host therefore requires an
explicit `--home` on every command and in every unit file. Do not assume the
default will keep them apart.

## Version

Verified 2026-09-17: the live testnet reports `axelard 1.5.5`, and the newest
public tag in the 1.5 line is `v1.5.3`. Testnet runs ahead of the published
releases, which is normal for a testnet and is exactly why the mainnet guide
uses `<reviewed-release-tag>` instead of pinning a number. Read the current
required version from the network and from Axelar's release channel before you
build; do not copy `v1.5.3` out of this paragraph into a production command.

```bash
set -Eeuo pipefail
AXELAR_REPO='https://github.com/axelarnetwork/axelar-core'
AXELARD_VERSION='<reviewed-release-tag>'
EXPECTED_COMMIT='<official-release-commit>'

test "$AXELARD_VERSION" != '<reviewed-release-tag>'
test "$EXPECTED_COMMIT" != '<official-release-commit>'
```

## Verification

The same gate as mainnet, with the testnet chain ID:

```bash
axelard status --home "$HOME/.axelar" | jq -e '
  .node_info.network == "axelar-testnet-lisbon-3"
  and (.sync_info.catching_up == false)
  and ((.sync_info.latest_block_height | tonumber) > 0)
'
```

Cross-check the height against an independent public testnet endpoint before
registering anything on chain.

## POSTHUMAN does not operate this network

POSTHUMAN runs the Axelar mainnet validator, not the testnet. Every value above
was read from public sources — the live testnet API, the Axelar community
repository and the genesis file itself — rather than from a node we operate, so
there is no first-party operational experience behind it. Treat the mainnet
guides as the reviewed material and this page as the testnet delta.
