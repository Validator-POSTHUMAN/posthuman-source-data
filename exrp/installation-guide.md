# XRPL EVM Mainnet node

XRPL EVM is a Cosmos SDK chain with an EVM execution layer. One binary,
`exrpd`, serves CometBFT consensus, the Cosmos REST/gRPC APIs and an Ethereum
JSON-RPC endpoint at the same time. Consensus is **Proof of Authority**: the
validator set is admitted by a vote of the existing validators, not by stake
weight.

| Setting | Value |
|---|---|
| Chain ID (Cosmos) | `xrplevm_1440000-1` |
| Chain ID (EVM) | `1440000` / `0x15f900` |
| Binary | `exrpd` |
| Home | `/var/lib/exrpd/.exrpd` |
| CometBFT | `0.38.19` |
| Cosmos SDK | `v0.53.x-xrplevm` |
| Gas / staking denom | `axrp`, 18 decimals, displayed as XRP |

**The Cosmos chain ID has seven digits, not six.** A `xrplevm_144000-1` value
in `client.toml` produces deterministic app-hash divergence during bootstrap
even when the genesis file and the binary are both correct: the node starts,
looks healthy, and then refuses to agree with the network. Check this first if
a fresh node diverges.

## Which version to install

Two sources, and they answer different questions:

