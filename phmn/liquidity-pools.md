# PHMN Liquidity Pools

PHMN liquidity is managed by the [Liquidity SubDAO](https://daodao.zone/dao/cosmos1pu90e2gm2kq9lvheqzrh0tl9dw5aqg6v5gr9jug2eqdel0vzuxkqvg72nn) under a mandate from PHMN governance.

## Pools

| Pool | DEX | Seed liquidity |
|------|-----|----------------|
| PHMN/USDC | BeeZee | 6,857 PHMN / 11,575 USDC |
| PHMN/BTC | Osmosis | 6,857 PHMN / BTC (from 11,575 USDC swap) |

## How the liquidity was formed

1. **Controlled pool + buyback.** Liquidity SubDAO solely seeded a PHMN/USDC pool (27,313 PHMN / 11,624 USDC, 0% swap fee) and bought back **13,598.69 PHMN** with 11,526 USDC in a single transaction. A proprietary pool eliminates frontrunning, sandwich attacks and bot speculation that a large market order in a public pool would suffer.
2. **Result.** Pool price after buyback ≈ **1.69 USDC per PHMN**; excess supply from the unauthorized mint removed from circulation.
3. **Split into two pools.** The remaining liquidity was split into two equal halves: a **PHMN/USDC** pool on BeeZee DEX, and a **PHMN/BTC** pool on Osmosis DEX (the USDC half swapped to BTC).
4. **Bought-back PHMN** (13,598.69) is held in the Liquidity SubDAO treasury and can be used only for new PHMN pools or per decisions voted by PHMN holders locked in POSTHUMAN DAS.

Full calculation and rationale: [EN](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/liquidity-pools/liquidity-subdao-pool-and-buyback_en.md) / [RU](https://github.com/validator-POSTHUMAN/new-phmn/blob/main/liquidity-pools/liquidity-subdao-pool-and-buyback.md)
