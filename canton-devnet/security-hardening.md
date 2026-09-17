# Canton Network DevNet — Validator Security Hardening

DevNet coin is worthless, so the usual reasoning is that hardening does not
matter. That reasoning is what makes DevNet hosts the weakest link in most
operators' estates. Three DevNet-specific risks, before the general rules:

- **DevNet boxes are shared.** They are the host everyone parks a second node,
  an indexer, a bridge or a test service on. POSTHUMAN's DevNet Canton
  validator shares a host with several unrelated services. Every extra service
  is extra blast radius for the whole box, and a Canton validator with a wallet
  UI is on it.
- **DevNet is where credentials get reused.** An SSH key, a wallet password, an
  alert token or a backup destination shared with MainNet turns a throwaway
  host into a path to production.
- **DevNet nodes get forgotten.** POSTHUMAN's own sat `Up 7 weeks (unhealthy)`
  on a version three releases behind the network. An unmaintained node is an
  unpatched node.

## Network exposure

Canton's own requirement: a validator has **no external ingress requirements**
and does not need to whitelist any SVs or validators inbound. It needs egress
on 443 to the Super Validators, which is usually already allowed.

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp                          # restrict to your admin CIDR
ufw insert 1 allow out to 172.19.0.0/16   # Docker internal, if needed
ufw enable
ufw status verbose
```

On a shared DevNet host, audit what else is listening before you assume the
Canton stack is the only thing exposed:

```bash
ss -tlnp | grep -v '127.0.0.1'
docker ps --format '{{.Names}}\t{{.Ports}}'
nmap -Pn -p- your.devnet.ip        # from another host
```

Every non-loopback listener needs a justification, including the ones that
belong to other projects on the same box.

### Docker publishes past ufw

`docker run -p` writes to the `DOCKER-USER` chain and bypasses ufw's INPUT
rules, so a published port is reachable from the internet even with ufw set to
deny. This bites hardest on shared hosts, where a neighbouring service was
started with `-p` by someone who assumed the firewall covered it. The Splice
bundle binds nginx to `127.0.0.1:8888` — keep the bind address if you patch the
compose file.

## Wallet and ANS UI

Even on DevNet, treat the Wallet UI as a wallet console, so the habit survives
the promotion to MainNet.

- nginx binds `127.0.0.1:8888` only
- reach it over an SSH tunnel:

  ```bash
  ssh -L 8888:127.0.0.1:8888 user@your-server -N
  ```

  with `127.0.0.1 wallet.localhost ans.localhost` in your **local**
  `/etc/hosts`, then open `http://wallet.localhost:8888`
- keep HTTP basic auth on, with a password not used anywhere else:

  ```bash
  apt install -y apache2-utils
  cd ~/.canton/<version>/splice-node/docker-compose/validator/nginx
  htpasswd -c .htpasswd YOUR_USERNAME
  chmod 600 .htpasswd
  ```

### Unsafe auth mode

`compose-disable-auth.yaml` removes authentication from the validator API. It
is near-universal on DevNet because it makes scripting easy, and it is safe
**only** because the port is loopback-bound. Unsafe auth plus an exposed 8888
hands the wallet to anyone. If you enable it, re-verify the bind address
afterwards — on a shared host, verify it again after any neighbouring service
is redeployed.

It also requires valid placeholder URLs or the Wallet UI crashes on a Zod
validation error:

```bash
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
```

## Container and volume hygiene

Two real DevNet failures worth designing against, both from POSTHUMAN
operations:

- **Postgres volume ownership.** A data volume owned by the host user while the
  `postgres:14` container runs as UID/GID `999:999` produces `Permission
  denied` on `pg_control`, `pg_wal` and `pg_stat_tmp`, and an exit code 139.
  Check the volume owner against the container user before blaming the image.
- **Non-root image UIDs.** The `canton-participant` and `validator-app` images
  run as `nonroot` UID `1001` while their writable `/app` files are owned by
  UID `1004`; the participant then fails on a repeatable-migration SQL file.
  The fix is an explicit `user:` in the compose file, recorded as a
  timestamped backup before the edit.

Also note that `postgres-splice`, `wallet-web-ui` and `ans-web-ui` ship with
restart policy `no` in some bundles. After a host reboot they stay exited and
the participant loops. Start them explicitly, wait for Postgres and participant
health, then restart the validator once.

## SSH and host hardening

- key-based authentication only — `PasswordAuthentication no`,
  `PermitRootLogin no`
- restrict SSH to an admin CIDR or a VPN
- `fail2ban` on the SSH jail
- unattended security updates
- a dedicated non-root user owning the Canton deployment
- **separate keys from MainNet.** A DevNet host should not be able to reach a
  MainNet host, and a MainNet backup destination should not accept a DevNet key

```bash
chmod 700 ~/.canton
chmod 600 ~/.canton/toolkit.conf
```

## Secrets handling

- never paste a secret into a shell command — it lands in `~/.bash_history`
  and in `ps` output while it runs
- never commit `.env`, `toolkit.conf` or `.htpasswd`
- `.env` at mode 600, owned by the node user
- rotate anything that has been in a chat message, ticket or screenshot
- use distinct alert channels for DevNet, so a token leak on a shared box
  cannot spoof or silence MainNet alerts

```bash
grep -rIl --exclude-dir=.git -E 'ONBOARDING_SECRET|POSTGRES_PASSWORD|BOT_TOKEN' ~ 2>/dev/null
ls -l ~/.canton/*/splice-node/docker-compose/validator/.env
```

On DevNet the onboarding secret is self-service — you can obtain one from the
network endpoint rather than from a sponsor. That convenience is exactly why it
ends up pasted into shell history; put it in the file instead.

## Duplicate identity after a migration

If you move a DevNet validator between hosts, the old host must be fenced:
containers stopped and the cron entries that would restart them disabled.
POSTHUMAN migrated a DevNet validator in August 2026 and had to explicitly keep
the source host's containers and cron disabled to prevent a duplicate identity.
Canton does not slash for it, but two nodes claiming one party is a state you
will spend a day untangling.

## Upgrades and network resets

- pull images only from
  `ghcr.io/digital-asset/decentralized-canton-sync/docker/*` and bundles only
  from the `digital-asset/decentralized-canton-sync` releases
- pre-pull images while the old node runs, then stop and start
- never downgrade — a migrated participant schema cannot be rolled back
- a **migration ID change means a network reset**: full redeployment, all data
  deleted, fresh onboarding secret, new identities backup. It is not an
  upgrade and must not be treated as one

Resets happen roughly every three months on DevNet and are announced in the
Global Synchronizer Foundation's `#validator-operations` channel.

## Verification checklist

- `ufw status verbose` shows deny-incoming with SSH as the only allowance
- `ss -tlnp` shows no non-loopback listener other than SSH — including services
  that belong to other projects on the same host
- an external port scan finds only SSH
- `.env`, `toolkit.conf`, `.htpasswd` are mode 600
- `PasswordAuthentication no`, verified with `sshd -T`
- no credential, key or alert channel is shared with a MainNet host
- the node's running image matches `/info`, so it is actually patched

## Related

- **Backup & Recovery** — resets, identities, and what actually survives
- **Monitoring** — alerting on the signals above
- **DevNet Installation Guide** — onboarding and first start

---

**POSTHUMAN validators** — https://posthuman.digital
