# XRPL EVM Mainnet node

Current network values:

| Setting | Value |
|---|---|
| Chain ID | `xrplevm_1440000-1` |
| EVM chain ID | `1440000` |
| Recommended release | `v10.0.2` |
| Binary | `exrpd` |
| Home | `/var/lib/exrpd/.exrpd` |

Check the [official network page](https://docs.xrplevm.org/pages/operators/resources/networks)
before installation. Use a newer version only when the project has published
it for Mainnet.

## Install the verified binary

```bash
sudo apt-get update
sudo apt-get install -y curl jq lz4 zstd

cd /tmp
VERSION=10.0.2
curl -fLO "https://github.com/xrplevm/node/releases/download/v${VERSION}/checksums.txt"
curl -fLO "https://github.com/xrplevm/node/releases/download/v${VERSION}/node_${VERSION}_Linux_amd64.tar.gz"
grep " node_${VERSION}_Linux_amd64.tar.gz$" checksums.txt | sha256sum -c -
tar -xzf "node_${VERSION}_Linux_amd64.tar.gz"
sudo install -m 0755 bin/exrpd /usr/local/bin/exrpd
exrpd version
```

## Initialize and configure

```bash
sudo useradd --system --home /var/lib/exrpd --create-home \
  --shell /usr/sbin/nologin exrpd 2>/dev/null || true
sudo install -d -o exrpd -g exrpd -m 0700 /var/lib/exrpd/.exrpd

MONIKER=your-node-name
sudo -u exrpd /usr/local/bin/exrpd init "$MONIKER" \
  --chain-id xrplevm_1440000-1 \
  --home /var/lib/exrpd/.exrpd

sudo -u exrpd curl -fsSL \
  https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/genesis.json \
  -o /var/lib/exrpd/.exrpd/config/genesis.json

PEERS="$(curl -fsSL https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/peers.txt \
  | awk '{print $1}' | sort -R | head -n 10 | paste -sd, -)"
sudo sed -i "s|^persistent_peers *=.*|persistent_peers = \"${PEERS}\"|" \
  /var/lib/exrpd/.exrpd/config/config.toml

sudo sed -i \
  's/^evm-chain-id *=.*/evm-chain-id = 1440000/' \
  /var/lib/exrpd/.exrpd/config/app.toml
sudo sed -i \
  's/^indexer *=.*/indexer = "null"/' \
  /var/lib/exrpd/.exrpd/config/config.toml
sudo chown -R exrpd:exrpd /var/lib/exrpd/.exrpd
```

## Run with systemd

Create `/etc/systemd/system/exrpd.service`:

```ini
[Unit]
Description=XRPL EVM Mainnet node
After=network-online.target
Wants=network-online.target

[Service]
User=exrpd
Group=exrpd
ExecStart=/usr/local/bin/exrpd start --home /var/lib/exrpd/.exrpd
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Start and verify:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now exrpd
curl -fsS http://127.0.0.1:26657/status \
  | jq '.result.sync_info | {latest_block_height,latest_block_time,catching_up}'
```

For a faster bootstrap, restore a verified snapshot before the first start.
Keep RPC, REST, gRPC, and EVM JSON-RPC private unless access controls and rate
limits are in place.

Validator safety: keep only one active signer for each
`priv_validator_key.json` and never roll back `priv_validator_state.json`.
