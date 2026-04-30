# 🚀 Restore Shentu Node from [Posthuman](https://snapshots.shentu.posthuman.digital/) Snapshots

This guide explains how to restore your Shentu node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop Shentu Node**
Before restoring, stop the Shentu process to prevent database corruption:

```bash
sudo systemctl stop shentud
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.shentud/data/priv_validator_state.json $HOME/.shentud/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.shentud/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.shentu.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.shentud
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.shentud/priv_validator_state.json.backup $HOME/.shentud/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Shentu Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart shentud
sudo journalctl -u shentud -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 
