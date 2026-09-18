# XRPL EVM Mainnet endpoints

All POSTHUMAN endpoints below are public, verified 2026-09-18.

## POSTHUMAN

| Service | Address |
|---|---|
| CometBFT RPC | <https://rpc.exrp.posthuman.digital> |
| Cosmos REST | <https://rest.exrp.posthuman.digital> |
| Cosmos gRPC | `grpc.exrp.posthuman.digital:443` |
| EVM JSON-RPC | <https://rpc.exrp.posthuman.digital/evm> |
| Snapshots | <https://snapshots.exrp.posthuman.digital> |
| P2P peer | `71891d3e4790ca8187d38d7acf40ca881074a06b@peer.exrp.posthuman.digital:62656` |

The published peer is a **non-signing** node with voting power zero. It is not
the validator signer, deliberately: a signer's P2P address is not something to
publish.

```bash
# Cosmos
curl -s https://rpc.exrp.posthuman.digital/status | jq .result.sync_info
curl -s https://rest.exrp.posthuman.digital/cosmos/base/tendermint/v1beta1/node_info | jq .

# EVM
curl -s -X POST https://rpc.exrp.posthuman.digital/evm \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# {"jsonrpc":"2.0","id":1,"result":"0x15f900"}   → 1440000
```

A gRPC root answers HTTP/2 `415` to an ordinary HTTPS request. That is the
expected response, not an outage.

## Official network

| | |
|---|---|
| Documentation | <https://docs.xrplevm.org> |
| Operators section | <https://docs.xrplevm.org/pages/operators> |
| Networks reference | <https://docs.xrplevm.org/pages/operators/resources/networks> |
| Explorer | <https://explorer.xrplevm.org> |
| Governance / validators | <https://governance.xrplevm.org/validators> |
| Node releases | <https://github.com/xrplevm/node/releases> |
| Genesis, peers | <https://github.com/xrplevm/networks/tree/main/mainnet> |
| Discord | <https://discord.gg/xrplevm> |

## Independent public endpoints

Useful as the second opinion every health check needs. Neither is operated by
POSTHUMAN.

| | |
|---|---|
| Official Cosmos RPC | <https://cosmos-rpc.xrplevm.org> |
| Official EVM JSON-RPC | <https://rpc.xrplevm.org> |
| ITRocket services | <https://itrocket.net/services/mainnet/xrplevm/> |
| ITRocket RPC | <https://xrplevm-mainnet-rpc.itrocket.net> |

## Chain identifiers

| | |
|---|---|
| Cosmos chain ID | `xrplevm_1440000-1` |
| EVM chain ID | `1440000` / `0x15f900` |
| Denom | `axrp`, 18 decimals |
| Bech32 prefix | `ethm` (`ethmvaloper` for operators) |
