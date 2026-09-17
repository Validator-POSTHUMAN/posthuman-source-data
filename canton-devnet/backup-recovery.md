# Canton Network DevNet — Backup & Recovery

DevNet data has no value and is deliberately destroyed roughly every three
months. So the honest question is not "how do I protect this data" but "what is
this node for". The answer that makes a DevNet validator worth running: it is
where the MainNet recovery procedure gets rehearsed, on a schedule, for free.

Treat every DevNet reset as a disaster-recovery drill you were given advance
notice of.

## Network resets

DevNet and TestNet are reset roughly every three months, staggered so the two
never reset at the same time. The exact time is announced in the
`#validator-operations` channel run by the
[Global Synchronizer Foundation](https://sync.global/).

A reset requires a **full redeployment** and loses all data on the node. Until
you complete it, the node is not functional — but it keeps running and keeps
looking alive. POSTHUMAN's own DevNet validator demonstrates the end state:

```
running=0.6.14  network=0.8.1
container: Up 7 weeks (unhealthy)
sync lag: 128,225,261 ms
unhealthy background services: UpdateIngestionService, UserWalletAutomationService
retry failures: 122,127
```

Nothing there says "the network was reset". You only learn that by comparing
against `/info`.

```bash
curl -s https://docs.dev.global.canton.network.sync.global/info | jq .
```

Alert on `sv.migration_id` changing. That is the reset notification your
monitoring can actually act on.

### Reset procedure

1. Stop the node and remove **all** state: Docker volumes and databases,
   including any managed Postgres. Helm deployments: uninstall all charts and
   delete all PVCs.
2. Acquire a **fresh onboarding secret**. On DevNet you can do this yourself by
   calling the network endpoint — no sponsor round-trip, which is one more
   reason to rehearse here rather than on TestNet.
3. Redeploy with the migration ID from the announcement, checked against
   `/info`. Both the validator and the participant configuration carry it.
4. **Take a new identities backup.** Identities change as part of the reset, so
   every backup taken before it is now worthless.

Step 4 is the one operators skip, and skipping it on MainNet is unrecoverable.
Practise it here.

### Do not upgrade across a reset

A node that missed a reset cannot be brought back by upgrading the image. It is
on a synchronizer that no longer accepts it. Rebuild it through the procedure
above.

## Backups between resets

Even on DevNet, run the real backup procedure — the point is the rehearsal.

| Backup | Contains | Frequency | Where it goes |
|---|---|---|---|
| Node identities | participant private keys + topology snapshot | after onboarding, after every reset | off-host, mode 0600 |
| Postgres dumps | validator app DB and participant DB | every 4 hours | off-host with short retention |

### 1. Node identities backup

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

TOKEN=$(python3 get-token.py administrator)   # requires pyjwt

curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_devnet_identity_$(date -u +%Y%m%dT%H%M%SZ).json

jq -e '.id and (.keys | length > 0)' ~/canton_devnet_identity_*.json
```

The `jq` check is not optional even here: an error body is still a file, and
discovering that on MainNet is the expensive way to learn it.

### 2. Postgres backups

Validator app **strictly before** participant. The order is a protocol
requirement: a participant dump older than its matching validator dump cannot be
restored as a pair.

```bash
backup_dir=~/canton-backups
mkdir -p "$backup_dir"

docker exec <postgres-container> \
  pg_dump -U cnadmin validator \
  > "$backup_dir/validator-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"

active_participant_db=$(docker exec <participant-container> \
  bash -c 'echo $CANTON_PARTICIPANT_POSTGRES_DB')

docker exec <postgres-container> \
  pg_dump -U cnadmin "$active_participant_db" \
  > "$backup_dir/${active_participant_db}-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"
```

Read the container names rather than assuming: DevNet deployments frequently
use a `splice-devnet-*` project prefix instead of `splice-validator-*`. Read
the participant database name from the container too — it carries the migration
ID and changes on every reset.

### Automating it

```bash
~/canton-validator-toolkit/scripts/backup.sh          # manual run
```

```
BACKUP_TYPE=rsync
REMOTE_HOST=ubuntu@backup.example.com
REMOTE_PATH=~/canton-backups/devnet
RETENTION_DAYS=1
```

Short retention is correct on DevNet: dumps from before the last reset belong
to a network that no longer exists.

Alert on the **upload** step, not only the dump. POSTHUMAN's real DevNet backup
failure was exactly this: local dumps succeeded, the remote sync failed with
`Permission denied (publickey)` after the backup key fell out of the
destination's `authorized_keys`, and the guarded auto-upgrade aborted behind
it. The node looked fine; the backups had stopped leaving the host.

### The 30-day ceiling applies here too

A database backup older than 30 days cannot restore a participant on any Canton
network — sequencer pruning means it can never catch up. On DevNet the reset
usually invalidates a backup long before that limit does.

## Restoring from a database backup

Only meaningful for a backup taken since the last reset.

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

./stop.sh
docker volume ls | grep postgres-splice          # confirm the exact name first
docker volume rm <project>_postgres-splice

docker compose up -d postgres-splice
docker exec <postgres-container> pg_isready      # repeat until ready

docker exec -i <postgres-container> \
  psql -U cnadmin validator < "$validator_dump_file"

docker exec -i <postgres-container> \
  psql -U cnadmin "participant-$migration_id" < "$participant_dump_file"

docker compose down
./start.sh -s "https://sv.sv-2.dev.global.canton.network.digitalasset.com" \
  -o "" -p "YOUR_VALIDATOR_NAME" -m "1" -w
```

Users onboarded after the backup was taken must be re-onboarded by hand.

## Re-onboarding from an identities backup

The MainNet-critical path, rehearsed cheaply:

```bash
./start.sh \
  -s "https://sv.sv-2.dev.global.canton.network.digitalasset.com" \
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
  configuration is wrong — the exception is a network reset, where a fresh
  secret genuinely is required.
- **`-P` must never have been used before**, and every later restart must pass
  the same value.

Run this at least once before you ever need it on MainNet. Time it; that number
is your real MainNet RTO.

## Verification checklist

- `sv.migration_id` from `/info` matches the recorded value, or a reset is in
  progress and the redeployment is tracked
- identities backup exists and was taken **after** the most recent reset,
  verified with `jq`, stored off-host at mode 0600
- both dumps exist for the last cycle, validator timestamp earlier than
  participant timestamp
- newest remote copy is actually off-host — check the destination, not the
  local directory
- the re-onboarding path has been executed at least once and timed

## Related

- **Security Hardening** — duplicate identity, shared hosts, volume ownership
- **Monitoring** — the migration-ID and version-drift alerts that catch a reset
- **DevNet Installation Guide** — the start.sh flags used above

---

**POSTHUMAN validators** — https://posthuman.digital
