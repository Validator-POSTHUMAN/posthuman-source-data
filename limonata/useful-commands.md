# Limonata Testnet — Useful Commands

Replace `LIMONATA_HOME` if your node uses a non-default home directory.

```bash
export LIMONATA_HOME="$HOME/.limonatad"
export LIMONATA_RPC="http://127.0.0.1:26657"
export OFFICIAL_RPC="https://cosmos-rpc.limonata.xyz"
```

## Version and service

```bash
limonatad version --long
systemctl is-active limonatad.service
systemctl is-enabled limonatad.service
sudo journalctl -u limonatad.service --since '15 minutes ago' --no-pager
```

## Sync status

```bash
curl -fsS "$LIMONATA_RPC/status" | jq '.result.sync_info | {
  latest_block_height,
  latest_block_time,
  catching_up
}'

curl -fsS "$OFFICIAL_RPC/status" | jq '.result.sync_info | {
  latest_block_height,
  latest_block_time,
  catching_up
}'
```

Compare both heights after 30 seconds. A healthy node advances and eventually
reports `catching_up: false`.

## Peer count

```bash
curl -fsS "$LIMONATA_RPC/net_info" | jq '{n_peers: .result.n_peers}'
```

## Chain identity

```bash
curl -fsS "$LIMONATA_RPC/status" | jq -r '.result.node_info.network'
limonatad status --home "$LIMONATA_HOME" 2>&1 |
  jq '.node_info.network, .sync_info.catching_up'
```

Expected Cosmos chain ID: `limonata_10777-1`. The EVM chain ID is `10777`.

## Validator state

Run this only for a validator you operate:

```bash
limonatad query staking validator <cosmosvaloper...> \
  --node "$OFFICIAL_RPC" --output json |
  jq '.validator // . | {status, jailed, tokens, moniker: .description.moniker}'
```

Do not expose local RPC, REST, gRPC, EVM RPC, metrics, or pprof merely to run
these checks. Loopback access is sufficient.