- the [Networks table](https://docs.xrplevm.org/pages/operators/resources/networks)
  gives the last **consensus-breaking** version and its upgrade height;
- the live fleet gives the current **patch** level, which the table lags.

Verified 2026-09-18: the docs table still names `v10.1.0`, while
`cosmos-rpc.xrplevm.org` answers `abci_info` with `10.2.1` and an independent
ITRocket node answers `10.2.0` — at the same height and the same app hash.
`v10.2.0` and `v10.2.1` are `cosmos/evm` dependency bumps
(`v0.6.2-august-2026-hotfix-xrplevm.1` and `.2`), not a fork. Run the newest
patch in the current major line; there is no upgrade height to wait for.

```bash
curl -s https://cosmos-rpc.xrplevm.org/abci_info | jq -r .result.response.version
curl -s https://xrplevm-mainnet-rpc.itrocket.net/abci_info | jq -r .result.response.version
```

The `v11.x` tags in the release list are the **testnet/devnet** line. Do not
install them on mainnet before the mainnet upgrade proposal passes and the
Networks table gains its row.

## System requirements

| Resource | Minimum |
|---|---|
| OS | Linux AMD64, Ubuntu 22.04 / 24.04 LTS |
| CPU | 8 physical cores |
| RAM | 32 GB |
| Disk | 1 TB NVMe SSD |
| Network | 100 Mbps |

An archive node needs considerably more than 1 TB. Everything below assumes
pruned operation.

## 1. Install the verified binary

```bash
sudo apt-get update
sudo apt-get install -y curl wget jq lz4 zstd build-essential git rsync

cd /tmp
VERSION=10.2.1
curl -fLO "https://github.com/xrplevm/node/releases/download/v${VERSION}/checksums.txt"
curl -fLO "https://github.com/xrplevm/node/releases/download/v${VERSION}/node_${VERSION}_Linux_amd64.tar.gz"
grep " node_${VERSION}_Linux_amd64.tar.gz$" checksums.txt | sha256sum -c -
tar -xzf "node_${VERSION}_Linux_amd64.tar.gz"
sudo install -m 0755 bin/exrpd /usr/local/bin/exrpd
exrpd version
```

The checksum line is not decoration. It is the only step here that
distinguishes the release from whatever the network handed you.

### Build from source

Check the Go version upstream requires before compiling; an older toolchain
fails late and confusingly.

```bash
curl -fsSL https://raw.githubusercontent.com/xrplevm/node/main/go.mod | awk '/^go /{print $2; exit}'
go version

git clone https://github.com/xrplevm/node.git
cd node && git checkout v10.2.1
make build
sudo install -m 0755 build/exrpd /usr/local/bin/exrpd
```

## 2. Initialize and configure

```bash
sudo useradd --system --home /var/lib/exrpd --create-home \
  --shell /usr/sbin/nologin exrpd 2>/dev/null || true
sudo install -d -o exrpd -g exrpd -m 0700 /var/lib/exrpd/.exrpd

MONIKER=your-node-name
sudo -u exrpd /usr/local/bin/exrpd init "$MONIKER" \
  --chain-id xrplevm_1440000-1 \
  --home /var/lib/exrpd/.exrpd

sudo -u exrpd /usr/local/bin/exrpd config set client chain-id xrplevm_1440000-1 \
  --home /var/lib/exrpd/.exrpd

sudo -u exrpd curl -fsSL \
  https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/genesis.json \
  -o /var/lib/exrpd/.exrpd/config/genesis.json

PEERS="$(curl -fsSL https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/peers.txt \
  | awk '{print $1}' | sort -R | head -n 10 | paste -sd, -)"
sudo sed -i "s|^persistent_peers *=.*|persistent_peers = \"${PEERS}\"|" \
  /var/lib/exrpd/.exrpd/config/config.toml
sudo chown -R exrpd:exrpd /var/lib/exrpd/.exrpd
```

### `evm-chain-id` is mandatory from v10

In `app.toml`, under `[evm]`:

```toml
[evm]
evm-chain-id = 1440000
```

Testnet is `1449000`, devnet `1449900`. Without it the EVM layer will not
agree with the network.

### Other settings worth setting deliberately

```toml
# app.toml
minimum-gas-prices = "0.25axrp"
```

```toml
# config.toml — a validator does not need the tx index
indexer = "null"
```

Turn the indexer off on a signer and leave it on for an RPC node: it is the
difference between a small database and one that grows without a ceiling, and
between `/tx?hash=` working and not.

### POSTHUMAN peer

```
522e624a77123c67762b5c1ff70ac20d377b0179@peer.exrp.posthuman.digital:61656
```

## 3. Bootstrap the data directory

Do not sync from genesis unless you specifically need full historical replay —
that means walking every hard fork with the matching binary, in order.

Restore the POSTHUMAN Zstandard snapshot (Snapshots tab) or use State Sync.
Both are safe on a fresh home and both are **forbidden on an active validator
signer home**: never restore chain state over a running signer, and never roll
`data/priv_validator_state.json` backwards.

## 4. Run

### systemd

`/etc/systemd/system/exrpd.service`:

```ini
[Unit]
Description=XRPL EVM Mainnet node
After=network-online.target
Wants=network-online.target

[Service]
User=exrpd
Group=exrpd
WorkingDirectory=/var/lib/exrpd
Environment="HOME=/var/lib/exrpd"
ExecStart=/usr/local/bin/exrpd start --home /var/lib/exrpd/.exrpd
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now exrpd
sudo journalctl -u exrpd -f
```

### Cosmovisor

Use `cosmovisor run start`, never `cosmovisor start`. The second form is a
different command and does not do what the unit file implies.

```bash
sudo env GOBIN=/usr/local/bin go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest
sudo -u exrpd mkdir -p /var/lib/exrpd/.exrpd/cosmovisor/genesis/bin
sudo install -m 0755 -o exrpd -g exrpd /usr/local/bin/exrpd \
  /var/lib/exrpd/.exrpd/cosmovisor/genesis/bin/exrpd
sudo -u exrpd ln -sfn /var/lib/exrpd/.exrpd/cosmovisor/genesis \
  /var/lib/exrpd/.exrpd/cosmovisor/current
```

Unit environment:

```ini
Environment="DAEMON_NAME=exrpd"
Environment="DAEMON_HOME=/var/lib/exrpd/.exrpd"
Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=false"
Environment="UNSAFE_SKIP_BACKUP=false"
ExecStart=/usr/local/bin/cosmovisor run start --home /var/lib/exrpd/.exrpd
```

`DAEMON_ALLOW_DOWNLOAD_BINARIES=false` is not optional on a signer: it is the
difference between an upgrade you staged and reviewed, and one the chain handed
you at a block height.

If restored data carries `data/upgrade-info.json`, pre-stage the binary under
`cosmovisor/upgrades/<name>/bin/` before the first start, or the process exits
immediately looking for a directory that does not exist.

### Docker

```bash
docker run -d --name xrplevm-node --restart unless-stopped \
  -p 127.0.0.1:26657:26657 \
  -v /root/.exrpd:/root/.exrpd \
  --entrypoint exrpd peersyst/exrp:v10.2.1 start
```

Bind published ports to `127.0.0.1`, not `0.0.0.0`. Docker writes its iptables
rules ahead of `ufw`, so a bare `-p 26657:26657` publishes the RPC to the
internet on a host whose firewall reads as correct.

## 5. Verify against the network, not against itself

```bash
curl -fsS http://127.0.0.1:26657/status \
  | jq '.result.sync_info | {latest_block_height,latest_block_time,catching_up}'
```

`catching_up=false` alone is not health. Compare a common height against an
independent source and check the app hash, not only the height:

```bash
H=$(curl -s http://127.0.0.1:26657/status | jq -r .result.sync_info.latest_block_height)
curl -s "http://127.0.0.1:26657/block?height=$H"        | jq -r .result.block.header.app_hash
curl -s "https://cosmos-rpc.xrplevm.org/block?height=$H" | jq -r .result.block.header.app_hash
```

Two independent sources beat one. The official RPC and ITRocket disagree with
each other only when something real has happened.

## POSTHUMAN endpoints

| Service | URL |
|---|---|
| RPC | `https://rpc.exrp.posthuman.digital` |
| REST | `https://rest.exrp.posthuman.digital` |
| gRPC | `https://grpc.exrp.posthuman.digital` |
| Snapshots | `https://snapshots.exrp.posthuman.digital` |
| Peer | `522e624a77123c67762b5c1ff70ac20d377b0179@peer.exrp.posthuman.digital:61656` |

## Validator safety

Keep exactly one active signer per `priv_validator_key.json`. Never run a
second copy "just to catch up", never roll back `priv_validator_state.json`,
and never run `exrpd unsafe-reset-all` on a signer home. Uptime never justifies
double-sign risk.

## Next

- **Snapshots** — restore from the published Zstandard artifact
- **State Sync** — bootstrap with no download
- **Create validator** — the Proof of Authority admission process
- **Monitoring** — what to alert on, and what means nothing
- **Security hardening** — key custody, firewall, signer isolation
