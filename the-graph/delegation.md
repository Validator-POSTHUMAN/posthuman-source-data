# The Graph — Delegating GRT

How to delegate GRT to an Indexer on The Graph Network, what the numbers mean,
and what changed under Graph Horizon.

The protocol runs on **Arbitrum One**. GRT and gas must be on Arbitrum One, not
Ethereum mainnet. Bridge first if your GRT is on L1.

---

## POSTHUMAN Indexer

| Field | Value |
| --- | --- |
| Indexer address | `0x0874e792462406dc12EE96b75E52A3BdbBA3a123` |
| Query endpoint | `https://index.web34ever.com/` |
| Indexing reward cut | 35% indexer / 65% delegators |
| Query fee cut | 85% indexer / 15% delegators |
| Profile | [Graph Explorer](https://thegraph.com/explorer/profile/0x0874e792462406dc12EE96b75E52A3BdbBA3a123?view=Indexing&chain=arbitrum-one) |

Delegate directly: <https://thegraph.com/explorer/delegate?chain=arbitrum-one>

---

## Prerequisites

- A wallet (MetaMask or any EVM wallet) connected to **Arbitrum One**.
- GRT on Arbitrum One.
- A small amount of ETH on Arbitrum One for gas.

---

## How to delegate

1. Open <https://thegraph.com/explorer/delegate?chain=arbitrum-one> and connect
   your wallet. Confirm the network selector shows Arbitrum One.
2. Pick an Indexer. Under Graph Horizon you also pick a **data service** —
   currently `SubgraphService`, the data service for subgraph indexing. The
   official UI only supports SubgraphService today.
3. Enter the amount, approve the GRT spend, then confirm the delegate
   transaction. Two transactions on a first delegation: `approve`, then
   `delegate`.
4. Verify on the Indexer's profile page that your delegation appears under
   the Delegators list, and that your own profile shows the position.

### Undelegating

1. Open your profile, select the delegation, and submit **Undelegate**.
2. Wait out the **28-day thawing period**. During that window the tokens earn
   no rewards and cannot be moved.
3. After 28 days, submit **Withdraw** to return GRT to your wallet. The
   withdrawal is a separate transaction; tokens do not arrive automatically.

Horizon allows multiple undelegation requests in flight at once. The Graph's
own docs quote two different caps for this (100 in the Horizon change notes,
1,000 in the delegator docs) — treat it as "many, not one" and check the UI
for the current limit rather than relying on either number.

---

## What changed under Graph Horizon

| Topic | Before | Under Horizon |
| --- | --- | --- |
| Delegation target | Indexer only | Indexer **and** data service (`SubgraphService`) |
| Delegation tax | 0.5% burned on delegate | **Removed entirely** |
| Undelegation requests | One at a time | Many simultaneously |
| Slashing of delegation | Not possible | Technically possible, **not enabled**; indexer stake is slashed first |
| Reward cuts | Global staking parameters | Set per data service |
| Existing delegations | — | Auto-migrated to `SubgraphService`, no action needed |

The 28-day thawing period and the reward formula did not change.

---

## Choosing an Indexer

Four numbers decide your yield. Read them before delegating, not after.

### 1. Indexing reward cut

The share the Indexer keeps. Cut `100%` means delegators receive **nothing**.
A profile showing `1,000,000` in raw subgraph data is 100%, not a large number
of tokens — the field is parts-per-million.

### 2. Query fee cut

Same idea, applied to query fee rebates.

### 3. Delegation capacity

The network delegation ratio is **16**: an Indexer can put at most
`16 × self-stake` of delegated GRT to work.

```
capacity     = self_stake × 16
head_room    = capacity − currently_delegated
```

Delegating past capacity dilutes rewards for **every** delegator on that
Indexer, including the ones who were there first. Check head room first.

Worked example, POSTHUMAN BrightWave, verified 2026-09-17 at epoch 1383:

```
self-stake   328,485 GRT
capacity     328,485 × 16 = 5,255,766 GRT
delegated      990,213 GRT
head room    ~4,265,553 GRT
```

### 4. Whether the Indexer actually allocates

An Indexer that does not allocate its stake earns no indexing rewards, so its
delegators earn no indexing rewards either. On the profile, compare
`allocatedTokens` against `stakedTokens + delegatedTokens`.

**Dead profiles are the most common delegator mistake.** A retired Indexer can
keep an Explorer page, keep showing delegated GRT, and pay nothing — zero
stake, zero allocations, 100% cut. Two such profiles exist in POSTHUMAN's own
history; both still hold stranded delegation. Before delegating, confirm the
profile has non-zero self-stake **and** non-zero allocated tokens.

### Verifying the numbers yourself

Every value above comes from the network subgraph rather than from any
dashboard's presentation of it:

```graphql
{
  indexer(id: "0x0874e792462406dc12ee96b75e52a3bdbba3a123") {
    stakedTokens
    delegatedTokens
    allocatedTokens
    indexingRewardCut
    queryFeeCut
    url
  }
}
```

Addresses must be lowercase. Amounts are in wei-scale GRT (18 decimals); cuts
are parts-per-million (`350000` = 35%).

---

## Risks

- **28-day exit.** Undelegation is not instant and earns nothing while
  thawing. Choose an Indexer you are willing to stay with.
- **Over-delegation.** Delegating beyond capacity dilutes everyone's yield.
- **Cut changes.** An Indexer can raise its cut later. Re-check periodically.
- **Future slashability.** Horizon adds the technical capability for delegated
  stake to be slashed. It is not enabled for SubgraphService today, and indexer
  stake would be slashed first, but watch governance proposals.
- **Gas.** Delegating, undelegating and withdrawing are each on-chain
  transactions on Arbitrum One.

---

## Useful tools

| Tool | Use |
| --- | --- |
| [Graph Explorer](https://thegraph.com/explorer) | Official profiles, delegation UI, ROI estimate |
| [GraphSeer](https://graphseer.com/indexers) | Indexer and deployment analytics |
| [graphtools.pro](https://graphtools.pro/delegators/) | Delegator activity log, refreshed every 8h |
| [Indexer Tools](https://indexer-tools.vincenttaglia.com) | Allocation and subgraph dashboards |

A wider review of the ecosystem tooling is on the **Tooling** tab.

---

## Related

- [Installation guide](https://nodes.posthuman.digital/chains/the-graph?tab=installation-guide)
- [Monitoring](https://nodes.posthuman.digital/chains/the-graph?tab=monitoring)
- [Security hardening](https://nodes.posthuman.digital/chains/the-graph?tab=security-hardening)
- Official docs: <https://thegraph.com/docs/en/resources/roles/delegating/delegating/>
- Graph Horizon: <https://thegraph.com/docs/en/graph-horizon/overview/>
