# 🚀 Restore Sidechain Node from [Posthuman](https://snapshots.sidechain.posthuman.digital/) Snapshots

This guide explains how to restore your Side node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop Sidechain Node**
Before restoring, stop the Side process to prevent database corruption:

```bash
sudo systemctl stop sided
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.side/data/priv_validator_state.json $HOME/.side/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.side/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.sidechain.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.side
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.side/priv_validator_state.json.backup $HOME/.side/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Side Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart sided
sudo journalctl -u sided -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 

