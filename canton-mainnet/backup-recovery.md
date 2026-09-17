# Canton Network MainNet — Backup & Recovery

On a Cosmos chain a lost node is an inconvenience: sync from a snapshot, restore
the consensus key, rejoin. On Canton a lost node can be **permanent loss of
assets**. The participant's namespace key is what proves you own the party, the
Canton Coin balance and the CNS entries. There is no way to reconstruct it from
the network.

Recovery of assets is possible only if at least one of these is true:

- a database backup less than 30 days old exists, or
- an up-to-date identities backup exists, or
- the participant used an external KMS and the KMS still holds the keys.

If none holds, the keys are gone and so is everything they prove. Everything
below exists to make sure at least one of them always holds.

## Two backups, not one

| Backup | Contains | Frequency | Where it goes |
|---|---|---|---|
| Node identities | participant private keys + topology snapshot | after onboarding, and after any identity change | secret manager, off-host |
| Postgres dumps | validator app DB and participant DB | every 4 hours | off-host storage with retention |

Take both. The identities backup alone recovers your balance but not your
history; the database backup alone recovers everything but only for 30 days.

### 1. Node identities backup

This file contains the participant's **private keys**. It is exactly as
sensitive as the key material itself and must be stored in a secret manager,
not beside the database dumps.

On a Docker Compose deployment with auth disabled:

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

TOKEN=$(python3 get-token.py administrator)   # requires pyjwt

curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_mainnet_identity_$(date -u +%Y%m%dT%H%M%SZ).json
```

With auth enabled, use a Bearer token from your OAuth provider with claims for
the validator app.

Verify the file is real before trusting it — an empty or error-body JSON is the
classic silent failure:

```bash
jq -e '.id and (.keys | length > 0)' ~/canton_mainnet_identity_*.json
```

Then move it off the host immediately, and remove the local copy:

```bash
chmod 600 ~/canton_mainnet_identity_*.json
# upload to your secret manager, verify the upload, then:
shred -u ~/canton_mainnet_identity_*.json
```

### 2. Postgres backups

Back up **both** databases at least every 4 hours. There is a strict order
requirement, and getting it wrong produces a backup pair that cannot be
restored together:

> The validator app's database backup must be taken at a point in time
> **strictly earlier** than the participant's. Let the validator dump finish
> before starting the participant dump.

```bash
backup_dir=~/canton-backups
mkdir -p "$backup_dir"

# 1. validator app DB — first
docker exec splice-validator-postgres-splice-1 \
  pg_dump -U cnadmin validator \
  > "$backup_dir/validator-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"

# 2. participant DB — strictly after the above completes
active_participant_db=$(docker exec splice-validator-participant-1 \
  bash -c 'echo $CANTON_PARTICIPANT_POSTGRES_DB')

docker exec splice-validator-postgres-splice-1 \
  pg_dump -U cnadmin "$active_participant_db" \
  > "$backup_dir/${active_participant_db}-$(date -u +%Y-%m-%dT%H:%M:%S%:z).dump"
```

The participant database name carries the migration ID — `participant-4` on
MainNet today. Read it from the container rather than hardcoding it; it changes
when the network performs a hard migration.

### Automating it

The POSTHUMAN toolkit runs this every 4 hours, compresses the dumps, ships them
to rsync-over-SSH or Cloudflare R2, prunes both local and remote copies by
`RETENTION_DAYS`, and alerts only on failure and on recovery:

```bash
~/canton-validator-toolkit/scripts/backup.sh          # manual run
```

Configuration lives in `~/.canton/toolkit.conf`:

```
BACKUP_TYPE=rsync            # rsync | r2 | skip
REMOTE_HOST=ubuntu@backup.example.com
REMOTE_PATH=~/canton-backups/mainnet
RETENTION_DAYS=7
```

Whatever you automate, alert on backup **failure**. A backup job that has been
silently failing for a month is indistinguishable from having no backups, and
that is the state in which the 30-day limit below becomes fatal.

### Retention rules that are not optional

- **30 days is a hard ceiling for database backups.** The sequencer prunes its
  history; a participant restored from a backup older than 30 days can never
  catch up on the synchronizer and will not become operational again.
- If you enabled participant pruning but want longer auditability, keep
  historical backups spaced no further apart than the pruning window.
- Keep backups across a logical synchronizer upgrade. A backup taken before an
  LSU is only restorable while the old physical synchronizer is still up.

## Restoring the node from backups

Possible when a database backup exists, it is under 30 days old, and no logical
synchronizer upgrade has happened since it was taken (or the old physical
synchronizer is still running).

```bash
cd ~/.canton/<version>/splice-node/docker-compose/validator

