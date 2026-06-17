# PHMN Migration: Final Snapshot and Distribution Rules

## Short Summary

POSTHUMAN is preparing a migration from the old PHMN token to a new PHMN token
on Cosmos Hub using TokenFactory.

The new PHMN token will keep the same maximum supply as the old one:

`131,072 PHMN`

Before creating and distributing the new token, we are publishing a final
snapshot of old PHMN ownership. This snapshot will be used as the base for the
new PHMN distribution.

After this snapshot is published, any transfers of old PHMN will not change the
new PHMN distribution. If an old PHMN balance changes after publication, that
change will be ignored for migration purposes.

## Why We Are Doing This

The old PHMN token contract on Juno had a compromised minter. Because of that,
an unauthorized mint happened.

To protect PHMN holders and make future governance safer, POSTHUMAN will move
PHMN to a new TokenFactory token on Cosmos Hub.

The new setup is designed so that:

- users receive new PHMN based on the final published snapshot;
- excluded incident-related addresses do not receive new PHMN;
- SubDAO treasury balances are moved to new SubDAO treasuries;
- all undistributed and reserve PHMN is controlled by the new Strategic SubDAO;
- no single person can release large PHMN amounts without SubDAO approval.

## Final Snapshot Rule

The final migration snapshot is based on old PHMN balances across:

- Juno
- Osmosis
- Neutron
- BeeZee

The snapshot is corrected for IBC accounting.

This is important because old PHMN is a CW20 token on Juno. When PHMN is moved
to Osmosis or Neutron through IBC, the original CW20 tokens remain locked in
Juno IBC escrow contracts, while voucher tokens appear on the destination
chains.

For this reason, we do not simply add Juno + Osmosis + Neutron raw balances.
That would double-count the same PHMN.

The corrected accounting model is:

1. Count normal Juno holders.
2. Exclude Juno IBC escrow contract balances.
3. Count actual Osmosis, Neutron, and BeeZee PHMN voucher holders instead.
4. For multi-hop IBC, count the final holder chain when verified.
5. Keep unresolved accounting gaps in quarantine until they are understood.

The corrected old PHMN supply is:

`121,822 PHMN`

A later BeeZee check found `0.904878 PHMN` that moved from Osmosis to BeeZee. This does not change the corrected total. It only changes the final owner mapping for that small amount: the Osmosis channel escrow row is replaced by the three BeeZee holder rows.

The old contract cap is:

`131,072 PHMN`

The remaining capacity that was not minted under the old token is:

`9,250 PHMN`

## What Happens After Publication

Once this snapshot is published:

- old PHMN transfers after publication will not be counted;
- old PHMN sales or purchases after publication will not change the new
  distribution;
- the final distribution will use the published snapshot and correction rules;
- any later movement of old PHMN is irrelevant for the new token migration.

This protects users from last-minute balance manipulation and gives everyone a
clear public reference point.

## Excluded and Quarantined Balances

Some balances will not be distributed to the old snapshot address.

These include:

- confirmed attacker address cluster;
- compromised minter address, unless the team later publishes a different
  explicit decision;
- addresses and related clusters excluded by the incident investigation;
- unresolved accounting rows that cannot yet be safely mapped to a user.

The confirmed attacker cluster currently holds:

`15,100 PHMN`

The compromised minter address currently holds:

`2,032.149313 PHMN`

These balances will not be treated as normal user allocations.

Excluded and quarantined PHMN will remain under DAO-controlled handling instead
of being distributed to incident-related or unclear addresses.

## SubDAO Treasury Rerouting

Some old PHMN belongs to POSTHUMAN SubDAO treasuries.

These balances are visible in the snapshot, but they should not be sent back to
the old treasury addresses. They will be redirected to the new SubDAO treasury
addresses.

### New Strategic SubDAO

DAO:

https://daodao.zone/dao/cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy

New Cosmos treasury:

`cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy`

