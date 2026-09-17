# NEAR Testnet Validator Guide

Testnet mirrors mainnet mechanics: `neard` runs the node, each epoch the
validator set is decided by a stake auction, and a validator that misses the
seat price simply does not validate that epoch. It is the right place to
rehearse the rhythm — pool creation, `ping`, key rotation, upgrades — because
falling out of the set is a normal event rather than an incident.

## What differs from mainnet

| | Mainnet | Testnet |
|---|---|---|
| Chain ID | `mainnet` | `testnet` |
| Release channel | latest **stable** tag | latest **release candidate** |
| Staking-pool factory | `poolv1.near` | `pool.f863973.m0` |
| Pool account | `<name>.poolv1.near` | `<name>.pool.f863973.m0` |
| Owner account suffix | `.near` | `.testnet` |
| Tokens | bought | [faucet](https://near-faucet.io/) |
| Public RPC | `https://free.rpc.fastnear.com` | `https://test.rpc.fastnear.com`, `https://rpc.testnet.near.org` |
| Explorer | [nearblocks.io](https://nearblocks.io) | [testnet.nearblocks.io](https://testnet.nearblocks.io) |

Epoch length is the same in blocks, so the feedback loop for "did my change
work" is still hours, not minutes. Plan rehearsals accordingly.

## Hardware

| Role | CPU | RAM | Storage |
|------|-----|-----|---------|
| Chunk/block producer (recommended) | 8+ physical cores | 32 GB | 1 TB SSD, 15k IOPS |
| Chunk validator (recommended) | 8+ physical cores | 16 GB | 512 GB SSD |
| Chunk validator (minimum) | 8+ physical cores | 8 GB | 1.5 TB NVMe |

Source: [near-nodes.io archival/validator hardware](https://near-nodes.io/validator/hardware-validator).

## 1. Build the release candidate

Testnet runs RC builds ahead of mainnet. Check
[nearcore releases](https://github.com/near/nearcore/releases) and pick the
latest RC tag.

```bash
sudo apt update && sudo apt install -y git curl jq build-essential pkg-config \
  libssl-dev clang cmake protobuf-compiler llvm

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

git clone https://github.com/near/nearcore && cd nearcore
git fetch origin --tags
git tag -l --sort=-v:refname | head -10
git checkout tags/<latest-rc-tag> -b testnet-node
make neard
sudo install -m 0755 target/release/neard /usr/local/bin/neard
neard --version
```

## 2. Initialise

```bash
neard --home ~/.near init --chain-id testnet --download-genesis --download-config validator
```

The testnet genesis file is large (6 GB+) and the download runs for a long
time with no progress output. That is expected.

Confirm the chain ID before starting. A node initialised against the wrong
chain runs perfectly and is on the wrong network:

```bash
jq -r '.chain_id' ~/.near/genesis.json
```

Use `--download-config rpc` instead if this host is an RPC node rather than a
validator, or `archival` for full history.

## 3. Refresh boot nodes and start

```bash
BOOT_NODES=$(curl -s -X POST https://rpc.testnet.near.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"network_info","params":[],"id":"dontcare"}' \
  | jq -r '.result.active_peers as $active | .result.known_producers as $known |
      $active[] as $peer | $known[] | select(.peer_id == $peer.id) |
      "\(.peer_id)@\($peer.addr)"' | paste -sd "," -)

cp ~/.near/config.json ~/.near/config.json.backup
jq --arg newBootNodes "$BOOT_NODES" '.network.boot_nodes = $newBootNodes' \
  ~/.near/config.json > ~/.near/config.tmp && mv ~/.near/config.tmp ~/.near/config.json
```

```bash
sudo tee /etc/systemd/system/neard.service > /dev/null <<'EOF'
[Unit]
Description=NEAR testnet node
After=network-online.target
Wants=network-online.target

[Service]
User=near
Group=near
Type=simple
ExecStart=/usr/local/bin/neard --home /home/near/.near run
Restart=on-failure
RestartSec=30
KillSignal=SIGINT
TimeoutStopSec=45
LimitNOFILE=1000000
Environment=RUST_LOG=info

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now neard
journalctl -u neard -f
```

```bash
sudo ufw allow 22/tcp
sudo ufw allow 24567/tcp comment 'NEAR P2P'
sudo ufw enable
```

Keep `3030` on loopback. It serves both RPC and Prometheus metrics.

## 4. Verify sync

```bash
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{chain: .result.chain_id, version: .result.version.version,
         height: .result.sync_info.latest_block_height,
         syncing: .result.sync_info.syncing}'

curl -s -X POST https://rpc.testnet.near.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq -r '.result.sync_info.latest_block_height'
```

`syncing` must be `false` and the two heights must be close before you go
further.

## 5. Accounts and tokens

```bash
npm install -g near-cli-rs@latest near-validator

# create a testnet account funded by the faucet
near account create-account sponsor-by-faucet-service <you>.testnet \
  autogenerate-new-keypair save-to-keychain network-config testnet create
```

Top it up at [near-faucet.io](https://near-faucet.io/). You need 30 NEAR for
pool storage plus gas plus the stake you intend to self-bond.

## 6. Generate the staking key

```bash
near generate-keypair save-to-file ~/near-staking-key.json
chmod 600 ~/near-staking-key.json
```

This is the key `neard` signs with. It is **not** a full-access key on any
account and must never be confused with the owner key.

## 7. Deploy the staking pool

```bash
export OWNER=<you>.testnet
export POOL=<pool-name>
export STAKE_PUBKEY=ed25519:<public-key-from-step-6>

near contract call-function as-transaction pool.f863973.m0 create_staking_pool \
  json-args "{\"staking_pool_id\": \"$POOL\",
              \"owner_id\": \"$OWNER\",
              \"stake_public_key\": \"$STAKE_PUBKEY\",
              \"reward_fee_fraction\": {\"numerator\": 5, \"denominator\": 100}}" \
  prepaid-gas '300.0 Tgas' \
  attached-deposit '30 NEAR' \
  sign-as "$OWNER" \
  network-config testnet \
  sign-with-keychain \
  send
```

Your pool is now `<pool-name>.pool.f863973.m0`.

## 8. Install `validator_key.json`

```json
{
  "account_id": "<pool-name>.pool.f863973.m0",
  "public_key": "ed25519:<public-key>",
  "secret_key": "ed25519:<secret-key>"
}
```

```bash
chmod 600 ~/.near/validator_key.json
sudo systemctl restart neard
```

`account_id` is the **pool**, not the owner. The private field is `secret_key`,
not `private_key`. A running `neard` does not reload this file — `restart`,
never `start`.

## 9. Stake and ping

```bash
near contract call-function as-transaction "$POOL.pool.f863973.m0" deposit_and_stake \
  json-args '{}' prepaid-gas '300.0 Tgas' attached-deposit '<amount> NEAR' \
  sign-as "$OWNER" network-config testnet sign-with-keychain send

near contract call-function as-transaction "$POOL.pool.f863973.m0" ping \
  json-args '{}' prepaid-gas '300.0 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER" network-config testnet sign-with-keychain send
```

Ping every epoch. Set the same systemd timer you will use on mainnet — testnet
is where you find out it silently fails.

## 10. Confirm you are in the set

Proposals apply two epochs out.

```bash
near-validator proposals network-config testnet
near-validator validators network-config testnet next
near-validator validators network-config testnet now
```

```bash
curl -s -X POST https://rpc.testnet.near.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
  | jq --arg p "$POOL.pool.f863973.m0" '.result.current_validators[] | select(.account_id==$p) |
      {stake, blocks: "\(.num_produced_blocks)/\(.num_expected_blocks)",
       chunks: "\(.num_produced_chunks)/\(.num_expected_chunks)",
       endorsements: "\(.num_produced_endorsements)/\(.num_expected_endorsements)"}'
```

Produced close to expected is the real health signal. A validator in the set
producing far less than expected is being penalised, and the cause is almost
always the host.

## What to rehearse here before touching mainnet

- Staking-key rotation: `update_staking_key` on the pool, then replace
  `validator_key.json` and restart — in that order, at the start of an epoch.
- A `neard` version upgrade, including any database migration in the release
  notes, and the rollback path.
- The `ping` timer failing, and whether your monitoring notices.
- Commission change and its visibility to delegators.
- Full host rebuild from backed-up keys.

## Related guides

The mainnet guides apply unchanged except for the factory and network name:
**Installation guide**, **Validator signaling**, **Keys & custody**,
**Security**, **Monitoring**, **State sync**, **Upgrades**.

---

**Created by POSTHUMAN validators** — https://posthuman.digital
