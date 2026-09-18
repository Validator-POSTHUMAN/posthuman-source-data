# Bitcoin AI Operations Skill

This tab links the Bitcoin-specific AI-agent skill for node, RPC, Lightning and mining operations. The skill is operator-neutral and provider-neutral: it assumes no particular pool, wallet, hosting provider, explorer, custody arrangement or cloud, and it contains no production hosts, RPC credentials, wallet material or channel state.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/bitcoin
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/bitcoin/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/bitcoin/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/bitcoin/scripts/bitcoin-healthcheck.sh

## Read this first: Bitcoin has no validator set

Bitcoin has no staking, no delegation, no commission, no jail and no slashing. There is nothing to register, nothing to bond, nothing to unjail, and no consensus key to double-sign with. Proof-of-stake reflexes carried over from Cosmos, Ethereum or Solana produce wrong answers here.

The one place with double-signing-shaped risk is **Lightning**, and it is severe: broadcasting an outdated channel commitment lets the counterparty take the channel balance. Apply validator-grade single-instance discipline to a Lightning node — one running instance, one channel database, never a restored copy alongside the original.

## What it helps agents do

- Verify a Bitcoin Core node: chain, height against headers, `verificationprogress`, `initialblockdownload`, peers, inbound reachability, disk and mempool state.
- Compare the local tip **hash** against independent public sources rather than the height, so a node on a different chain at the same height is not reported as healthy.
- Choose and verify pruning, `assumeutxo`, `txindex` and the optional indexes, including which choices cost a full reindex to change later.
- Review the RPC and indexer surface: cookie versus `rpcauth`, ZMQ topics, Electrum and Esplora backends.
- Operate LND and Core Lightning: channel backups, the recovery paths each backup actually permits, and the force-close and sweep behaviour to expect.
- Review a mining setup honestly, including the solo-block arithmetic, which is the figure most public material gets wrong.
- Plan and verify upgrades, including the v30.0 and v31.0 default changes that break runbooks written before them.
- Triage incidents and write a concise operator report.

## Operational scope

- Ports: mainnet `8333`/`8332`, testnet3 `18333`/`18332`, testnet4 `48333`/`48332`, signet `38333`/`38332`, regtest `18444`/`18443`.
- Current release line: Bitcoin Core `v31.1`. `v28.x` and older receive no updates.
- Public read APIs used for independent comparison: `mempool.space/api` and `blockstream.info/api`.

## Safety boundaries

The skill is read-only by default. It does not move funds, open or close channels, broadcast transactions, generate or move keys, or mutate services. Wallet, channel, mining-payout and firewall changes stay behind the operator's own approvals.

`bitcoin-healthcheck.sh` is a read-only check and prints no credential. A passing check is evidence, not proof: confirm sync, chain agreement, reachability and backups independently before calling a node healthy.

## Related guides

The full operator set for this network is on the other tabs of this page: installation, Docker install, configuration, pruning and storage, RPC and indexes, Lightning node, mining, monitoring, security hardening, backup and recovery, useful commands, upgrades, troubleshooting, testnets and the operator toolbox.
