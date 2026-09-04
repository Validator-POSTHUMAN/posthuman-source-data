# Celestia Mainnet Validator Upgrade Signaling

Celestia uses CIP-10 in-protocol upgrade signaling for application versions
`v3` and later. Validators signal readiness for an application version; the
threshold is **5/6 of total voting power**, not 5/6 of validator count.

At celestia-app v9, a separate `try-upgrade` transaction tallies signals. If
quorum exists, it records an activation height **232,616 blocks** after that
transaction's height (approximately 7 days at the source's assumed cadence).
Test and observe the release on Mocha before any mainnet signal.

## Safety model

A signal is a signed on-chain transaction and a public commitment that the
validator is ready. Do not signal merely because a release exists.

Before signaling:

1. Confirm the official upgrade announcement, target application version,
   network, delay, release tag, source commit, and required configuration.
2. Confirm Mocha testing and activation evidence, including any incident or
   rollback notice.
3. Build or stage the exact binary outside the live path. Verify its source
   commit, checksum, `celestia-appd version --long` output, glibc requirement,
   CPU benchmark, and startup/config compatibility without activating it on the
   validator.
4. Preserve the current binary and configuration as rollback artifacts.
5. Confirm the validator wallet is the operator for the intended validator and
   that the node is on chain ID `celestia`.
6. Obtain explicit transaction approval for the exact version and generated
   transaction document.

Signaling is not an upgrade mechanism. The replacement binary must already be
staged and verified before signaling. Do not rely on an automatic binary fetch.

## Read-only queries

Replace `<version>` with the integer application version from the official
announcement.

```bash
celestia-appd query signal tally <version> \
  --node <trusted-mainnet-rpc>
celestia-appd query signal missing-validators <version> \
  --node <trusted-mainnet-rpc>
celestia-appd query signal upgrade \
  --node <trusted-mainnet-rpc>
celestia-appd version --long
```

Cross-check the tally and pending-upgrade result against an independent source,
such as the mainnet Celenium upgrade page. A stale RPC or explorer is not a
valid basis for signaling.

## Approval-gated transaction shape

The shape below is intentionally non-runnable. Use it only to define the fields
that an operator-controlled transaction procedure must generate for review.

```text
<APPROVED-CELESTIA-APPD> tx signal signal <APP-VERSION> \
  --from <VALIDATOR-WALLET> \
  --chain-id celestia \
  --node <TRUSTED-MAINNET-RPC> \
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

- Confirm the transaction is included and the validator's signaling state is
  reflected in two independent queries.
- Read the pending upgrade's exact activation height from independent queries.
  Do not derive it from wall-clock quorum time or a dashboard estimate.
- Keep the verified target binary and rollback artifact available.
- Alert if the pending version, activation height, or announced release changes.
- Re-check official status and incident history before activation.

## Sources

Evidence reviewed at official docs commit
`8fbaa868a323c13d3edae2875d9b27765eb29c45` and celestia-app commit
`6f4b596e47f80683adb1a161ca7cb640dcd9d206`:

- `operate/maintenance/network-upgrades`
- celestia-app `x/signal/README.md`
- celestia-app `x/signal/cli/query.go`
- celestia-app `x/signal/cli/tx.go`
- celestia-app `pkg/appconsts/app_consts.go`
- celestia-app `pkg/appconsts/versioned_consts.go`
- [CIP-10](https://cips.celestia.org/cip-010.html)
