# GenLayer Full Node Setup Guide (Ubuntu, Docker, Asimov)

This guide installs a **GenLayer full node / RPC node** on Ubuntu using Docker Compose.

It is written for:
- **full node mode**
- **GenLayer Asimov testnet**
- **Docker-based setup**

---

## 1. Requirements

- Ubuntu 22.04+ recommended
- x86_64 server
- Docker + Docker Compose plugin
- Node.js 18+ only if you also want to use the GenLayer CLI
- At least one working **LLM provider API key**
- Open outbound HTTPS access
- Optional: open inbound TCP `9151` if you want public RPC access

---

## 2. Install Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker version
docker compose version

```

## 3. Create working directory

```bash
mkdir -p ~/genlayer/configs/node
cd ~/genlayer
```

### 4. Create .env

Replace YOUR_OPENROUTER_KEY with a real API key.
You can use another supported provider if preferred, but at least one must be configured.

```bash
cat > .env <<'EOF'
WEBDRIVER_PORT=4444

NODE_VERSION=v0.5.7
NODE_CONFIG_PATH=./configs/node/config.yaml
NODE_DATA_PATH=./data

NODE_RPC_PORT=9151
NODE_OPS_PORT=9153

NODE_PASSWORD=12345678

GENLAYERNODE_LOGGING_LEVEL=INFO

OPENROUTERKEY=YOUR_OPENROUTER_KEY
EOF
```

## 5. Create configs/node/config.yaml

This is a full node config for Asimov.
Important:

genlayerchainrpcurl must be HTTP(S)
genlayerchainwebsocketurl must be WSS
do not put https://... into the websocket field

```bash
cat > configs/node/config.yaml <<'EOF'
rollup:
  genlayerchainrpcurl: "..."
  genlayerchainwebsocketurl: "..."

consensus:
  consensusaddress: "0xe66B434bc83805f380509642429eC8e43AE9874a"
  genesis: 17326

datadir: "./data/node"

logging:
  level: "INFO"
  json: false
  file:
    enabled: true
    level: "DEBUG"
    folder: logs
    maxsize: 10
    maxage: 7
    maxbackups: 30
    localtime: false
    compress: true

node:
  mode: "full"
  admin:
    port: 9155
  rpc:
    port: 9151
    endpoints:
      groups:
        genlayer: true
        genlayer_debug: true
        ethereum: true
        zksync: true
      methods:
        gen_call: true
        gen_getContractSchema: true
        gen_getTransactionStatus: true
        gen_getTransactionReceipt: true
        gen_dbg_ping: true
        eth_blockNumber: true
        eth_getBlockByNumber: true
        eth_getBlockByHash: true
        eth_sendRawTransaction: true
        zks_getTransaction: true
  ops:
    port: 9153
    endpoints:
      metrics: true
      health: true
      balance: false

genvm:
  root_dir: ./third_party/genvm
  start_manager: true
  manager_url: http://127.0.0.1:3999
  permits: 8

metrics:
  interval: "15s"
  collectors:
    node:
      enabled: true
    genvm:
      enabled: true
    webdriver:
      enabled: true
EOF
```

### 6. Create docker-compose.yaml

```bash
cat > docker-compose.yaml <<'EOF'
services:
  webdriver-container:
    container_name: genlayer-node-webdriver
    image: yeagerai/genlayer-genvm-webdriver:0.0.10
    shm_size: 2gb
    security_opt:
      - no-new-privileges:true
    environment:
      PORT: 4444
    ports:
      - "${WEBDRIVER_PORT:-4444}:4444"
    restart: unless-stopped

  genlayer-node:
    image: yeagerai/genlayer-node:${NODE_VERSION:-v0.5.7}
    entrypoint: ["sh", "-c", "/app/bin/genlayernode run --password ${NODE_PASSWORD:-12345678}"]
    container_name: genlayer-node
    restart: unless-stopped
    env_file:
      - path: ./.env
        required: false
    ports:
      - "${NODE_RPC_PORT:-9151}:9151"
      - "${NODE_OPS_PORT:-9153}:9153"
    volumes:
      - ${NODE_CONFIG_PATH:-./configs/node/config.yaml}:/app/configs/node/config.yaml:ro
      - ${NODE_DATA_PATH:-./data}:/app/data
      - ./genvm-module-web-docker.yaml:/app/third_party/genvm/config/genvm-module-web.yaml
      - /var/run/docker.sock:/var/run/docker.sock:ro
    security_opt:
      - no-new-privileges:true
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        compress: "true"
    depends_on:
      - webdriver-container
    profiles:
      - node
EOF
```

## 7. Create genvm-module-web-docker.yaml

```bash
cat > genvm-module-web-docker.yaml <<'EOF'
webdriver_host: http://webdriver-container:4444
EOF
```

## 8. Start the node

```bash
cd ~/genlayer
docker compose --profile node up -d
docker compose ps
docker logs -f genlayer-node
```

## 9. Basic health checks

Check ops health

```bash
curl http://127.0.0.1:9153/health
```

Check JSON-RPC ping

```bash
curl -X POST http://127.0.0.1:9151 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"gen_dbg_ping","params":[],"id":1}'


Check block number

```bash
curl -X POST http://127.0.0.1:9151 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

Check chain ID on upstream RPC

```bash
curl -s -X POST https://rpc-asimov.genlayer.com \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

Expected result:

{"jsonrpc":"2.0","result":"0x107d","id":1}

## 10. Optional: install CLI and inspect network

```bash
sudo apt update
sudo apt install -y nodejs npm
npm install -g genlayer

```bash
genlayer network set testnet-asimov
genlayer network info
genlayer config get network
```

## 11. Optional: run doctor

Docker one-shot doctor

```bash
cd ~/genlayer
set -a
source .env
set +a
```

```bash
docker run --rm \
  --entrypoint /app/bin/genlayernode \
  --env-file ./.env \
  -v "${NODE_CONFIG_PATH:-./configs/node/config.yaml}:/app/configs/node/config.yaml:ro" \
  yeagerai/genlayer-node:${NODE_VERSION:-v0.5.7} \
  doctor
```

### Local binary doctor

If you use the local binary instead of Docker, remember that .env is not automatically loaded into your current shell:

```bash
cd ~/genlayer
set -a
source .env
set +a
./bin/genlayernode doctor
```

## 12. Firewall recommendations

UFW example

Open only RPC if you need public access:

```bash
sudo ufw allow 9151/tcp
sudo ufw status
```

Recommended:

  - expose 9151/tcp only if you want external RPC
  - keep 9153/tcp private
  - do not expose 4444/tcp publicly

