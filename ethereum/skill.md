# Ethereum AI Operations Skill

This tab links the Ethereum-specific AI-agent skill for node and validator
operations. The skill is operator-neutral and provider-neutral: it assumes no
particular hosting provider, relay, staking pool, custody arrangement or cloud,
and it contains no production hosts, RPC credentials, mnemonics or keystores.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/ethereum
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/ethereum/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/ethereum/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/ethereum/scripts/ethereum-healthcheck.sh

## Read this first: one irreversible mistake

Ethereum staking has exactly one action you cannot undo — **running the same
validator key in two places at once**. Two processes signing for one public key
produce a slashable double vote: the stake is cut, the validator is
force-exited, and the penalty scales with how many others are slashed alongside
you.

The asymmetry that decides every incident: an offline validator loses a few
cents an hour, a double-signing validator loses ETH and is ejected. **Uptime
never justifies a second instance.**

Note what an attacker with the validator signing key *cannot* do: move your
funds. Withdrawals go to the withdrawal address and the signing key cannot
change that. The signing key is a slashing liability, not a theft liability —
which is why it may live on a networked server and the mnemonic may not.

## What it helps agents do

- Verify a node properly: chain ID, `eth_syncing`, and the Beacon API's
  `is_syncing`, **`is_optimistic`** and `sync_distance` — then the head slot
  against an independent source.
- Catch the failure that looks healthy. A beacon node in optimistic mode has
  every service active, a normal log and an advancing head, and its validator's
  attestations are worthless. systemd and height-based monitors all report it as
  fine.
- Triage missed attestations in frequency order — clock, optimistic status,
  Engine API, peers, disk, key count — instead of guessing.
- Choose a client pair as an operational decision, with the 33% and 66%
  diversity thresholds and current shares from a live source.
- Run the validator lifecycle: key generation on an offline machine,
  withdrawal-credential choice, deposit, activation, fee recipient, doppelganger
  protection, exits, partial withdrawals and consolidations.
- Move keys safely: the fixed non-overlapping order, with the EIP-3076 slashing
  protection interchange, and the rule that restoring a keystore without its
  slashing database is a slashing event waiting to happen.
- Separate a routine client update from a fork deadline, and verify after both.
- Review network exposure, including the fact that Docker publishes ports past
  ufw and that listeners, not firewall rules, are the evidence.

## Operational scope

- Ports: public `30303` TCP/UDP and `9000`/`9001`; loopback only `8545`, `8546`,
  `8551`, `5052`, `18550` and every metrics port.
- Mainnet chain ID `1`, deposit contract
  `0x00000000219ab540356cBB839Cbe05303d7705Fa`. Staking testnet is **Hoodi**
  (`560048`); Holesky is deprecated and shut down.
- Fork state: Deneb, Electra/Pectra and Fulu/Fusaka are active on mainnet;
  Glamsterdam is next and unscheduled. Fusaka's BPO forks are fork-critical.
- Pectra predeploys: withdrawal requests
  `0x00000961Ef480Eb55e80D19ad83579A64c007002`, consolidation requests
  `0x0000BBdDc7CE488642fb579F8B00f3a590007251`.

## Safety boundaries

The skill is read-only by default. It does not generate or move keys, broadcast
transactions, submit deposits, exits or consolidations, move funds, or mutate
services. Those stay behind the operator's own approvals. It refuses to proceed
when validator key uniqueness cannot be proven, and says so.

`ethereum-healthcheck.sh` is a read-only check and prints no credential. A
passing check is evidence, not proof: for a validator, confirm attestation
inclusion externally over the last two epochs before calling it healthy.

## Related guides

The full operator set for this network is on the other tabs of this page:
installation across every client pair, Docker install, create validator,
pruning and storage, archive node, endpoints, upgrades, useful commands,
monitoring, security hardening, troubleshooting, testnets and operator tooling.
