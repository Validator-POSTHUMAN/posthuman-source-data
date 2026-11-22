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

The penalties documented so far come from **unanswered jobs**; FLOP has not published full slashing rules. There is no pause, so the skill keeps any planned outage within half of the job deadline.

The skill is operator-neutral. It never authorizes:
- creating a replacement miner account;
- running `miner register` by hand;
- requesting a second sponsorship;
- printing key material or session tokens;
- removing Docker volumes.

Read the [reviewed SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/53ed75664dce6067dea7e25598f2b50551b09fe3/flop/SKILL.md) (Git blob `3e0edf71778fa612827ff21e751027193b677a65`) and the [installation guide](/node-ops/flop-devnet/installation).
