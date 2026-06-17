# PHMN Recovery Checklist

Last updated: 2026-06-18

This checklist tracks what has already been completed for the old PHMN to new
PHMN migration, and what still needs to happen before the new PHMN TokenFactory
token is created on Cosmos Hub and distributed.

The authoritative snapshot package remains the CSV/JSON files in this
directory. This checklist is a progress tracker, not a replacement for the
snapshot files or the migration policy.

## Current Goal

Restore PHMN by:

1. Creating a new PHMN TokenFactory token on Cosmos Hub.
2. Distributing new PHMN according to the final old-PHMN snapshot and published
   migration rules.
3. Creating a new POSTHUMAN DAS controlled by the new PHMN.
4. Opening a one-week lock window for holders.
5. Adding staged liquidity only after the lock window ends.
6. Using part of the Liquidity SubDAO funds for buybacks from the new pools
   after liquidity is restored.

## Completed

- [x] Confirmed the old Juno CW20 PHMN minter compromise and unauthorized mint.
- [x] Collected and published incident-related address evidence for the
      confirmed attacker/minter cluster.
- [x] Created the final ownership snapshot across Juno, Osmosis, Neutron, and
      BeeZee.
- [x] Corrected IBC escrow double-counting so bridged PHMN is counted at the
      final holder chain instead of being double-counted on Juno.
- [x] Published `phmn_address_lookup.csv` / `.json` so holders can search old
      source addresses and see snapshot amounts and distribution status.
- [x] Published `phmn_final_snapshot_expanded_rows.csv` / `.json` for
      source-level accounting.
- [x] Published `phmn_final_snapshot_user_attribution.csv` / `.json` for
      grouped holder attribution by normalized Cosmos address.
- [x] Expanded the old POSTHUMAN DAS staking contract row into per-user active
      stake and pending-claim rows.
- [x] Identified and published SubDAO treasury reroute rules for the new
      Strategic SubDAO and Liquidity SubDAO.
- [x] Applied the 2026-06-17 Osmosis gap correction for
      `osmo1z0e05ptv5hpfh4lp54373t86zxquv3y5vkfm5p`.
- [x] Added Osmosis pool liquidity audit files showing PHMN currently held by
      Osmosis pool accounts.
- [x] Published distribution status totals in
      `distribution_status_summary.csv` / `.json`.
- [x] Published SHA-256 checksums for the package files.

## Current Public Snapshot State

- Corrected old PHMN snapshot total: `121,822.000000 PHMN`.
- New PHMN maximum supply target: `131,072.000000 PHMN`.
- Remaining reserve/cap difference to be controlled by the new Strategic
  SubDAO: `9,250.000000 PHMN`, before applying any additional quarantine or
  excluded-balance routing policy.
- `phmn_address_lookup.csv`: source-level lookup rows for public address search.
- `phmn_final_snapshot_user_attribution.csv`: grouped holder attribution rows
  by normalized Cosmos address.
- Current package row counts: `phmn_address_lookup.csv` has `26,030`
  source-level data rows, and `phmn_final_snapshot_user_attribution.csv` has
  `23,476` grouped holder rows.
- Current unresolved Osmosis accounting gap after correction:
  `57.230100 PHMN`.
- Current DAS unattributed residual: `0.010001 PHMN`.
- Current Osmosis pool-account PHMN audit total: `65.821395 PHMN`.

## Decisions Already Made

- [x] Old PHMN transfers after the final snapshot publication do not affect the
      new PHMN distribution.
- [x] Old SubDAO treasury balances are rerouted to the new SubDAO treasuries,
      not sent back to old treasury addresses.
- [x] LP-provider PHMN that cannot yet be attributed to individual LP share
      holders will be temporarily routed to a Strategic SubDAO bucket until the
      LP holders are resolved.
- [x] The remaining Osmosis unresolved accounting gap will be routed to a
      quarantine / Strategic SubDAO bucket.
