# Celestia Mainnet Snapshot

**Publication resumed — checked 2026-11-25.** Current metadata identifies
chain `celestia`, height `16219577`, `created_at = 2026-11-25T12:39:47Z`,
and size `13995807021` bytes. The archive responds to full and range requests.
The complete 13,995,807,021-byte archive independently matched the published
SHA-256, passed `lz4 -t`, and its tar listing contained 7,315 members under
`data/` with no links or unexpected paths (checked 2026-11-25 UTC). These
integrity checks do **not** prove current-archive restore compatibility. The
current archive has not passed an end-to-end restore test; validate it on an
isolated non-signing node before recovery.

**Validator-state hazard:** the archive includes `data/priv_validator_state.json`
reset to height/round/step zero for a disposable zero-power snapshot source.
Never install that file on a signing validator or overwrite its current state.
A validator restore must exclude the archive's copy and preserve the newest
local signer state after stopping and fencing the signer. The historical recipe
below is disabled; it must not be treated as a safe validator restore procedure.

Historical restore evidence: an earlier archive passed an end-to-end restore
on 2026-09-27 (height `14445450`, 371 advancing blocks), and a separate
2026-11-08 publisher archive passed a restore check (379 advancing blocks).
Neither result proves the bytes published today. The publisher copies the
node's pruned data without offline application-state rewriting.

POSTHUMAN provides a pruned Celestia consensus-node snapshot for chain ID
`celestia`.

- DB backend: PebbleDB
- Intended publication cadence: twice daily, around 01:20 and 13:20 CET
  (Europe/Berlin), with timer jitter. Read `created_at` from `snapshot.json` rather than assuming freshness.
- Archive format: `snapshot-latest.tar.lz4`; read `snapshot_size_bytes` from
  `snapshot.json` before download because its size changes with the source data.
- Resumable: yes. The host answers byte-range requests, so an interrupted
  download continues instead of starting over.
- Current archive restore-verified: **no**. Historical tests are scoped above.
- Node parameters behind it: `pruning = custom` / `keep-recent = 100` /
  `interval = 10`, `min-retain-blocks = 30000`,
  `indexer = null`, PebbleDB. The archive inherits exactly those, so it is not an
  archive node and carries no transaction index.

## Snapshot Endpoint

- Index: https://snapshots-celestia-mainnet.posthuman.digital/
- Metadata: https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json
- Snapshot file: `https://snapshots-celestia-mainnet.posthuman.digital/snapshot-latest.tar.lz4`
- Genesis: `https://snapshots-celestia-mainnet.posthuman.digital/genesis.json`
- Addrbook: `https://snapshots-celestia-mainnet.posthuman.digital/addrbook.json`

The snapshot contains the `data/` directory and is extracted directly into
`$HOME/.celestia-app`. Configure both CometBFT and app DB backends as
PebbleDB before starting from this snapshot.

### An alternative source

ITRocket publishes a PebbleDB Celestia snapshot with a machine-readable index.
Historical example only: its metadata at the 2026-10-28 check reported height `15377714` (live chain
above `15382800`), size `3.3G`, and a four-hour interval. It was not downloaded
or restore-tested in this check. POSTHUMAN restored its own node from that
provider twice in September; that historical proof is not proof of this
particular archive.

It is somebody else's artifact: confirm the height against a live RPC, keep
`priv_validator_key.json` and `priv_validator_state.json` out of the extraction,
and stop the node only after the download and decompression have succeeded.

## Preflight

Always compare snapshot metadata with a trusted live RPC before restore:

**The Quick Restore below remains a non-executable historical reference until
the current archive passes an isolated non-signing restore test and the
validator-state handling is separately reviewed.** Publication resuming alone
does not re-enable this recipe. Use the v11 multiplexer with embedded v10.6.0
while mainnet is on protocol app 10.

```bash
# The POSTHUMAN candidate you are about to restore.
curl -fsS https://snapshots-celestia-mainnet.posthuman.digital/snapshot.json | jq .

# Two independent views of the live chain: ours and somebody else's.
curl -fsS https://rpc-celestia-mainnet.posthuman.digital/status | \
  jq -r '.result.node_info.network, .result.sync_info.latest_block_height, .result.sync_info.catching_up'
curl -fsS https://celestia-rpc.publicnode.com/status | \
  jq -r '.result.sync_info.latest_block_height'
```

