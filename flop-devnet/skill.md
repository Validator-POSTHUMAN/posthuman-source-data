# FLOP miner skill

The [FLOP miner operations skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/flop) covers a GPU inference miner on the FLOP devnet public path.

It covers:
- preflight: genesis, account dry run, digest-pinned images, model identity and the allowlisted decode policy;
- sponsorship replies;
- the backend, endpoint and worker start order;
- calibration;
- read-only health checks, including the worker's own readiness;
- signer-fence recovery and the IPv4-first fix for hosts without IPv6;
- the downtime budget;
- safe retirement.

The penalties documented so far come from **unanswered jobs**; FLOP has not published full slashing rules. There is no pause, so the skill keeps any planned outage within half of the job deadline.

The skill is operator-neutral. It never authorizes:
- creating a replacement miner account;
- running `miner register` by hand;
- requesting a second sponsorship;
- printing key material or session tokens;
- removing Docker volumes.

Read the [reviewed SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/a9865bbc00bb3d47a3909e415b73eca99ddbe289/flop/SKILL.md) (Git blob `dee4264970cb7793656327e030d40264af3af11d`) and the [installation guide](/node-ops/flop-devnet/installation).