# 1. stop everything
./stop.sh

# 2. wipe the database volume
docker volume rm compose_postgres-splice

# 3. bring up only postgres
docker compose up -d postgres-splice
docker exec splice-validator-postgres-splice-1 pg_isready   # repeat until ready

# 4. restore the validator app DB
docker exec -i splice-validator-postgres-splice-1 \
  psql -U cnadmin validator < "$validator_dump_file"

# 5. restore the participant DB — migration_id must match the current network
docker exec -i splice-validator-postgres-splice-1 \
  psql -U cnadmin "participant-$migration_id" < "$participant_dump_file"

# 6. stop postgres, then start the validator normally
docker compose down
./start.sh -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "" -p "YOUR_VALIDATOR_NAME" -m "4" -w
```

Check the volume name before step 2 — it is derived from the Compose project
name and is `splice-validator_postgres-splice` on a default install:

```bash
docker volume ls | grep postgres-splice
```

Users onboarded after the backup was taken must be re-onboarded by hand. The
restore does not bring them back.

## Recovering from an identities backup (re-onboarding)

Use this when the database is gone, too old, or untrustworthy. A new validator
is stood up holding the original namespace key; the Super Validators supply the
contracts the migrated parties are stakeholders of, which restores the Canton
Coin balance and CNS entries.

```bash
./start.sh \
  -s "https://sv.sv-2.global.canton.network.digitalasset.com" \
  -o "" \
  -p "YOUR_ORIGINAL_PARTY_HINT" \
  -m "4" \
  -i "/path/to/identities-dump.json" \
  -P "a-new-participant-id-never-used-before" \
  -w
```

Three details decide whether this works:

- **Keep the original party hint.** The process preserves party IDs; changing
  the hint creates a different party and recovers nothing.
- **Do not request a new onboarding secret.** Pass `-o ""`. If the node asks
  for one, the configuration is wrong — fix the configuration rather than
  asking the SV sponsor for a fresh secret.
- **`-P` must be a participant identifier never used before**, and every
  subsequent restart must pass the same `-P` value.

After it comes up, log in as administrator and confirm the balance. Other users
hosted on the validator re-onboard themselves; their balances and CNS entries
are recovered.

### No identities backup, only a participant database

An identities backup can be assembled from a participant DB backup: restore the
database into a temporary Postgres, run a temporary participant against it
(only the participant — the validator app is not needed), open a Canton console
and export the keys and the topology snapshot to `identities-dump.json`. If the
restored participant exits immediately, set

```
ADDITIONAL_CONFIG_EXIT_ON_FATAL_FAILURES=canton.parameters.exit-on-fatal-failures = false
```

The exact console commands are in the Splice disaster-recovery documentation.
This is a recovery of last resort; it is far cheaper to take the identities
backup now.

## Logical synchronizer upgrade

If the Global Synchronizer itself breaks, Super Validators roll forward to a new
physical synchronizer. Validators then run the LSU procedure on their own node
using the parameters the SVs publish. This is not a disaster on your side —
watch the SV announcement channels and follow the published steps. The relevant
preparation is the retention rule above: keep backups across the upgrade.

## Rehearse it

A backup that has never been restored is a hypothesis. Once per quarter:

1. Take a fresh dump pair.
2. Restore it onto a throwaway host.
3. Confirm the participant reaches healthy and sync lag drops under 60 s.
4. Record how long it took — that number is your real RTO.

POSTHUMAN keeps MainNet, TestNet and DevNet backups on a separate host, and the
one failure mode seen in practice was not a bad dump but a broken SSH key on
the backup destination: local dumps succeeded, the remote sync failed with
`Permission denied (publickey)`, and the auto-upgrade aborted behind it. Alert
on the upload step, not only on the dump step.

## Verification checklist

- both dumps exist for the last cycle, validator dump timestamp earlier than
  participant dump timestamp
- the newest remote copy is under 4 hours old and under 30 days in retention
- an identities backup exists off-host, verified with `jq`, stored in a secret
  manager
- `docker exec ... pg_isready` succeeds against the restored instance in the
  last rehearsal
- backup failure produces an alert — tested by breaking it on purpose once

## Related

- **Security Hardening** — how to store what you just backed up
- **Monitoring** — alerting on backup failure and node health
- **MainNet Installation Guide** — the start.sh flags used above

---

**POSTHUMAN validators** — https://posthuman.digital
