# Ethereum Operator CLI Sheet

Every command assumes the layout from **Installation**: execution JSON-RPC on
`127.0.0.1:8545`, Beacon API on `127.0.0.1:5052`, services named `execution`,
`consensus` and `validator`.

Nothing here is destructive except where marked.

---

## Services

````bash
systemctl is-active execution consensus validator
sudo systemctl restart consensus
sudo journalctl -fu consensus
sudo journalctl -u validator --since '1 hour ago' | grep -i error
systemctl show execution -p NRestarts
````

---

## Execution layer — JSON-RPC

A helper makes the rest readable:

````bash
rpc() { curl -s -X POST -H 'Content-Type: application/json' \
  --data "{\"jsonrpc\":\"2.0\",\"method\":\"$1\",\"params\":${2:-[]},\"id\":1}" \
  http://127.0.0.1:8545 | jq; }
````

| Question | Command |
|---|---|
| Which chain? | `rpc eth_chainId` → `0x1` is mainnet |
| Synced? | `rpc eth_syncing` → `false` is synced |
| Head block | `rpc eth_blockNumber` |
| Peer count | `rpc net_peerCount` |
| Client version | `rpc web3_clientVersion` |
| Gas price | `rpc eth_gasPrice` |
| Balance | `rpc eth_getBalance '["0xADDRESS","latest"]'` |
| Nonce | `rpc eth_getTransactionCount '["0xADDRESS","latest"]'` |
| Block by number | `rpc eth_getBlockByNumber '["latest",false]'` |
| Receipt | `rpc eth_getTransactionReceipt '["0xTXHASH"]'` |
| Fee history | `rpc eth_feeHistory '[5,"latest",[25,50,75]]'` |

Hex to decimal, which you will want constantly:

````bash
printf '%d\n' "$(rpc eth_blockNumber | jq -r .result)"
````

---

## Consensus layer — Beacon API

````bash
beacon() { curl -s "http://127.0.0.1:5052$1" | jq; }
````

| Question | Command |
|---|---|
| Synced? | `beacon /eth/v1/node/syncing` |
| Head slot | `beacon /eth/v1/beacon/headers/head` |
| Peer count | `beacon /eth/v1/node/peer_count` |
| Node identity | `beacon /eth/v1/node/identity` |
| Client version | `beacon /eth/v1/node/version` |
| Health (status code only) | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5052/eth/v1/node/health` |
| Finality | `beacon /eth/v1/beacon/states/head/finality_checkpoints` |
| Fork / spec | `beacon /eth/v1/config/spec` |
| One validator | `beacon /eth/v1/beacon/states/head/validators/0xPUBKEY` |
| Validator count | `beacon '/eth/v1/beacon/states/head/validator_balances'` |
| Genesis | `beacon /eth/v1/beacon/genesis` |

`node/health` returns `200` synced, `206` syncing, `503` not initialised — the
cleanest thing to point a health check at.

The three fields that matter in `node/syncing`:

````bash
curl -s http://127.0.0.1:5052/eth/v1/node/syncing \
  | jq '{syncing:.data.is_syncing, optimistic:.data.is_optimistic, distance:.data.sync_distance}'
````

---

## Validator

````bash
# Lighthouse
lighthouse account validator list --datadir /var/lib/validator
lighthouse account validator slashing-protection export /tmp/slashing.json
lighthouse account validator slashing-protection import /tmp/slashing.json

# Keymanager API (any client that implements it)
curl -s -H "Authorization: Bearer $(cat /var/lib/validator/api-token.txt)" \
  http://127.0.0.1:5062/eth/v1/keystores | jq '.data | length'
````

Validator status and balance without trusting the local node:

````bash
curl -s "https://beaconcha.in/api/v1/validator/0xPUBKEY" | jq '.data | {status, balance, effectivebalance}'
````

---

## ethdo — the validator swiss army knife

[`wealdtech/ethdo`](https://github.com/wealdtech/ethdo) `v1.39.1`. Read-only
unless you pass a private key.

````bash
ethdo --connection=http://127.0.0.1:5052 node info
ethdo --connection=http://127.0.0.1:5052 chain status
ethdo --connection=http://127.0.0.1:5052 validator info --validator=0xPUBKEY
ethdo --connection=http://127.0.0.1:5052 validator summary --validator=0xPUBKEY --epoch=-1
ethdo --connection=http://127.0.0.1:5052 validator credentials get --validator=0xPUBKEY
````

`validator summary` for the previous epoch is the fastest way to answer "did
this validator attest correctly and how late".

---

## Host

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
du -sh /var/lib/execution /var/lib/consensus
iostat -x 5 3
free -h
timedatectl status
sudo ss -tlnp | grep -vE '127\.0\.0\.1|\[::1\]'
sudo ufw status numbered
````

The `ss` line is the security check that matters: anything other than sshd and
the P2P listeners in that output is exposed to the internet.

---

## External checks

````bash
# is the P2P port really reachable? run from ANOTHER host
nc -vz <node-public-ip> 30303
nc -vzu <node-public-ip> 9000

# what the network thinks of your validator
curl -s "https://beaconcha.in/api/v1/validator/0xPUBKEY/attestationefficiency" | jq
````

---

## Marked destructive

Read twice. These delete data.

````bash
# wipe execution chain data (keys unaffected; costs a full resync)
sudo systemctl stop execution
sudo -u execution geth --datadir /var/lib/execution removedb

# wipe beacon chain data (fast to recover with checkpoint sync)
sudo systemctl stop consensus
sudo rm -r /var/lib/consensus/beacon

# eth-docker: deletes chain data for the configured network
./ethd terminate
````

None of these should ever touch `/var/lib/validator`. If a command you are about
to run names that path, stop.
