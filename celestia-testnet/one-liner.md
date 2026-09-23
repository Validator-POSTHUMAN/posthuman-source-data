# Historical Celestia One-Liner — Not a Mocha-5 Installer

The former one-liner documented Mocha-4. It is not a validated installer or
recovery path for Mocha-5/app v10. Its executable examples, legacy endpoint
inventory and snapshot replacement recipe have been retired from this page.
Do not reuse Mocha-4 databases, snapshots, homes or signer state on Mocha-5.

## Current Mocha-5 documentation

- Target app: **v10.2.0-mocha**, activation height **1082619**.
- [New-node installation](installation-guide.md).
- [Existing-node upgrade and multiplexer](multiplexer.md).
- [Snapshot provenance and recovery boundaries](snapshots.md).
- [Keys and signer boundaries](keys.md).
- [Current node-ops index](links.md).

Snapshot recovery must preserve the latest signing state after the signer is
stopped and fenced. Never restore an older `priv_validator_state.json`, copy a
consensus key to another live signer, or stream an unverified archive directly
into a live home. A legacy helper is not an exception to these requirements.

DA **v0.34.2-mocha** is informational only. POSTHUMAN operates neither Bridge
nor Light. Fibre/escrow activation, DA deployment, transactions and network
exposure require separate decisions; this page offers no automatic activation.

The [historical helper repository](https://github.com/Validator-POSTHUMAN/celestia-oneliner)
is retained for provenance, not as a current operational recommendation.
