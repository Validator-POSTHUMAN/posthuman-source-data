# Celestia Mocha-5 Keys and Signer Boundaries

Celestia uses several independent key domains. Mocha-5 is a new chain from
height 1, not an in-place continuation of Mocha-4. Never reuse Mocha-4 chain
data or signer state for Mocha-5.

## Key domains

| Domain | Purpose | Mocha-5 location | Safety boundary |
| --- | --- | --- | --- |
| celestia-app wallet | Signs account transactions | Mocha-5 celestia-app keyring | Not the consensus signer |
| Consensus signer | Signs consensus votes and proposals | `$MOCHA_5_HOME/config/priv_validator_key.json` | One live signer only |
| Consensus signer state | Records last signed height, round, and step | `$MOCHA_5_HOME/data/priv_validator_state.json` | New Mocha-5 state; never copy Mocha-4 state |
| celestia-node bridge keyring | DA account and bridge identity | `$HOME/.celestia-bridge-mocha-5/keys/` | Must remain on P2P network `mocha` |
| celestia-node light keyring | DA account and light identity | `$HOME/.celestia-light-mocha-5/keys/` | Must remain on P2P network `mocha` |
| Blobstream EVM key | Signs attestations for the registered validator address | `$HOME/.orchestrator-mocha-5/keystore/` | Must match Mocha-5 on-chain registration |
| Blobstream P2P key | Identifies the orchestrator on Blobstream P2P | `$HOME/.orchestrator-mocha-5/keystore/` | Separate from consensus and DA identities |

Set `MOCHA_5_HOME` to the reviewed dedicated consensus home, such as
`$HOME/.celestia-app-mocha-5`; do not infer it from an old service.

## Non-negotiable handling rules

- Never place wallet recovery words, raw signing material, or unlock secrets in
  commands, command arguments, unit files, environment files, documentation,
  tickets, shell history, or logs.
- Never open or print signer or wallet files during routine verification.
- Never start a candidate validator signer until every old signer is proven
  stopped, disabled, and unable to restart.
- Never copy Mocha-4 `priv_validator_state.json` into Mocha-5. It contains
  incompatible signed-height history and can prevent signing or create unsafe
  recovery decisions.
- Keep backups encrypted, access-controlled, and restore-tested without
  activating signing.
- This guide intentionally omits key deletion, raw import/export, signer
  generation, and key transfer commands.

## Read-only identity inventory

```bash
celestia-appd keys list --home "$MOCHA_5_HOME"
celestia-appd tendermint show-validator --home "$MOCHA_5_HOME"

cel-key list --keyring-backend test \
  --keyring-dir "$HOME/.celestia-bridge-mocha-5/keys" \
  --node.type bridge --p2p.network mocha
cel-key list --keyring-backend test \
  --keyring-dir "$HOME/.celestia-light-mocha-5/keys" \
  --node.type light --p2p.network mocha

stat -c '%n %a %U:%G' \
  "$MOCHA_5_HOME/config/priv_validator_key.json" \
  "$MOCHA_5_HOME/data/priv_validator_state.json"
```

The pinned celestia-app v9 source has no legacy `blobstream` module, and the
archived orchestrator binary lacks a reconciled current Mocha-5 release pin.
Only after the gate in [the Blobstream guide](blobstream-orchestrator.md) is
resolved may an operator use the selected binary's read-only key-list
interface. The shape below is intentionally non-runnable:

```text
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys evm list \
  --home <REVIEWED-MOCHA-5-ORCHESTRATOR-HOME>
<APPROVED-BLOBSTREAM-BINARY> orchestrator keys p2p list \
  --home <REVIEWED-MOCHA-5-ORCHESTRATOR-HOME>
```

Confirm every service uses the dedicated `-mocha-5` home or store. Public
identifiers from wallet, consensus, DA, and Blobstream domains are not
interchangeable.

## Backup set by role

- **Mocha-5 validator:** wallet backup, consensus signer, new Mocha-5 signer
  state, configuration, and public consensus/operator-address mapping.
- **Bridge or light node:** complete role-specific `-mocha-5/keys/` directory,
  configuration, and expected public account and peer IDs.
- **Blobstream orchestrator:** EVM and P2P keystores, configuration, and the
  Mocha-5 validator-to-EVM mapping.

Keep Mocha-4 backups labeled and isolated. Never restore them into paths used by
Mocha-5 services.

## Migration and recovery gate

1. Identify the exact chain ID `mocha-5`, P2P network `mocha`, role, source,
   destination, service, store, and expected public identifier.
2. Prove every prior signer is stopped, disabled, and unable to restart.
3. Preserve current Mocha-5 signer state and configuration.
4. Restore through an approved secure channel without printing contents.
5. Re-check owner, restrictive modes, service home, and chain identity.
6. Start only after a second one-signer review.
7. Verify fresh external Mocha-5 commits before declaring recovery complete.

## Sources

Evidence reviewed from the official Celestia docs repository at commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45`:

- `operate/networks/mocha-testnet`
- `operate/keys-wallets/celestia-app-wallet`
- `operate/keys-wallets/celestia-node-key`
- `operate/blobstream/key-management`
- `operate/blobstream/orchestrator`

The Blobstream compatibility warning was cross-checked against official
celestia-app tag `v9.0.6-mocha`, commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`, especially `app/app.go`,
`app/modules.go`, and `specs/src/state_machine_modules_v1.md` through
`state_machine_modules_v9.md`.
