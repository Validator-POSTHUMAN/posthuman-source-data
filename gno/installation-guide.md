# Gnoland Mainnet — Full Node Installation Guide

This guide installs a non-signing Gnoland full node on `gnoland-1`. Validator
admission is a separate, governance-controlled procedure — see the last
section before planning one.

Tested release: `v1.5.0`, commit
`e75fef82c02876a4df92ad6e325c5479b9532168`.

## Requirements

- Linux x86_64/amd64; Ubuntu 24.04 is recommended
- Go 1.25.9 or newer (the `go.mod` of `v1.5.0` declares 1.25.9)
- 4+ CPU cores
- 16 GB+ RAM — genesis alone loads 3,262,486 balance entries
- 200 GB+ SSD storage
- `git`, `curl`, `jq`, `lz4`, `tar`, `gzip`, and `sha256sum`
- inbound TCP `26656` for P2P

Keep RPC on loopback unless you operate a separately secured TLS reverse
proxy with request limits, unsafe-method blocking, monitoring, and firewall
rules.

## 1. Build the pinned binaries

```bash
GNO_TAG=v1.5.0
GNO_COMMIT=e75fef82c02876a4df92ad6e325c5479b9532168
GNO_SOURCE="$HOME/gno"

git clone --branch "$GNO_TAG" --depth 1 https://github.com/gnolang/gno.git "$GNO_SOURCE"
test "$(git -C "$GNO_SOURCE" rev-parse HEAD)" = "$GNO_COMMIT"

cd "$GNO_SOURCE"
go build -o /tmp/gnoland ./gno.land/cmd/gnoland
go build -o /tmp/gnokey ./gno.land/cmd/gnokey
sudo install -m 0755 /tmp/gnoland /usr/local/bin/gnoland
sudo install -m 0755 /tmp/gnokey /usr/local/bin/gnokey

gnoland version
gnokey version
```

Keep the source tree. `gnoland start` needs it as `--gnoroot-dir`.

## 2. Initialize an independent node identity

Choose your moniker:

```bash
MONIKER="YOUR_MONIKER"
GNO_HOME="$HOME/gnoland-mainnet"
DATA_DIR="$GNO_HOME/data"
CONFIG="$DATA_DIR/config/config.toml"

install -d -m 0700 "$DATA_DIR" "$DATA_DIR/secrets"
gnoland secrets init -data-dir "$DATA_DIR/secrets"
gnoland config init -config-path "$CONFIG"
chmod -R go-rwx "$DATA_DIR/secrets"
```

`$DATA_DIR/secrets` must exist before `gnoland start` runs. Without it the node
exits with `open …/data/secrets/write-file-atomic-…: no such file or
directory`, which names a temporary file rather than the missing directory.

Never copy another validator's `secrets/` directory or validator state into a
new node. Each full node must have its own consensus and P2P identity.

## 3. Download and verify genesis

The launch genesis is a **release asset**. It is not in the repository —
`misc/deployments/mainnet.gno.land/genesis.json` is gitignored — and
`https://rpc.gno.land/genesis` serves a different, re-serialized body that
cannot match the published digest. Download the compressed asset:

```bash
curl -fL --retry 3 \
  -o "$DATA_DIR/genesis.json.gz" \
  https://github.com/gnolang/gno/releases/download/chain%2Fmainnet/genesis.json.gz

echo "32a0fef8db3c71fa8360dee39a0149ee961be115ba81363a15f854e4aad446c9  $DATA_DIR/genesis.json.gz" \
  | sha256sum -c -

gzip -dk "$DATA_DIR/genesis.json.gz"

echo "ea22691003130eae3ba975b7d16460706b5d75ce6c04ae82c0c4faeab7de91f0  $DATA_DIR/genesis.json" \
  | sha256sum -c -
test "$(jq -r '.chain_id' "$DATA_DIR/genesis.json")" = "gnoland-1"
```

Both checksums must pass before the node is started. The uncompressed file is
324 MB. The same two digests are published by the release's `CHECKSUMS.txt`
and by the `CHECKSUMS_DATA` block committed inside
`misc/deployments/mainnet.gno.land/gen-genesis.sh`, so the download path needs
no trust of its own.

Do not attempt to rebuild genesis with `gen-genesis.sh`. The upstream
allocation data has moved past the launch pin, and the script refuses rather
than producing a genesis that would panic at `InitChain`.

## 4. Configure RPC, P2P, pruning, and peers

