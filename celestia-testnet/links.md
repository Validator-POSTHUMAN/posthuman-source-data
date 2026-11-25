# Celestia Mocha-5 — Node Operations Index

**Checked 2026-11-25:** live Mocha-5 app `v11.0.0-mocha`, protocol app `11`.
The app-v10 activation at height **1082619** is historical. DA-node guides
have separately pinned releases; verify them against current upstream before
installing. Mainnet and retired Mocha-4 are separate networks.

- [App upgrade, verification and rollback boundaries](/chains/celestia-testnet?tab=multiplexer)
- [New app-node installation](/chains/celestia-testnet?tab=installation-guide)
- [Consensus full node versus DA roles](/chains/celestia-testnet?tab=full-node-setup)
- [Bridge informational guide](/chains/celestia-testnet?tab=bridge-node-setup)
- [Light informational guide](/chains/celestia-testnet?tab=light-node-setup)
- [Monitoring and activation checks](/chains/celestia-testnet?tab=monitoring)
- [Signaling and pending-plan gate](/chains/celestia-testnet?tab=validator-signaling)
- [Keys and signer boundaries](/chains/celestia-testnet?tab=keys)
- [Snapshots and Mocha-4 exclusions](/chains/celestia-testnet?tab=snapshots)

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
