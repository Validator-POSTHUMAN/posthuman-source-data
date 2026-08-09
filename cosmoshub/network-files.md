# Cosmos Hub — POSTHUMAN bootstrap files

POSTHUMAN publishes read-only bootstrap artifacts from its non-signing Cosmos
Hub RPC. They are refreshed hourly only while the local node is synced.

- Manifest: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/manifest.json>
- Genesis: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/genesis.json>
- Sanitized addrbook: <https://rpc.cosmos.posthuman.digital/files/cosmoshub/addrbook.json>

The manifest records the generation time, source URL, byte count and SHA-256
for each download. The addrbook is not a raw copy: it contains only public
IPv4 entries that were successful and not banned by the POSTHUMAN RPC node.

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
