# Solana Testnet Security Hardening

Testnet SOL is worthless, so the temptation is to skip this page. Do not. The
testnet node is a real internet-facing Linux host with a hot signing key on it,
it sits in the same network as your production infrastructure, and every habit
you form here you will repeat on mainnet.

Apply the mainnet hardening guide in full. What follows is what changes.

## What the threat actually is here

| Not the threat | The threat |
|---|---|
| Losing test SOL | a compromised host used as a foothold into your network |
| Slashing (Solana has none) | a stolen SSH key or a reused credential that also opens mainnet |
| Test stake | sloppy practice carried to mainnet by the same hands |

A testnet validator is an always-on server with open UDP ports and a key file.
Treat it as production infrastructure that happens to run a test chain.

## Non-negotiables, same as mainnet

- validator runs as a dedicated **non-root** user;
- SSH keys only, root login disabled, source-restricted, `fail2ban` installed;
- UFW default-deny, only SSH from a management address plus the pinned dynamic
  port range;
- RPC **not** reachable from the internet — `--private-rpc`,
  `--rpc-bind-address 127.0.0.1`, and the firewall enforcing it;
- no egress filtering;
- public IPv4, no NAT;
- system patched weekly.

````bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <management-ip> to any port 22 proto tcp
sudo ufw allow 8000:8050/tcp
sudo ufw allow 8000:8050/udp
sudo ufw enable
````

## Key separation

- **Separate identity, vote account and withdrawer from mainnet.** Never reuse
  the mainnet identity keypair on testnet.
- Withdrawer generated on a workstation and kept off the validator — yes, even
  for a worthless vote account. The procedure is the product.
- Key files `chmod 600`, owned by the service user.
- Unstaked spare identity present, and the handover practised.

## Credential hygiene across clusters

The realistic path from a testnet compromise to a mainnet loss is shared
credentials, not shared SOL:

- separate SSH keys per host, not one key for the fleet;
- no shared `authorized_keys` between testnet and mainnet validators;
- no monitoring or deployment credential that is valid on both;
- secrets in root-owned `EnvironmentFile`s mode `600`, never on a command line
  and never in shell history.

## Supply chain — stricter here, not looser

Testnet is where new client versions and forks land first, which makes it the
most likely place to install something unverified.

- install from the official release channel or a **signed tag**;
- record release tag, resolved commit and binary SHA-256;
- keep the previous release directory for rollback;
- never install a build from an unattributed link or a chat message.

If you are evaluating a fork or an orderflow stack, do it on a **separate,
non-staked** testnet validator with its own identity — not on the SFDP node, and
not on a host that shares credentials with mainnet.

## Service isolation

````ini
[Service]
User=sol
LimitNOFILE=1000000
LimitMEMLOCK=2000000000
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=true
ReadWritePaths=/mnt/ledger /mnt/accounts /home/sol
````

Verify with `systemd-analyze verify` and a real restart. Testnet is the right
place to find out that an over-tight `ProtectSystem` breaks bank load.

## Checklist

- [ ] separate identity / vote account / withdrawer from mainnet
- [ ] withdrawer off the validator host
- [ ] non-root service user, key files `600`
- [ ] SSH keys only, root disabled, source-restricted, fail2ban on
- [ ] SSH keys not shared with mainnet hosts
- [ ] UFW default-deny; only SSH + pinned P2P range open
- [ ] RPC closed to the internet
- [ ] binary provenance recorded; previous release retained
- [ ] monitoring runs on a different host, labelled by cluster
- [ ] identity and vote account balance alerts configured

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
