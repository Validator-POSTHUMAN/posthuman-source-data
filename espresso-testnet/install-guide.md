# Espresso Decaf Testnet — Node and Validator Setup

Decaf is Espresso's persistent testnet, used to rehearse integrations and node
setups before mainnet. **Every command and environment variable is identical to
mainnet** — only the L1, contract addresses, endpoints and genesis file differ.

Follow the full procedure in the
[Espresso node and validator guide](/node-ops/espresso/installation), then
substitute the values below. Monitoring and hardening are unchanged:

- [Monitoring](/node-ops/espresso/monitoring)
- [Security hardening](/node-ops/espresso/security-hardening)

Verified against the official operator documentation on 2026-09-16.

---

## Decaf values

|                      | Decaf testnet                                                     |
| -------------------- | ----------------------------------------------------------------- |
| L1                   | Ethereum Sepolia                                                  |
| Container image      | `ghcr.io/espressosystems/espresso-network/espresso-node:20260910` |
| Genesis file         | `/genesis/decaf.toml`                                             |
| Stake table contract | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037`                      |
| Query service        | `https://query.decaf.testnet.espresso.network`                    |
| Config cache         | `https://cache.decaf.testnet.espresso.network`                    |
| State relay          | `https://state-relay.decaf.testnet.espresso.network`              |
| Block explorer       | `https://explorer.decaf.testnet.espresso.network`                 |
| Staking UI           | `https://stake.decaf.espresso.network/`                           |

### Sepolia contracts

| Contract     | Address                                      |
| ------------ | -------------------------------------------- |
| Stake Table  | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037` |
| ESP Token    | `0xb3e655a030e2e34a18b72757b40be086a8f43f3b` |
| Reward Claim | `0xe81908e34dbb4ba01f27f8769264199727be50c8` |
| Light Client | `0x303872bb82a191771321d4828888920100d0b3e4` |

---

## Environment differences

```bash
ESPRESSO_NODE_GENESIS_FILE=/genesis/decaf.toml
ESPRESSO_STATE_RELAY_SERVER_URL=https://state-relay.decaf.testnet.espresso.network
ESPRESSO_NODE_STATE_PEERS=https://query.decaf.testnet.espresso.network
ESPRESSO_NODE_API_PEERS=https://query.decaf.testnet.espresso.network

# First start only:
ESPRESSO_NODE_CONFIG_PEERS=https://cache.decaf.testnet.espresso.network

# Sepolia, not Ethereum mainnet:
ESPRESSO_L1_PROVIDER=https://<your-sepolia-rpc>
ESPRESSO_L1_WS_PROVIDER=wss://<your-sepolia-ws-rpc>
```

`staking-cli` takes `--network decaf` wherever the mainnet guide uses
`--network mainnet`, and `STAKE_TABLE_ADDRESS` becomes the Sepolia address
above.

---

## Getting a delegation

Decaf ESP is not publicly distributed. A registered Decaf node stays out of
consensus until the Espresso team delegates to it.

1. Register the validator and start the node, exactly as on mainnet.
2. Confirm it is registered and reachable:
   `staking-cli --network decaf stake-table-entry --address $VALIDATOR_ADDRESS`.
3. Ask for a delegation in `#decaf-node-ops` on the
   [Espresso Discord](https://discord.gg/espresso).

The node joins consensus once that delegation is active — 2 epochs after the
Sepolia transaction finalizes.

---

## What Decaf is good for

Rehearse anything you would not want to get wrong on mainnet with real ESP:

- `register-validator` and the exact metadata document;
- `update-consensus-keys` and the third-epoch activation window;
- `update-network-config` after moving the node to a new host or DNS name;
- `deregister-validator` → `claim-validator-exit` and the ~7-day escrow;
- `unclaimed-rewards` / `claim-rewards` against a query service;
- the whole monitoring and alerting stack, before it matters.

Sepolia gas is free; mainnet mistakes are not.

---

## Official resources

- Run a Validator Node: <https://docs.espressosys.com/network/developer/operators/run-a-node>
- Networks & contracts: <https://docs.espressosys.com/network/network/networks>
- Discord: <https://discord.gg/espresso>
