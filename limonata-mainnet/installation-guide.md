# Limonata mainnet installation

Mainnet: `limonata_20777-1`, EVM `20777` (`0x5129`), base denom `aLIMO`, 18 decimals (1 LIMO = 10^18 aLIMO). This is a separate chain from the retired testnet. Never reuse its genesis, blockstore, peers or snapshots.

Approved binary: `v0.4.0-mainnet.3+src.c43879f764ef`, Linux amd64. This procedure creates a **new non-signing full node**. Existing validators must retain their original mainnet consensus/P2P identities and latest signing state; never initialize over their home. Installation does not admit a new validator.

## 1. Prerequisites and downloads

Use a dedicated unprivileged Linux amd64 account with Bash, curl, tar, sha256sum and jq. Check RAM and free NVMe capacity against current official guidance; no benchmark-backed minimum hardware specification is asserted here. Check port conflicts; expose only the intended P2P port (default TCP 26656), keeping management APIs private.

Run each block only after the previous checks pass; retain the same shell and staging directory. This downloads artifacts into a new temporary directory, never directly into a node home.

```bash
set -euo pipefail
LIMO_STAGE=$(mktemp -d)
cd "$LIMO_STAGE"
LIMO_RELEASE=https://github.com/Limonata-Blockchain/limonata/releases/download/v0.4.0-mainnet.3
curl --fail --location --retry 3 "$LIMO_RELEASE/limonatad-linux-amd64.tar.gz" -o binary.tar.gz
curl --fail --location --retry 3 "$LIMO_RELEASE/Limonata-Mainnet-Final-Genesis-17.tar.gz" -o final.tar.gz
sha256sum --check <<'SUMS'
2e0b2c332c3a207dd759fd467abc44be4e14718160c752fb348e1123f9eb53b0  binary.tar.gz
5a2fe722c90208b0872ba3e00dc575803e7af70f65052373b1714648729568d8  final.tar.gz
SUMS
tar -tzf binary.tar.gz
tar -tzf final.tar.gz
```

Before extraction inspect the listings: binary archive contains `limonatad`; final package contains public files under `Limonata-Mainnet-Final/`. Reject unexpected paths, traversal, links or secret files. Both checksums must pass.

```bash
tar -xzf binary.tar.gz
tar -xzf final.tar.gz
sha256sum --check <<'SUMS'
594d36fb0874b9abfbc182e7e104a0333f7df365d8d656d2f492a5f2fdf0724b  limonatad
944ad7370836c7a6f185002f6d599abe29f6cf7ce6ad30c83800537dc8d03460  Limonata-Mainnet-Final/genesis.json
SUMS
(cd Limonata-Mainnet-Final && sha256sum --check SHA256SUMS)
jq -e '.chain_id == "limonata_20777-1" and .genesis_time == "2026-11-12T23:58:16Z"' Limonata-Mainnet-Final/genesis.json
./limonatad version
```

Expected version: `v0.4.0-mainnet.3+src.c43879f764ef`. Read `START-MAINNET.txt`. Do not execute bundled signing helpers: the genesis ceremony is over. Never start on the historical precollection genesis.

## 2. Fresh full-node initialization

These guards refuse an existing home or installed daemon. The binary defaults to a different home, so always pass `--home`.

```bash
LIMO_HOME="$HOME/.limonata-mainnet"
test ! -e "$LIMO_HOME"
install -d -m 0755 "$HOME/.local/bin"
test ! -e "$HOME/.local/bin/limonatad"
install -m 0755 ./limonatad "$HOME/.local/bin/limonatad"
umask 077
"$HOME/.local/bin/limonatad" init full-node --chain-id limonata_20777-1 --home "$LIMO_HOME"
install -m 0600 Limonata-Mainnet-Final/genesis.json "$LIMO_HOME/config/genesis.json"
install -m 0600 Limonata-Mainnet-Final/config.toml "$LIMO_HOME/config/config.toml"
install -m 0600 Limonata-Mainnet-Final/app.toml "$LIMO_HOME/config/app.toml"
```

Before starting, review [Configuration](configuration.md): set your moniker, check `evm-chain-id = 20777`, private API bindings and the current peer list. Remove your own node ID if present. A new full node needs no imported validator key or account keyring. For existing genesis validators, follow [Validator admission](create-validator.md) instead.

## 3. Start and verify

Run the verified daemon in the foreground using an empty memory keyring:

```bash
"$HOME/.local/bin/limonatad" start --home "$HOME/.limonata-mainnet" --keyring-backend memory
```

In a second terminal use [Useful commands](useful-commands.md). Require the correct chain, advancing blocks, nonzero peers, `catching_up=false` and a same-height block hash match against independent mainnet RPCs. Process uptime is not sync, signing or DKG proof.

After foreground checks pass, stop the process cleanly before configuring a supervisor. Use a systemd unit for the same unprivileged account with resolved absolute binary/home paths, `--keyring-backend memory`, `Restart=on-failure` and reviewed file limits. Review ownership, paths, port conflicts and journal before enabling it. Never launch a second process for the same home.

If a fresh install fails, stop the new process and retain stage/home/logs for diagnosis. Never reset an existing signer, overwrite keys, restore older signing state or downgrade across state-breaking upgrades.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
