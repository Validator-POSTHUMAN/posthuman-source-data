# Celestia Mocha-5 — Node Operations Index

**Reviewed 2026-09-23:** app `v10.2.0-mocha`, activation height **1082619**;
DA `v0.34.2-mocha`. Mainnet and historical Mocha-4 are separate networks.

- [App upgrade, verification and rollback boundaries](multiplexer.md)
- [New app-node installation](installation-guide.md)
- [Consensus full node versus DA roles](full-node-setup.md)
- [Bridge informational guide](bridge-node-setup.md)
- [Light informational guide](light-node-setup.md)
- [Monitoring and activation checks](monitoring.md)
- [Signaling and pending-plan gate](validator-signaling.md)
- [Keys and signer boundaries](keys.md)
- [Snapshots and Mocha-4 exclusions](snapshots.md)

POSTHUMAN operates neither Bridge nor Light. The Fibre JSON-RPC namespace
requires configured core v10; Fibre and escrow activation need a separate
decision and are not part of this documentation update.

## Public references

- **RPC (ITRocket)**: https://celestia-testnet-rpc.itrocket.net
- **REST (ITRocket)**: https://celestia-testnet-api.itrocket.net
- **Snapshots (ITRocket)**: https://server-6.itrocket.net/testnet/celestia/
- **Peers**: the previously listed POSTHUMAN `:28756` source is retired; verify a current public Mocha-5 peer before configuration.
- **Official genesis**: https://raw.githubusercontent.com/celestiaorg/networks/main/mocha-5/genesis.json
