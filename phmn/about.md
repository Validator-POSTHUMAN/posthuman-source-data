# PHMN — POSTHUMAN Ecosystem Token

PHMN is the governance token of the POSTHUMAN ecosystem. In June 2026 PHMN migrated from a CW20 contract on Juno to a native TokenFactory token on Cosmos Hub.

## Token

| Parameter | Value |
|-----------|-------|
| Chain | Cosmos Hub (`cosmoshub-4`) |
| Denom | `factory/cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy/PHMN` |
| Symbol | PHMN |
| Decimals | 6 |
| Max supply | 131,072 PHMN |
| Type | `sdk.coin` (TokenFactory) |
| Creator / admin | Strategic Treasury SubDAO |

The TokenFactory admin is a SubDAO, not a personal wallet. No single person can mint or release PHMN without SubDAO approval.

## Governance

PHMN governs POSTHUMAN via [DAO DAO](https://daodao.zone) on Cosmos Hub:

- [POSTHUMAN DAS](https://daodao.zone/dao/cosmos1lj6knrgumqr5a9jxmkqeag476gmzgn24mv0w3548tyw6a5ryr7ms6xl599) — main governance space; lock PHMN to vote
- [Strategic Treasury SubDAO](https://daodao.zone/dao/cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy) — holds undistributed and reserve PHMN; 3 of 5 votes required
- [Liquidity SubDAO](https://daodao.zone/dao/cosmos1pu90e2gm2kq9lvheqzrh0tl9dw5aqg6v5gr9jug2eqdel0vzuxkqvg72nn) — manages PHMN liquidity pools
- [Reputation SubDAO](https://daodao.zone/dao/cosmos1nxxz937qd6zqxllwplydy6hts97c4amaqj8jxa57nsme3dmckk4s3mqujr) — RESP token authority

## Why the token migrated

The minter of the old CW20 PHMN contract on Juno was compromised and an unauthorized mint happened. To protect holders and make supply control safer, PHMN moved to a new TokenFactory token on Cosmos Hub with SubDAO-controlled supply. Details are in the **migration** tab.

## Resources

- [Official migration statement](https://github.com/Validator-POSTHUMAN/new-dao-structure/blob/main/docs/official-phmn-migration-statement.md)
- [new-phmn](https://github.com/validator-POSTHUMAN/new-phmn) — migration data, snapshots, distribution rules
- [new-dao-structure](https://github.com/Validator-POSTHUMAN/new-dao-structure) — DAO and SubDAO registry
- [Public explainer (EN)](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/reports/PHMN_PUBLIC_EXPLAINER_EN_2026-06-16.md) / [RU](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/reports/PHMN_PUBLIC_EXPLAINER_RU_2026-06-16.md)
