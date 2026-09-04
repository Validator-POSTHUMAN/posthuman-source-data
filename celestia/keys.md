# Celestia Mainnet Keys and Signer Boundaries

Celestia uses several independent key domains. Treating them as interchangeable
can cause loss of funds, loss of DA identity, Blobstream failure, or validator
double-signing.

## Key domains

| Domain | Purpose | Typical location | Safety boundary |
| --- | --- | --- | --- |
| celestia-app wallet | Signs account transactions such as staking, signaling, and Blobstream registration | Configured celestia-app keyring | Not the consensus signer |
| Consensus signer | Signs consensus votes and proposals | `$CELESTIA_HOME/config/priv_validator_key.json` | One live signer only |
| Consensus signer state | Records the last signed height, round, and step | `$CELESTIA_HOME/data/priv_validator_state.json` | Must remain paired with the signer during recovery or migration |
| celestia-node DA keyring | DA account and node-local identity for bridge or light stores | `$HOME/.celestia-bridge/keys/` or `$HOME/.celestia-light/keys/` | Keep role and network matched |
| Blobstream EVM key | Signs Blobstream attestations for the validator's registered EVM address | Orchestrator keystore | Must match on-chain registration |
| Blobstream P2P key | Identifies the orchestrator on the separate Blobstream P2P network | Orchestrator keystore | Separate from consensus and DA P2P identities |

`CELESTIA_HOME` must be the reviewed consensus home, not an assumed default.

## Non-negotiable handling rules

- Never place wallet recovery words, raw signing material, or unlock secrets in
  commands, command arguments, unit files, environment files, documentation,
  tickets, shell history, or logs.
- Never open or print signer or wallet files during routine verification.
- Never start a candidate validator signer until the previous signer is proven
  stopped, disabled, and unable to restart. Uptime does not override the
  one-signer invariant.
- Preserve `priv_validator_state.json` with its consensus signer. Never
  regenerate or lower it during recovery.
- Keep backups encrypted, access-controlled, offline where practical, and
  tested through a documented restore drill that does not activate signing.
- This guide intentionally omits key deletion, raw import/export, signer
  generation, and key transfer commands.

## Read-only identity inventory

These commands display public identifiers or file metadata only. Review output
before attaching it to an incident because paths and account names can still be
operationally sensitive.

```bash
celestia-appd keys list
celestia-appd tendermint show-validator

cel-key list --keyring-backend test \
  --keyring-dir "$HOME/.celestia-bridge/keys" \
  --node.type bridge --p2p.network celestia
cel-key list --keyring-backend test \
  --keyring-dir "$HOME/.celestia-light/keys" \
  --node.type light --p2p.network celestia

stat -c '%n %a %U:%G' \
  "$CELESTIA_HOME/config/priv_validator_key.json" \
  "$CELESTIA_HOME/data/priv_validator_state.json"
```

The pinned celestia-app v9 source has no legacy `blobstream` module, and the
archived orchestrator binary lacks a reconciled current release pin. Only after
the gate in [the Blobstream guide](blobstream-orchestrator.md) is resolved may
an operator use the selected binary's read-only key-list interface. The shape
below is intentionally non-runnable:

```text
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys evm list \
  --home <REVIEWED-MAINNET-ORCHESTRATOR-HOME>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys p2p list \
  --home <REVIEWED-MAINNET-ORCHESTRATOR-HOME>
```

Do not assume that an address shown by one domain belongs to any other domain.
Record the expected public identifiers in a protected inventory and compare
only those identifiers during verification.

## Backup set by role

- **Consensus validator:** wallet backup, consensus signer, signer state,
  configuration, and the public consensus/operator-address mapping.
- **Bridge or light node:** the complete role-specific `keys/` directory,
  configuration, and the expected public account and peer IDs.
- **Blobstream orchestrator:** EVM keystore, P2P keystore, configuration, and
  the on-chain validator-to-EVM mapping.

A filesystem snapshot is not enough unless its consistency point, encryption,
restore procedure, and access controls are known. Do not co-locate all domains
in one broadly accessible backup.

## Migration and recovery gate

Before any key-bearing restore or move:

1. Identify the exact network, role, source host, destination host, service,
   store, and expected public identifier.
2. Stop and disable the old signer where applicable; prove no process, service,
   container, or remote signer can still sign.
3. Preserve current signer state and configuration before changing data.
4. Restore through an approved secure channel without printing contents.
5. Re-check ownership and restrictive file modes.
6. Start only after a second review of network identity and the one-signer
   invariant.
7. Verify recent external commits before declaring validator recovery complete.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/keys-wallets/celestia-app-wallet`
- `operate/keys-wallets/celestia-node-key`
- `operate/blobstream/key-management`
- `operate/blobstream/orchestrator`
- `operate/consensus-validators/validator-node`

The Blobstream compatibility warning was cross-checked against official
celestia-app tag `v9.0.6`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`, especially `app/app.go`,
`app/modules.go`, and `specs/src/state_machine_modules_v1.md` through
`state_machine_modules_v9.md`.
