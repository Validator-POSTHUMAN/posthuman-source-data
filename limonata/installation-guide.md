# Limonata Testnet — Full Node Installation Guide

This guide installs a non-signing Limonata full node on
`limonata_10777-1`. Validator creation and grant participation are separate
procedures covered by the official validator documentation.

Tested release: `limonata-v0.3.4` (`77fc357f`) on 2026-07-25.

## Requirements

- Linux x86_64/amd64; Ubuntu 24.04 is recommended
- glibc 2.38 or newer for the prebuilt binary
- 2+ CPU cores
- 4 GB+ RAM
- 50 GB+ SSD storage
- `curl`, `jq`, `tar`, and `sha256sum`
- inbound TCP `26656` for P2P

Keep CometBFT RPC, REST, gRPC, EVM JSON-RPC, metrics, and pprof on loopback
unless you operate a separately secured public RPC service.

## 1. Install the checksum-verified binary

The commands below pin the release instead of following a moving `latest`
link.

```bash
LIMONATA_VERSION=limonata-v0.3.4
LIMONATA_ARCHIVE=limonatad-linux-amd64.tar.gz
LIMONATA_TMP=$(mktemp -d)

curl -fL --retry 3 \
  -o "$LIMONATA_TMP/$LIMONATA_ARCHIVE" \
  "https://github.com/Limonata-Blockchain/limonata/releases/download/$LIMONATA_VERSION/$LIMONATA_ARCHIVE"

printf '%s  %s\n' \
  '73aa3ac82f961ad2908a948d0f32b1c5e242f78082be8fbaae1e7e5c35be16b5' \
  "$LIMONATA_TMP/$LIMONATA_ARCHIVE" | sha256sum -c -

tar -xzf "$LIMONATA_TMP/$LIMONATA_ARCHIVE" -C "$LIMONATA_TMP"

printf '%s  %s\n' \
  'e5e5ecdbb8e6837902872e8d775f746a2d4775277e33395454fc1013390e6a35' \
  "$LIMONATA_TMP/limonatad" | sha256sum -c -

sudo install -m 0755 "$LIMONATA_TMP/limonatad" /usr/local/bin/limonatad
limonatad version --long
```

Expected application version: `v0.3.4`, commit `77fc357f`.

## 2. Initialize the node and verify genesis

Choose a public moniker before running:

```bash
MONIKER="YOUR_MONIKER"
CHAIN_ID=limonata_10777-1
LIMONATA_HOME="$HOME/.limonatad"

limonatad init "$MONIKER" \
  --chain-id "$CHAIN_ID" \
  --home "$LIMONATA_HOME"

curl -fL --retry 3 \
  -o "$LIMONATA_HOME/config/genesis.json" \
  https://limonata.xyz/genesis.json

printf '%s  %s\n' \
  'bb76a6d8abbb1bdeaa41d92811066b16bd6a48f58f7136e3fcb71226b6af4569' \
  "$LIMONATA_HOME/config/genesis.json" | sha256sum -c -
```

Do not replace the official genesis if `validate-genesis` reports a
`burn_bps` range error on v0.3.4. This release currently rejects the official
genesis because a dormant-module validation check is too strict; the
checksum-verified official file is the correct network genesis.

## 3. Configure the application and peer

```bash
CFG="$HOME/.limonatad/config/config.toml"
APP="$HOME/.limonatad/config/app.toml"
PEER="4b154368aab24cb5b31c927efd50c73d0f4f9799@142.127.103.79:26656"

sed -i "s#^persistent_peers =.*#persistent_peers = \"$PEER\"#" "$CFG"
sed -i 's/^type = "flood"/type = "app"/' "$CFG"
sed -i 's/^minimum-gas-prices = .*/minimum-gas-prices = "0aLIMO"/' "$APP"
```

The app-side mempool and both chain IDs are required by the current network.

## 4. Configure state sync

Use the official CometBFT RPC, not the EVM JSON-RPC endpoint:

