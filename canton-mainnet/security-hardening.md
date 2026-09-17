# Canton Network MainNet — Validator Security Hardening

Canton has no slashing. That removes one class of risk and replaces it with a
worse one: the value sits in the participant's private keys, and losing them
loses the Canton Coin balance and the CNS entries permanently. There is no
validator set to rejoin and no unbonding period to survive — either you hold
the namespace key or you do not.

Read this alongside the Backup & Recovery tab. On Canton the two are the same
subject viewed from opposite ends.

## Threat model in one table

| Asset | Where it lives | Loss means |
|---|---|---|
| Participant namespace key | participant Postgres DB, or an external KMS | permanent loss of party identity, CC balance, CNS entries |
| Identities backup file | wherever you put it | the same key in plain form — treat it as the key itself |
| Wallet UI session | nginx on `127.0.0.1:8888` | ability to move CC out of the validator |
| Onboarding secret | `.env`, shell history, chat with the SV sponsor | one-shot; only useful before onboarding, 48 h validity |
| Alert channel tokens | `~/.canton/toolkit.conf` | spoofed alerts, silenced alerts |
| Postgres credentials | `.env` | full node state |

Note the absence of a "consensus key that must never double-sign". That Cosmos
reflex does not apply here. The rule that replaces it: **the namespace key must
never be lost, and must never leave a location you control.**

## Network exposure

Canton's own requirement is short and worth quoting in full: a validator has
**no external ingress requirements** and does not need to whitelist any other
SVs or validators. Egress on port 443 to all Super Validators is what the node
actually needs, and that is usually already allowed.

So the correct MainNet firewall admits nothing from the internet except your
own administrative SSH:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp                         # restrict further to your admin CIDR
ufw enable
ufw status verbose
```

If you need the Docker bridge reachable for local tooling, allow it explicitly
rather than widening the public policy:

```bash
ufw insert 1 allow out to 172.19.0.0/16
```

Verify from outside the host that nothing else answers:

```bash
nmap -Pn -p- your.validator.ip
```

Anything open beyond SSH on a Canton validator is a misconfiguration, not a
feature.

> The MainNet IP whitelist is the reverse direction and is often confused with
> ingress. Super Validators whitelist **your** IP so that your node may read
> their Scan and SV endpoints. It grants you outbound access; it does not open
> anything inbound on your host.

### Docker publishes past ufw

`docker run -p` writes to the `DOCKER-USER` chain and bypasses ufw's INPUT
rules. A container published with `-p 8888:8888` is reachable from the internet
even with ufw set to deny. The Splice bundle binds nginx to `127.0.0.1:8888`
for exactly this reason. If you patch the compose file, keep the bind address.

Check what is actually published, not what you intended to publish:

```bash
docker ps --format '{{.Names}}\t{{.Ports}}'
ss -tlnp | grep -v '127.0.0.1'
```

Every line in the second command that is not loopback needs a justification.

## Wallet and ANS UI

The Wallet UI can move Canton Coin. Treat it as a hot wallet console.

- nginx binds `127.0.0.1:8888` only. Never rebind it to `0.0.0.0`, and never
  put it behind a plain HTTP reverse proxy on a public port.
- Access over an SSH tunnel:

  ```bash
  ssh -L 8888:127.0.0.1:8888 user@your-server -N
  ```

  with `127.0.0.1 wallet.localhost ans.localhost` in your **local** `/etc/hosts`,
  then open `http://wallet.localhost:8888`.
- Keep HTTP basic auth on. Create it properly and never reuse a password from
  elsewhere:

  ```bash
  apt install -y apache2-utils
  cd ~/.canton/<version>/splice-node/docker-compose/validator/nginx
  htpasswd -c .htpasswd YOUR_USERNAME
  chmod 600 .htpasswd
  ```
- If you need remote access without a tunnel, use a Cloudflare Tunnel or a
  Tailscale address. Both avoid opening a port. A Cloudflare Tunnel also gives
  you TLS and an access policy in front of the basic auth.

### Unsafe auth mode

`compose-disable-auth.yaml` removes authentication from the validator API. It
exists for local scripting and monitoring, and it is safe **only** because the
port is loopback-bound. Running unsafe auth and exposing 8888 at the same time
hands the wallet to the internet. If you enable it, re-verify the bind address
afterwards.

## SSH and host hardening

Nothing Canton-specific here, but the node is only as safe as the host:

- key-based authentication only — `PasswordAuthentication no`,
  `PermitRootLogin no`, `KbdInteractiveAuthentication no`
- restrict SSH to an admin CIDR or put it behind a VPN
- `fail2ban` on the SSH jail
- unattended security updates for the base OS
- a dedicated non-root user owning the Canton deployment; do not run the node
  as root
- full-disk encryption if the host is not in a facility you control — the
  participant database contains private keys at rest

