# PHMN Migration (2026)

Old PHMN — CW20 on Juno (`juno1rws84uz7969aaa7pej303udhlkt3j9ca0l3egpcae98jwak9quzq8szn2l`) — was replaced by new PHMN, a TokenFactory token on Cosmos Hub. The reason: the old contract minter was compromised and an unauthorized mint happened.

## Timeline

1. Final snapshot of old PHMN ownership published — later transfers of old PHMN do not change the distribution.
2. **2026-06-22** — new PHMN distributed to holders according to the snapshot and rules in [new-phmn](https://github.com/validator-POSTHUMAN/new-phmn).
3. One-week window to lock new PHMN in the new [POSTHUMAN DAS](https://daodao.zone/dao/cosmos1lj6knrgumqr5a9jxmkqeag476gmzgn24mv0w3548tyw6a5ryr7ms6xl599).
4. After the lock window — liquidity pools with new PHMN (see the **liquidity pools** tab).

## Snapshot rules (short version)

- Snapshot covers all networks and IBC locations where old PHMN existed, corrected for IBC escrow double-counting. Corrected old supply: **121,822 PHMN**.
- Confirmed attacker cluster and incident-related addresses are excluded.
- Old SubDAO treasury balances moved to the new SubDAO treasuries.
- All undistributed and reserve PHMN is controlled by the [Strategic Treasury SubDAO](https://daodao.zone/dao/cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy).

Full rules: [README (EN)](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/README.md) / [RU](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/README_ru.md)

## Old addresses that did not receive new PHMN

Some old addresses (contracts, modules, escrows, incident cluster) do not receive new PHMN directly. The public register with reasons:

- [Register (EN)](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/reports/PHMN_OLD_ADDRESSES_NOT_RECEIVING_NEW_PHMN_REGISTER.md) / [RU](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/reports/PHMN_OLD_ADDRESSES_NOT_RECEIVING_NEW_PHMN_REGISTER_RU.md)

## Data and verification

- [Final snapshot and distribution CSVs](https://github.com/validator-POSTHUMAN/new-phmn/tree/main/snapshots)
- [SHA256 checksums](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/checksums/SHA256SUMS)
- [Incident reports and analysis](https://github.com/validator-POSTHUMAN/new-phmn/tree/main/reports)
