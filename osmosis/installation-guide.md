# Osmosis Mainnet Node Installation

This guide installs a non-signing `osmosis-1` full node with Cosmovisor on a
dedicated Linux user. Validator key creation and validator transactions are
intentionally outside this public guide.

The pinned binary below was the latest stable Osmosis release when this guide
was verified. Before a new installation, compare it with the current official
release and any on-chain upgrade plan.

## 1. Prepare the host

Recommended baseline: Ubuntu 22.04/24.04, 8 CPU cores, 32 GB RAM, fast NVMe,
and at least 1 TB of free disk. Archive requirements are substantially higher.

```bash
sudo apt update
sudo apt install -y curl jq lz4 ca-certificates

sudo useradd --create-home --shell /bin/bash osmosis
sudo install -d -o osmosis -g osmosis -m 0750 /home/osmosis/.osmosisd
```

Expose only P2P publicly. Keep RPC, REST, gRPC, and Prometheus on loopback or
behind an authenticated, rate-limited gateway.

## 2. Install the checksum-verified binary

Official release: `v31.0.3`.

```bash
OSMOSIS_VERSION="31.0.3"
OSMOSIS_SHA256="9d06a23cb407c0668d7c8240894485c29ba1e54d5cb3492bc0a3781a97fb622f"
OSMOSIS_FILE="osmosisd-${OSMOSIS_VERSION}-linux-amd64"
OSMOSIS_URL="https://github.com/osmosis-labs/osmosis/releases/download/v${OSMOSIS_VERSION}/${OSMOSIS_FILE}"

install -d -m 0700 "$HOME/osmosis-install"
curl -fL --retry 3 --output "$HOME/osmosis-install/$OSMOSIS_FILE" "$OSMOSIS_URL"
printf '%s  %s\n' "$OSMOSIS_SHA256" "$HOME/osmosis-install/$OSMOSIS_FILE" | sha256sum --check --strict
sudo install -o root -g root -m 0755 "$HOME/osmosis-install/$OSMOSIS_FILE" /usr/local/bin/osmosisd
osmosisd version --long
```

The expected application version is `31.0.3`. Stop if the checksum or version
does not match.

## 3. Install Cosmovisor

Install a supported Go toolchain from its official distribution, then build
the pinned Cosmovisor module through the Go checksum database:

```bash
COSMOVISOR_VERSION="v1.7.1"
GOBIN="$HOME/osmosis-install/bin" go install \
  "cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@${COSMOVISOR_VERSION}"
sudo install -o root -g root -m 0755 \
  "$HOME/osmosis-install/bin/cosmovisor" /usr/local/bin/cosmovisor

sudo -u osmosis -H bash -c '
set -euo pipefail
mkdir -p "$HOME/.osmosisd/cosmovisor/genesis/bin" \
  "$HOME/.osmosisd/cosmovisor/backup"
cp /usr/local/bin/osmosisd "$HOME/.osmosisd/cosmovisor/genesis/bin/osmosisd"
ln -sfn genesis "$HOME/.osmosisd/cosmovisor/current"
DAEMON_NAME=osmosisd \
DAEMON_HOME="$HOME/.osmosisd" \
DAEMON_DATA_BACKUP_DIR="$HOME/.osmosisd/cosmovisor/backup" \
  /usr/local/bin/cosmovisor version
'
```

Do not enable automatic binary downloads for a production validator. Stage
each upgrade from its official release and verify its checksum first.

## 4. Initialize and verify genesis

The genesis source is pinned to the official Osmosis networks commit
`bd29d5ae445ce7bee05bf1c09c498d5230f8abb7`.

```bash
GENESIS_URL="https://media.githubusercontent.com/media/osmosis-labs/networks/bd29d5ae445ce7bee05bf1c09c498d5230f8abb7/osmosis-1/genesis.json"
GENESIS_SHA256="1cdb76087fabcca7709fc563b44b5de98aaf297eedc8805aa2884999e6bab06d"

sudo -u osmosis -H /home/osmosis/.osmosisd/cosmovisor/current/bin/osmosisd \
  init <your-node-moniker> --chain-id osmosis-1 --home /home/osmosis/.osmosisd

sudo -u osmosis -H curl -fL --retry 3 \
  --output /home/osmosis/.osmosisd/config/genesis.json "$GENESIS_URL"

printf '%s  %s\n' "$GENESIS_SHA256" /home/osmosis/.osmosisd/config/genesis.json | \
  sha256sum --check --strict

jq -er '.chain_id == "osmosis-1"' /home/osmosis/.osmosisd/config/genesis.json
```

## 5. Configure peers, pruning, and private APIs

Use multiple independently operated seeds. Refresh the list from the official
Cosmos chain registry before installation.

```bash
SEEDS="f515a8599b40f0e84dfad935ba414674ab11a668@osmosis.blockpane.com:26656,ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:12556"

sudo -u osmosis -H sed -i \
  -e "s|^seeds *=.*|seeds = \"$SEEDS\"|" \
  -e 's|^laddr *= "tcp://127.0.0.1:26657"|laddr = "tcp://127.0.0.1:26657"|' \
  /home/osmosis/.osmosisd/config/config.toml
```

Set the desired pruning and indexer policy explicitly in `app.toml` and
`config.toml`. A public RPC/snapshot node should be non-signing and separately
verified before publication.

## 6. Install the systemd service

```ini
[Unit]
Description=Osmosis node
After=network-online.target
Wants=network-online.target

[Service]
User=osmosis
Group=osmosis
Environment=DAEMON_NAME=osmosisd
Environment=DAEMON_HOME=/home/osmosis/.osmosisd
Environment=DAEMON_DATA_BACKUP_DIR=/home/osmosis/.osmosisd/cosmovisor/backup
Environment=DAEMON_ALLOW_DOWNLOAD_BINARIES=false
Environment=UNSAFE_SKIP_BACKUP=false
ExecStart=/usr/local/bin/cosmovisor run start --home /home/osmosis/.osmosisd
Restart=on-failure
RestartSec=10
LimitNOFILE=1048576
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/osmosis/.osmosisd

[Install]
WantedBy=multi-user.target
```

Save the unit as `/etc/systemd/system/osmosis.service`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now osmosis.service
```

## 7. Verify

```bash
systemctl is-active osmosis.service
systemctl show osmosis.service -p NRestarts --value
curl -fsS http://127.0.0.1:26657/status | jq '.result | {
  chain_id: .node_info.network,
  height: .sync_info.latest_block_height,
  block_time: .sync_info.latest_block_time,
  catching_up: .sync_info.catching_up,
  voting_power: .validator_info.voting_power
}'
curl -fsS http://127.0.0.1:26657/net_info | jq '.result.n_peers'
```

Require `osmosis-1`, a fresh advancing height, `catching_up=false`, healthy
peers, and stable restart count. For a validator, additionally prove bonded,
not-jailed/not-tombstoned status and multiple fresh external signatures before
declaring success.

## Sources

- Osmosis releases: https://github.com/osmosis-labs/osmosis/releases
- Osmosis networks: https://github.com/osmosis-labs/networks
- Chain registry: https://github.com/cosmos/chain-registry/tree/master/osmosis
- Osmosis documentation: https://docs.osmosis.zone/