```bash
PEERS="g15rcv5yqef3kvnmueqvkyw8y05sd40jz9p3n5su@seed-1.gno.land:26656,g1ck2yeyvvnpl92237gcea0z68jx07a4nnyvuaan@seed-2.gno.land:26656,g17zx8uj0rqkkrsdkz3jvt8kp0k5ry30aw3qplww@peer-gnoland.posthuman.digital:38656"

gnoland config set -config-path "$CONFIG" moniker "$MONIKER"
gnoland config set -config-path "$CONFIG" proxy_app tcp://127.0.0.1:26658
gnoland config set -config-path "$CONFIG" rpc.laddr tcp://127.0.0.1:26657
gnoland config set -config-path "$CONFIG" rpc.unsafe false
gnoland config set -config-path "$CONFIG" rpc.max_open_connections 300
gnoland config set -config-path "$CONFIG" rpc.max_body_bytes 2000000
gnoland config set -config-path "$CONFIG" p2p.laddr tcp://0.0.0.0:26656
gnoland config set -config-path "$CONFIG" p2p.persistent_peers "$PEERS"
gnoland config set -config-path "$CONFIG" p2p.seeds "$PEERS"
gnoland config set -config-path "$CONFIG" p2p.pex true
gnoland config set -config-path "$CONFIG" p2p.max_num_outbound_peers 40
gnoland config set -config-path "$CONFIG" consensus.timeout_commit 3s
gnoland config set -config-path "$CONFIG" mempool.size 10000
gnoland config set -config-path "$CONFIG" application.prune_strategy syncable
gnoland config set -config-path "$CONFIG" tx_event_store.event_store_type none
```

`application.prune_strategy syncable` keeps a normal full node compact. An
archive node that must answer historical queries — for an explorer or an
indexer — uses `nothing` instead and needs materially more disk.

If UFW is already active, expose only P2P:

```bash
sudo ufw allow 26656/tcp
```

## 5. Restore the latest snapshot

Syncing `gnoland-1` from genesis works but is slow. Use the dedicated
[snapshot guide](?tab=snapshots) to download, verify, and extract POSTHUMAN's
latest `db/` + `wal/` archive before starting the node. The snapshot never
contains keys, configuration, or genesis.

Genesis is still required when restoring from a snapshot: the node reads
`--genesis` on every start.

## 6. Create the systemd service

Replace every `YOUR_USERNAME` occurrence with the Linux account that owns
`$HOME/gnoland-mainnet`.

```ini
[Unit]
Description=Gnoland mainnet full node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/gnoland-mainnet
Environment=GNOROOT=/home/YOUR_USERNAME/gno
ExecStart=/usr/local/bin/gnoland start \
  --chainid gnoland-1 \
  --genesis /home/YOUR_USERNAME/gnoland-mainnet/data/genesis.json \
  --data-dir /home/YOUR_USERNAME/gnoland-mainnet/data \
  --gnoroot-dir /home/YOUR_USERNAME/gno \
  --skip-genesis-sig-verification \
  --log-level info
Restart=on-failure
RestartSec=30
TimeoutStartSec=7200
TimeoutStopSec=600
LimitNOFILE=65535
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

`TimeoutStartSec=7200` is not padding. The **first** start processes the whole
genesis allocation before the node serves anything; a default timeout sends
`SIGTERM` half-way through and the next start begins again from nothing.
Later restarts on an existing database take seconds.

Save the unit as `/etc/systemd/system/gnoland.service`, then:

```bash
sudo systemd-analyze verify /etc/systemd/system/gnoland.service
sudo systemctl daemon-reload
sudo systemctl enable --now gnoland.service
```

## 7. Verify sync and identity

```bash
systemctl is-active gnoland.service
systemctl is-enabled gnoland.service

curl -fsS http://127.0.0.1:26657/status | jq '.result | {
  network: .node_info.network,
  height: .sync_info.latest_block_height,
  catching_up: .sync_info.catching_up,
  validator_address: .validator_info.address,
  voting_power: .validator_info.voting_power
}'

curl -fsS https://rpc.gno.land/status \
  | jq -r '.result.sync_info.latest_block_height'

curl -fsS http://127.0.0.1:26657/net_info | jq '.result.n_peers'
```

The local chain must be `gnoland-1`, height must advance, and a non-signing
full node reports voting power `0`.

Then prove the node agrees with the network rather than merely running. One
wrong genesis balance changes the height-1 app hash, after which a node cannot
follow the chain at all:

```bash
H=$(curl -fsS https://rpc.gno.land/status | jq -r '.result.sync_info.latest_block_height')
H=$((H - 20))
curl -fsS "http://127.0.0.1:26657/block?height=$H" | jq -r '.result.block.header.app_hash'
curl -fsS "https://rpc.gno.land/block?height=$H"   | jq -r '.result.block.header.app_hash'
```

Both commands must print the same value.

## 8. Becoming a validator is governance, not a transaction

The `gnoland-1` validator set was fixed at genesis and changes only through an
approved GovDAO proposal. Registering a profile in
[`r/gnops/valopers`](https://gno.land/r/gnops/valopers) creates a **candidate**
entry; it does not join the active set, there is no self-bonding transaction,
and mainnet has no faucet. Plan any validator ambition around that process —
until it completes, the node above is a full node with voting power `0`.
