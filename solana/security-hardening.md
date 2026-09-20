# Solana Validator Security Hardening

Solana has no slashing today, so the threat model is not "sign the wrong thing".
It is: **key theft**, **host compromise**, and **silent loss of the vote
account**. Everything below is ordered by what it actually prevents.

## 1. Key custody — the part that is irreversible

| Key | Rule |
|---|---|
| Authorized withdrawer | never on the validator, never in a repo, never in chat. Hardware wallet, paper, or multisig. |
| Validator identity | hot by necessity, `chmod 600`, owned by the service user, backed up offline and restore-tested |
| Vote account keypair | not secret after creation, but keep it `600` anyway |
| Spare (unstaked) identity | on the host, used for every safe restart and cutover |

The withdrawer can change the identity, the commission and the withdraw
authority, and can drain the vote account. Losing it is unrecoverable; leaking
it is total loss. Nothing else on this page matters as much.

Use the `-checked` authority commands so authority can never be handed to a key
you do not hold:

````bash
solana vote-authorize-voter-checked <vote-account> <current> <new-keypair>
solana vote-authorize-withdrawer-checked <vote-account> <current> <new-keypair>
````

Keep the identity balance small — weeks of vote fees, not years — and top it up
from cold storage.

## 2. Never run two voting processes on one identity

Solana has no slashing, but duplicate block and vote production is detected and
punished socially and economically: forks, dropped stake, delegation-program
removal. Treat it as a hard rule.

The safe cutover always goes through the unstaked spare identity and the tower
file:

````bash
# on the node giving up the identity
agave-validator --ledger /mnt/ledger set-identity /home/sol/unstaked-identity.json

# copy the tower to the receiving node, then
agave-validator --ledger /mnt/ledger set-identity --require-tower /home/sol/validator-keypair.json
````

`--require-tower` refusing to proceed is the protection working. Do not bypass
it under time pressure — an uptime gap is cheap; two nodes voting on one
identity is not.

## 3. Host hardening

Run the validator as a dedicated non-root user:

````bash
sudo adduser --disabled-password --gecos "" sol
````

The systemd unit runs as that user. Nothing about a validator needs root at
runtime.

SSH:

````
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowUsers sol admin
````

````bash
sudo systemctl reload ssh
sudo apt -y install fail2ban && sudo systemctl enable --now fail2ban
````

Restrict SSH to a static management address at the firewall, not only in
`sshd_config`. Keep the system patched — weekly `apt update && apt upgrade` at
minimum, and enable unattended security updates.

## 4. Firewall

Solana needs its dynamic port range reachable from anywhere; everything else
should be closed.

````bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-management-ip> to any port 22 proto tcp
sudo ufw allow 8000:8050/tcp
sudo ufw allow 8000:8050/udp
sudo ufw enable
sudo ufw status numbered
````

Pin the range with `--dynamic-port-range 8000-8050` so the firewall rule and the
process agree. Without it the validator picks ports in 8000–10000 and your rule
is a guess.

**Do not expose RPC.** On a staked mainnet validator, ports 8899 and 8900 should
not be reachable from the internet:

- `--private-rpc` restricts what the RPC will answer;
- `--rpc-bind-address 127.0.0.1` keeps it off the public interface;
- the firewall is what actually enforces it.

An open RPC on a voting validator is both a DoS surface and free compute for
strangers. If you need public RPC, run a separate RPC node.

Outbound traffic from the validator must **not** be filtered. Solana's gossip,
turbine and repair paths talk to the whole cluster; egress ACLs break consensus
participation in ways that are hard to diagnose.

## 5. Do not run behind NAT

Upstream Agave does not support it and will not accept patches for it. A
validator needs a stable public IPv4 address. If you are behind NAT you are
debugging traversal problems alone, during incidents.

## 6. Service isolation

````ini
[Service]
User=sol
LimitNOFILE=1000000
LimitMEMLOCK=2000000000
LogRateLimitIntervalSec=0
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=true
ReadWritePaths=/mnt/ledger /mnt/accounts /home/sol
````

Add the hardening directives incrementally and verify with
`systemd-analyze verify` and a real restart — an over-tight `ProtectSystem` that
blocks the accounts path fails at bank load, not at start.

## 7. Supply chain

You are installing a binary that will hold a hot key and a large stake
relationship.

- install from the official release channel or build from a **signed tag**;
- record the release tag, the resolved commit, and the SHA-256 of the binary you
  actually deployed;
- verify the downloaded archive against the digest published with the release,
  and verify the running binary afterwards:

````bash
sha256sum "$(readlink -f "$(command -v agave-validator)")"
agave-validator --version
````

Keep the previous release directory in place so rollback is a symlink change,
not a download. Never install a client build from an unattributed link, a chat
message, or a mirror you cannot tie to the upstream project.

## 8. Backups worth having

- identity keypair, restore-tested against its pubkey;
- the validator startup script and systemd unit;
- `sysctl`, `limits`, firewall and logrotate configuration;
- a written record of: identity pubkey, vote account pubkey, BLS public key,
  commission, who holds the withdrawer and how to reach them.

Do **not** back up the ledger or the accounts database. They are disposable and
rebuilt from a snapshot; treating them as precious is what leads to restoring
stale state onto a running validator.

## 9. Operational rules that prevent most incidents

- change one thing at a time, and verify against an external RPC after each;
- keep a rollback for every change before you make it;
- never free disk space by deleting the ledger, accounts, tower or keys;
- never restart "just to see"; a restart is a snapshot load with a real cost;
- record what you deployed — version, commit, hash, time — so an incident starts
  from facts rather than from memory.

## Review checklist

- [ ] withdrawer offline, custody documented, second person can reach it
- [ ] identity `600`, backup restore-tested
- [ ] unstaked spare identity present
- [ ] validator runs as non-root
- [ ] SSH: keys only, no root, restricted source, fail2ban on
- [ ] UFW default-deny, only SSH + the pinned dynamic port range open
- [ ] RPC not reachable from the internet
- [ ] no egress filtering
- [ ] public IPv4, no NAT
- [ ] binary provenance recorded (tag, commit, SHA-256)
- [ ] previous release retained for rollback
- [ ] monitoring runs on a different host
- [ ] vote account and identity balance alerts configured

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
