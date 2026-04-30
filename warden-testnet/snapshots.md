# 🚀 Restore Warden testnet Node from [Posthuman](https://snapshots.warden-testnet.posthuman.digital/) Snapshots

This guide explains how to restore your Warden testnet node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop Warden testnet Node**
Before restoring, stop the Side process to prevent database corruption:

```bash
sudo systemctl stop warden
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.warden/data/priv_validator_state.json $HOME/.warden/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.warden/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.warden-testnet.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.warden
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.warden/priv_validator_state.json.backup $HOME/.warden/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Warden testnet Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart warden
sudo journalctl -u warden -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 

