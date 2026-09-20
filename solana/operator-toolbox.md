# Solana Operator Toolbox

The Solana tooling ecosystem is unusually large and unusually uneven. Most
dashboards measure something real; very few measure the same thing the same way.
This page is a review of what is worth an operator's attention, what each tool
actually answers, and where it will mislead you.

**Rule of thumb:** use third-party surfaces to *explain* a number, never to
*discover* an outage. Discovery belongs to your own monitoring and to
`agave-watchtower`.

## Explorers

| Tool | Use it for | Caveat |
|---|---|---|
| [explorer.solana.com](https://explorer.solana.com/) | official, first-party; accounts, transactions, blocks, validator list, cluster stats | supports `?cluster=testnet` / `devnet`; the reference for "what does the chain actually say" |
| [Solscan](https://solscan.io/) | richest transaction and token decoding, best for tracing stake and reward flows | third-party interpretation; cross-check anything consequential against the official explorer |
| [Solana Beach](https://solanabeach.io/) | validator pages, epoch state, stake movement, at-a-glance cluster view | lags during congestion |
| [solana-foundation/explorer](https://github.com/solana-foundation/explorer) | the open-source explorer itself | the practical base if you want to self-host an explorer rather than build one |

For an operator the explorer question is almost always the same three lookups:
the **vote account** (commission, credits, delinquency, BLS key), the **identity
account** (balance, version in gossip), and the **stake accounts** delegated to
you.

## Validator performance and scoring

| Tool | Answers |
|---|---|
| [validators.app](https://www.validators.app/) | scoring, delinquency history, **data-centre and ASN concentration** — the authoritative view for SFDP concentration criteria; has a notification API |
| [Trillium](https://live.trillium.so/) | per-epoch rewards, MEV, block production, small-block analysis, pool views |
| [ValidBlocks dashboards](https://dashboards.validblocks.com/) | block-level production and validator dashboards |
| [Stakeutils](https://stakeutils.com/) | validator scoring and stake movement |
| [GD Index](https://gdindex.app/) | decentralisation scoring |
| [Pumpkin's Pool watchtower](https://pumpkinspool.com/watchtower/stake-concentration) | stake-concentration views |
| [Jito StakeNet / Steward](https://www.jito.network/) | how Jito scores and allocates to your validator |

**How to read these honestly.** They differ in denominator and in identity
method. Trillium's "small block" label, for instance, is relative to the
completed epoch (`total_cu < p10` OR `user_tx < p10`) — it is a diagnostic
starting point, not a client ranking, a causal finding or a quality verdict.
Version, scheduler mode, region, hosting and cohort composition all move these
views. Treat a disagreement between two dashboards as a question about
methodology, not as evidence of a problem.

The two that matter operationally are **validators.app** (because SFDP
concentration criteria are defined against it) and whichever pool dashboard
governs stake you actually receive.

## Hardware and configuration references

| Tool | Use |
|---|---|
| [solanahcl.org](https://www.solanahcl.org/) | community hardware compatibility list, auto-generated from the `solanahcl` repository — the sanity check before buying |
| [Anza operations docs](https://docs.anza.xyz/operations/validator-or-rpc-node) | first-party requirements, setup, best practices |
| [SIMD tracker](https://simd.mixy.one/) | readable index of Solana Improvement Documents — where Alpenglow, the admission ticket, commission collectors and slot-time changes are specified |
| [Agave feature-gate tracker](https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule) | which feature activates in which epoch — read before every upgrade |

The SIMD tracker deserves a place in the weekly routine. Most of the operational
surprises of the last year — the admission ticket, the commission collector
split, slot-time reductions — arrived as SIMDs months before they changed a
runbook.

## Clients and forks

Classification matters, because "client" is overloaded in Solana discussions:

- **Agave** — the production baseline, maintained by Anza. Everything below
  derives from it unless stated.
- **Jito-Solana** — a fork/distribution of the validator with MEV tips and
  bundles. Widely run; not an independent implementation.
- **Frankendancer** — hybrid: Firedancer networking and block production with
  Agave execution and consensus.
- **Firedancer** — the independent from-scratch C implementation. Read release
  artifacts rather than README wording; the two have disagreed.
- **BAM / FireBAM** — block-assembly and scheduling infrastructure around Jito
  and Firedancer, not clients.
- **Raiku, Rakurai, Harmonic, Flowra** — forks and orderflow stacks at varying
  maturity. Several have published onboarding while core endpoints, program
  addresses or audits were still unpublished.

**Operator rule for any non-baseline client or orderflow stack:** require
commit-pinned source and an upstream diff, reproducible or signed artifacts with
a digest, exact endpoints and program/upgrade authorities, a written
data-retention and orderflow-access policy, and testnet evidence of the failure
and fallback path. Onboarding forms and marketing pages are not adoption
evidence. And note that SFDP expects the client you run on testnet to match the
one you run on mainnet — you cannot pilot a fork on the existing SFDP testnet
node.

## Stake pools and delegation

| Tool | Use |
|---|---|
| [jpool](https://app.jpool.one/) | DAO-governed pool, validator set and scoring |
| [Marinade](https://marinade.finance/) | mSOL, native staking, and the Stake Auction Marketplace |
| [Jito](https://www.jito.network/) | JitoSOL and the Steward scoring that allocates it |
| [Lum Labs pools advisor](https://pools-advisor.lumlabs.io/calculator) | comparison calculator across pools |
| [Solana Foundation delegation criteria](https://solana.org/delegation-criteria) | the criteria your node is actually graded on |

Pool scoring is a moving target governed by DAOs and committees. Read the
current formula before changing anything about the node to satisfy it, and treat
bidding mechanics as a business decision with a real cost.

## Network and connectivity

| Tool | Use |
|---|---|
| [DoubleZero](https://doublezero.xyz/) | dedicated network fabric for shred distribution; `--shred-receiver-address` on the validator |
| [Malbec Labs publisher check](https://data.malbeclabs.com/dz/publisher-check) | verifies DoubleZero publisher status for a validator |
| [Staking Facilities Firedancer dashboard](https://fd-mainnet.stakingfacilities.com/) | public Firedancer-oriented cluster view |

DoubleZero changes the shred path, so it belongs in the same change-control
class as a client upgrade: verify the route, the receiver address and the
retransmit evidence in logs after enabling it, not just that the daemon is up.

## Governance

`svmgov` is the validator-side CLI for the SVM governance process — proposal
support and formal votes. Two things operators get wrong:

- `support_proposal` is a **signed on-chain transaction** that contributes your
  active stake toward the 15% activation threshold. It is not a read-only
  action and it is not a vote.
- A formal vote is separate, happens in a defined epoch window after activation,
  and requires an allocation whose For/Against/Abstain basis points total 10,000.

Install a commit-pinned official CLI, list proposals, and get an explicit
decision per proposal ID before signing anything. See the governance guide.

## AI and agent tooling

The Solana Foundation maintains [awesome-solana-ai](https://github.com/solana-foundation/awesome-solana-ai),
an index of agent frameworks, MCP servers and SDKs around Solana. For validator
operations specifically the useful subset is narrow: RPC access skills, explorer
and validator-metric lookups, and read-only monitoring helpers. Anything that
offers to sign, delegate or move funds on your behalf belongs behind an explicit
human approval, not inside an automation.

## What we run

POSTHUMAN's own Solana operations use: Anza docs as the source of truth,
`agave-watchtower` on a separate host for delinquency, `node_exporter` plus
RPC-derived gauges for the metrics in the monitoring guide, validators.app for
concentration criteria, Trillium for per-epoch reward analysis, and the SIMD
tracker in the weekly review. Everything else on this page is consulted, not
depended on.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
