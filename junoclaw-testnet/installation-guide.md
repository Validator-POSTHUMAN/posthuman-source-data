# JunoClaw G2 — validator onboarding and node guide

JunoClaw G2 is an invited, equal-weight public testnet built on Commonware Simplex BFT. Its node binary is `slay3rd`; it is **not** the Cosmos Juno (`junod`) testnet. There is no consensus-layer staking, delegation, slashing or validator-creation transaction. An operator joins only through a coordinated set-change and threshold-key ceremony.

## Before you request a seat

The [official validator guide](https://junoclaw.xyz/docs/onboarding/validators/) requires a dedicated host and network failure domain, a stable public IP, key-only SSH, NTP drift below two seconds and an operator reachable during upgrade windows. Minimum resources are 2 CPU cores, 4 GB RAM and 20 GB SSD; 4 cores, 8 GB and 50 GB SSD are recommended. Peers require inbound TCP 7001. gRPC TCP 9090 can remain private.

A second live signer for the same seat is unsafe. Plan active/passive failover and prove the old signer is fenced before starting another.

## Release and configuration

The [official release list](https://github.com/Dragonmonk111/layer-sdk/releases) published `v0.6.0-rc11` on 2026-10-17. Its release notes describe a donor-root quorum gate, `force_state_sync` and peer-mesh diagnostics. The version used by the live validator set must be confirmed with the coordinator before installation: binary/config changes are coordinated, and the publication of rc11 does not imply every seat runs it.

Download release artifacts from the exact selected tag; verify each binary against that tag's `MANIFEST.sha256` before installation. Do not pipe the network installer into a shell without inspecting and pinning it. The [run-a-node reference](https://junoclaw.xyz/docs/reference/run-a-node/) has a devnet example with `chain_id = "junoclaw-1"`; **do not copy it to G2**. Obtain the G2 chain ID, `genesis.json`, `node.toml`, peer public keys, assigned validator index, restart anchor and release from the coordinator. At the time of this guide, the G2 deployment uses `junoclaw-g1`; verify it again for each window.

The configuration must point to the local private `keys.json`, genesis and data directory. `validator_index` must match the issued share. Keep P2P 7001 reachable; bind gRPC 9090 privately unless a public query service was separately approved. Never enable `insecure_devnet` on G2.

## Threshold-share ceremony

Generate the identity on the final signer host with the coordinator-approved, checksum-verified ceremony tool. Share only the **public** `share-request.json`. Never send or publish `keys.json`, the encrypted dealings or the finalized BLS share. Check the round, player/dealer IDs, prior group public key and recipient before acknowledgement; finalize locally only after the complete reviewed bundle and coordinator acceptance. Back up private keys through an approved offline custody procedure, never as an ad-hoc transfer to a second live host.

## First start and state sync

Verify the exact release, config/genesis digests, time, disk, peer IDs, and absence of another live signer. Start only in the coordinated window. A restart anchor alone does not import application state. A joining seat may need certified state sync: a snapshot at H must match a certified block at H+1 from enough independent donors. If the chain is halted at H and no H+1 exists, stop and get an explicit coordinator/owner decision before using a halted-chain fallback. rc10's fallback trusted the first donor root despite `min_anchor_agree = 2`; inspect the actual installed rc11 behavior before relying on its new quorum gate.

Preserve consensus, WAL and `mayo_sigs.log` across restarts or recovery. Never reset or restore older signer journals to make a node sync.

## Verify and monitor

A running process is not proof of participation. Confirm authenticated peers, advancing finalized height, stable restart count, and identical digest/app hash at the same height on an independent peer. Confirm this seat's fresh partial signature appears in a finalized certificate; distinguish directly observed evidence from coordinator reports. Alert on finalized-height stalls, clock drift and lost peers. Coordinate every binary/config upgrade across the validator set.

## Sources

- [Validators and G2 requirements](https://junoclaw.xyz/docs/onboarding/validators/)
- [Run a node](https://junoclaw.xyz/docs/reference/run-a-node/)
- [Release artifacts](https://github.com/Dragonmonk111/layer-sdk/releases)
- [Portable JunoClaw operator skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/junoclaw)
