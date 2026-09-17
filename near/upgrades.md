# NEAR Node Upgrades

There is no Cosmovisor on NEAR and no on-chain upgrade plan with a halt height
that stops the node politely. A `neard` release that carries a protocol
version bump must be running **before** the protocol switches, or the node
falls out of the network at the switch.

## Release channels

| Network | Use |
|---------|-----|
| mainnet | the latest **stable** tag |
| testnet | the latest **release candidate** |

Track [github.com/near/nearcore/releases](https://github.com/near/nearcore/releases)
and the NEAR validator announcement channels. Reference point at the time of
writing: stable `2.13.4`, mainnet protocol version `86`.

Check what you are running and what the chain expects:

```bash
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{node_version: .result.version.version,
         protocol_version: .result.protocol_version,
         latest_protocol_version: .result.latest_protocol_version}'
```

`latest_protocol_version` above `protocol_version` means the network is voting
toward a version your node may not support. Resolve that before the switch, not
after.

## Procedure

Build on a non-validator host first. A 25-minute compile on the validator, with
the service running, is a self-inflicted outage.

```bash
cd ~/nearcore
git fetch origin --tags
git checkout tags/<new-version> -b node-<new-version>
make neard
./target/release/neard --version
```

Stage the new binary beside the current one so rollback is a file move, not a
rebuild:

```bash
sudo cp /usr/local/bin/neard /usr/local/bin/neard.$(neard --version | awk '{print $2}')
sudo install -m 0755 target/release/neard /usr/local/bin/neard.new
```

Swap and restart:

```bash
sudo systemctl stop neard
sudo mv /usr/local/bin/neard.new /usr/local/bin/neard
sudo systemctl start neard
journalctl -u neard -f
```

Restart between assigned chunks where you can. There is no perfect window on a
~1.1 s block time, but a restart at the start of an epoch costs less than one
mid-epoch.

## Database migrations

Some releases migrate the store on first start (2.13.0, for example, ran a
48 → 49 migration for continuous epoch sync). Migrations can take a long time
and the node is unavailable throughout.

- Read the release notes before starting the new binary.
- Do not interrupt a migration. A half-migrated store usually means a re-sync.
- Watch the logs rather than assuming: `journalctl -u neard -f | grep -i migrat`.

## Verification

Do not call an upgrade complete until all four hold:

```bash
neard --version                                   # 1. new version on disk
systemctl is-active neard                         # 2. active
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' \
  | jq '{v: .result.version.version, h: .result.sync_info.latest_block_height,
         syncing: .result.sync_info.syncing}'     # 3. synced, height advancing
```

4. Fresh produced work in the current epoch — sample the validator counters
   twice, 30 seconds apart, and confirm produced endorsements increase:

```bash
POOL=<name>.poolv1.near
for i in 1 2; do
  curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"validators","params":[null]}' \
    | jq --arg p "$POOL" -c '.result.current_validators[] | select(.account_id==$p) |
        {e: .num_produced_endorsements, exp: .num_expected_endorsements}'
  sleep 30
done
```

"Service is active" is not a health signal. Neither is a cumulative epoch ratio
that has not yet recovered from the restart gap.

## Rollback

```bash
sudo systemctl stop neard
sudo mv /usr/local/bin/neard.<previous-version> /usr/local/bin/neard
sudo systemctl start neard
```

Rollback works only if the new release did not migrate the store. If it did,
the old binary will refuse the new database version and you need a re-sync.
This is the reason to read release notes first.

## Related guides

- **Installation guide** — build prerequisites and the systemd unit
- **Monitoring** — `version_build` and `protocol_version` drift alerts
- **Security** — why the previous binary stays on disk
