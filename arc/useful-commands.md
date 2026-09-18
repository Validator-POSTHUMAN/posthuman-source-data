# Arc Network mainnet — command sheet

Everything here is read-only unless marked. `. ~/.arc_env` first.

## Versions

```sh
arc-node-execution --version
arc-node-consensus --version
arc-snapshots --version

# what the node reports over RPC
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'

# what the network runs
curl -s -X POST https://rpc.mainnet.arc.io -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getVersion","params":[],"id":1}'
```

## Height and agreement

```sh
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# with Foundry
cast block-number --rpc-url http://127.0.0.1:8545
cast block-number --rpc-url https://rpc.mainnet.arc.io

# by hash, which is the check that settles it
H=$(cast block-number --rpc-url http://127.0.0.1:8545)
cast block --rpc-url http://127.0.0.1:8545      "$H" --json | jq -r .hash
cast block --rpc-url https://rpc.mainnet.arc.io "$H" --json | jq -r .hash
```

## Chain identity

```sh
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# 0x13b2 = 5042 mainnet
# 0x4cef52 = 5042002 testnet

cast chain-id --rpc-url http://127.0.0.1:8545
```

## Exposure

```sh
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"rpc_modules","params":[],"id":1}' | jq .result

# pending-tx guard: expect an error with code -32001, not a filter id
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_newPendingTransactionFilter","params":[],"id":1}' | jq .error

# anything here is public
ss -ltnp | grep -vE '127\.0\.0\.1|\[::1\]'
```

## The `arc` namespace

```sh
curl -s -X POST http://127.0.0.1:8545 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"arc_getCertificate","params":[21000000],"id":1}'
```

Requires `--enable-arc-rpc` on the EL and `--rpc.addr` on the CL: the EL
proxies this to the CL's REST API at `127.0.0.1:31000`.

## Gas and fees

```sh
curl -s -X POST https://rpc.mainnet.arc.io -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}'

cast gas-price --rpc-url https://rpc.mainnet.arc.io
cast basefee   --rpc-url https://rpc.mainnet.arc.io
```

The mempool enforces a **20 Gwei `maxFeePerGas` floor**, and the base-fee cap
is `20,000` gwei. A transaction below the floor is not slow, it is rejected.

Gas is USDC: 18 decimals natively, 6 as an ERC-20. One balance, two
representations — never added together.

## Services

```sh
systemctl is-active arc-execution arc-consensus
systemctl status arc-execution --no-pager -l
sudo journalctl -u arc-execution -f
sudo journalctl -u arc-consensus -f
sudo journalctl -u arc-consensus --since "10 min ago" | grep -iE 'err|panic|warn|follow'

# EL first, CL second — always
sudo systemctl restart arc-execution
sudo systemctl restart arc-consensus
```

## Metrics

```sh
curl -s http://127.0.0.1:9001   | head      # execution, served at /
curl -s http://127.0.0.1:29000/metrics | head  # consensus, served at /metrics
```

Different paths. That asymmetry is the usual reason one half of a dashboard is
empty.

## Disk

```sh
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh "$ARC_EXECUTION" "$ARC_CONSENSUS"
ls -l "$ARC_RUN"          # reth.ipc and auth.ipc must both exist
```

## Snapshots

```sh
arc-snapshots download --chain=arc-mainnet --el-profile=full \
  --execution-path "$ARC_EXECUTION" --consensus-path "$ARC_CONSENSUS"

cat "$ARC_EXECUTION"/.snapshot-url 2>/dev/null
cat "$ARC_CONSENSUS"/.snapshot-url 2>/dev/null
```

## Docker

```sh
docker compose ps
docker compose logs -f arc-snapshots
docker compose logs -f
```

Avoid `docker compose config` in a shared terminal — it prints the resolved
environment.

## Destructive — review first

```sh
# Replaces BOTH layers regardless of what they hold.
# arc-snapshots download --chain=arc-mainnet --force ...

# Deletes the consensus-layer private key — your node's network identity.
# It cannot be recovered.
# docker compose down -v
# rm -rf ~/.arc
```

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
