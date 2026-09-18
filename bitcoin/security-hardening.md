# Bitcoin Node Security Hardening

Bitcoin has no slashing, so the failure modes are different from a
proof-of-stake validator: nobody can burn your stake, but an exposed RPC port
or a compromised wallet file is an irreversible loss, and a node fed a false
view of the chain will happily credit payments that never happened.

Order of priority: **keys, then RPC exposure, then network privacy, then host.**

## 1. Keys and wallets

The strongest control is not having keys on the node at all:

````ini
disablewallet=1
````

An infrastructure node — explorer backend, Electrum server, payment gateway
watcher, Lightning chain source — does not need a wallet. Then a compromise
costs you a resync, not funds.

When a wallet must exist on the node:

| Control | How |
|---|---|
| Encrypt it | `bitcoin-cli encryptwallet "<passphrase>"`, then `walletpassphrase` only for the operation that needs it |
| Watch-only | import descriptors with public keys only; sign elsewhere |
| Hardware signer | Core supports external signers; keys never reach the host |
| Separate hosts | a node holding funds is not the node serving public traffic |
| Backups | see **Backup and recovery** — descriptors and `wallet.dat` are key material |

Rules that do not bend:

- Never put a wallet passphrase, seed or `wallet.dat` in a command line, an
  environment variable, a log, a config file in git, or a chat message.
- Never restore a wallet backup onto a host you are not certain is clean.
- A `wallet.dat` copied off a compromised host is compromised, permanently.

## 2. RPC exposure

This is the failure that actually happens.

````ini
server=1
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcauth=<service>:<salt>$<hash>
rpcwhitelist=<service>:getblockchaininfo,getblockhash,getblock,getrawtransaction
````

- Port `8332` **never** faces the internet. Not behind a password, not
  "temporarily", not behind a load balancer you trust.
- One `rpcauth` identity per consumer, each with its own `rpcwhitelist`. A
  compromised indexer must not be able to call `stop` or touch a wallet.
- Remote access is an SSH tunnel or a WireGuard link, never a wider bind.
- `rpcauth` lines are hashes and safe in config management; the generated
  password is not — it goes to the secret store.

Verify from outside the host after every change:

````bash
nc -vz <public-ip> 8332    # must fail
nc -vz <public-ip> 28332   # ZMQ, must fail
nc -vz <public-ip> 8333    # P2P, may succeed by design
````

**Docker publishes ports around `ufw`.** `-p 8332:8332` in a container writes
iptables rules that bypass the host firewall on most setups. Map it as
`127.0.0.1:8332:8332` and check from outside anyway.

## 3. Firewall

````bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 8333/tcp          # only if you intend to serve peers
sudo ufw enable
sudo ufw status numbered
````

`-natpmp` defaults to `1` since v30.0, so a node behind a capable router may
open its own P2P port. Set `natpmp=0` if exposure is something you manage
deliberately.

Nothing else. Electrum, ZMQ, REST and metrics ports stay on loopback or a
private interface; publish them through a reverse proxy with TLS,
authentication and rate limits, or over Tor.

## 4. Network privacy

A clear-net node broadcasts which transactions originate with you, and its IP
ties your on-chain activity to a location. Three levels:

**Tor for outbound only** — cheap, no downside:

````ini
proxy=127.0.0.1:9050
````

**Tor for everything, with a hidden service** — Core creates and manages its
own onion service when it can reach the Tor control port:

````ini
proxy=127.0.0.1:9050
listen=1
listenonion=1
torcontrol=127.0.0.1:9051
onlynet=onion
````

`onlynet=onion` means *all* peers are onion peers. It is the strongest privacy
setting and it makes you dependent on Tor's health — a Tor outage is a node
outage. `tor` as a value of `onlynet` was **removed in v31.0**; use `onion`.

**Private transaction broadcast** — new in v31.0:

````ini
privatebroadcast=1
````

