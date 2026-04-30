# 🚀 Restore XRPL EVM Node from [Posthuman](https://snapshots.exrp.posthuman.digital/) Snapshots

This guide explains how to restore your XRPL EVM node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop XRPL EVM Node**
Before restoring, stop the XRPL EVM process to prevent database corruption:

```bash
sudo systemctl stop exrpd
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.exrpd/data/priv_validator_state.json $HOME/.exrpd/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.exrpd/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.exrp.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.exrpd
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.exrpd/priv_validator_state.json.backup $HOME/.exrpd/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart XRPL EVM Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart exrpd
sudo journalctl -u exrp -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 
