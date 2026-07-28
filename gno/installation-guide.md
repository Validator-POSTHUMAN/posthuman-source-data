# Gnoland Topaz — Full Node Installation Guide

This guide installs a non-signing Gnoland full node on `topaz-1`. Validator
registration and key custody are separate procedures.

Tested source commit:
`fc40526511474e40b8a66419f5ba28255085bc08` from `chain/topaz`.

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

## 1. Build the pinned Topaz binaries

```bash
GNO_COMMIT=fc40526511474e40b8a66419f5ba28255085bc08
GNO_SOURCE="$HOME/gno"

git clone --branch chain/topaz https://github.com/gnolang/gno.git "$GNO_SOURCE"
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

Both commands should report the Topaz build.

## 2. Initialize an independent node identity

Choose your moniker:

```bash
MONIKER="YOUR_MONIKER"
GNO_HOME="$HOME/gnoland-topaz"
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
curl -fsS --retry 3 https://rpc.topaz.testnets.gno.land/genesis \
  | jq -e '.result.genesis' \
  > "$DATA_DIR/genesis.json"

test "$(jq -r '.chain_id' "$DATA_DIR/genesis.json")" = "topaz-1"
sha256sum "$DATA_DIR/genesis.json"
```

Record the printed checksum in your operations log and cross-check it with a
second trusted Topaz operator before starting a validator.

## 4. Configure RPC, P2P, pruning, and peers

```bash
SEEDS="g19q07ssuafhmg6r7ys7wp7rpc4jxc85cpvdy426@seed-1.topaz.testnets.gno.land:26656,g15k98e65gm8h7fdr3yr4tqn82lvch4a97a3sg3j@seed-2.topaz.testnets.gno.land:26656"
PEERS="g18ncv9au4sq4d7jxjduxj4sstm3zl2lvd3kehqu@44.213.204.244:26656,g1zzyjtaj4lv4vlx6nvaf95rpe68sdhh38t968gs@54.72.126.143:26656,g190ajdkf9dmmrnl2ne0wca2nppes6fn5prmqjv2@peer-gnoland.posthuman.digital:37656"

gnoland config set -config-path "$CONFIG" moniker "$MONIKER"
gnoland config set -config-path "$CONFIG" proxy_app tcp://127.0.0.1:26658
gnoland config set -config-path "$CONFIG" rpc.laddr tcp://127.0.0.1:26657
gnoland config set -config-path "$CONFIG" rpc.unsafe false
gnoland config set -config-path "$CONFIG" rpc.max_open_connections 300
gnoland config set -config-path "$CONFIG" rpc.max_body_bytes 2000000
gnoland config set -config-path "$CONFIG" p2p.laddr tcp://0.0.0.0:26656
gnoland config set -config-path "$CONFIG" p2p.seeds "$SEEDS"
gnoland config set -config-path "$CONFIG" p2p.persistent_peers "$PEERS"
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
`$HOME/gnoland-topaz`.

```ini
[Unit]
Description=Gnoland Topaz full node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/gnoland-topaz
Environment=GNOROOT=/home/YOUR_USERNAME/gno
ExecStart=/usr/local/bin/gnoland start \
  --chainid topaz-1 \
  --genesis /home/YOUR_USERNAME/gnoland-topaz/data/genesis.json \
  --data-dir /home/YOUR_USERNAME/gnoland-topaz/data \
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

curl -fsS https://rpc.topaz.testnets.gno.land/status \
  | jq -r '.result.sync_info.latest_block_height'

curl -fsS http://127.0.0.1:26657/net_info \
  | jq '.result.n_peers'
```

The local chain must be `topaz-1`, height must advance, and a non-signing full
node should report voting power `0`.

## AppHash mismatch warning

Topaz can currently crash with an AppHash mismatch tracked in
[gnolang/gno#6011](https://github.com/gnolang/gno/issues/6011). Preserve logs
and the old `db/` + `wal/`, then restore only those directories from a known
healthy backup or verified snapshot. Do not replace `secrets/`, configuration,
genesis, or validator signer state. Do not deploy an unreviewed patch to a
production validator.
