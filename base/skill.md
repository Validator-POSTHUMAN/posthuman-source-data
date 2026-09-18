# Base AI Operations Skill

This tab links the Base-specific AI-agent skill for node operations. The skill
is operator-neutral and provider-neutral: it assumes no particular hosting
provider, L1 provider, cloud or RPC customer, and it contains no production
hosts, RPC credentials or engine secrets.

## Repository

- Skill page: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/base
- SKILL.md: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/base/SKILL.md
- Raw SKILL.md: https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/base/SKILL.md
- Healthcheck script: https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/base/scripts/base-healthcheck.sh

## Read this first: what Base is not

A Base node is a **follower**. It derives the L2 chain from data the sequencer
posts to Ethereum L1 and from the sequencer's gossip feed. It does not propose
blocks, does not attest, holds no consensus key, has no stake and **cannot be
slashed**.

Do not carry Ethereum-staking reflexes across. There is no double-sign risk, no
slashing-protection database, no key uniqueness to prove and no unbonding clock.
Restarting a Base node is safe. Deleting its data directory is safe — the data
is entirely reconstructible from a snapshot.

That inverts the usual priority order. What costs you on Base is not an
irreversible signing mistake; it is **serving wrong answers with confidence**,
missing a wall-clock fork deadline, or publishing an RPC that someone else then
runs their application on.

## The failure this skill exists for

`optimism_syncStatus` reports several heads, and two of them decide everything:

- **`unsafe_l2`** comes from the sequencer's gossip feed and advances every two
  seconds whether or not the node can reach Ethereum.
- **`safe_l2`** advances only when the node has read the batch back from L1.

A node whose unsafe head is at the tip and whose safe head is frozen has stopped
verifying Ethereum and become a sequencer-trusting mirror. The process is up,
the logs are normal, `eth_blockNumber` climbs, `docker compose ps` is green, and
every height-based monitor reports success.

The skill checks `unsafe − safe` and samples the safe head twice, because a
single reading cannot tell "advancing" from "stopped a second ago".

## What it helps agents do

- Verify a node in the right order: `eth_chainId`, `eth_syncing`,
  `optimism_syncStatus`, then an independent comparison against a public
  endpoint — by hash, not only by height.
- Diagnose a frozen safe head as an L1, beacon or blob-availability problem
  rather than a Base problem.
- Restore a V2 snapshot in the order that works: download and place first, node
  stopped, contents directly in the data directory and never nested.
- Choose a node type from what the consumers actually query, and say plainly
  when a request needs an archive node — because the choice cannot be reversed
  after initial sync.
- Separate a routine release from a fork-critical one and drive the upgrade to
  a verified advancing safe head, not to "the container is up".
- Review exposure starting from the shipped `docker-compose.yml`, which
  publishes six ports on `0.0.0.0` past `ufw`, with `debug` in the RPC
  namespace list and wildcard CORS.
- Read zero peers as blocked **egress** to `30301/tcp+udp` and `9200/udp`, not
  as a P2P bug.
- Recognise exit code `8` with `Could not retrieve public IP` as the rollup
  node's IP-discovery step failing, and reach for the systemd path when the
  host has restricted egress.

## Operational scope

- Chain IDs: Base Mainnet `8453` (`0x2105`), Base Sepolia `84532` (`0x14a34`).
  Block time 2 s.
- Ports: public `30303` TCP/UDP and `9222` TCP/UDP; loopback only `8545`,
  `8546`, `7545`, `7300`, `7301`, `6060`; `8551` never published at all.
- Egress to `30301` TCP/UDP and `9200` UDP is required to reach Base bootnodes.
- `base/node` is **archived** since 4 September 2026; releases moved to
  `base/base` at `v1.3.0`. Any runbook that clones `base/node` is stale.
- Cobalt activates on Base Sepolia on 23 September 2026 and on Base Mainnet on
  30 September 2026, and requires release `v1.4.0`, which also deprecates the
  `--rollup.disable-tx-pool-gossip` flag.
- reth `--full` retains **10,064 blocks — about five to six hours on Base**, not
  the days an Ethereum operator would expect.

## Safety boundaries

Read-only by default. The skill broadcasts no transactions, moves no funds,
handles no keys, and does not mutate node state without operator approval.
Approval is required before deleting or replacing a data directory, changing
`NODE_TAG` or unit flags on a production node, restarting a node that serves
production traffic, exposing any port off loopback, or running any `basectl`
subcommand under `conductor`, `sequencer`, `proofs` or `p2p` peer management.

Credential handling is explicit: `BASE_NODE_L1_ETH_RPC` and
`BASE_NODE_L1_BEACON` normally carry a provider API key in the URL path and are
never printed or pasted. `BASE_NODE_L2_ENGINE_AUTH_RAW` ships as a public
constant in `.env.mainnet`, so the skill recommends generating a per-node
secret and treats a reachable Engine API as grounds to distrust the chain data.

`base-healthcheck.sh` is read-only and prints no credential. A passing check is
evidence, not proof.

## Related guides

The full operator set for this network is on the other tabs of this page:
installation, binaries and systemd, snapshots, pruning and storage, RPC and
Flashblocks, monitoring, security hardening, upgrades, useful commands,
troubleshooting, testnets, operator tooling and endpoints.