`sendrawtransaction` then broadcasts only over Tor or I2P, with a separate
connection per transaction, so recipients never learn your IP and two of your
transactions cannot be linked by connection. **This requires v31.1** — v31.0
leaked the clear-net address under some conditions, which is exactly the thing
the feature exists to prevent. Inspect and control the queue with
`getprivatebroadcastinfo` and `abortprivatebroadcast`.

Also available: `i2psam` for I2P, and `asmap`/`asmap=1` to bucket peers by ASN
so one network operator cannot dominate your peer set. v31.0 embeds an asmap
built 2026-03-05, so no external file is needed — but the feature stays off
until you set the flag.

## 5. Host hardening

````bash
# SSH: keys only, no root login
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload ssh

sudo apt -y install unattended-upgrades fail2ban
sudo systemctl enable --now unattended-upgrades fail2ban
````

- Dedicated unprivileged service user, no shell, no sudo.
- systemd sandboxing as in the installation guide: `ProtectSystem=full`,
  `ProtectHome=true`, `NoNewPrivileges=true`, `PrivateDevices=true`,
  `MemoryDenyWriteExecute=true`.
- Data directory `0700`, config `0600`, cookie file never world-readable.
- Full-disk encryption on anything holding a wallet.
- No unrelated services on a node that holds funds.

## 6. Supply chain

The binary you install is the whole trust model:

- Verify `SHA256SUMS.asc` against `bitcoin-core/guix.sigs` builder keys, every
  release, and require **multiple independent builders** to have signed the
  same hashes. Reproducible builds are the reason this check is meaningful.
- Pin the exact release and its digest in your deployment tooling. No floating
  `latest` tags, no `curl … | sh` installers.
- Same rule for LND, Core Lightning, electrs, Fulcrum and miner firmware.
  Replacing the payout address is the standard ASIC malware payload.
- Watch the [announcements list](https://bitcoincore.org/en/list/announcements/join/)
  — it is how security releases reach you.

Version currency is a security control on its own: **v28.x and older are end of
life** and receive no fixes, including security fixes.

## 7. Operational rules

- One `bitcoind` per data directory. Two processes on one datadir corrupt it.
- Never copy `blocks/` or `chainstate/` from an untrusted source — a node that
  trusts someone else's chainstate has given up the only thing it does.
- Compare your tip hash to independent sources continuously, not once. See
  **Monitoring**.
- Give every restart time to flush: `TimeoutStopSec=1200`, or 20 minutes of
  `stop_grace_period` in Compose. `kill -9` costs a reindex.
- Record what each node is for. A node that backs Lightning, serves an
  explorer, and holds a hot wallet is three risk profiles in one box.

## Verification checklist

````bash
systemctl show bitcoind -p NRestarts -p ActiveState
bitcoin-cli getnetworkinfo | jq '{version, subversion, networks: [.networks[] | select(.reachable) | .name], warnings}'
bitcoin-cli getrpcinfo | jq '.active_commands'
ss -tlnp | grep -E '8332|8333|2833'          # RPC/ZMQ on 127.0.0.1 only
ls -l /var/lib/bitcoind/.cookie              # 0600, owned by the daemon user
sudo ufw status numbered
````

From a second host: RPC and ZMQ ports must refuse, P2P may answer if you chose
to serve peers.

## Sources

- [bitcoincore.org — v31.1 release notes, private broadcast IP leak fix](https://bitcoincore.org/en/releases/31.1/)
- [bitcoincore.org — v31.0 release notes, `-privatebroadcast`, asmap, `onlynet`](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes, `-natpmp` default](https://bitcoincore.org/en/releases/30.0/)
- [bitcoin/bitcoin — `doc/tor.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/tor.md)
- [bitcoin/bitcoin — `doc/i2p.md`](https://github.com/bitcoin/bitcoin/blob/master/doc/i2p.md)
- [bitcoin-core/guix.sigs](https://github.com/bitcoin-core/guix.sigs)
