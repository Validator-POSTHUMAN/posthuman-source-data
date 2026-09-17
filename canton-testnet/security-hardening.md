# Canton Network TestNet — Validator Security Hardening

TestNet carries no real value, which is exactly why it is dangerous: it is
where operators practise the habits they will later apply to MainNet. Harden it
to the same standard, and it becomes a rehearsal instead of a liability.

Two TestNet-specific risks are worth stating before the general rules:

- **TestNet hosts are the usual source of credential reuse.** An SSH key, a
  wallet password, an alert token or a backup destination shared with MainNet
  turns a throwaway host into a path to production.
- **A TestNet host is a real internet host.** It gets scanned, brute-forced and
  mined on like any other. "It is only testnet" is not a firewall.

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

Verify from outside the host:

```bash
nmap -Pn -p- your.validator.ip
```

Anything open beyond SSH is a misconfiguration.

> The TestNet IP whitelist is the opposite direction and is often confused with
> ingress. Super Validators whitelist **your** IP so your node may read their
> Scan and SV endpoints. It grants outbound access; it opens nothing inbound.

### Docker publishes past ufw

`docker run -p` writes to the `DOCKER-USER` chain and bypasses ufw's INPUT
rules. A container published with `-p 8888:8888` is reachable from the internet
even with ufw set to deny. The Splice bundle binds nginx to `127.0.0.1:8888`
for this reason — keep the bind address if you patch the compose file.

```bash
ss -tlnp | grep -v '127.0.0.1'
docker ps --format '{{.Names}}\t{{.Ports}}'
```

Every non-loopback listener needs a justification.

## Wallet and ANS UI

The Wallet UI moves Canton Coin. Even on TestNet, treat it as a wallet console
so the habit survives the promotion to MainNet.

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
is common on TestNet because it makes scripting easy, and it is safe **only**
because the port is loopback-bound. Unsafe auth plus an exposed 8888 hands the
wallet to the internet. If you enable it, re-verify the bind address
afterwards — this is the single most likely TestNet mistake.

It also requires valid placeholder URLs or the Wallet UI crashes on a Zod
validation error:

```bash
AUTH_URL=https://unsafe.auth
SPLICE_APP_UI_NETWORK_FAVICON_URL=https://www.canton.network/hubfs/cn-favicon-05%201-1.png
SPLICE_APP_UI_NETWORK_NAME="Canton Network"
```

## Key custody

The participant namespace key proves ownership of the party and its balance.
On TestNet the balance is not valuable, but the procedure is — and identities
**change on every network reset**, so a backup taken before a reset is not a
backup of the current node.

- take a fresh identities backup after every reset and after any identity
  change
- store it at mode `0600` and off-host
- never reuse a TestNet identities file, party hint or participant ID on
  MainNet

KMS is worth knowing about here even though you will not use it on TestNet: it
is Kubernetes-only, cannot be migrated onto an existing participant, and
therefore has to be decided before a MainNet node is first onboarded. Rehearsal
on TestNet is when you find that out cheaply.

## SSH and host hardening

- key-based authentication only — `PasswordAuthentication no`,
  `PermitRootLogin no`
- restrict SSH to an admin CIDR or a VPN
- `fail2ban` on the SSH jail
- unattended security updates
- a dedicated non-root user owning the Canton deployment
- **separate keys from MainNet.** A TestNet host should not be able to reach a
  MainNet host, and a MainNet backup destination should not accept a TestNet
  key

```bash
chmod 700 ~/.canton
chmod 600 ~/.canton/toolkit.conf
```

## Secrets handling

Secrets on a TestNet validator: onboarding secret, Postgres password, wallet
basic-auth password, alert channel tokens, backup destination credentials.

- never paste a secret into a shell command — it lands in `~/.bash_history`
  and in `ps` output while it runs
- never commit `.env`, `toolkit.conf` or `.htpasswd`, including to a private
  repository
- `.env` at mode 600, owned by the node user
- rotate anything that has been in a chat message, ticket or screenshot
- use distinct alert channels for TestNet, so a TestNet token leak cannot
  spoof or silence MainNet alerts

```bash
grep -rIl --exclude-dir=.git -E 'ONBOARDING_SECRET|POSTGRES_PASSWORD|BOT_TOKEN' ~ 2>/dev/null
ls -l ~/.canton/*/splice-node/docker-compose/validator/.env
```

## Upgrades and network resets

- pull images only from
  `ghcr.io/digital-asset/decentralized-canton-sync/docker/*` and bundles only
  from the `digital-asset/decentralized-canton-sync` releases
- pre-pull images while the old node runs, then stop and start
- never downgrade — a migrated participant schema cannot be rolled back
- a **migration ID change means a network reset**: full redeployment, all data
  deleted, fresh onboarding secret from your SV sponsor, new identities backup.
  It is not an upgrade and must not be treated as one

Resets happen roughly every three months on TestNet and are announced in the
Global Synchronizer Foundation's `#validator-operations` channel.

## Verification checklist

- `ufw status verbose` shows deny-incoming with SSH as the only allowance
- `ss -tlnp` shows no non-loopback listener other than SSH
- an external port scan finds only SSH
- `.env`, `toolkit.conf`, `.htpasswd` are mode 600
- `PasswordAuthentication no`, verified with `sshd -T`
- no credential, key or alert channel is shared with a MainNet host
- an identities backup exists that was taken **after** the most recent reset

## Related

- **Backup & Recovery** — resets, identities, and what actually survives
- **Monitoring** — alerting on the signals above
- **TestNet Installation Guide** — onboarding, whitelisting, first start

---

**POSTHUMAN validators** — https://posthuman.digital
