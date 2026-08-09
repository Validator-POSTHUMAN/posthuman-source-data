# Cosmos Hub — POSTHUMAN bootstrap files

POSTHUMAN publishes read-only bootstrap artifacts from its non-signing Cosmos
Hub RPC. They are refreshed hourly only while the local node is synced.

- Manifest: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/manifest.json>
- Genesis: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/genesis.json>
- Sanitized addrbook: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/addrbook.json>
- Live peer discovery: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/peers.json>
- Node version telemetry: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/version.json>

The manifest records the generation time, source URL, byte count and SHA-256
for each download. The addrbook is not a raw copy: it contains only public
IPv4 entries that were successful and not banned by the POSTHUMAN RPC node.

## Live peer discovery

`peers.json` is an optional discovery feed, not a node configuration. Each
hour it checks at most 80 sanitized addrbook entries from the non-signing RPC
and publishes up to 25 endpoints with a successful TCP connection at
generation time. The response has a two-hour `expires_at` value.

It does **not** prove consensus participation, peer identity beyond the local
addrbook record, uptime, validator status, or future reachability. Never
automatically write this list to `persistent_peers` or a production node
configuration; use it only as a bounded troubleshooting/discovery hint.

## Version telemetry

`version.json` is refreshed with the bootstrap artifacts. It reports the
running read-only RPC-node Gaia build and the latest stable release published
by the official `cosmos/gaia` GitHub repository. `status: "current"` means the
two version tags match; `release_available` is informational only.

It never downloads, installs, or switches a binary. For any node upgrade,
verify the on-chain upgrade plan and the official checksum independently.

## Verify before replacing local configuration

```bash
FILES=https://rpc.cosmos.posthuman.digital/files/cosmoshub
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

curl -fsSLo "$WORKDIR/manifest.json" "$FILES/manifest.json"
jq -e '.schema == "posthuman.network-files/v1" and .chain_id == "cosmoshub-4"' \
  "$WORKDIR/manifest.json"

for file in genesis addrbook; do
  curl -fsSLo "$WORKDIR/$file.json" "$FILES/$file.json"
  expected=$(jq -r ".artifacts.$file.sha256" "$WORKDIR/manifest.json")
  actual=$(sha256sum "$WORKDIR/$file.json" | awk '{print $1}')
  test "$actual" = "$expected"
done

curl -fsSLo "$WORKDIR/peers.json" "$FILES/peers.json"
expected=$(jq -r '.discovery.live_peers.sha256' "$WORKDIR/manifest.json")
actual=$(sha256sum "$WORKDIR/peers.json" | awk '{print $1}')
test "$actual" = "$expected"
jq -e '.schema == "posthuman.live-peers/v1" and .automatic_config_update == false and (.peers | type == "array")' \
  "$WORKDIR/peers.json"
```

Only after the checks pass, copy the files to the initialized Gaia home:

```bash
install -m 0644 "$WORKDIR/genesis.json" "$HOME/.gaia/config/genesis.json"
install -m 0644 "$WORKDIR/addrbook.json" "$HOME/.gaia/config/addrbook.json"
```

`genesis.json` is sourced from the official Cosmos Hub mainnet repository;
the serving manifest retains that origin. For a validator, compare the
official network source and chain ID independently before any recovery or
first start. These files do not replace a snapshot/recovery procedure.
