# XRPL EVM Mainnet security hardening

XRPL EVM is Proof of Authority. That changes the threat model in one specific
way and in no other: your place in the validator set is granted by a vote of
your peers rather than bought with stake, so losing it is a social event as
well as a technical one. Everything below the consensus layer is ordinary
Cosmos validator security, and double-signing is still the unrecoverable
failure.

## The one rule that outranks uptime

**Never let two processes hold the same `priv_validator_key.json`.**

Before any action that moves, copies, restores or migrates a node — and before
starting a service you did not start — prove the other copy cannot sign:

```bash
# on every host that has ever held this key
systemctl is-active exrpd cosmovisor-exrpd
systemctl is-enabled exrpd cosmovisor-exrpd
pgrep -af exrpd
ss -ltnp | grep -E ':(26656|26657|61656|62656)'
```

Inactive is not enough — a disabled unit with a live listener is a running
node. Uptime never justifies double-sign risk. `tombstoned: true` in the
slashing module is permanent.

## Ports

| Port | Service | Exposure |
|---|---|---|
| `26656` | CometBFT P2P | **public** — required |
| `26657` | CometBFT RPC | loopback or reviewed proxy |
| `1317` | Cosmos REST | loopback or reviewed proxy |
| `9090` | Cosmos gRPC | loopback or reviewed proxy |
| `8545` | EVM JSON-RPC | loopback or reviewed proxy |
| `8546` | EVM WebSocket | loopback or reviewed proxy |
| `26660` | Prometheus | loopback only |

POSTHUMAN runs non-default ports per network on shared hosts (mainnet
`626xx`, testnet `616xx`); the principle is unchanged.

```bash
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 26656/tcp
sudo ufw enable
sudo ufw status numbered
```

**`ufw status` is not evidence.** Docker writes its iptables rules ahead of
`ufw`, so a container started with `-p 26657:26657` is reachable from the
internet on a host whose firewall reads as correct. The evidence is the
listener and an external probe:

```bash
ss -ltnp | grep -vE '127\.0\.0\.1|\[::1\]'
```

Anything in that output is public. If you publish RPC deliberately, put a
reverse proxy in front with TLS, rate limiting and request-size limits —
`exrpd` enforces no per-client limit, so one client can saturate it.

## Keys

| File | What it is | If lost | If copied |
|---|---|---|---|
| `config/priv_validator_key.json` | consensus signing key | validator stops | **double-sign risk** |
| `config/node_key.json` | P2P identity | new node ID | impersonation on the P2P layer |
| `data/priv_validator_state.json` | last signed height/round | must not be restored backwards | — |
| keyring | operator account (`ethm1…`) | funds and operator control | funds and operator control |

- `chmod 700` on the node home, `0600` on the key files.
- Back up `priv_validator_key.json` and `node_key.json` **offline**. Never in
  a snapshot archive, never in a repository, never in chat.
- `priv_validator_state.json` is not a backup artifact. Rolling it back is how
  a double-sign happens.
- The operator key belongs in `--keyring-backend file` or on hardware, never
  in `test`, and not on the validator host at all if you can avoid it.

For a serious deployment, take the signing key off the node entirely: a remote
signer (TMKMS or Horcrux) makes "two nodes with the same key" structurally
impossible rather than procedurally discouraged. XRPL EVM documents a Horcrux
path at
<https://docs.xrplevm.org/pages/operators/advanced/adding-horocrux>.

## Sentry topology

A validator should not be dialable from the open internet. Put sentries in
front:

```toml
# validator config.toml
pex = false
persistent_peers = "<sentry-ids>@<sentry-ips>:26656"
private_peer_ids = ""
addr_book_strict = false
```

```toml
# sentry config.toml
private_peer_ids = "<validator-node-id>"
```

`private_peer_ids` on the sentry is the part that is easy to forget and the
part that does the work: without it, sentries gossip the validator's address
to the network and the topology is decorative.

## Host

From the official validator-security guidance, plus what we enforce:

- `PermitRootLogin no`, `PasswordAuthentication no`, keys only, `AllowUsers`
  scoped to the accounts that need it;
- unattended security updates, with a staging host if you have one;
- AppArmor or SELinux enabled;
- no unnecessary services; every listener accounted for;
- `fail2ban` on SSH — note that it also bans *you* for roughly 30 minutes
  after repeated failed attempts, so do not brute-force usernames on your own
  fleet;
- systemd hardening in the unit: `NoNewPrivileges`, `PrivateTmp`,
  `ProtectSystem=full`.

## Node configuration

```toml
# config.toml
max_num_inbound_peers = 100
max_num_outbound_peers = 10
flush_throttle_timeout = "100ms"
indexer = "null"          # on a signer; "kv" on an RPC node
```

```toml
# app.toml
pruning = "custom"
pruning-keep-recent = "100"
pruning-interval = "10"
```

A validator that also serves public RPC is two jobs on one host with one
failure domain. Split them.

## Before every risky action

1. Read the runbook for the action, not your memory of it.
2. Prove the anti-double-sign condition.
3. Confirm you have a rollback: previous binary, previous `data/`, and the key
   backup you have actually tested restoring.
4. Define what "it worked" means *before* starting — height advancing, app
   hash matching, node present in `last_commit`.
5. Record what you did.
