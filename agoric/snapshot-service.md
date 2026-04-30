# POSTHUMAN snapshot service for Agoric
Updated every 24 hours

## Stop the service
```
sudo systemctl stop agoric
```
## Backup priv_validator_state.json
```
cp ~/.agoric/data/priv_validator_state.json ~/.agoric/priv_validator_state.json.backup
```
## Remove old data
```
rm -rf ~/.agoric/data
```
## Download and Extract the snapshot
```
curl https://snapshots.agoric.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C ~/.agoric/
```
## Restore priv_validator_state.json
```
mv ~/.agoric/priv_validator_state.json.backup ~/.agoric/data/priv_validator_state.json
```

## Restart the service
```
sudo systemctl start agoric && sudo journalctl -u agoric -f -o cat
```
