# Validator admission and activation

The final genesis has 17 initial validators. The release states a maximum active set of 100 and defers some operators to post-launch onboarding. This is not proof of unrestricted admission, current capacity or a grant allocation.

1. Obtain current official post-launch admission instructions. Confirm economic requirements, grant restrictions, power caps and exact account/operator/consensus identities. A synced full node is not a bonded validator.
2. Existing genesis validators must retain the same mainnet home, consensus and P2P identities associated with their accepted gentx. Prove the consensus key cannot sign anywhere else before activation. Never reinitialize the home, copy another validator's key, or reuse testnet data.
3. Before any create-validator, grant, delegation or unjail transaction, query live staking/slashing/fee parameters, sequence, spendable funds and eligibility. Keep the wallet outside the validator home. Verify Cosmos/EVM address conversion; mainnet uses aLIMO with 18 decimals and EVM chain 20777.
4. Review the unsigned payload, consensus public key, self-delegation, commission, minimum self-delegation, fees and gas. Simulate and approve the exact operation using the official current workflow. No generic broadcast or fixed-fee command is provided because admission is not established here.
5. Verify inclusion with code 0, bonded/not-jailed state, positive power and fresh commit signatures from independent RPC. Also confirm current epoch DKG membership and readiness; bonding alone proves neither.

Downtime jail and tombstoning differ. Resolve the cause and query current eligibility before reviewing one unjail transaction; never retry broadcasts automatically. A wallet mnemonic is not consensus recovery material.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
