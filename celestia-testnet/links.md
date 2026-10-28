# Celestia Mocha-5 — Node Operations Index

**Checked 2026-10-28:** live Mocha-5 app `v10.5.0-mocha`, protocol app `10`.
The app-v10 activation at height **1082619** is historical. DA-node guides
have separately pinned releases; verify them against current upstream before
installing. Mainnet and retired Mocha-4 are separate networks.

- [App upgrade, verification and rollback boundaries](multiplexer.md)
- [New app-node installation](installation-guide.md)
- [Consensus full node versus DA roles](full-node-setup.md)
- [Bridge informational guide](bridge-node-setup.md)
- [Light informational guide](light-node-setup.md)
- [Monitoring and activation checks](monitoring.md)
- [Signaling and pending-plan gate](validator-signaling.md)
- [Keys and signer boundaries](keys.md)
- [Snapshots and Mocha-4 exclusions](snapshots.md)

POSTHUMAN operates neither Bridge nor Light, but does operate a Mocha-5 Fibre
server. Its signer link, service and escrow actions require their own checks;
do not infer them from DA-node installation guides.

## Public references

- **RPC (POSTHUMAN)**: https://rpc-celestia-testnet.posthuman.digital
- **REST (POSTHUMAN)**: https://rest-celestia-testnet.posthuman.digital
- **External RPC (ITRocket)**: https://celestia-testnet-rpc.itrocket.net
- **Snapshots (ITRocket)**: https://server-6.itrocket.net/testnet/celestia/
- **Peers**: the previously listed POSTHUMAN `:28756` source is retired; verify a current public Mocha-5 peer before configuration.
- **Official genesis**: https://raw.githubusercontent.com/celestiaorg/networks/main/mocha-5/genesis.json
