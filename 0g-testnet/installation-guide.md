# Setup Guide

#### 1. Download Package

Download the latest package for node binaries:
```bash
wget -O galileo.tar.gz https://github.com/0glabs/0gchain-NG/releases/download/v2.0.2/galileo-v2.0.2.tar.gz
```

#### 2. Extract Package
Extract the package to your home directory:
```bash
tar -xzvf galileo.tar.gz -C ~
```
#### 3. Copy Files and Set Permissions
Copy the configuration files and set proper permissions:
```bash
cd galileo-v2.0.2
cp -r 0g-home {your data path}
sudo chmod 777 ./bin/geth
sudo chmod 777 ./bin/0gchaind
```
#### 4. Initialize Geth
Initialize the Geth client with the genesis file:
```bash
./bin/geth init --datadir /{your data path}/0g-home/geth-home ./genesis.json
```
#### 5. Initialize 0gchaind
Create a temporary directory for initial configuration:
```bash
./bin/0gchaind init {node name} --home /{your data path}/tmp
```
#### 6. Copy Node Files
Move the generated keys to the proper location:
```bash
cp /{your data path}/tmp/data/priv_validator_state.json /{your data path}/0g-home/0gchaind-home/data/
cp /{your data path}/tmp/config/node_key.json /{your data path}/0g-home/0gchaind-home/config/
cp /{your data path}/tmp/config/priv_validator_key.json /{your data path}/0g-home/0gchaind-home/config/
```
Note: The temporary directory can be deleted after this step.

#### 7. Start 0gchaind
Note: The command below includes restaking flags and is intended for validator nodes only. Non-validator nodes can omit the --chaincfg.restaking.* flags.
```bash
cd ~/galileo-v2.0.2
nohup ./bin/0gchaind start \
    --rpc.laddr tcp://0.0.0.0:26657 \
    --chaincfg.chain-spec devnet \
    --chaincfg.restaking.enabled \
    --chaincfg.restaking.symbiotic-rpc-dial-url ${ETH_RPC_URL} \
    --chaincfg.restaking.symbiotic-get-logs-block-range ${BLOCK_NUM} \
    --chaincfg.kzg.trusted-setup-path=kzg-trusted-setup.json \
    --chaincfg.engine.jwt-secret-path=jwt-secret.hex \
    --chaincfg.kzg.implementation=crate-crypto/go-kzg-4844 \
    --chaincfg.block-store-service.enabled \
    --chaincfg.node-api.enabled \
    --chaincfg.node-api.logging \
    --chaincfg.node-api.address 0.0.0.0:3500 \
    --pruning=nothing \
    --home /{your data path}/0g-home/0gchaind-home \
    --p2p.seeds 85a9b9a1b7fa0969704db2bc37f7c100855a75d9@8.218.88.60:26656 \
    --p2p.external_address {your node ip}:26656 > /{your data path}/0g-home/log/0gchaind.log 2>&1 &
```
#### 8. Start Geth
```bash
cd ~/galileo-v2.0.2
nohup ./bin/geth --config geth-config.toml \
     --nat extip:{your node ip} \
     --bootnodes enode://de7b86d8ac452b1413983049c20eafa2ea0851a3219c2cc12649b971c1677bd83fe24c5331e078471e52a94d95e8cde84cb9d866574fec957124e57ac6056699@8.218.88.60:30303 \
     --datadir /{your data path}/0g-home/geth-home \
     --networkid 16601 > /{your data path}/0g-home/log/geth.log 2>&1 &
```

#### 9. Verify Setup
Check the logs to confirm your node is running properly:
###### Check Geth logs
```bash
tail -f /{your data path}/0g-home/log/geth.log
```
###### Check 0gchaind logs
```bash
tail -f /{your data path}/0g-home/log/0gchaind.log
```
#### Check logs to confirm your node is running properly.
