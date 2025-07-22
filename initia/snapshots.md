# 🚀 Restore Initia Node from [Posthuman](https://snapshots.initia.posthuman.digital/) Snapshots

This guide explains how to restore your Initia node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop Initia Node**
Before restoring, stop the Kyve process to prevent database corruption:

```bash
sudo systemctl stop initia
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.initia/data/priv_validator_state.json $HOME/.initia/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.initia/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.initia.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.kyve
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.initia/priv_validator_state.json.backup $HOME/.initia/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Initia Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart initia
sudo journalctl -u initia -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 

