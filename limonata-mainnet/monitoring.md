# Health, signing and DKG monitoring

Monitor disk/inodes, memory, clock synchronization, service restart count, peers, latest block time/height and catching_up. A live process, peers or catching_up=false alone do not prove progression.

Compare against independent Comet RPCs for `limonata_20777-1`. Validators additionally require bonded/not-jailed state, positive power, slashing signing-info/missed-block checks and fresh commit signatures for their exact consensus address. Validate REST and EVM identity separately; eth_chainId must equal 0x5129.

For the encrypted mempool, inspect committed `encmempool_dkg_round_opened` and `encmempool_dkg_finalized` events with current official source/API semantics. Verify committee membership, evaluation points and finalized QUAL. Threshold is weighted evaluation points, not merely validator count. Bonding or ordinary block production does not prove DKG readiness. The approved binary has no query encmempool CLI.

Routine maintenance requires an ACTIVE epoch with no open DKG round, unique signer control and retained DKG identity. After restart verify ECIES key permissions/persistence without printing it, then fresh signatures and current committee/readiness. On a network-wide stall or ambiguous DKG transition retain evidence and coordinate rather than cycling services.

Use independent RPC fallback and height-lag/missed-signature alerts. Scrape private metrics only; never expose pprof or management APIs. Record timestamps, public heights and event IDs without logging secrets or private topology. See [Read-only commands](useful-commands.md).

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
