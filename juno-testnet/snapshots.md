# 🚀 Restore Juno Node from [Posthuman](https://snapshots.juno-testnet.posthuman.digital/) Snapshots

This guide explains how to restore your Juno node using a snapshot from **Posthuman**.

---

## **🛑 Step 1: Stop juno Node**
Before restoring, stop the Kyve process to prevent database corruption:

```bash
sudo systemctl stop juno
```

---

## **📌 Step 2: Backup Validator State (IMPORTANT)**
To avoid double signing issues, **backup your validator state file**:

```bash
cp $HOME/.juno/data/priv_validator_state.json $HOME/.juno/priv_validator_state.json.backup
```

---

## **🗑 Step 3: Remove Old Blockchain Data**
Delete the old data to **free space** and **prevent conflicts**:

```bash
rm -rf $HOME/.juno/data
```

---

## **📥 Step 4: Download & Extract the Latest Posthuman Snapshot**
> **Note:** Since Posthuman updates snapshots **every 24 hours**, use the latest one:

```bash
curl -L https://snapshots.juno-testnet.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C $HOME/.juno
```



---

## **📂 Step 5: Restore Validator State**
Move back the **backup validator state file**:

```bash
mv $HOME/.kyve/priv_validator_state.json.backup $HOME/.juno/data/priv_validator_state.json
```

---

## **▶️ Step 6: Restart Juno Node & Monitor Logs**
Now, restart the service and monitor its logs:

```bash
sudo systemctl restart juno
sudo journalctl -u juno -fo cat
```

---

## **✅ Done!**
Your node should now sync from the restored **Posthuman snapshot**. 🚀 

