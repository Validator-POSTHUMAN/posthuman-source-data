# Solana AI Validator Skill

The [Solana validator operations skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/21f42c37c4789f49ba391168d548294e9ac056ab/solana) covers validator and RPC-node installation, restarts, upgrades, identity cutovers, monitoring, SFDP checks, and incident diagnosis on Solana mainnet and testnet. It supports Agave and its forks, but does not cover governance voting or application development.

## Read the skill

- [SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/21f42c37c4789f49ba391168d548294e9ac056ab/solana/SKILL.md) (Git blob `016855acca26e0ed1aca139c14a62565a9b7345d`)
- [Raw SKILL.md](https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/21f42c37c4789f49ba391168d548294e9ac056ab/solana/SKILL.md)
- [Operations reference](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/21f42c37c4789f49ba391168d548294e9ac056ab/solana/references/operations.md)
- [Monitoring and security reference](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/21f42c37c4789f49ba391168d548294e9ac056ab/solana/references/monitoring-security.md)
- [Troubleshooting reference](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/21f42c37c4789f49ba391168d548294e9ac056ab/solana/references/troubleshooting.md)
- [Evaluation scenarios](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/21f42c37c4789f49ba391168d548294e9ac056ab/solana/examples/evaluation-cases.md)

## Safety boundaries

The skill is operator-neutral and contains no POSTHUMAN server inventory or credentials. Before acting, supply your own target, cluster, service, identity and key-custody information, then verify current flags and requirements against official Solana and Agave sources. A staked identity must never vote on two hosts at once; cutovers require tower continuity and `--require-tower`. Do not expose the authorized withdrawer. Key movement, transactions, data deletion and public RPC exposure require operator approval. Confirm signing with two advancing external vote and root samples, not only a running process.
