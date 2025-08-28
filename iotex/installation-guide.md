# IoTeX Delegate Manual


## Release Status

Here are the software versions we use:

- MainNet: v2.2.1

## Join MainNet
This is the recommended way to start an IoTeX node

> All the steps have written in scripts/all_in_one_mainnet.sh, you can directly run `sh scripts/all_in_one_mainnet.sh`

1. Pull the docker image:

```
docker pull iotex/iotex-core:v2.2.1
```

2. Set the environment with the following commands:

```
mkdir -p ~/iotex-var
cd ~/iotex-var

export IOTEX_HOME=$PWD

mkdir -p $IOTEX_HOME/data
mkdir -p $IOTEX_HOME/log
mkdir -p $IOTEX_HOME/etc

curl https://raw.githubusercontent.com/iotexproject/iotex-bootstrap/v2.2.1/config_mainnet.yaml > $IOTEX_HOME/etc/config.yaml
curl https://raw.githubusercontent.com/iotexproject/iotex-bootstrap/v2.2.1/genesis_mainnet.yaml > $IOTEX_HOME/etc/genesis.yaml
curl https://raw.githubusercontent.com/iotexproject/iotex-bootstrap/v2.2.1/trie.db.patch > $IOTEX_HOME/data/trie.db.patch
```

3. Edit `$IOTEX_HOME/etc/config.yaml`, look for `externalHost` and `producerPrivKey`, uncomment the lines and fill in your external IP and private key. If you leave `producerPrivKey` empty, your node will be assgined with a random key.

4. Start from a **baseline snapshot** (rather than sync from the genesis block), run the following commands:

```
curl -L https://t.iotex.me/mainnet-data-snapshot-latest > $IOTEX_HOME/data.tar.gz
```

or download from another website:

```
curl -L https://storage.iotex.io/mainnet-data-snapshot-latest.tar.gz > $IOTEX_HOME/data.tar.gz
```

**We will update the baseline snapshot on the 1st of every month**. 

5. Download the latest **incremental data** (Optional):

```
curl -L https://storage.iotex.io/mainnet-data-incr-latest.tar.gz > $IOTEX_HOME/incr.tar.gz
```

**We will update the incremental snapshot everyday**. 

We also provide incremental packages from the **past 7 days**.
You can choose any day within this period.
For example, if you want to use the data from April 27, 2025, the incremental package file name will be `mainnet-data-incr-2025-04-27.tar.gz`.

The file named **latest** corresponds to today’s data.

To restore, you only need the full baseline package of the same month and the incremental package of the selected date.

6. Extract the data packages in the correct order.
It is essential to extract the baseline package first, followed by the incremental package.

```
tar -xzf $IOTEX_HOME/data.tar.gz -C $IOTEX_HOME/data/ && tar -xzf $IOTEX_HOME/incr.tar.gz -C $IOTEX_HOME/data/
```

For advanced users, there are three options to consider:

- Option 1: If you plan to run your node as a gateway, please use the snapshot with index data:
https://t.iotex.me/mainnet-data-with-idx-latest.

  or download from another website:
```
curl -L https://storage.iotex.io/mainnet-data-with-idx-latest.tar.gz > $IOTEX_HOME/data.tar.gz
tar -xzf data.tar.gz
```

> mainnet-data-with-idx-latest.tar.gz will be update on Monday every week

- Optional 2: If you only want to sync chain data from 0 height without relaying on legacy delegate election data from Ethereum, you can setup legacy delegate election data with following command:
```bash
curl -L https://storage.iotex.io/poll.mainnet.tar.gz > $IOTEX_HOME/poll.tar.gz; tar -xzf $IOTEX_HOME/poll.tar.gz --directory $IOTEX_HOME/data
```

- Optional 3: If you want to sync the chain from 0 height and also fetching legacy delegate election data from Ethereum, please change the `gravityChainAPIs` in config.yaml to use your infura key with Ethereum archive mode supported or change the API endpoint to an Ethereum archive node which you can access.

5. Run the following command to start a node:

```
docker run -d --restart on-failure --name iotex \
        -p 4689:4689 \
        -p 8080:8080 \
        -v=$IOTEX_HOME/data:/var/data:rw \
        -v=$IOTEX_HOME/log:/var/log:rw \
        -v=$IOTEX_HOME/etc/config.yaml:/etc/iotex/config_override.yaml:ro \
        -v=$IOTEX_HOME/etc/genesis.yaml:/etc/iotex/genesis.yaml:ro \
        iotex/iotex-core:v2.2.1 \
        iotex-server \
        -config-path=/etc/iotex/config_override.yaml \
        -genesis-path=/etc/iotex/genesis.yaml
```

Now your node should be started successfully.

If you want to also make your node be a gateway, which could process API requests from users, use the following command instead:

```
docker run -d --restart on-failure --name iotex \
        -p 4689:4689 \
        -p 14014:14014 \
        -p 15014:15014 \
        -p 16014:16014 \
        -p 8080:8080 \
        -v=$IOTEX_HOME/data:/var/data:rw \
        -v=$IOTEX_HOME/log:/var/log:rw \
        -v=$IOTEX_HOME/etc/config.yaml:/etc/iotex/config_override.yaml:ro \
        -v=$IOTEX_HOME/etc/genesis.yaml:/etc/iotex/genesis.yaml:ro \
        iotex/iotex-core:v2.2.1 \
        iotex-server \
        -config-path=/etc/iotex/config_override.yaml \
        -genesis-path=/etc/iotex/genesis.yaml \
        -plugin=gateway
```

6. Ensure that TCP ports `4689` and `8080` are open on your firewall and load balancer (if applicable). Additionally, if you intend to use the node as a gateway, make sure the following ports are open:
- `14014` for the IoTeX native gRPC API
- `15014` for the Ethereum JSON API
- `16014` for the Ethereum WebSocket
