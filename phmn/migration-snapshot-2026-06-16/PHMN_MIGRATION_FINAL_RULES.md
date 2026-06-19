# PHMN Migration Final Rules

## Purpose

POSTHUMAN is preparing a migration from the old PHMN token to a new PHMN
TokenFactory token on Cosmos Hub.

The final distribution candidate keeps the old token cap:

`131,072 PHMN`

The package in this directory is for final public review before creating the new
denom and preparing the final broadcast file.

## Snapshot Scope

The final candidate is based on old PHMN ownership across:

- Juno
- Osmosis
- Neutron
- BeeZee

IBC escrow double-counting is corrected. Old PHMN locked in Juno IBC escrow is
not counted together with destination-chain voucher ownership.

Old PHMN transfers after the final snapshot publication do not change the new
PHMN distribution.

## Distribution Rules

### 1. Normal Eligible Holders

Rows with normal eligible ownership receive new PHMN at the effective normalized
Cosmos destination address.

### 2. Attacker and Incident Exclusions

The following are not paid to their old source addresses:

- confirmed attacker cluster;
- compromised minter address;
- other incident-related rows explicitly marked as excluded.

Their amounts are routed to Strategic SubDAO handling.

### 3. Olim-Linked Exclusion

Operator-confirmed Olim-linked clusters are excluded from the direct new PHMN
drop.

In this final candidate, one Olim source row has nonzero PHMN:

- `juno1eltl6qu6y538vhux3mk3pjpn7redx8najm4u3e`
- `300.009116 PHMN`
- source type: DAS staked

This amount is routed to the Strategic SubDAO treasury, not to the old
normalized Cosmos address.

The `juno187...` cluster is tracked as Olim-linked by investigation evidence,
but has `0 PHMN` in this PHMN distribution candidate and therefore does not
change the PHMN totals.

### 4. SubDAO and Core-Team Treasury Reroutes

Old treasury, SubDAO, and marked core-team source balances are not sent back to
the old source addresses.

They are rerouted to the new SubDAO treasury addresses listed in the
distribution candidate and the old-address exclusion/reroute list.

### 5. Unresolved Osmosis Accounting Gap

The remaining unresolved Osmosis accounting gap is not safely mapped to a user
address.

It is quarantined and routed to Strategic SubDAO handling.

Remaining unresolved gap:

`57.230100 PHMN`

### 6. Remaining Capacity

The old PHMN cap is `131,072 PHMN`; corrected old PHMN supply is lower than the
cap.

The unminted remaining capacity is routed to the Strategic SubDAO treasury.

### 7. Strategic SubDAO Recipient

Strategic SubDAO treasury:

`cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy`

This recipient receives:

- excluded incident amounts;
- Olim-linked excluded amount;
- unresolved accounting gap;
- remaining capacity;
- Strategic SubDAO treasury reroutes.

## Denom Rule

The current CSV uses:

`DENOM_TBD`

This is not the final broadcast denom.

After creating the new TokenFactory denom:

1. Replace `DENOM_TBD` with the real denom.
2. Recalculate `SHA256SUMS`.
3. Publish the denom-filled final package.
4. Use only the denom-filled broadcast CSV for real distribution.

## Current Candidate Summary

- Version: `v2_olim_excluded`
- Recipient rows: `23,456`
- Total: `131,072.000000 PHMN`
- Olim override rows: `1`
- Olim override amount: `300.009116 PHMN`
