# DungeonChain (`dungeon-1`) node installation

DungeonChain cannot use the shared generated installation guide, for one
concrete reason: its genesis is published as a **compressed archive**, not as a
`genesis.json`. The generated guide pipes a URL straight into
`config/genesis.json`, which would leave a gzip blob where the daemon expects
JSON, and the node would fail to start with a parse error that says nothing
about the real cause.

There is a second trap. The repository publishes **two** genesis archives, and
only one of them is correct for a node being installed today.

| Archive | Genesis time | `app_version` | Use it? |
| --- | --- | --- | --- |
| `genesis.json.tar.gz` | 2024-10-17 | 1.0.0 | **No.** The original ICS genesis, from before the chain left Interchain Security. |
| `genesis-hardfork.tar.gz` | 2025-03-27 | 4.0.0 | **Yes.** The post-hardfork genesis the live chain continues from. |

`dungeon-1` hard-forked out of ICS at height `7824000`. A node started from the
pre-hardfork genesis will not reach the current chain.

Verified 2026-09-17 against two independent public endpoints: the live network
reports `dungeond 9.0.0` on `dungeon-1`. Check the current release before you
install — this guide records what was true when it was written, not a permanent
pin.

## 1. Build the binary

```bash
set -Eeuo pipefail
DUNGEON_VERSION='v9.0.0'
DUNGEON_REPO='https://github.com/Crypto-Dungeon/dungeonchain'

cd "$(mktemp -d)"
git clone "$DUNGEON_REPO" dungeonchain
cd dungeonchain
git checkout "$DUNGEON_VERSION"
make install
dungeond version
```

`dungeond version` must print the version you checked out. The daemon's default
home is `$HOME/.dungeonchain` — note the name does not match the network id.

## 2. Initialise

```bash
MONIKER='<your-moniker>'
dungeond init "$MONIKER" --chain-id dungeon-1
```

## 3. Install the genesis

This is the step the generated guide gets wrong. Download the **hardfork**
archive and extract it; do not redirect it into `genesis.json`.

```bash
set -Eeuo pipefail
GENESIS_URL='https://github.com/Crypto-Dungeon/dungeonchain/raw/main/network/dungeon-1/genesis-hardfork.tar.gz'

curl -fsSL "$GENESIS_URL" -o /tmp/dungeon-genesis.tar.gz
tar -xzf /tmp/dungeon-genesis.tar.gz -C "$HOME/.dungeonchain/config"
rm -f /tmp/dungeon-genesis.tar.gz
```

The archive contains a single member, `genesis.json`, so it extracts straight
into `config/`. Verify before going further:

```bash
jq -r '.chain_id, .app_version, .genesis_time' "$HOME/.dungeonchain/config/genesis.json"
```

Expect `dungeon-1`, `4.0.0` and `2025-03-27T19:30:00.555168606Z`. If you see
`1.0.0` and a 2024 timestamp you extracted the pre-hardfork archive; delete it
and start this step again.

```bash
dungeond validate-genesis
```

## 4. Peers and sync

Take seeds and persistent peers from the network directory in the repository,
`network/dungeon-1/`, and set them in `config/config.toml`. Public RPC and REST
endpoints for cross-checking your node's height:

- `https://api.dungeongames.io`
- `https://api.dungeon.chaintools.tech`

A fresh node from genesis replays from the hardfork height. Use a published
snapshot instead if one is available from a provider you already trust.

## 5. Service

```bash
sudo tee /etc/systemd/system/dungeond.service > /dev/null <<EOF
[Unit]
Description=dungeond daemon
After=network-online.target

[Service]
User=$USER
ExecStart=$(which dungeond) start
Restart=on-failure
RestartSec=10
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable dungeond.service
sudo systemctl start dungeond.service
journalctl -u dungeond.service -f
```

The unit passes no `--home`, so the daemon uses `$HOME/.dungeonchain` — the same
directory this guide wrote the genesis into. If you run the daemon as a
different user than the one that initialised the node, pass `--home` explicitly
in `ExecStart` rather than relying on the default.

## 6. Before you make it a validator

Back up `config/priv_validator_key.json` before the node ever signs, and never
start the same consensus key on two hosts. The hardfork notes in the repository
carry the same warning for a reason.
