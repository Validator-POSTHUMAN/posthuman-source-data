# Celestia — One-Liner Manager

**Do not use the linked manager for new installs or upgrades.** At the
2026-10-28 review its source still selected Go `1.24.1`, while the current
Celestia app source requires Go `1.26.6`; this tab's former v9/DA version
matrix and direct execution examples are retired. Use the reviewed
[consensus installation guide](installation-guide.md),
[snapshot status](snapshots.md), and upstream release notes until the manager
has been upgraded and tested for app v10 and current DA releases.

## Repository

```text
https://github.com/Validator-POSTHUMAN/celestia-oneliner
```

## Current version context

- Mainnet chain ID: `celestia`
- Recommended consensus multiplexer: `v10.5.0`
- Current protocol app: `10`
- App v10 activated at height: `15116658`
- POSTHUMAN consensus snapshot DB: PebbleDB
- Source-build Go: `1.26.6`

Before installing, verify the live mainnet height and sync state:

```bash
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.sync_info.latest_block_height'
```

## Historical manager scope (not validated for app v10)

- Consensus node install and update.
- Pruned or archive node profile.
- Snapshot restore.
- RPC/API/gRPC exposure controls.
- Firewall helper.
- Validator wallet and validator transaction helpers.
- Data Availability nodes; its former `full storage node` role is retired in
  current Celestia DA software.

## POSTHUMAN Mainnet Services

- Explorer: https://explorer.posthuman.digital/celestia
- RPC fallback (PublicNode): https://celestia-rpc.publicnode.com
- REST: https://rest-celestia-mainnet.posthuman.digital
- gRPC: https://grpc-celestia-mainnet.posthuman.digital
- Snapshots: https://snapshots-celestia-mainnet.posthuman.digital/
- Peer: `9f21a4f163710710aa7932e1832a257ef326186f@peer-celestia-mainnet.posthuman.digital:40656`
- Addrbook: `https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json`

<!-- The POSTHUMAN archive is withdrawn from the restore path; see celestia/snapshots.md -->
The restore procedure lives in one place now: **[Celestia Mainnet Snapshot](snapshots.md)**.
It uses our own archive, which was restore-verified end to end on 2026-09-27, and
names a third-party alternative. Do not copy the old one-line
`curl | lz4 | tar` restore from earlier revisions of this document: it neither
resumes nor verifies a checksum.

## Safety Notes

- Back up validator keys and `priv_validator_state.json` before deleting data.
- Do not broadcast validator, governance, staking, unjail, or PayForBlob
  transactions without reviewing signer, account, sequence, gas, fees, and
  messages.
- Do not expose bridge JSON-RPC publicly unless auth, firewall, proxy, and rate
  limits are intentionally configured.
- Verify service health after every install or update.
