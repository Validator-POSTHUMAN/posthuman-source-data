# Celestia — One-Liner Manager

POSTHUMAN maintains a helper script for installing and managing Celestia
consensus and Data Availability nodes.

## Repository

```text
https://github.com/Validator-POSTHUMAN/celestia-oneliner
```

Run:

```bash
bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

For a persistent terminal:

```bash
screen -S celestia-manager
bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

## Current Version Matrix

- Mainnet chain ID: `celestia`
- Recommended consensus wrapper: `v9.0.6`
- Current protocol app: `v9`
- App v9 activated at height: `11771698`
- POSTHUMAN consensus snapshot DB: PebbleDB
- Celestia DA node version: `v0.31.4`
- Go: `1.26.2+`

Before installing, verify the live mainnet height and sync state:

```bash
curl -fsS https://celestia-rpc.publicnode.com/status | \
  jq -r '.result.sync_info.latest_block_height'
```

If the one-liner default version lags behind this page, override versions
explicitly:

```bash
export NETWORK_TYPE=mainnet
export APP_VERSION=v9.0.6
export BRIDGE_VERSION=v0.31.4

bash -c "$(curl -sL https://raw.githubusercontent.com/Validator-POSTHUMAN/celestia-oneliner/main/celestia-manager.sh)"
```

## What the Manager Covers

- Consensus node install and update.
- Pruned or archive node profile.
- Snapshot restore.
- RPC/API/gRPC exposure controls.
- Firewall helper.
- Validator wallet and validator transaction helpers.
- Data Availability nodes:
  - bridge node
  - full storage node
  - light node

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
