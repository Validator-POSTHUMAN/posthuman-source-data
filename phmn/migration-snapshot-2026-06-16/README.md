# PHMN Final Distribution Review Package

This directory is the current public review package for the new PHMN migration.

Russian version: [README_RU.md](README_RU.md)

It supersedes the earlier audit-only migration snapshot package. The files here
are intentionally limited to the final distribution candidate, the review
breakdown, the old-address exclusion/reroute list, final rules, summary, and
checksums.

## Current Status

- Version: `v2_olim_excluded`
- Source snapshot package: `phmn/migration-snapshot-2026-06-16`
- Source data base commit used to build this candidate: `95941d5`
- New PHMN denom: `DENOM_TBD`
- Total new PHMN supply: `131,072.000000 PHMN`
- Recipient rows: `23,456`
- Decimals: `6`

`DENOM_TBD` is intentional during public review. After the new TokenFactory denom
is created, the denom column must be replaced with the real denom, checksums must
be recalculated, and only that final denom-filled CSV should be used for
broadcast.

## Files

- `phmn_final_distribution_broadcast_candidate.csv` - broadcast-shaped
  distribution candidate with columns:
  `recipient_address,amount_micro,amount_phmn,denom`.
- `phmn_final_distribution_broadcast_candidate_breakdown.csv` - review
  breakdown showing the source rows and rules behind the recipient totals.
- `phmn_old_addresses_not_receiving_new_phmn.csv` - old PHMN source addresses
  or accounting rows that do not receive new PHMN on the old address, with the
  reason and destination/handling.
- `PHMN_MIGRATION_FINAL_RULES.md` - final migration rules used by the candidate.
- `summary.json` - machine-readable summary of totals and applied rules.
- `SHA256SUMS` - checksums for this package.

## Review Scope

Community review should focus on:

1. Recipient address correctness.
2. Amount correctness.
3. Excluded incident and Olim-linked rows.
4. SubDAO/core-team treasury reroutes.
5. The unresolved Osmosis accounting gap handling.
6. Any obvious duplicate or missing address.

Old PHMN transfers after the final snapshot do not change this candidate.

## Main Totals

- Total distribution candidate: `131,072.000000 PHMN`
- Olim override routed to Strategic SubDAO: `300.009116 PHMN`
- Strategic SubDAO recipient:
  `cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy`

## Verification

From this directory:

```bash
sha256sum -c SHA256SUMS
```

Expected result: every file reports `OK`.
