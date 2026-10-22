# JunoClaw validator skill

The [JunoClaw G2 validator operations skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/junoclaw) covers coordinated threshold reshares, single-signer cutovers, halted-chain state sync, advancing finality and independent signing evidence.

The 2026-10-22 round expanded G2 to eight seats with a 6-of-8 threshold and five dealers, preserving the prior full BLS group public key. Those values are historical, not defaults for the next ceremony. The skill requires every dealer to wait for the complete accepted acknowledgement set before logging; a missing acknowledgement may reveal a player's share.

The skill is operator-neutral: private host inventory, approved binaries, coordinator messages and key custody stay with the operator. It never authorizes copying a private share, running two signers, resetting signer journals or changing the validator set. The rc14v3 fleet binary used for this round was checksum-verified locally but not independently tied to an official release; obtain authenticated provenance before a new installation.

Read the [reviewed SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/20ca8ba0f4b9c307fce25160ebc7f57fd130a3e4/junoclaw/SKILL.md) (Git blob `2c54ffc2316f117f8bf2a7e6f55e2b16dcea3521`) and the [installation guide](/chains/junoclaw-testnet).
