# Avalanche CLI Sheet

> These commands query a local AvalancheGo API on `127.0.0.1:9650`. They do
> not sign or broadcast transactions. Source for the endpoint and methods:
> [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc).

```bash
API=http://127.0.0.1:9650
```

## Version and network identity

`info.getNodeVersion` returns the AvalancheGo version, Git commit, database
version, VM versions, and plugin RPC protocol; `info.getNetworkName` returns
the selected network. Source: [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc#infogetnodeversion).

```bash
curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.getNodeVersion"}' \
  "$API/ext/info" | jq '.result'

curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.getNetworkName"}' \
  "$API/ext/info" | jq -r '.result.networkName'
```

## Health and bootstrap

The unfiltered `/ext/health` response is the aggregate health view recommended
for operators. `info.isBootstrapped` checks one chain alias at a time. Sources:
[Health RPC](https://build.avax.network/docs/rpcs/other/health-rpc), [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc#infoisbootstrapped).

```bash
curl -fsS "$API/ext/health" | jq '{healthy, checks}'

for chain in P X C; do
  curl -fsS -H 'content-type:application/json' \
    --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"info.isBootstrapped\",\"params\":{\"chain\":\"$chain\"}}" \
    "$API/ext/info" | jq -r --arg chain "$chain" '"\($chain): \(.result.isBootstrapped)"'
done
```

## NodeID, peers, and observed uptime

`info.getNodeID` returns the public validator identity and BLS proof,
`info.peers` returns active peers, and `info.uptime` reports stake-weighted peer
observations of this node. Source: [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc#infogetnodeid).

```bash
curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.getNodeID"}' \
  "$API/ext/info" | jq '.result'

curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.peers","params":{"nodeIDs":[]}}' \
  "$API/ext/info" | jq '{numPeers:.result.numPeers}'

curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.uptime"}' \
  "$API/ext/info" | jq '.result'
```

## P-Chain height and validator record

`platform.getHeight` returns the current P-Chain height.
`platform.getCurrentValidators` can filter by NodeID once validation has
started. Source: [P-Chain RPC](https://build.avax.network/docs/rpcs/p-chain).

```bash
curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"platform.getHeight"}' \
  "$API/ext/bc/P" | jq -r '.result.height'

NODE_ID='NodeID-...'
curl -fsS -H 'content-type:application/json' \
  --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"platform.getCurrentValidators\",\"params\":{\"nodeIDs\":[\"$NODE_ID\"]}}" \
  "$API/ext/bc/P" | jq '.result.validators'
```

## C-Chain execution height

The C-Chain EVM JSON-RPC endpoint is `/ext/bc/C/rpc`; `eth_blockNumber`
returns the latest block number visible to that API. Sources: [node RPC paths](https://build.avax.network/docs/nodes/run-a-node/from-source#rpc), [C-Chain API](https://build.avax.network/docs/rpcs/c-chain).

```bash
curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  "$API/ext/bc/C/rpc" | jq -r '.result'
```

## Prometheus metrics

AvalancheGo exposes Prometheus-format node metrics at `/ext/metrics` when the
Metrics API is enabled; the node option defaults to enabled. Sources:
[monitoring guide](https://build.avax.network/docs/nodes/maintain/monitoring), [configuration flags](https://build.avax.network/docs/nodes/configure/configs-flags#apis).

```bash
curl -fsS "$API/ext/metrics" | grep -E \
  'avalanche_(health_checks_failing|resource_tracker_disk_available_percentage|stake_percent_connected|snowman_polls_(successful|failed))'
```