Audit the account that owns the node:

```bash
id
sudo -l
ls -la ~/.canton
```

The deployment directory and `~/.canton/toolkit.conf` should not be
world-readable:

```bash
chmod 700 ~/.canton
chmod 600 ~/.canton/toolkit.conf
```

## Secrets handling

Secrets that end up on a Canton validator: the onboarding secret, the Postgres
password, the wallet basic-auth password, alert channel tokens, backup
destination credentials (SSH key or R2 keys), and the identities backup.

Rules that actually prevent the common incidents:

- Never paste a secret into a shell command. It lands in `~/.bash_history`,
  in `ps` output while it runs, and in any screen recording. Put it in the file
  and reference the file.
- Never commit `.env`, `toolkit.conf` or `.htpasswd` to a repository, including
  a private one.
- Keep `.env` at mode 600, owned by the node user.
- Rotate anything that has ever been in a chat message, a ticket or a
  screenshot. The onboarding secret expires in 48 hours anyway; the Postgres
  password and alert tokens do not.
- Store the identities backup in a secret manager, not next to the database
  dumps.

A quick check for leaked material on the host:

```bash
grep -rIl --exclude-dir=.git -E 'ONBOARDING_SECRET|POSTGRES_PASSWORD|BOT_TOKEN' ~ 2>/dev/null
ls -l ~/.canton/*/splice-node/docker-compose/validator/.env
```

## Key custody and KMS

By default the participant generates its keys itself and stores them in its own
Postgres database. That is acceptable only if the database backup and the
identities backup are both protected to the standard of the key itself, because
they contain it.

For a stronger posture, Splice participants support Canton's **External Key
Storage** mode against an external KMS (GCP KMS and AWS KMS drivers require a
Canton Enterprise licence). Two constraints decide whether you can use it:

- KMS is supported on the **Helm/Kubernetes** deployment only. Docker Compose
  deployments cannot use it today.
- You cannot migrate an existing participant to a KMS, or between KMS
  providers. The namespace root key cannot be rotated, and importing it into a
  KMS would give away the benefit. The supported path is: stand up a fresh
  KMS-backed validator, transfer assets to it, retire the old one.

So the KMS decision is made once, before onboarding. If you are on Compose and
want KMS later, plan a full re-onboarding, not a config change.

Session keys are a related detail: Splice participants use one-hour session
encryption keys by default, so an adversary with a memory snapshot could
decrypt up to one hour of traffic. Tune
`canton.participants.participant.crypto.session-signing-keys` only with the
Canton documentation in front of you.

## Upgrade and supply-chain safety

- Pull images only from
  `ghcr.io/digital-asset/decentralized-canton-sync/docker/*` and bundles only
  from the `digital-asset/decentralized-canton-sync` GitHub releases. Verify the
  tag you downloaded matches the version you intended.
- Back up before every upgrade, without exception. The upgrade path is
  irreversible once the participant has migrated its schema.
- Pre-pull images while the old node is still running, then stop and start —
  this keeps downtime to seconds instead of minutes.
- Never downgrade. A participant that has migrated forward cannot be rolled
  back onto an older schema; your rollback path is the backup, not the previous
  directory.
- Read the release notes for a migration ID change. A migration ID bump is a
  network-level event, not a routine version bump.

## Monitoring is a security control

Two alerts in the Monitoring tab are security-relevant, not just operational:

- a sudden drop in `splice_wallet_unlocked_amulet_balance` that you did not
  initiate is a wallet compromise signal
- a validator that goes unhealthy right after an SSH login you did not make
  needs an access review before a restart

Ship node and Docker logs off the host so an attacker who gets root cannot
erase the evidence.

## Incident checklist

If you suspect compromise:

1. Do not wipe anything. Snapshot the host and preserve logs first.
2. Revoke SSH access and rotate every credential on the host.
3. Move the CC balance only from a trusted path, and only after confirming the
   wallet UI was not the entry point.
4. Confirm you hold a current identities backup **off** the host before any
   destructive step.
5. Rebuild on new infrastructure and re-onboard from the identities backup
   rather than restoring a possibly-tampered database.

## Verification checklist

- `ufw status verbose` shows deny-incoming with SSH as the only allowance
- `ss -tlnp` shows no non-loopback listener other than SSH
- an external port scan finds only SSH
- `.env`, `toolkit.conf`, `.htpasswd` are mode 600
- `PasswordAuthentication no` in `sshd_config`, verified with `sshd -T`
- an identities backup exists, is under 30 days old, and is stored off-host in
  a secret manager
- a restore has been rehearsed at least once on a throwaway host

## Related

- **Backup & Recovery** — the procedures this guide's key-custody rules protect
- **Monitoring** — alerting on the signals above
- **MainNet Installation Guide** — onboarding, whitelisting, first start

---

**POSTHUMAN validators** — https://posthuman.digital
