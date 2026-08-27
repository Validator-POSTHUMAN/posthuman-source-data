# Gnoland Pearl — Full Node Installation Guide

This guide installs a non-signing Gnoland full node on `pearl-1`. Validator
registration and key custody are separate procedures.

Tested source commit:
`c4c72fdd288c757e8da0d93aae867fa479b1b15c` from `chain/pearl`.

## Requirements

- Linux x86_64/amd64; Ubuntu 24.04 is recommended
- Go 1.25.9 or the version declared by the pinned source commit
- 4+ CPU cores
- 8 GB+ RAM
- 100 GB+ SSD storage
- `git`, `curl`, `jq`, `lz4`, `tar`, and `sha256sum`
- inbound TCP `26656` for P2P

Keep RPC on loopback unless you operate a separately secured TLS reverse
proxy with request limits, unsafe-method blocking, monitoring, and firewall
rules.

## 1. Build the pinned Pearl binaries

```bash
GNO_COMMIT=c4c72fdd288c757e8da0d93aae867fa479b1b15c
GNO_SOURCE="$HOME/gno"

git clone --branch chain/pearl https://github.com/gnolang/gno.git "$GNO_SOURCE"
git -C "$GNO_SOURCE" checkout "$GNO_COMMIT"
test "$(git -C "$GNO_SOURCE" rev-parse HEAD)" = "$GNO_COMMIT"

cd "$GNO_SOURCE"
go build -o /tmp/gnoland ./gno.land/cmd/gnoland
go build -o /tmp/gnokey ./gno.land/cmd/gnokey
sudo install -m 0755 /tmp/gnoland /usr/local/bin/gnoland
sudo install -m 0755 /tmp/gnokey /usr/local/bin/gnokey

gnoland version
gnokey version
```

Both commands should report the Pearl build.

## 2. Initialize an independent node identity

Choose your moniker:

```bash
MONIKER="YOUR_MONIKER"
GNO_HOME="$HOME/gnoland-pearl"
DATA_DIR="$GNO_HOME/data"
CONFIG="$DATA_DIR/config/config.toml"

install -d -m 0700 "$DATA_DIR"
gnoland secrets init -data-dir "$DATA_DIR/secrets"
gnoland config init -config-path "$CONFIG"
chmod -R go-rwx "$DATA_DIR/secrets"
```

Never copy another validator's `secrets/` directory or validator state into a
new node. Each full node must have its own consensus and P2P identity.

## 3. Download and verify genesis

```bash
curl -fL --retry 3 \
  -o "$DATA_DIR/genesis.json" \
  https://github.com/gnolang/gno/releases/download/chain/pearl/genesis.json

test "$(jq -r '.chain_id' "$DATA_DIR/genesis.json")" = "pearl-1"
echo "c45fe60c8c8a1f859d9e4d5aad7ce4d100ff0eb78302e71318ba0de481a8dc91  $DATA_DIR/genesis.json" \
  | sha256sum -c -
```

The checksum must pass before the node is started.

## 4. Configure RPC, P2P, pruning, and peers

```bash
PEERS="g1m37xukfq6yl555k93fcyzns83qnmgyax9zm875@seed-1.pearl.testnets.gno.land:26656,g1ngukqd3khekaqjf90k45cglzm0l25wwzl2fkn2@seed-2.pearl.testnets.gno.land:26656,g1zq6h7d7302wqwd7hycndq9qqx9d3tsew3c4d7d@peer-gnoland.posthuman.digital:37656"

gnoland config set -config-path "$CONFIG" moniker "$MONIKER"
gnoland config set -config-path "$CONFIG" proxy_app tcp://127.0.0.1:26658
gnoland config set -config-path "$CONFIG" rpc.laddr tcp://127.0.0.1:26657
gnoland config set -config-path "$CONFIG" rpc.unsafe false
gnoland config set -config-path "$CONFIG" rpc.max_open_connections 300
gnoland config set -config-path "$CONFIG" rpc.max_body_bytes 2000000
gnoland config set -config-path "$CONFIG" p2p.laddr tcp://0.0.0.0:26656
gnoland config set -config-path "$CONFIG" p2p.persistent_peers "$PEERS"
gnoland config set -config-path "$CONFIG" p2p.pex true
gnoland config set -config-path "$CONFIG" consensus.timeout_commit 3s
gnoland config set -config-path "$CONFIG" consensus.peer_gossip_sleep_duration 10ms
gnoland config set -config-path "$CONFIG" p2p.flush_throttle_timeout 10ms
gnoland config set -config-path "$CONFIG" mempool.size 10000
gnoland config set -config-path "$CONFIG" p2p.max_num_outbound_peers 40
gnoland config set -config-path "$CONFIG" application.prune_strategy syncable
gnoland config set -config-path "$CONFIG" tx_event_store.event_store_type none
```

If UFW is already active, expose only P2P:

```bash
sudo ufw allow 26656/tcp
```

## 5. Restore the latest snapshot

Use the dedicated [snapshot guide](?tab=snapshots) to download, verify, and
extract POSTHUMAN's latest `db/` + `wal/` archive before starting the node.
The snapshot never contains keys, configuration, or genesis.

## 6. Create the systemd service

Replace every `YOUR_USERNAME` occurrence with the Linux account that owns
`$HOME/gnoland-pearl`.

```ini
[Unit]
Description=Gnoland Pearl full node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/gnoland-pearl
Environment=GNOROOT=/home/YOUR_USERNAME/gno
ExecStart=/usr/local/bin/gnoland start \
  --chainid pearl-1 \
  --genesis /home/YOUR_USERNAME/gnoland-pearl/data/genesis.json \
  --data-dir /home/YOUR_USERNAME/gnoland-pearl/data \
  --gnoroot-dir /home/YOUR_USERNAME/gno \
  --skip-genesis-sig-verification \
  --log-level info
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

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

curl -fsS https://rpc.pearl.testnets.gno.land/status \
  | jq -r '.result.sync_info.latest_block_height'

curl -fsS http://127.0.0.1:26657/net_info \
  | jq '.result.n_peers'
```

The local chain must be `pearl-1`, height must advance, and a non-signing full
node should report voting power `0`.
