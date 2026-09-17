# NEAR Validator Security

Scope: the host, the network surface and the operational habits. Key custody is
covered separately in the **Keys & custody** guide.

## Threat model in one paragraph

NEAR has no Cosmos-style double-sign slashing, so the classic "two nodes, one
key, instant slash" catastrophe does not apply. What does apply: an exposed RPC
port on a validator is a denial-of-service and resource-exhaustion surface; a
compromised owner account is total loss; and any outage during your assigned
chunk production costs endorsements and therefore rewards immediately. Secure
for availability and for account compromise, in that order.

## Network surface

| Port | Purpose | Validator | RPC node |
|------|---------|-----------|----------|
| `24567/tcp` | P2P | must be reachable | must be reachable |
| `3030/tcp` | JSON-RPC **and** Prometheus `/metrics` | loopback or private interface | public, behind a reverse proxy |

`3030` serves both RPC and metrics from the same listener. There is no separate
metrics port to expose selectively. On a validator, bind it to loopback:

```json
// ~/.near/config.json
"rpc": {
  "addr": "127.0.0.1:3030"
}
```

```bash
sudo systemctl restart neard
ss -tlnp | grep 3030          # must show 127.0.0.1:3030, not 0.0.0.0:3030
```

If a validator's `3030` is deliberately published — for example because a
monitoring stack scrapes it across hosts — record that decision, restrict it
by source address, and do not describe it afterwards as loopback-only.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     comment 'ssh'
sudo ufw allow 24567/tcp  comment 'NEAR P2P'
sudo ufw allow from <monitoring-host-ip> to any port 3030 proto tcp comment 'NEAR metrics scrape'
sudo ufw enable
sudo ufw status numbered
```

Serve public RPC from a separate host built with the `rpc` config profile,
behind TLS and rate limiting. A validator that also answers public RPC is one
traffic spike away from missing chunks.

## Host hardening

```bash
# SSH: keys only, no root login
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload ssh

sudo apt install -y fail2ban unattended-upgrades
sudo systemctl enable --now fail2ban
```

Run `neard` as a dedicated unprivileged user, never root. Harden the unit:

```ini
[Service]
User=near
Group=near
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=/home/near/.near
```

Verify after editing: `systemd-analyze security neard`.

## Availability is a security property

On NEAR the cheapest way to lose money is to be offline during your assigned
chunks. Two specific failure modes we have seen in production:

- **OOM kill under memory pressure.** `neard` spikes during state transitions.
  Keep 8 GiB of headroom above steady state, or configure swap, and alert on
  available memory — not only on the process being up.
- **Disk exhaustion.** Check *every* mount, not just `/`:

  ```bash
  df -h | grep -v 'tmpfs\|udev\|loop'
  ```

Set `Restart=on-failure` with a `RestartSec` long enough that a crash loop is
visible in monitoring rather than hidden by instant restarts.

## Upgrade discipline

- Track [nearcore releases](https://github.com/near/nearcore/releases) and the
  NEAR validator announcement channels. A protocol upgrade that you miss stops
  your node at the switch height.
- Build and test the new binary on a non-validator host first.
- Keep the previous binary on disk so a rollback is a `systemctl` restart, not
  a 25-minute rebuild.

## Backups

- **Keys** — encrypted, off-host, checksum-verified. See **Keys & custody**.
- **`config.json`** — version it; a lost custom config is hours of rediscovery.
- **`data/`** — disposable. Re-sync it rather than restoring a stale copy.
  If you do copy a chain database between hosts with `rsync`, the final pass
  must use `--checksum`: `neard` uses an LSM-tree store, and size+mtime alone
  will silently miss changed SST files.

## Incident checklist

Before touching anything, capture evidence:

```bash
systemctl status neard --no-pager
journalctl -u neard -n 500 --no-pager > /tmp/neard-incident-$(date -u +%Y%m%dT%H%M%SZ).log
curl -s -X POST http://127.0.0.1:3030 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"status","params":[]}' | jq .result.sync_info
free -h; df -h | grep -v 'tmpfs\|udev\|loop'
```

Then confirm against external truth — a public RPC and
[nearblocks.io](https://nearblocks.io/node-explorer) — before concluding that
the network, rather than your node, is the problem. A low-endorsement alert is
often retrospective: the cumulative epoch ratio stays below threshold for hours
after the node itself has fully recovered. Check whether *fresh* expected
endorsements are being produced before restarting anything.

## Related guides

- **Keys & custody** — the four NEAR secrets and how to scope them
- **Monitoring** — what to alert on, and what not to alert on
- **Installation guide** — config profiles and firewall basics
