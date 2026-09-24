# GenLayer — Security Hardening

GenLayer's threat model is not a validator's usual one. There is no consensus key
to double-sign with, and the two things most likely to cost you something are an
LLM provider key with a bill attached and a WebDriver port that should never have
been reachable.

Take those two seriously and the rest is ordinary Docker hygiene.

Verified against the reviewed [installation guide](install-guide.md) and
[troubleshooting](troubleshooting.md) for the Asimov testnet.

---

## 1. The LLM provider key is the expensive secret

The node cannot execute Intelligent Contracts without at least one LLM provider
API key, and that key sits in the environment file the compose stack reads. It is
not a signing key — a leak does not let anyone act as your validator — but it is
metered spend, and a leaked key is someone else's inference paid for by you until
you notice.

```bash
chmod 600 .env
chown "$USER":"$USER" .env
```

- **Never commit the env file.** Add it to `.gitignore` before the first commit,
  not after. A key that reached a repository is burned even if the commit is
  removed.
- **Scope the key at the provider.** Use a key created for this node, with a
  spend cap if the provider offers one, and no other permissions.
- **Rotate the key, not the node.** Recovering from a leak means revoking at the
  provider and restarting the stack with a new value. Nothing on the node needs
  rebuilding.
- **Keep it out of the process table.** Read it from the env file, as the
  installation guide does. A key passed on a command line lands in shell history
  and in `ps` output for every user on the host.
- **Watch the spend.** A provider balance alert is a security control here, not
  an accounting one: unexpected spend is the first symptom of a leaked key.

If you run a validator rather than a full node, the operator wallet address is
configuration and the wallet itself belongs somewhere else entirely — not on the
node, and not in the same env file.

---

## 2. Three ports, and only one is ever public

| Port | Service | Exposure |
|---|---|---|
| `9151` | JSON-RPC | public **only** if you deliberately serve public RPC |
| `9153` | ops / health | loopback only |
| `4444` | WebDriver | loopback only — never public |

The installation guide's own recommendation is exactly this: keep `9153` private
and do not expose `4444`.

**The WebDriver port is the one to be careful about.** It drives a browser on
your host. Reachable from the internet, it is remote code execution wearing a
test-automation hat — not a data leak, a foothold. There is no configuration that
makes a public WebDriver acceptable.

```bash
sudo ufw deny 4444/tcp
sudo ufw deny 9153/tcp
# only if you intend to serve public RPC:
sudo ufw allow 9151/tcp comment 'GenLayer JSON-RPC'
sudo ufw status
```

### Docker publishes past the firewall

This matters more here than the rules do. A compose file with

```yaml
ports:
  - "4444:4444"
```

publishes on **all interfaces** and inserts its own DNAT rules ahead of `ufw`, so
a `ufw deny` can be green while the port is wide open. Bind loopback explicitly
in the compose file instead of relying on the firewall:

```yaml
ports:
  - "127.0.0.1:4444:4444"
  - "127.0.0.1:9153:9153"
  - "9151:9151"        # only when public RPC is intended
```

Then verify listeners rather than rules — this is the only check that tells the
truth:

```bash
sudo ss -lntp | grep -E ':(9151|9153|4444|9155)'
```

Anything bound to `0.0.0.0` that you did not mean to publish is the finding.

If you need the ops endpoint or the WebDriver from your workstation, use an SSH
local-forward:

```bash
ssh -N -L 9153:127.0.0.1:9153 <user>@<node-host>
```

---

## 3. Outbound egress must work

Unusually for a node guide, the advice here is *not* to lock egress down
blindly. The node needs outbound HTTPS to the LLM provider and to the upstream
Asimov RPC. A default-deny egress policy applied without those exceptions
produces a node that starts, passes `/health`, and executes nothing — which
presents as a stalled chain, not as a firewall problem.

If you do restrict egress, allow the provider endpoint and
`rpc-asimov.genlayer.com` explicitly, and record why in the same place you record
the rules.

---

## 4. Docker hygiene

- **Pin the image.** Use an exact tag or, better, a digest. `latest` means the
  node changes under you at the next recreate, which is both a reliability and a
  supply-chain problem.
- **Run the stack as a non-root user** where the image supports it, and never add
  the node's user to the `docker` group on a shared host — membership of that
  group is equivalent to root.
- **Do not mount the Docker socket** into any container in this stack. Nothing in
  the documented setup needs it.
- **Keep the data directory outside the image** and back up nothing else: the
  database is reproducible by resync, so there is no backup obligation here, only
  a resync cost.
- Prefer `docker compose pull` followed by a deliberate recreate over any
  unattended updater. Read the release notes first; on a testnet a breaking
  release can require the documented clean-and-resync.

---

## 5. Host baseline

- key-only SSH, no password authentication, no root login
- `fail2ban` or equivalent on the SSH port
- unattended security updates
- no other unauthenticated service on the box — in particular no exposed
  metrics, no remote desktop, no second WebDriver from an unrelated project

---

## 6. What Asimov being a testnet does and does not excuse

The Asimov testnet carries no economic value, so a lost database or a recreated
stack costs time only. Two habits still transfer and are worth keeping now:

- the provider key discipline, because on any paid network that key is real money
  from the first day, and
- the port discipline, because the WebDriver risk is identical on a testnet host
  — an attacker who lands on your test box is on your network either way.

Everything else a testnet is for — throwaway hosts, aggressive upgrades, deleting
`data/node` to reproduce a bug — is fine.
