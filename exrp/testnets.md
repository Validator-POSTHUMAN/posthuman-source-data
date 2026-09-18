# XRPL EVM test networks

Three networks, three chain IDs, three version lines. The one mistake that
matters is applying a testnet schedule to mainnet.

| Network | Cosmos chain ID | EVM chain ID | Line |
|---|---|---|---|
| Mainnet | `xrplevm_1440000-1` | `1440000` / `0x15f900` | `v10.2.x` |
| Testnet | `xrplevm_1449000-1` | `1449000` / `0x161c28` | `v10.1.0`+ / `v11` |
| Devnet | `xrplevm_1449900-1` | `1449900` | `v11.x` |

The `v11` tags in the release list are the testnet and devnet line. They are
not a mainnet upgrade until a mainnet proposal passes and the Networks table
gains its row.

## Testnet

| | |
|---|---|
| Genesis | <https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/testnet/genesis.json> |
| Peers | <https://raw.githubusercontent.com/xrplevm/networks/main/testnet/peers.txt> |
| POSTHUMAN RPC | <https://rpc.exrp-testnet.posthuman.digital> |
| POSTHUMAN REST | <https://rest.exrp-testnet.posthuman.digital> |
| POSTHUMAN gRPC | `grpc.exrp-testnet.posthuman.digital:443` |
| POSTHUMAN snapshots | <https://snapshots.exrp-testnet.posthuman.digital> |
| POSTHUMAN peer | `e80a91daedb88e1dc429ab60036b3819bb48057d@peer.exrp.posthuman.digital:61656` |

Installation is identical to mainnet with three substitutions:

```bash
exrpd config set client chain-id xrplevm_1449000-1
exrpd init <moniker> --chain-id xrplevm_1449000-1
```

```toml
# app.toml
[evm]
evm-chain-id = 1449000
```

## Devnet

| | |
|---|---|
| Chain ID | `xrplevm_1449900-1` |
| EVM chain ID | `1449900` |
| Genesis | <https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/devnet/genesis.json> |
| Peers | <https://raw.githubusercontent.com/xrplevm/networks/main/devnet/peers.txt> |

Devnet runs the newest code first — it took `v11` at height `2089191` on
2026-06-29, long before either of the other networks. Snapshots are not always
published; state sync or a genesis sync may be the only options.

## Use the testnet as a rehearsal, not as a demo

The value of a testnet validator to a mainnet operator is that it makes the
next mainnet upgrade boring:

1. Take the upgrade on testnet first, with the same Cosmovisor layout, the same
   unit files and the same runbook you will use on mainnet.
2. Record the exact plan name, what the logs looked like at the switch, and how
   long the pre-upgrade backup took.
3. Feed anything surprising back into the runbook before the mainnet height.

The advisory board asks for exactly this — testnet participation and a
published test report are among the named validator contributions.

## Do not cross the streams

- Separate `priv_validator_key.json` per network. A key is per network; reusing
  one is not a shortcut, it is a way to lose two validators at once.
- Separate homes, separate ports, separate systemd units. POSTHUMAN uses
  `626xx` for mainnet and `616xx` for testnet on shared hosts precisely so a
  mistyped port cannot reach the wrong chain.
- Separate monitoring. A testnet alert that pages the mainnet rotation trains
  people to ignore pages.

## Faucet and explorers

| | |
|---|---|
| Testnet explorer | <https://explorer.testnet.xrplevm.org> |
| Governance / validators | <https://governance.xrplevm.org/validators> |
| Discord (`#faucet`, `#become-a-validator`) | <https://discord.gg/xrplevm> |
