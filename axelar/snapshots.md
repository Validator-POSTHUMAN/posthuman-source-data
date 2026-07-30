# Restore Axelar from a POSTHUMAN Snapshot

This procedure downloads and verifies the complete archive before touching
live node data. Validator operators must preserve their final signer state and
prove that no second host can sign with the same consensus key.

## Snapshot metadata

```bash
SNAP_URL="https://snapshots.axelar.posthuman.digital/data_latest.tar.lz4"
META_URL="https://snapshots.axelar.posthuman.digital/snapshot.json"
SNAP_DIR="$HOME/axelar-snapshot"
SNAP_FILE="$SNAP_DIR/data_latest.tar.lz4"

mkdir -p "$SNAP_DIR"
curl -fsS "$META_URL" | jq
```

Confirm the metadata says `axelar-dojo-1`, record `snapshot_size_bytes`,
`snapshot_sha256`, `snapshot_height`, and `created_at`, and compare the
snapshot with independent Axelar RPC truth. Do not continue across an
incompatible upgrade boundary. For validator recovery, authenticate the
checksum through an approved secondary channel; metadata served beside the
archive protects against accidental corruption but is not independent
provenance.

## 1. Download while the node stays online

```bash
sudo apt update
sudo apt install -y aria2 jq lz4

aria2c --continue=true \
  --max-connection-per-server=8 \
  --split=8 \
  --min-split-size=64M \
  --file-allocation=none \
  --dir="$SNAP_DIR" \
  --out="$(basename "$SNAP_FILE")" \
  "$SNAP_URL"
```

Never pipe a remote response directly into the live Axelar home.

## 2. Verify checksum, LZ4, and archive layout

Use the Axelar Safe Recovery Kit verifier:

```bash
curl -fsSLo "$SNAP_DIR/axelar-snapshot-verify.sh" \
  https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/f42a0e9b9b5e403edc54df5c53a5b9d221070ca0/axelar/scripts/axelar-snapshot-verify.sh
chmod 700 "$SNAP_DIR/axelar-snapshot-verify.sh"

EXPECTED_SHA256="<snapshot_sha256-from-metadata>"
EXPECTED_SIZE="<snapshot_size_bytes-from-metadata>"

"$SNAP_DIR/axelar-snapshot-verify.sh" \
  --archive "$SNAP_FILE" \
  --sha256 "$EXPECTED_SHA256" \
  --size "$EXPECTED_SIZE"
```

The verifier rejects checksum mismatches, corrupt LZ4 streams, path traversal,
absolute paths, links, special files, entries outside `data/`, and unexpected
database layouts in one complete archive pass. Stop if any check fails.

## 3. Extract into staging

Check free space for the archive, extracted data, rollback copy, and OS safety
margin. Then extract separately:

```bash
STAGE="$SNAP_DIR/extracted"
chmod 600 "$SNAP_FILE"

"$SNAP_DIR/axelar-snapshot-verify.sh" \
  --archive "$SNAP_FILE" \
  --sha256 "$EXPECTED_SHA256" \
  --size "$EXPECTED_SIZE"

install -d -m 700 "$STAGE"

lz4 -dc "$SNAP_FILE" |
  tar -xf - --no-same-owner --no-same-permissions -C "$STAGE"

test -d "$STAGE/data"
```

Re-run verification immediately before extraction and keep the archive
access-restricted. Do not extract over `$HOME/.axelar/data`.

## 4. Protect signer and companion state

Resolve the actual Axelar, vald, and tofnd service names first. For a validator:

1. Stop vald, then tofnd when required by the local runbook.
2. Stop the Axelar node and prove all related processes are absent.
3. Create an access-restricted backup outside `$HOME/.axelar/data`.
4. Preserve `$HOME/.axelar/config/`, keyring data, the final
   `priv_validator_state.json`, vald configuration, and tofnd state.
5. Verify backup ownership, mode, size, and integrity without printing secret
   contents.

Never start a validator with the snapshot-provided signer state. Restore the
preserved final state into staged `data/`. If snapshot height and signer state
cannot be reconciled, keep the validator stopped.

## 5. Reversible cutover

Prefer a rename-based swap instead of deleting live data:

```bash
AXELAR_HOME="$HOME/.axelar"
ROLLBACK="$AXELAR_HOME/data.rollback.$(date -u +%Y%m%dT%H%M%SZ)"

test ! -e "$ROLLBACK"
mv "$AXELAR_HOME/data" "$ROLLBACK"
mv "$STAGE/data" "$AXELAR_HOME/data"
```

Restore the preserved validator state where applicable, then restore the
expected owner and permissions. Start the Axelar node once.

If capacity cannot retain the rollback database, stop and obtain explicit
approval before deleting the exact old `data/` path. Do not use a broad home
deletion, glob, or generic `unsafe-reset-all`.

## 6. Verify before resuming vald

Require all of the following:

- correct chain ID and running Axelar binary;
- stable service with no panic, corruption, or restart loop;
- fresh block time and advancing local height;
- convergence with an independent RPC and `catching_up=false`;
- healthy peers;
- validator bonded, not jailed, and signing fresh external commits;
- monitoring recovered and disk headroom acceptable.

Only then start tofnd and vald in the approved order. Verify
`axelard health-check`, broadcaster funding/proxy state, external-chain
maintainer status, and successful new vald transactions.

The complete validator-neutral recovery reference is available at:

https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/f42a0e9b9b5e403edc54df5c53a5b9d221070ca0/axelar/references/safe-recovery.md
