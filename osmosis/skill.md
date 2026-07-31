# Osmosis Validator Operations AI Skill

POSTHUMAN maintains an original, validator-neutral Osmosis operations skill.
It does not contain production hosts, ports, keys, credentials, addresses, or
private topology.

## Immutable release

- Package: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/SKILL.md
- Inventory schema: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/references/inventory.schema.json
- Fake inventory example: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/examples/inventory.example.json
- Healthcheck: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/scripts/osmosis-healthcheck.sh
- Deterministic tests: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/scripts/osmosis-healthcheck-test.sh
- Evaluation scenarios: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/716461ccdf8aafb68b84c5ed851b42d9a2f111e2/osmosis/evals/osmosis-skill-scenarios.md

## Coverage

- consensus freshness, reference-height gap, peers, version, disk, and restarts;
- recent validator signing, staking status, jailed/tombstoned state;
- bounded critical and Osmosis-module log counters;
- Cosmovisor upgrade preparation and post-upgrade verification;
- snapshot provenance, safe layout, signer-state, staging, and rollback gates;
- separate non-signing RPC/REST/gRPC publication requirements;
- IBC incident triage without broad node or relayer restarts;
- transaction approval gates for unjail, staking, governance, and validator edits.

The helper is read-only. It does not restart services, modify configuration,
write keys, sign transactions, or broadcast.

## Example

```bash
osmosis-healthcheck.sh \
  --host <ssh-target> \
  --service <osmosis-systemd-service> \
  --rpc http://127.0.0.1:<rpc-port> \
  --public-rpc https://<independent-rpc> \
  --valcons <HEX_CONSENSUS_ADDRESS> \
  --valcons-bech32 <osmovalcons...> \
  --valoper <osmovaloper...>
```

Load the skill together with your own non-secret inventory before using it for
alert triage, upgrades, public-service changes, or recovery.
