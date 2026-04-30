# 🚀 Restore Provenance Node from [Posthuman](https://snapshots.provenance.posthuman.digital/) Snapshots

This guide explains how to restore your provenance node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop Provenance Node**
Before restoring, stop the provenance process to prevent database corruption:

```bash
sudo systemctl stop provenanced
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.provenanced/data/priv_validator_state.json $HOME/.provenanced/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.provenanced/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.provenance.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.provenanced
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.provenanced/priv_validator_state.json.backup $HOME/.provenanced/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Provenance Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart provenanced
sudo journalctl -u provenanced -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **[Posthuman](https://snapshots.provenance.posthuman.digital/) snapshot**. 🚀 