```bash
CFG="$HOME/.limonatad/config/config.toml"
RPC=https://cosmos-rpc.limonata.xyz

LATEST=$(curl -fsS "$RPC/block" | jq -r '.result.block.header.height')
TRUST_HEIGHT=$(( (LATEST - 2000) / 1000 * 1000 ))
TRUST_HASH=$(curl -fsS "$RPC/commit?height=$TRUST_HEIGHT" \
  | jq -r '.result.signed_header.commit.block_id.hash')

test "$TRUST_HEIGHT" -gt 0
test "${#TRUST_HASH}" -eq 64

sed -i "/^\\[statesync\\]/,/^\\[/ {
  s/^enable *=.*/enable = true/
  s#^rpc_servers *=.*#rpc_servers = \"$RPC,$RPC\"#
  s/^trust_height *=.*/trust_height = $TRUST_HEIGHT/
  s/^trust_hash *=.*/trust_hash = \"$TRUST_HASH\"/
  s/^trust_period *=.*/trust_period = \"168h0m0s\"/
}" "$CFG"

printf 'trust_height=%s\ntrust_hash=%s\n' "$TRUST_HEIGHT" "$TRUST_HASH"
```

Cross-check the printed height and hash with another trusted operator before
starting a production validator. For a non-signing full node, the official
RPC provides the current bootstrap source.

## 5. Create the systemd service

Replace every `YOUR_USERNAME` occurrence with the Linux account that owns
`$HOME/.limonatad`.

```ini
[Unit]
Description=Limonata Testnet Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
ExecStart=/usr/local/bin/limonatad start \
  --home /home/YOUR_USERNAME/.limonatad \
  --chain-id limonata_10777-1 \
  --evm.evm-chain-id 10777 \
  --minimum-gas-prices 0aLIMO
Restart=on-failure
RestartSec=10
TimeoutStopSec=60
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
```

Save the unit as `/etc/systemd/system/limonatad.service`, then validate and
start it:

```bash
sudo systemd-analyze verify /etc/systemd/system/limonatad.service
sudo systemctl daemon-reload
sudo systemctl enable --now limonatad.service
```

If UFW is already enabled, expose only P2P:

```bash
sudo ufw allow 26656/tcp
```

Do not expose `26657`, `1317`, `9090`, `8545`, `8546`, metrics, or pprof
without authentication, TLS, rate limits, monitoring, and an explicit public
RPC design.

## 6. Verify sync and health

```bash
systemctl is-active limonatad.service
systemctl is-enabled limonatad.service

limonatad status --home "$HOME/.limonatad" 2>&1 \
  | jq '.sync_info | {
      latest_block_height,
      latest_block_time,
      catching_up
    }'

curl -fsS http://127.0.0.1:26657/net_info \
  | jq '.result.n_peers'

sudo journalctl -u limonatad.service \
  --since '10 minutes ago' \
  --no-pager
```

Repeat the local height check after 30 seconds. The height must advance,
`catching_up` must eventually become `false`, and the local height should
remain close to:

```bash
curl -fsS https://cosmos-rpc.limonata.xyz/status \
  | jq -r '.result.sync_info.latest_block_height'
```

## Backup and recovery notes

- Back up `config/node_key.json` for stable P2P identity.
- A validator must also protect `config/priv_validator_key.json`,
  `data/priv_validator_state.json`, and any DKG key/state required by the
  current Limonata release.
- Never copy a validator consensus key to a second live signer.
- Back up keys before replacing node data.
- State sync is suitable for rebuilding disposable application data, but it
  is not a substitute for consensus-key and signer-state backups.

For validator onboarding, grants, or DKG-sensitive recovery, coordinate with
the Limonata team and follow the official validator documentation.

## Upgrade procedure

1. Review the official release notes and confirm whether the upgrade is
   rolling or height-gated.
2. Download the exact release and verify its published checksum.
3. Back up keys, signer state, configuration, and the current binary.
4. Stop only `limonatad.service`, replace the binary, and restart it.
5. Verify the reported version, advancing height, `catching_up=false`,
   peer count, logs, and validator signing if applicable.

Never run two processes with the same validator consensus key during an
upgrade or recovery.