Old SubDAO treasury balances rerouted to Strategic SubDAO New:

`3,276.387140 PHMN`

### New Liquidity SubDAO

DAO:

https://daodao.zone/dao/cosmos1pu90e2gm2kq9lvheqzrh0tl9dw5aqg6v5gr9jug2eqdel0vzuxkqvg72nn

New Cosmos treasury:

`cosmos1pu90e2gm2kq9lvheqzrh0tl9dw5aqg6v5gr9jug2eqdel0vzuxkqvg72nn`

Old Liquidity SubDAO treasury balances and the marked core-team Osmosis PHMN
balance rerouted to Liquidity SubDAO New:

`30,371.280659 PHMN`

This includes the core-team Osmosis address
`osmo1hyjhy0tp6geral2g9vj9nyteglf8t5q4pqwre8` with
`12,661.704217 PHMN`. That amount is sent to Liquidity SubDAO in the final
distribution, not to the old Osmosis address.

These reroutes do not change the total PHMN supply. They only change the
destination address for treasury-owned PHMN in the new distribution.

## New Token Minting Plan

The new PHMN token on Cosmos Hub will be created with the same maximum supply as
the old PHMN token:

`131,072 PHMN`

POSTHUMAN plans to mint the full amount immediately.

Then:

- the eligible snapshot amount will be distributed to users and treasury
  destinations according to the published rules;
- excluded or quarantined balances will not be sent to excluded addresses;
- all remaining PHMN will go to the new Strategic SubDAO treasury.

The Strategic SubDAO will be responsible for future PHMN allocations such as
stake-drops and reserves.

The goal is that no large PHMN amount can be released to the market without a
governance proposal and multisig approval. The intended control policy is at
least 3 of 5 signers.

## What Users Need To Do

At this stage, regular users do not need to move old PHMN.

The important rule is:

Do not rely on old PHMN transfers after the final snapshot publication.

If you transfer old PHMN after the snapshot is published, the new PHMN
distribution will still use your balance from the published snapshot.

## Published Files

The following files are the current migration accounting artifacts.

### Corrected ownership snapshot

`canonical_ownership_current_with_beezee.csv`

This is the corrected ownership-oriented snapshot. It excludes Juno IBC escrow
double-counting, resolves the verified BeeZee multi-hop IBC balance, and
reconciles to:

`121,822 PHMN`

SHA-256:

`32540b083eaef52cc1b9c33d045d8df443f91d0e3e460a61416ad34fdf438075`

The previous corrected snapshot without the BeeZee holder expansion was:

`canonical_ownership_current.csv`

Its total was already correct, but `0.904878 PHMN` was still mapped to the
Osmosis channel escrow address instead of the BeeZee end holders.

### Supply accounting correction report

`PHMN_SUPPLY_ACCOUNTING_CORRECTION_RU_2026-06-16.md`

SHA-256:

`169f9a37a7edd52c767e3b3b1339700c6625edf15a639f27b3f877743260e7ab`

### BeeZee IBC correction report

`PHMN_BEEZEE_IBC_CORRECTION_2026-06-16.md`

SHA-256:

`2633b03ff92c32d4e90e419c69423007da5c455bd37704fc4b42c94bc043ed5e`

### SubDAO reroute adjustment

`subdao_reroute_adjustments.csv`

SHA-256:

`3c52160e6484a1d5b56a495e3cf595a87c26f3c5ca09bbfa2530a75c441dd5a9`

## Plain-Language Meaning

In simple terms:

- we took a final snapshot of old PHMN balances;
- we corrected it so PHMN bridged to Osmosis, Neutron, and BeeZee is not counted twice;
- transfers after publication will not affect the migration;
- attacker and incident-related addresses will not receive new PHMN as normal
  holders;
- SubDAO treasury PHMN will move to the new SubDAO treasuries;
- the new token will have the same total limit as before;
- the remaining PHMN reserve will be controlled by the new Strategic SubDAO.
