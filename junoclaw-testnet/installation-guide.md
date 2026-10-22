# JunoClaw G2 — validator onboarding and node guide

JunoClaw G2 is an invited, equal-weight public testnet built on Commonware Simplex BFT. Its node binary is `slay3rd`; it is **not** the Cosmos Juno (`junod`) testnet. There is no consensus-layer staking, delegation, slashing or validator-creation transaction. A seat joins only through a coordinated set-change and threshold-key ceremony.

## Before you request a seat

The [official validator guide](https://junoclaw.xyz/docs/onboarding/validators/) requires a dedicated host and network failure domain, a stable public IP, key-only SSH, NTP drift below two seconds and an operator reachable during upgrade windows. Minimum resources are two CPU cores, 4 GB RAM and 20 GB SSD; four cores, 8 GB and 50 GB SSD are recommended. Peers require inbound TCP 7001. gRPC TCP 9090 can remain private.

A second live signer for the same seat is unsafe. Plan active/passive failover and prove the old signer is fenced before starting another.

## Release and configuration

Confirm the **current** fleet build and config with the coordinator for every window. The [official releases](https://github.com/Dragonmonk111/layer-sdk/releases) and their manifests are the preferred provenance source. The 2026-10-22 G2 reshare used a coordinator-distributed rc14 ceremony tool and rc14v3 fleet binary. POSTHUMAN verified the coordinator-supplied binary digest locally, but could not establish its full build commit or independent publisher authenticity. Do not install a forwarded HTTP binary solely because its checksum matches a value from the same message; obtain authenticated provenance and the exact fleet approval first. Earlier rc11/rc12 references are historical, not current install recommendations.

Download only the approved release/package and verify its digest before installation. Do not pipe a network installer into a shell without inspection and pinning. The [run-a-node reference](https://junoclaw.xyz/docs/reference/run-a-node/) has a devnet example with `chain_id = "junoclaw-1"`; **do not copy it to G2**. The 2026-10-22 G2 round used `junoclaw-g1`; reconfirm chain ID, genesis, node config, peer public keys, assigned validator index, threshold, restart anchor and binary for each set change.

The config must point to the local private `keys.json`, genesis and data directory. `validator_index` must match the issued share. Keep P2P 7001 reachable; bind gRPC 9090 privately unless a public query service was separately approved. Never enable `insecure_devnet` on G2.

## Threshold-share ceremony

On 2026-10-22, round 2 expanded the roster to eight seats with a 6-of-8 threshold and five dealers. Independent observation of the complete ceremony logs confirmed the **full previous BLS group public key unchanged**. This records one completed round; future roster, quorum and tool versions require fresh verification.

1. Generate or retain the identity on the final signer with the approved, checksum-verified tool. Share only its public identity request. Never print, send or publish `keys.json`, `dealer.seed`, decrypted shares or the finalized BLS share. Recipient-sealed dealing files can be relayed only to their named recipients through the approved ceremony route; they are not public downloads.
2. Inspect each archive's member types and exact round, player/dealer IDs, recipient and previous group key before extraction. Players acknowledge **every** expected dealer with the pinned tool. Verify the complete acknowledgement set, zero complaints and coordinator acceptance before dealers generate logs. A missing ack can cause a player's share to be revealed in dealer logs.
3. Dealers keep the seed on the signer until the log is generated and verified, then follow the approved retention/cleanup decision. Observe all logs independently and require the full prior group key to remain identical. Finalize against a protected **same-host copy** of the live key, verify the new share index and stage it without replacing the live key before the coordinated window.

## First start, state sync and cutover

Verify the target, exact binary/config/genesis digests, time, disk, peer IDs and absence of another live signer. A restart anchor alone does not import application state. A joining seat may need certified state sync: normally a snapshot at H must match certified H+1 from enough independent donors. If the chain is halted at H and no H+1 exists, stop and obtain the coordinator-approved halted-chain anchor path, donor identity and explicit trust decision. A single-donor `min_anchor_agree = 1` path offers less independent corroboration than multi-donor agreement; inspect the installed binary's actual behavior.

At the coordinated window, stop the prior signer and verify its process and listeners are absent before swapping binary, finalized local key and host-specific config. Preserve protected rollback artifacts and signer journals. Do not wipe app state because another seat was told to do so. Start one service and verify the running binary digest, loaded index/threshold, accepted anchor and stable restart count. Never blindly restore the old key or journal after the new share may have signed.

## Verify and monitor

A running process is not proof of signing. Check authenticated peers, advancing **local** finalized height and matching digest/app hash at a common height on an independent peer. Verify this seat's index in a fresh finalized certificate bitmap; label coordinator-supplied or peer-side evidence as relayed until independently decoded. Alert on finalized-height stalls, clock drift and lost peers. Preserve `data/consensus`, `data/wal` and `data/mayo_sigs.log` across recovery; never roll signer journals back to make a node sync.

## Sources

- [Validators and G2 requirements](https://junoclaw.xyz/docs/onboarding/validators/)
- [Run a node](https://junoclaw.xyz/docs/reference/run-a-node/)
- [Official release artifacts](https://github.com/Dragonmonk111/layer-sdk/releases)
- [Portable JunoClaw operator skill, merged 2026-10-22](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/20ca8ba0f4b9c307fce25160ebc7f57fd130a3e4/junoclaw/SKILL.md) (Git blob `2c54ffc2316f117f8bf2a7e6f55e2b16dcea3521`)
