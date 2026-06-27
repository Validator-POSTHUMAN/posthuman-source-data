# 🚀 Restore Axelar Node from [POSTHUMAN](https://snapshots.axelar.posthuman.digital/) Snapshots

This guide explains how to restore your Axelar node using a snapshot served by
**POSTHUMAN**.

---

## **📥 Step 1: Download the Latest POSTHUMAN Snapshot**
> **Note:** use the latest available snapshot. Check the HTTP `Last-Modified`
> header before downloading.

Download the snapshot first. Do not stop the node or delete the existing data
until the file is fully downloaded.

```bash
SNAP_URL="https://snapshots.axelar.posthuman.digital/data_latest.tar.lz4"
SNAP_DIR="$HOME/axelar-snapshot"
SNAP_DATE=$(curl -fsSI "$SNAP_URL" | awk -F': ' 'tolower($1)=="last-modified"{print $2}' | xargs -I{} date -u -d "{}" +%Y-%m-%d)
SNAP_BASENAME="axelar_${SNAP_DATE}.tar.lz4"
SNAP_FILE="$SNAP_DIR/$SNAP_BASENAME"

sudo apt update
sudo apt install -y aria2 lz4

mkdir -p "$SNAP_DIR"

aria2c --continue=true \
  --max-connection-per-server=8 \
  --split=8 \
  --min-split-size=64M \
  --file-allocation=none \
  --dir="$SNAP_DIR" \
  --out="$SNAP_BASENAME" \
  "$SNAP_URL"
```

---

## **🛑 Step 2: Stop Axelar Node**
Before replacing the data directory, stop the axelar process to prevent database corruption:

```bash
sudo systemctl stop axelar
```

---

## **📌 Step 3: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.axelar/data/priv_validator_state.json $HOME/.axelar/priv_validator_state.json.backup
```

---

## **🗑 Step 4: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.axelar/data
```

---

## **📦 Step 5: Extract the Snapshot**
Extract the downloaded snapshot into your Axelar home directory:

```bash
lz4 -dc "$SNAP_FILE" | tar -xf - -C "$HOME/.axelar"
```

---

## **📂 Step 6: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.axelar/priv_validator_state.json.backup $HOME/.axelar/data/priv_validator_state.json
```

---

## **▶️ Step 7: Restart Axelar Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart axelar
sudo journalctl -u axelar -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **POSTHUMAN snapshot**. 🚀
