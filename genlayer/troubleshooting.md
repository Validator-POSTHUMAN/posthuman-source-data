# Troubleshooting
## A. flag: password is required

Your container is starting genlayernode run without --password.

**Fix:**

set NODE_PASSWORD in .env

**ensure docker-compose.yaml entrypoint includes:**
```bash
entrypoint: ["sh", "-c", "/app/bin/genlayernode run --password ${NODE_PASSWORD:-12345678}"]
```
## B. resolve ConsensusMain address from AddressManager: no contract code at given address

You are using the wrong upstream RPC endpoint.

Typical bad example:

generic zkSync Sepolia RPC
random public RPC unrelated to GenLayer

Good test:

```bash
curl -s -X POST https://rpc-asimov.genlayer.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xe66B434bc83805f380509642429eC8e43AE9874a","latest"],"id":1}'
```

If the result is 0x, your endpoint is wrong.

## C. dial unix: missing address

Your websocket field is empty or invalid.

Check:

```bash
grep -n 'genlayerchainwebsocketurl' configs/node/config.yaml
grep '^GENLAYERNODE_ROLLUP_' .env
```

Fix:

set a proper WSS URL
remove conflicting GENLAYERNODE_ROLLUP_* overrides from .env

```bash
sed -i '/^GENLAYERNODE_ROLLUP_/d' .env
```

## D. dependencies: get chain ID: Internal error

Most common causes:

genlayerchainwebsocketurl is wrong
genlayerchainwebsocketurl is set to https://... instead of wss://...
stale config or env override is being used

Check upstream HTTP chain ID:

```bash
curl -s -X POST https://rpc-asimov.genlayer.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```
Expected:

{"jsonrpc":"2.0","result":"0x107d","id":1}

Check current config:

```bash
grep -n 'genlayerchain' configs/node/config.yaml
grep '^GENLAYERNODE_' .env
```

Correct example:

```bash
rollup:
  genlayerchainrpcurl: "https://rpc-asimov.genlayer.com"
  genlayerchainwebsocketurl: "wss://rpc-asimov.genlayer.com/ws"
```

## E. No LLM provider is configured

At least one LLM provider key is required for GenVM.

Example using OpenRouter:

```bash
echo 'OPENROUTERKEY=YOUR_REAL_KEY' >> .env
```

Reload and restart:

```bash
set -a
source .env
set +a
```
```bash
docker compose down
docker compose up -d --force-recreate
```

## F. ValidatorWalletAddress not configured (required for validator mode)

This is expected if you are setting up a full node, not a validator.

At runtime the node may print something like:

SWITCHING to FULL MODE due to missing addresses

That is acceptable for a full node.

## G. docker compose down -v did not remove genlayer-node

Sometimes an old container remains attached to a removed network.

Clean it manually:

```bash
docker rm -f genlayer-node
docker rm -f genlayer-node-webdriver 2>/dev/null || true
docker network prune -f
docker compose up -d --force-recreate
```

If Docker still behaves strangely:
```bash
sudo systemctl restart docker
sleep 5
docker compose up -d --force-recreate
```

## H. Verify websocket manually with wscat

Install:
```bash
npm install -g wscat
```
Connect:

```bash
wscat -c wss://rpc-asimov.genlayer.com/ws
```
Send:

{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}

Expected result:

{"jsonrpc":"2.0","result":"0x107d","id":1}

## I. Check what the container actually sees

```bash
docker exec -it genlayer-node /bin/sh -lc 'env | sort | grep GENLAYERNODE_'
```
```bash
docker exec -it genlayer-node /bin/sh -lc 'sed -n "/rollup:/,/consensus:/p" /app/configs/node/config.yaml'
```
