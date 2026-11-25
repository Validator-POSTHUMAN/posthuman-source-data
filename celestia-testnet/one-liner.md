# Historical Celestia One-Liner — Not a Mocha-5 Installer

The former one-liner documented Mocha-4. It is not a validated installer or
recovery path for Mocha-5/app v11. Its executable examples, legacy endpoint
inventory and snapshot replacement recipe have been retired from this page.
Do not reuse Mocha-4 databases, snapshots, homes or signer state on Mocha-5.

## Current Mocha-5 documentation

- Current app binary: **v11.0.0-mocha**; active protocol app **11**, v11 activation height **2760281** (v10 height **1082619** is historical).
- [New-node installation](/chains/celestia-testnet?tab=installation-guide).
- [Existing-node upgrade and multiplexer](/chains/celestia-testnet?tab=multiplexer).
- [Snapshot provenance and recovery boundaries](/chains/celestia-testnet?tab=snapshots).
- [Keys and signer boundaries](/chains/celestia-testnet?tab=keys).
- [Current node-ops index](https://github.com/Validator-POSTHUMAN/posthuman-source-data/blob/main/celestia-testnet/links.md).

Snapshot recovery must preserve the latest signing state after the signer is
stopped and fenced. Never restore an older `priv_validator_state.json`, copy a
consensus key to another live signer, or stream an unverified archive directly
into a live home. A legacy helper is not an exception to these requirements.

DA **v0.34.2-mocha** is a historical informational pin, not a current
installer recommendation. POSTHUMAN operates neither Bridge
nor Light. Fibre/escrow activation, DA deployment, transactions and network
exposure require separate decisions; this page offers no automatic activation.

The [historical helper repository](https://github.com/Validator-POSTHUMAN/celestia-oneliner)
is retained for provenance, not as a current operational recommendation.