Stop if:

- `chain_id` is not `celestia`;
- `created_at` is stale relative to the twice-daily publication cadence;
- metadata height is far ahead of or inconsistent with trusted RPC height;
- snapshot file size is unexpectedly small;
- you cannot preserve keys and validator state.

## Quick Restore

Requires `aria2`, `jq` and `lz4`:

```text
sudo apt update && sudo apt install -y aria2 jq lz4
```

```text
export CELESTIA_HOME="$HOME/.celestia-app"
export SERVICE_NAME="celestia-appd"
export SNAP_DIR="$HOME/celestia-mainnet-snapshot-restore"

# Download and validate before stopping the node. Fetched to disk rather than
# piped into tar, so a dropped connection resumes and the archive is proven
# before anything touches live data.
rm -rf "$SNAP_DIR"
install -d -m 0700 "$SNAP_DIR"

SNAP_BASE="https://snapshots-celestia-mainnet.posthuman.digital"
curl -fsS "$SNAP_BASE/snapshot.json" -o "$SNAP_DIR/snapshot.json"
EXPECTED_SHA256="$(jq -er '.snapshot_sha256' "$SNAP_DIR/snapshot.json")"
EXPECTED_SIZE="$(jq -er '.snapshot_size_bytes' "$SNAP_DIR/snapshot.json")"
jq -er '.chain_id == "celestia"' "$SNAP_DIR/snapshot.json"

aria2c --continue=true --max-connection-per-server=8 --split=8 \
  --min-split-size=64M --file-allocation=none \
  --dir="$SNAP_DIR" --out=snapshot-latest.tar.lz4 \
  "$SNAP_BASE/snapshot-latest.tar.lz4"

test "$(stat -c %s "$SNAP_DIR/snapshot-latest.tar.lz4")" = "$EXPECTED_SIZE"
printf '%s  %s\n' "$EXPECTED_SHA256" "$SNAP_DIR/snapshot-latest.tar.lz4" | \
  sha256sum --check --strict
lz4 -t "$SNAP_DIR/snapshot-latest.tar.lz4"

lz4 -dc "$SNAP_DIR/snapshot-latest.tar.lz4" | tar -xf - -C "$SNAP_DIR"
test -d "$SNAP_DIR/data/application.db"

cp "$CELESTIA_HOME/data/priv_validator_state.json" \
   "$CELESTIA_HOME/priv_validator_state.json.backup" 2>/dev/null || true

sudo systemctl stop "$SERVICE_NAME"
BACKUP_DIR="$CELESTIA_HOME/data.before-snapshot-$(date +%Y%m%d-%H%M%S)"
if [ -d "$CELESTIA_HOME/data" ]; then
  mv "$CELESTIA_HOME/data" "$BACKUP_DIR"
fi
mv "$SNAP_DIR/data" "$CELESTIA_HOME/data"

sed -i -e 's|^db_backend *=.*|db_backend = "pebbledb"|' \
  "$CELESTIA_HOME/config/config.toml"

if grep -q '^app-db-backend' "$CELESTIA_HOME/config/app.toml"; then
  sed -i 's|^app-db-backend *=.*|app-db-backend = "pebbledb"|' \
    "$CELESTIA_HOME/config/app.toml"
else
  printf '\napp-db-backend = "pebbledb"\n' >> "$CELESTIA_HOME/config/app.toml"
fi

if [ -f "$CELESTIA_HOME/priv_validator_state.json.backup" ]; then
  mv "$CELESTIA_HOME/priv_validator_state.json.backup" \
     "$CELESTIA_HOME/data/priv_validator_state.json"
fi

sudo systemctl start "$SERVICE_NAME"
journalctl -u "$SERVICE_NAME" -f
```

## Verify

```bash
curl -fsS http://127.0.0.1:26657/status | jq -r '
  .result.node_info.network,
  .result.sync_info.latest_block_height,
  .result.sync_info.latest_block_time,
  .result.sync_info.catching_up'
```

The node is recovered when chain ID is `celestia`, block time is fresh, height
advances, and `catching_up=false`.

## Important Boundary

This is a consensus-node snapshot for `celestia-appd`. It is not a
`celestia-node` bridge/full/light node-store snapshot. Do not extract it into
`~/.celestia-bridge`, `~/.celestia-full`, or `~/.celestia-light`.
