# Canton Network TestNet — Backup & Recovery

TestNet has one property MainNet does not: it is **reset roughly every three
months**, and a reset deletes everything. That changes what backups are for.
On MainNet they protect assets. On TestNet they protect your procedure — the
reset is a free, scheduled disaster-recovery drill, and treating it as one is
the whole point of running a TestNet validator.

Everything else here mirrors MainNet exactly, deliberately: rehearse the
procedure you will have to execute for real.

## Network resets

DevNet and TestNet are reset roughly every three months, staggered so the two
never reset at the same time. The exact time is announced in the
`#validator-operations` channel run by the
[Global Synchronizer Foundation](https://sync.global/).

A reset requires a **full redeployment** and loses all data on the node. Until
you complete it, your node is not functional — but it keeps running and keeps
looking healthy in `docker ps`. POSTHUMAN's DevNet validator sat
`Up 7 weeks (unhealthy)` on `0.6.14` while the network ran `0.8.1` for exactly
this reason.

Detect a reset before it detects you: alert on `sv.migration_id` from `/info`
changing.

```bash
curl -s https://docs.test.global.canton.network.sync.global/info | jq .
```

### Reset procedure

1. Stop the node and remove **all** state: Docker volumes and databases,
   including any managed Postgres in AWS RDS, GCP CloudSQL or similar. Helm
   deployments: uninstall all charts and delete all PVCs.
2. Acquire a **fresh onboarding secret** — on TestNet, from your SV sponsor.
   On DevNet you can call the endpoint yourself.
3. Redeploy with the migration ID the announcement specifies. Check it against
   `/info` rather than assuming; both the validator and the participant
   configuration carry it.
4. **Take a new identities backup.** Identities change as part of the reset, so
   every backup taken before it is now worthless.

Step 4 is the one operators skip. A node redeployed after a reset with no fresh
identities backup is unrecoverable between the reset and the next backup run.

## Two backups, not one

Between resets, back up exactly as you would on MainNet.

| Backup | Contains | Frequency | Where it goes |
|---|---|---|---|
| Node identities | participant private keys + topology snapshot | after onboarding, after every reset, after any identity change | off-host, mode 0600 |
| Postgres dumps | validator app DB and participant DB | every 4 hours | off-host with retention |

### 1. Node identities backup

The file contains the participant's **private keys**. Store it off-host and at
mode `0600`, and never share TestNet and MainNet backup destinations.

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

TOKEN=$(python3 get-token.py administrator)   # requires pyjwt

curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_testnet_identity_$(date -u +%Y%m%dT%H%M%SZ).json
```

Verify it before trusting it — an error body is still a file:

```bash
jq -e '.id and (.keys | length > 0)' ~/canton_testnet_identity_*.json
```

### 2. Postgres backups

Every 4 hours, validator app **strictly before** participant. The order is a
protocol requirement, not a preference: a participant dump older than its
matching validator dump cannot be restored as a pair.

```bash
backup_dir=~/canton-backups
mkdir -p "$backup_dir"

docker exec splice-validator-postgres-splice-1 \
  pg_dump -U cnadmin validator \
  > "$backup_dir/validator-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"

active_participant_db=$(docker exec splice-validator-participant-1 \
  bash -c 'echo $CANTON_PARTICIPANT_POSTGRES_DB')

docker exec splice-validator-postgres-splice-1 \
  pg_dump -U cnadmin "$active_participant_db" \
  > "$backup_dir/${active_participant_db}-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"
```

Read the participant database name from the container. It carries the migration
ID — `participant-1` on TestNet today — and changes on every reset.

### Automating it

```bash
~/canton-validator-toolkit/scripts/backup.sh          # manual run
```

Configured in `~/.canton/toolkit.conf`:

```
BACKUP_TYPE=rsync            # rsync | r2 | skip
REMOTE_HOST=ubuntu@backup.example.com
REMOTE_PATH=~/canton-backups/testnet
RETENTION_DAYS=7
```

Alert on the **upload** step, not only the dump. POSTHUMAN's real TestNet
backup failure was not a bad dump: local dumps succeeded, the remote sync
failed with `Permission denied (publickey)` after the backup key fell out of
the destination's `authorized_keys`, and the guarded auto-upgrade aborted
behind it. The node looked fine; the backups had stopped leaving the host.

### Retention

- **30 days is a hard ceiling** for database backups on any Canton network.
  Sequencer pruning means a participant restored from anything older can never
  catch up.
- On TestNet, retention beyond the last reset is pointless — those dumps belong
  to a network that no longer exists. Prune them.

## Restoring from a database backup

Possible when the backup is under 30 days old, taken since the last reset, and
no logical synchronizer upgrade has happened since.

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

./stop.sh
docker volume ls | grep postgres-splice          # confirm the exact name first
docker volume rm splice-validator_postgres-splice

docker compose up -d postgres-splice
docker exec splice-validator-postgres-splice-1 pg_isready   # repeat until ready

docker exec -i splice-validator-postgres-splice-1 \
  psql -U cnadmin validator < "$validator_dump_file"

docker exec -i splice-validator-postgres-splice-1 \
  psql -U cnadmin "participant-$migration_id" < "$participant_dump_file"

docker compose down
./start.sh -s "https://sv.sv-2.test.global.canton.network.digitalasset.com" \
  -o "" -p "YOUR_VALIDATOR_NAME" -m "1" -w
```

Users onboarded after the backup was taken must be re-onboarded by hand.

## Re-onboarding from an identities backup

Use this when the database is gone, too old, or from before a reset.

```bash
./start.sh \
  -s "https://sv.sv-2.test.global.canton.network.digitalasset.com" \
  -o "" \
  -p "YOUR_ORIGINAL_PARTY_HINT" \
  -m "1" \
  -i "/path/to/identities-dump.json" \
  -P "a-new-participant-id-never-used-before" \
  -w
```

- **Keep the original party hint.** Changing it creates a different party and
  recovers nothing.
- **Pass `-o ""`.** If the node demands a new onboarding secret, the
  configuration is wrong — fix the configuration instead of asking the sponsor.
  (The exception is a network reset, where a fresh secret genuinely is
  required.)
- **`-P` must never have been used before**, and every later restart must pass
  the same value.

## Rehearse it — TestNet is where you are supposed to

The next reset is a scheduled outage you know about in advance. Use it:

1. Before the reset, take a dump pair and an identities backup.
2. Restore them onto a throwaway host and confirm the participant reaches
   healthy with sync lag under 60 s.
3. Time it. That number is your real MainNet RTO.
4. Then perform the reset for real and confirm the fresh identities backup
   lands off-host.

A backup that has never been restored is a hypothesis. TestNet is the cheapest
place to turn it into a fact.

## Verification checklist

- both dumps exist for the last cycle, validator timestamp earlier than
  participant timestamp
- newest remote copy under 4 hours old
- identities backup exists, was taken **after** the most recent reset, verified
  with `jq`, stored off-host at mode 0600
- `sv.migration_id` from `/info` matches the recorded value
- backup failure produces an alert — tested by breaking it on purpose once

## Related

- **Security Hardening** — how to store what you just backed up
- **Monitoring** — the migration-ID and version-drift alerts that catch a reset
- **TestNet Installation Guide** — the start.sh flags used above

---

**POSTHUMAN validators** — https://posthuman.digital
