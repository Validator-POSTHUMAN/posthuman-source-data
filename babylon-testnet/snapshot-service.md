# POSTHUMAN snapshot service for the Babylon testnet

(Updated every 72 hours)

## Install Required Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install curl git wget htop tmux build-essential jq make lz4 gcc unzip -y
```

## Stop the service
```
sudo systemctl stop babylon
```
## Backup priv_validator_state.json
```
cp ~/.babylond/data/priv_validator_state.json ~/.babylond/priv_validator_state.json.backup
```
## Remove old data
```
rm -rf ~/.babylond/data
```
## Download and Extract the snapshot
```
curl https://snapshots.babylon.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C ~/.babylond/
```
## Restore priv_validator_state.json
```
mv ~/.babylond/priv_validator_state.json.backup ~/.babylond/data/priv_validator_state.json
```

## Restart the service
```
sudo systemctl start babylon && sudo journalctl -u babylon -f -o cat
```
