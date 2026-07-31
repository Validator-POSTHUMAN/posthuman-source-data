# Restore Osmosis from a POSTHUMAN Snapshot

The POSTHUMAN Osmosis archive contains the pruned `data/` directory and the
matching top-level `wasm/` directory. Download and fully validate it before
stopping a node. Never extract a remote response directly over live data.

The public URL will be enabled only after POSTHUMAN completes external DNS,
TLS, byte-range, and restore verification.

## 1. Fetch metadata and archive

```bash
sudo apt update
sudo apt install -y aria2 jq lz4 python3

SNAP_BASE="https://snapshots-osmosis.posthuman.digital"
WORK="$HOME/osmosis-snapshot"
ARCHIVE="$WORK/osmosis_latest.tar.lz4"
META="$WORK/snapshot.json"

install -d -m 0700 "$WORK"
curl -fL --retry 3 --output "$META" "$SNAP_BASE/snapshot.json"
jq -e '.chain_id == "osmosis-1" and .snapshot_compression == "lz4"' "$META"

aria2c --continue=true --max-connection-per-server=8 --split=8 \
  --min-split-size=64M --file-allocation=none \
  --dir="$WORK" --out="$(basename "$ARCHIVE")" \
  "$SNAP_BASE/osmosis_latest.tar.lz4"
```

Compare `snapshot_height` and `created_at` with independent current chain
truth. Stop if the snapshot crosses an incompatible upgrade boundary.

## 2. Verify size, SHA-256, LZ4, and safe layout

```bash
EXPECTED_SIZE="$(jq -er '.snapshot_size_bytes' "$META")"
EXPECTED_SHA256="$(jq -er '.snapshot_sha256' "$META")"

test "$(stat -c %s "$ARCHIVE")" = "$EXPECTED_SIZE"
printf '%s  %s\n' "$EXPECTED_SHA256" "$ARCHIVE" | sha256sum --check --strict
lz4 -t "$ARCHIVE"

TAR_FILE="$WORK/osmosis_snapshot.tar"
lz4 -d "$ARCHIVE" "$TAR_FILE"
```

Validate the local tar before extraction:

```bash
python3 - "$TAR_FILE" <<'PY'
import pathlib
import sys
import tarfile

archive = pathlib.Path(sys.argv[1])
top = set()
has_data = False
with tarfile.open(archive, mode="r:") as tf:
    for member in tf:
        pure = pathlib.PurePosixPath(member.name)
        if pure.is_absolute() or ".." in pure.parts or not pure.parts:
            raise SystemExit(f"unsafe path: {member.name!r}")
        top.add(pure.parts[0])
        has_data = has_data or pure.parts[0] == "data"
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise SystemExit(f"unsafe entry type: {member.name!r}")
if not has_data or not top.issubset({"data", "wasm"}):
    raise SystemExit(f"unexpected archive layout: {sorted(top)}")
print(f"safe archive layout: {sorted(top)}")
PY
```

Budget disk for the compressed archive, decompressed tar, staged extraction,
rollback data, and operating-system safety margin.

## 3. Extract to staging while the node stays online

```bash
STAGE="$WORK/stage"
install -d -m 0700 "$STAGE"
tar --extract --file "$TAR_FILE" --directory "$STAGE" \
  --no-same-owner --no-same-permissions
test -d "$STAGE/data"
test -d "$STAGE/wasm"
```

## 4. Preserve final signer state and cut over reversibly

Resolve the real service and home first. For a validator, prove there is no
second process capable of signing with the same consensus key.

```bash
OSMOSIS_HOME="$HOME/.osmosisd"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$HOME/osmosis-recovery-$STAMP"

install -d -m 0700 "$BACKUP"
sudo systemctl stop <osmosis-service>
test "$(sudo systemctl is-active <osmosis-service> || true)" = "inactive"

cp -a "$OSMOSIS_HOME/config" "$BACKUP/config"
cp -a "$OSMOSIS_HOME/data/priv_validator_state.json" \
  "$BACKUP/priv_validator_state.json"

mv "$OSMOSIS_HOME/data" "$OSMOSIS_HOME/data.rollback.$STAMP"
mv "$OSMOSIS_HOME/wasm" "$OSMOSIS_HOME/wasm.rollback.$STAMP"
mv "$STAGE/data" "$OSMOSIS_HOME/data"
mv "$STAGE/wasm" "$OSMOSIS_HOME/wasm"

install -m 0600 "$BACKUP/priv_validator_state.json" \
  "$OSMOSIS_HOME/data/priv_validator_state.json"
```

Do not use snapshot-provided validator state. Do not delete rollback data until
the recovered node has been stable and signing has been externally verified.

## 5. Start once and verify

```bash
sudo systemctl start <osmosis-service>
sudo systemctl is-active <osmosis-service>
curl -fsS http://127.0.0.1:<rpc-port>/status | jq '.result | {
  chain_id: .node_info.network,
  height: .sync_info.latest_block_height,
  block_time: .sync_info.latest_block_time,
  catching_up: .sync_info.catching_up
}'
```

Require fresh advancing `osmosis-1` blocks, convergence with an independent
RPC, `catching_up=false`, healthy peers, stable restarts, bonded/not-jailed and
not-tombstoned state, and several fresh external signatures before declaring a
validator recovered.
