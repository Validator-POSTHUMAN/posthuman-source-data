# FLOP miner skill

The [FLOP miner operations skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/flop) covers a GPU inference miner on the FLOP devnet public path.

It covers:
- preflight: genesis, account dry run, digest-pinned images, model identity and the allowlisted decode policy;
- sponsorship replies;
- the backend, endpoint and worker start order;
- calibration;
- read-only health checks;
- the downtime budget;
- safe retirement.

A FLOP miner is penalised for **unanswered jobs**, not for double-signing. There is no pause, so the skill keeps any planned outage within half of the job deadline.

The skill is operator-neutral. It never authorizes:
- creating a replacement miner account;
- running `miner register` by hand;
- requesting a second sponsorship;
- printing key material or session tokens;
- removing Docker volumes.

Read the [reviewed SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/672a1ea567d44aaa2c70ea8343d1cc6f6ef493c0/flop/SKILL.md) (Git blob `e4ae10322f1464eb3e4398a2aad1318fba13b0a7`) and the [installation guide](/chains/flop-devnet).