- [x] The DAS unattributed residual will be routed to the new Strategic SubDAO.
- [x] Confirmed attacker/minter/excluded rows will not be distributed to the old
      source addresses. They will be handled by DAO-controlled policy buckets.
- [x] The new recovery order is: create new PHMN, distribute by final snapshot,
      create the new DAS, open a one-week lock window, then restore liquidity
      in staged tranches.

## Remaining Before Token Creation and Distribution

- [ ] Generate the final distribution CSV from the public snapshot package.
      This must be a broadcast-ready file, not an audit-only file.
- [ ] Apply all destination overrides in that final CSV: SubDAO reroutes, LP
      temporary bucket, Osmosis unresolved gap bucket, DAS residual bucket,
      attacker/minter exclusions, and any other quarantine rows.
- [ ] Verify the final distribution CSV totals exactly to
      `131,072.000000 PHMN` at micro-PHMN precision.
- [ ] Publish a clear status summary showing how much new PHMN goes to normal
      eligible holders, Liquidity SubDAO, Strategic SubDAO reserve, temporary
      LP bucket, unresolved/quarantine buckets, and excluded incident buckets.
- [ ] Build a transaction/address evidence graph for the incident-related
      addresses and publish the graph source data.
- [ ] Review the graph for false-positive links before using it for exclusion
      decisions.
- [ ] Verify Cosmos Hub TokenFactory live parameters before broadcasting:
      denom creation fee, denom format and length, metadata support, gas
      requirements, creator/admin controls, and mint authority controls.
- [ ] Decide and document the exact mint/admin authority model: DAO/multisig
      control or another enforceable no-extra-mint policy.
- [ ] Generate distribution transactions from the final CSV in dry-run or
      generate-only mode.
- [ ] Verify batch size, gas, fees, and total outputs before signing.
- [ ] Broadcast the distribution transactions.
- [ ] Preserve transaction hashes and publish post-distribution reconciliation.

## Evidence Graph Review Rules

The evidence graph must separate strong evidence from ordinary on-chain
activity. A connection is not enough by itself.

Do not treat these as automatic attacker links:

- shared DEX or swap contracts used by many users;
- liquidity pool contracts or pool module addresses;
- IBC escrow addresses;
- router contracts;
- SubDAO treasury payments;
- normal PHMN transfers between known community, team, or operator addresses;
- address interactions that only prove use of a common contract.

Each graph edge should be classified by type:

- direct PHMN transfer;
- direct gas funding transfer;
- swap / DEX interaction;
- IBC transfer;
- bridge / CCTP transfer;
- contract call through a shared contract;
- SubDAO treasury transfer;
- known benign operator or community interaction;
- unresolved weak link.

Operator-provided benign-context addresses must be used as controls when
reviewing the graph. One known high-activity PHMN sender address is:

- `juno1e8238v24qccht9mqc2w0r4luq462yxttdl93mj`

This address having interacted with Olim or other PHMN users must not be
treated as attacker evidence by itself.

## After Distribution

- [ ] Create the new POSTHUMAN DAS controlled by the new PHMN.
- [ ] Announce the new DAS and the one-week PHMN lock window.
- [ ] Team locks its new PHMN in the new POSTHUMAN DAS during the lock window.
- [ ] Wait one week for other holders to lock.
- [ ] Add new PHMN liquidity in staged tranches after the lock window ends.
- [ ] Use part of the Liquidity SubDAO funds for buybacks from the new PHMN
      liquidity pools.
- [ ] Publish final liquidity and buyback transaction references.

## Public Files To Watch

- `README.md`
- `PHMN_MIGRATION_FINAL_SNAPSHOT_POLICY.md`
- `phmn_address_lookup.csv`
- `phmn_final_snapshot_user_attribution.csv`
- `phmn_final_snapshot_expanded_rows.csv`
- `subdao_reroute_adjustments.csv`
- `distribution_status_summary.csv`
- `osmosis_phmn_pool_liquidity_audit.csv`
- `SHA256SUMS`
