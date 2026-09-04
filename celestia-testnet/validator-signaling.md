# Celestia Mocha-5 Validator Upgrade Signaling

Celestia uses CIP-10 in-protocol upgrade signaling for application versions
`v3` and later. Validators signal readiness for an application version; the
threshold is **5/6 of total voting power**, not validator count.

At celestia-app v9, a separate `try-upgrade` transaction tallies signals. If
quorum exists on Mocha, it records an activation height **66,462 blocks** after
that transaction's height (approximately 2 days at the source's assumed
cadence). Mocha is the proving ground: test and observe the release here before
any mainnet signal.

## Mocha-5 boundary

- Chain ID: `mocha-5`
- Dedicated consensus home: for example `$HOME/.celestia-app-mocha-5`
- Never reuse Mocha-4 data or `priv_validator_state.json`.

A signal is a signed on-chain transaction and a public readiness commitment. Do
not signal only because a release exists.

## Pre-signal gate

1. Confirm the official Mocha upgrade announcement, target app version, 2-day
   delay, release tag, source commit, and required configuration.
2. Confirm every query endpoint reports chain ID `mocha-5`.
3. Build or stage the exact binary outside the live path. Verify source commit,
   checksum, `celestia-appd version --long`, glibc requirement, CPU benchmark,
   and startup/config compatibility without replacing the live validator.
4. Preserve the current binary and configuration for rollback.
5. Confirm the selected wallet operates the intended Mocha-5 validator.
6. Obtain explicit approval for the exact version and generated transaction
   document.

Signaling does not install or activate software. Stage and verify the binary
first; do not depend on automatic downloads.

## Read-only queries

```bash
celestia-appd status --home "$MOCHA_5_HOME" | \
  jq -e '.NodeInfo.network == "mocha-5"'
celestia-appd query signal tally <version> \
  --home "$MOCHA_5_HOME" --node <trusted-mocha-5-rpc>
celestia-appd query signal missing-validators <version> \
  --home "$MOCHA_5_HOME" --node <trusted-mocha-5-rpc>
celestia-appd query signal upgrade \
  --home "$MOCHA_5_HOME" --node <trusted-mocha-5-rpc>
celestia-appd version --long
```

Cross-check against an independent Mocha-5 source such as the Mocha Celenium
upgrade page. Unknown or stale data is not a valid basis for signaling.

## Approval-gated transaction shape

The shape below is intentionally non-runnable. Use it only to define the fields
that an operator-controlled transaction procedure must generate for review.

```text
<APPROVED-CELESTIA-APPD> tx signal signal <APP-VERSION> \
  --from <MOCHA-5-VALIDATOR-WALLET> \
  --chain-id mocha-5 \
  --home <REVIEWED-MOCHA-5-HOME> \
  --node <TRUSTED-MOCHA-5-RPC> \
  --generate-only > <REVIEWED-UNSIGNED-OUTPUT>
```

Review chain ID, signer, message type, target version, fees, and account
sequence. Preparing the real document, signing, or broadcasting requires a
separate explicit approval and operator-controlled transaction procedure.

The current source also exposes `tx signal try-upgrade`, which persists the
pending upgrade after quorum and sets its activation height. This guide does
not provide a runnable form because it is a separate state-changing
transaction, not part of an individual validator's readiness signal.

## After an approved signal

- Confirm inclusion and the validator's signal through two independent sources.
- Read the pending upgrade's exact activation height from independent queries.
  Do not derive it from wall-clock quorum time or a dashboard estimate.
- Keep the target and rollback binaries available.
- Alert on any target-version, activation-height, release, status, or incident
  change.
- After activation, validate Mocha behavior before considering mainnet.

## Sources

Evidence reviewed at official docs commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45` and celestia-app commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`:

- `operate/networks/mocha-testnet`
- `operate/maintenance/network-upgrades`
- celestia-app `x/signal/README.md`
- celestia-app `x/signal/cli/query.go`
- celestia-app `x/signal/cli/tx.go`
- celestia-app `pkg/appconsts/app_consts.go`
- celestia-app `pkg/appconsts/versioned_consts.go`
- [CIP-10](https://cips.celestia.org/cip-010.html)
