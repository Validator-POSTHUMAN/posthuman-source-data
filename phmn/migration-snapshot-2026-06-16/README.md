# PHMN Migration Snapshot - 2026-06-16

This directory contains the public PHMN migration snapshot package.

The package is intended to let PHMN holders check old Juno, Osmosis, Neutron,
and BeeZee addresses and see the snapshot amount attributed to each address.

## How to Check an Address

Use phmn_address_lookup.csv.

Search for your old address in the source_address column.

Important columns:

- snapshot_amount_phmn - PHMN amount found in the final snapshot for that
  source address.
- distribution_status - how this row is handled in the new PHMN distribution.
- effective_destination_cosmos_address - destination for rows that are paid
  directly or rerouted.
- destination_note - explanation for reroutes, exclusions, and quarantined
  rows.

## Distribution Status Values

- eligible_snapshot - normal snapshot row. The amount is expected to be
  included for the holder according to the published migration rules.
- rerouted_to_subdao - the old address is a SubDAO/core-team treasury source.
  The amount is sent to the listed new SubDAO Cosmos treasury instead of the old
  address.
- excluded_incident - incident-related address. This is not treated as a
  normal holder allocation.
- quarantined_unresolved_accounting_gap - unresolved accounting gap, not
  mapped to a user address.

## Main Files

- phmn_address_lookup.csv / .json - easiest file for public address checks.
- phmn_final_snapshot_user_attribution.csv / .json - grouped by normalized
  Cosmos address and includes direct/voucher, DAS staked, and pending-claim
  components.
- phmn_final_snapshot_expanded_rows.csv / .json - source-level accounting
  rows used to build the lookup.
- osmosis_phmn_holders_for_distribution.csv / .json - all Osmosis PHMN
  holder rows, including the marked core-team Osmosis balance.
- subdao_reroute_adjustments.csv / .json - SubDAO/core-team reroute rules.
- special_addresses.csv / .json - incident and operator-reviewed special
  address groups.
- distribution_status_summary.csv / .json - totals by distribution status.
- PHMN_MIGRATION_FINAL_SNAPSHOT_POLICY.md - human-readable migration policy.
- snapshot_package_metadata.json - machine-readable package metadata.
- SHA256SUMS - file checksums.

## Snapshot Rule

The snapshot is based on old PHMN ownership across Juno, Osmosis, Neutron, and
BeeZee. IBC escrow double-counting is corrected. Old PHMN transfers after the
snapshot publication do not change the new PHMN distribution.

Decimals: 6.

See PHMN_MIGRATION_FINAL_SNAPSHOT_POLICY.md for the full rules.
