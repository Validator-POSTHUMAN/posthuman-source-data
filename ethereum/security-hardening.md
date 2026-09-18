# Ethereum Node and Validator Security Hardening

## What can actually go wrong

Ethereum staking has three loss modes, and they are not equally likely.

| Loss mode | Cause | Magnitude |
|---|---|---|
| **Stake stolen** | Withdrawal-address private key or mnemonic compromised | Everything |
| **Slashed** | The same validator key signs from two places | 1+ ETH immediately, forced exit, correlation penalty if others are slashed with you |
| **Penalised** | Node offline or attesting late | Small and continuous; roughly what you would have earned, inverted |

Note what is *not* on the list: an attacker with the validator signing key
cannot move your funds. Withdrawals go to the withdrawal address and nothing the
signing key does can change that. The signing key is a slashing liability, not a
theft liability — which is exactly why it can live on an internet-facing server
while the mnemonic must not.

**There is no double-sign risk from "starting the node twice" being harmless
here — it is not harmless.** Uptime never justifies running a second copy of a
validator key. A validator that is offline loses a little. A validator that is
running twice loses a lot and is ejected.

---

## 1. Key custody

| Material | Rule |
|---|---|
| Mnemonic (24 words) | Never on any networked machine. Paper, two locations. Not in a password manager that syncs, not photographed, not typed into a browser. |
| Withdrawal address key | Hardware wallet. This key can exit validators and withdraw the stake since Pectra. |
| Validator keystores | On the staking host only, owned by the validator user, mode `0600`, directory `0700`. |
| Keystore passwords | Same host, same ownership. Not in the shell history, not in the unit file's `ExecStart`. |
| Slashing protection DB | Backed up **with** the keystores, always as a pair. |

````bash
sudo chown -R validator:validator /var/lib/validator
sudo chmod 700 /var/lib/validator
sudo find /var/lib/validator -type f -exec chmod 600 {} +
````

**Restoring a keystore backup without its slashing protection database is a
slashing event waiting to happen.** The database records the highest slot each
key has signed for; without it, the client has no memory of what it already
signed and will happily sign again. If you ever restore from a backup of unknown
age, wait at least two full epochs — better, one weak subjectivity period —
before starting the VC, or import the interchange file first.

### Remote signing

For multi-node or institutional setups, put the keys behind a signer instead of
in the VC:

