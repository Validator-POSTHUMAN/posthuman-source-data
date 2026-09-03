# Axelar Validator Operations Skill

This page links the reviewed, validator-neutral Axelar operations skill. It
covers the classic validator plane (`axelard`, `vald`, a dedicated `tofnd`, the
broadcaster account, and external-chain maintainers) and the separately
isolated Amplifier verifier plane (`ampd`, an Amplifier-only `tofnd`, and one
handler/client pair per supported chain).

## Immutable release

- Repository: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks
- Reviewed merge commit: `3cf8bc02be02ca411c1ceffc0df0eeaf8090a652`
- Package: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/SKILL.md
- SKILL.md SHA-256: `ee1f14058a68ae881b8929d2d10cf0e3214ca4123b72d849aa726cee5c97106c`
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/references/inventory.schema.json
- Fake inventory example: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/examples/inventory.example.json
- Classic healthcheck: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/scripts/axelar-healthcheck.sh
- Amplifier healthcheck: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/scripts/axelar-amplifier-healthcheck.sh
- Monitoring reference: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/references/monitoring.md
- Safe recovery reference: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/references/safe-recovery.md
- Snapshot verifier: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/scripts/axelar-snapshot-verify.sh
- Evaluation scenarios: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/3cf8bc02be02ca411c1ceffc0df0eeaf8090a652/axelar/evals/axelar-skill-scenarios.md

## Coverage

### Classic validator plane

- exact network, host, service, binary, release, backup, rollback, and signer
  identity preflight;
- consensus freshness, local/reference height, peers, recent signatures,
  bonded/jailed state, disk, restarts, and bounded errors;
- independent `vald` and classic `tofnd` health and private-listener checks;
- broadcaster proxy mapping, fee balance, account sequence, transaction
  inclusion, and concurrent-account-use detection;
- expected-versus-observed external-chain maintainer membership, RPC identity,
  finality health, and submitted/late/missing votes;
- staged upgrades, incident isolation, snapshot verification, signer-state
  preservation, reversible cutover, and post-recovery acceptance.

### Amplifier verifier plane

- a separate Axelar full node and separate `tofnd` from the classic validator;
- exact `ampd`, handler, chain-client, contract-deployment, and chain-registry
  review;
- one independently supervised handler and operator-controlled full node or
  reviewed light client per supported chain;
- process, listener, Axelar freshness, handler/client parity, `/status`,
  `/metrics`, vote, multisig-proof, reward, funding, and authorization checks;
- independent failure domains so one handler incident does not restart
  unaffected handlers, `ampd`, or the classic validator stack.

## Safety boundaries

The skill contains no POSTHUMAN production hosts, private endpoints, keys,
credentials, signer state, wallet secrets, or real operator inventory.

It never auto-creates a validator, generates or moves keys, stakes, signs,
broadcasts, registers a broadcaster, changes maintainer support, bonds an
Amplifier verifier, registers public keys or chain support, authorizes a
verifier, or mutates services. A classic transaction may only be prepared as
an unsigned `--generate-only` document for separate review. Amplifier
activation stays a non-runnable review record.

The classic and Amplifier planes must not share `tofnd`. Signer uniqueness must
be proven before any start, migration, or recovery. Signer, gRPC, handler, and
monitoring listeners stay on loopback or an explicitly reviewed private
network; passwordless signer containers and wildcard signer binds are rejected.

## How to use

1. Download `axelar/SKILL.md` from the immutable commit above.
2. Verify its SHA-256 is exactly
   `ee1f14058a68ae881b8929d2d10cf0e3214ca4123b72d849aa726cee5c97106c`.
3. Load it together with the operator's private inventory for the exact Axelar
   role and target.
4. Use the classic or Amplifier read-only healthcheck only after every required
   inventory field is resolved.
5. Refresh current releases, network artifacts, deployment contracts,
   parameters, and advisories before any production change.
6. Keep custody, signing, broadcast, registration, authorization, funding,
   firewall exposure, data replacement, and service mutation behind their
   separate operator-controlled approvals.

A passing helper check is evidence, not proof of all duties. Complete each
plane's acceptance gate with independent chain, signer, vote, handler,
monitoring, and public-state evidence before claiming health.
