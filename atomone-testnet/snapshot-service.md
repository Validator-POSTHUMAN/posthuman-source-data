
# POSTHUMAN snapshot service for Atomone

## Stop the service
```
sudo systemctl stop atomoned
```
## Backup priv_validator_state.json
```
cp ~/.atomone/data/priv_validator_state.json ~/.atomone/priv_validator_state.json.backup
```
## Remove old data
```
rm -rf ~/.atomone/data
```
## Download and Extract the snapshot
```
curl https://snapshots.atomone-testnet.posthuman.digital/data_latest.lz4 | lz4 -dc - | tar -xf - -C ~/.atomone/
```
## Restore priv_validator_state.json
```
mv ~/.atomone/priv_validator_state.json.backup ~/.atomone/data/priv_validator_state.json
```

## Restart the service
```
sudo systemctl start atomoned && sudo journalctl -u atomoned -f -o cat
```