- [Web3Signer](https://github.com/Consensys/web3signer) — consensus-layer remote
  signer with its own slashing protection database in PostgreSQL. The VC holds
  no key material.
- [Dirk](https://github.com/attestantio/dirk) — distributed key manager with
  threshold signing.

This centralises the slashing protection decision in one place, which is the
real reason to do it. It does not remove the double-sign rule — two VCs pointed
at one Web3Signer with a shared database is safe; two Web3Signers with separate
databases is not.

---

## 2. Network exposure

Two ports face the internet. Everything else is loopback.

| Port | Protocol | Exposure | Why |
|---|---|---|---|
| `30303` | TCP + UDP | **Public** | Execution P2P and discovery |
| `9000` | TCP + UDP | **Public** | Consensus P2P and discovery |
| `9001` | UDP | **Public** | Consensus QUIC, client-dependent |
| `22` | TCP | Restricted to your IPs | SSH |
| `8545` / `8546` | TCP | **Loopback only** | JSON-RPC / WS |
| `8551` | TCP | **Loopback only** | Engine API |
| `5052` | TCP | **Loopback only** | Beacon API |
| `5054` / `6060` / `8008` / `8080` | TCP | **Loopback only** | Metrics |
| `18550` | TCP | **Loopback only** | MEV-Boost |

````bash
sudo ufw default deny incoming
sudo ufw allow from <your-ip> to any port 22 proto tcp
sudo ufw allow 30303 comment 'EL p2p'
sudo ufw allow 9000 comment 'CL p2p'
sudo ufw allow 9001/udp comment 'CL quic'
sudo ufw enable
````

**Verify listeners, not firewall rules.** The firewall tells you what you
intended; `ss` tells you what is true.

````bash
sudo ss -tlnp | grep -vE '127\.0\.0\.1|\[::1\]'
````

Anything in that output other than sshd and the two P2P listeners is a finding.

**Docker publishes ports past ufw.** A Compose file with `ports: ["8545:8545"]`
is reachable from the internet no matter what ufw says, because Docker writes
its own iptables rules in front. Bind explicitly:

````yaml
ports:
  - "127.0.0.1:8545:8545"
````

### If you must expose RPC

Do not expose it from the staking node. Run a second, keyless node for RPC
service, put it behind a reverse proxy with TLS, rate limiting and a method
allowlist, and never enable `admin`, `debug`, `personal` or `txpool` on a public
listener.

---

## 3. Host hardening

### SSH

````bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowUsers <operator>
````

````bash
sudo sshd -t && sudo systemctl reload ssh
````

Keep the current session open until you have proved a new one works.

### Automatic security updates

````bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
````

Allow security updates to install automatically; do **not** allow automatic
reboots on a validator host without deciding when they happen. An unattended
reboot during your proposal slot is a missed proposal.

### fail2ban

````bash
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
````

### systemd sandboxing

Add to every client unit. These cost nothing and remove whole classes of
post-exploitation:

````ini
[Service]
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictNamespaces=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=false
ReadWritePaths=/var/lib/execution
````

Set `ReadWritePaths` to that unit's data directory only. `MemoryDenyWriteExecute`
must stay `false` for JIT runtimes — Besu, Teku and Lodestar will not start with
it enabled.

Check the result:

````bash
systemd-analyze security execution.service
````

---

## 4. Supply chain

Client binaries are the most valuable thing an attacker could replace on your
box.

- **Verify checksums and signatures on every download.** Every client publishes
  them; Geth and Lighthouse also publish PGP signatures.
- **Pin versions.** Do not run `latest` in Docker and do not let a wrapper script
  auto-update a client on a validator host. `prysm.sh` downloads on every start —
  pin the binary instead.
- **Read the release notes before upgrading a consensus client.** A fork-relevant
  release is not optional, and a non-fork release can still change flag
  semantics.
- Build from source only if you will keep doing it; a stale self-built binary is
  worse than a verified release.

---

## 5. Operational rules

These are the rules that survive contact with an incident.

1. **Never start a second copy of a validator key.** Not to test. Not on a
   different machine "just to check". Not during a migration. Enable
   doppelganger protection everywhere as a backstop, and treat it as a backstop,
   not as permission.
2. **Migration order is: stop old, export slashing protection, import, start
   new.** Never overlapping. If you cannot stop the old host, you cannot start
   the new one.
3. **A missed epoch costs cents. A slash costs ETH.** When in doubt during an
   incident, leave the validator off.
4. **Back up the keystores and slashing DB together**, encrypted, off-host, and
   test the restore on a testnet.
5. **Test everything on Hoodi first** — upgrades, migrations, key operations,
   exits.
6. **One change at a time on a validator host**, with a verified state before
   and after.

---

## 6. Post-change verification

After any security change, prove the node still works rather than assuming it:

````bash
systemctl is-active execution consensus validator
sudo ss -tlnp | grep -vE '127\.0\.0\.1|\[::1\]'
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' http://127.0.0.1:8545
````

Then confirm from outside: attestations still landing on beaconcha.in within two
epochs. A hardening change that silently broke the Engine API looks perfectly
healthy from the shell.

## Sources

- [ethereum.org — Home staking](https://ethereum.org/staking/solo/)
- [EIP-3076 — Slashing protection interchange format](https://eips.ethereum.org/EIPS/eip-3076)
- [Web3Signer](https://github.com/Consensys/web3signer) · [Dirk](https://github.com/attestantio/dirk)
