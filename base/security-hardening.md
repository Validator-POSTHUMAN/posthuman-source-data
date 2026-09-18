# Base Node Security Hardening

A Base node has no consensus key, no validator, no stake and nothing to slash.
Delete the Ethereum-staking threat model from your head; it does not apply.

What is actually at risk:

| Loss mode | Realistic cost |
|---|---|
| Your RPC served to the internet | someone else's application runs on your hardware and your L1 bill |
| `debug_*` exposed | cheap remote CPU and memory exhaustion — a one-line DoS |
| pprof exposed | heap and CPU profiles of your process, plus the same DoS |
| L1 provider key leaked | your quota drained, your account charged |
| Engine API reachable | full control of the execution client's canonical chain |
| Data directory lost | days of resync, no permanent loss |

Nothing here loses funds directly. Everything here is someone spending your
money or your availability.

---

## 1. The default Compose file is not safe on a public host

This is the whole page in one section. The shipped `docker-compose.yml` uses
bare `host:container` port mappings, which bind `0.0.0.0`:

```yaml
  execution:
    ports:
      - "8545:8545"      # JSON-RPC          ← internet
      - "8546:8546"      # WebSocket RPC     ← internet
      - "7301:6060"      # Prometheus        ← internet
      - "30303:30303"    # P2P TCP           — correct, keep public
      - "30303:30303/udp"# P2P UDP           — correct, keep public
  node:
    ports:
      - "7545:8545"      # rollup node RPC   ← internet
      - "9222:9222"      # P2P TCP           — correct, keep public
      - "9222:9222/udp"  # P2P UDP           — correct, keep public
      - "7300:7300"      # Prometheus        ← internet
      - "6060:6060"      # pprof             ← internet
```

**Docker writes its own iptables rules ahead of `ufw`.** A host where
`ufw status` shows a tidy deny-by-default policy will still answer on every one
of those ports. `ufw` is not evidence. Listeners are evidence.

### Fix it before the first start

Edit the `ports:` blocks so everything except P2P binds to loopback:

```yaml
  execution:
    ports:
      - "127.0.0.1:8545:8545"
      - "127.0.0.1:8546:8546"
      - "127.0.0.1:7301:6060"
      - "30303:30303"
      - "30303:30303/udp"
  node:
    ports:
      - "127.0.0.1:7545:8545"
      - "9222:9222"
      - "9222:9222/udp"
      - "127.0.0.1:7300:7300"
      - "127.0.0.1:6060:6060"
```

If nothing on the host needs pprof, delete the `6060` mapping entirely rather
than binding it.

Keep the change in a `docker-compose.override.yml` instead of editing the
tracked file, so `git pull` on the next release does not silently revert it:

```yaml
# docker-compose.override.yml — not tracked by base/base
services:
  execution:
    ports: !override
      - "127.0.0.1:8545:8545"
      - "127.0.0.1:8546:8546"
      - "127.0.0.1:7301:6060"
      - "30303:30303"
      - "30303:30303/udp"
  node:
    ports: !override
      - "127.0.0.1:7545:8545"
      - "9222:9222"
      - "9222:9222/udp"
      - "127.0.0.1:7300:7300"
```

`!override` requires Compose v2.24 or newer. On older Compose, `ports:` merges
rather than replaces and the public mappings survive — check the result instead
of assuming it.

### Verify from outside, not from the host

```bash
# On the node: what is actually listening, and on which address
sudo ss -tulpn | grep -E '8545|8546|7545|7300|7301|6060|30303|9222'
docker compose ps --format 'table {{.Service}}\t{{.Ports}}'
```

A correct result shows `127.0.0.1:` on every RPC and metrics line, and
`0.0.0.0:` only on `30303` and `9222`.

Then prove it from another machine:

```bash
# From elsewhere — all four must fail
nc -vz -w3 <node-ip> 8545
nc -vz -w3 <node-ip> 7545
nc -vz -w3 <node-ip> 7300
nc -vz -w3 <node-ip> 6060
```

"Connection refused" or a timeout is the pass. A successful connect means you
are serving it, whatever `ufw status` says.

---

## 2. The RPC namespaces are wider than you would choose

The stock `execution-entrypoint` starts `base-reth-node` with:

```
--http.api=web3,debug,eth,net,txpool,miner
--ws.api=web3,debug,eth,net,txpool
--http.corsdomain="*"
--ws.origins="*"
```

Two things follow.

**`debug` is on by default.** `debug_traceTransaction`, `debug_traceCall` and
friends re-execute history on demand. One unauthenticated caller can pin every
core on the box. If the RPC is loopback-only this is a non-issue; the moment it
is published, it is the first thing that will be abused.

**CORS and WebSocket origins are wildcards.** Any page in any browser can reach
the node if it is reachable at all. That is a deliberate convenience for a local
development node and a mistake on a server.

If you intend to expose an RPC publicly, do not publish the node's port. Put a
reverse proxy in front of it and let the proxy own the policy:

- terminate TLS
- allow only `eth_*`, `net_*`, `web3_*`; reject `debug_*`, `txpool_*`, `miner_*`
  and `admin_*` at the proxy, by method name in the JSON body
- rate-limit per source address
- cap request body size and batch length

`etc/docker/proxyd/proxyd.toml` in `base/base` is the upstream reference for a
method-aware Base RPC proxy if you would rather not write the rules yourself.

---

## 3. The engine JWT is a published constant

`.env.mainnet` ships with:

```
BASE_NODE_L2_ENGINE_AUTH_RAW=688f5d737bad920bdfb2fc2f488d6b6209eebda1dae949a8de91398d932c517a
```

Both entrypoints write that value into the JWT file at start. It is committed to
a public repository, so **every default Base node in the world shares the same
engine secret.**

This is survivable only because the Compose file does not publish `8551`. The
Engine API is reachable solely from inside the Compose network. The rules that
follow from that:

- Never add `8551` to `ports:`. If you must reach it from another host, use an
  SSH tunnel or a private network — not a published port.
- If `8551` ever was reachable, treat the node as untrusted: an attacker with
  the engine API can drive `engine_forkchoiceUpdated` and make your execution
  client follow a chain of their choosing. Resync from a snapshot.
- Generate your own secret anyway. It costs nothing:

  ```bash
  openssl rand -hex 32
  ```

  Put it in `BASE_NODE_L2_ENGINE_AUTH_RAW` in your `.env` file. Both services
  read the same variable, so they stay in agreement.

Keep the `.env` file at `0600` and owned by the operator account. It holds the
engine secret and, usually, your L1 provider URL with its API key in the path.

---

## 4. The L1 endpoint is a credential

`BASE_NODE_L1_ETH_RPC` and `BASE_NODE_L1_BEACON` usually contain a provider key
inside the URL. Treat them accordingly:

- `.env` at `0600`, never committed, never pasted into a support channel or an
  issue. Redact the path segment, not just the hostname.
- Prefer your own L1 node. It removes the credential, the quota and the rate
  limit in one move.
- `docker compose config` prints the resolved environment. Do not run it into a
  shared terminal or a pasted log.
- Rotate the key if a log, a screenshot or a core dump ever contained it.

Leave `BASE_NODE_L1_TRUST_RPC=false`. With `true`, the rollup node stops
verifying what the L1 endpoint returns, and a compromised or simply wrong
provider becomes a wrong L2 chain that your node will defend as correct.

---

## 5. The node phones out to find its own IP

`consensus-entrypoint` resolves the public IP at every start by querying, in
order, `ifconfig.me`, `api.ipify.org`, `ipecho.net` and `v4.ident.me` — over
plain HTTP — and exports the answer as `BASE_NODE_P2P_ADVERTISE_IP`.

Three consequences, none of them documented upstream:

- **Egress-restricted hosts fail to start.** If all four are unreachable the
  script exits `8` before the node runs. The symptom is a container that exits
  immediately with no rollup-node log at all. Allow outbound HTTP to at least
  one of them, or run the binaries under systemd where you set the value
  yourself.
- **The advertised address comes from an unauthenticated third party over an
  unencrypted channel.** The blast radius is limited — a wrong answer degrades
  your peering, it does not expose anything — but it is a dependency you did not
  choose.
- **You cannot override it in Compose.** The export is unconditional and
  overwrites whatever you set. NAT, floating IPs and proxied networks need the
  systemd path.

---

## 6. Host hygiene

Nothing Base-specific, and all of it still true:

- Dedicated non-root user in the `docker` group. Do not run the stack as root.
  Membership in `docker` is root-equivalent — treat that account as privileged
  and keep it off shared login paths.
- SSH: key auth only, `PasswordAuthentication no`, `PermitRootLogin no`,
  fail2ban on the SSH jail.
- `ufw default deny incoming`, allow SSH from your ranges, allow `30303` and
  `9222` — and remember from §1 that this does **not** cover Docker-published
  ports.
- Unattended security upgrades on.
- `chrony` or `systemd-timesyncd` running. Clock drift breaks P2P before it
  breaks anything obvious.
- Monitor disk. A full disk on an NVMe running reth is a corrupted database and
  a resync, and it arrives faster than you expect at Base's block rate.

---

## 7. Supply chain

- Pin `NODE_TAG` to a release tag. `latest` means the binary changes at the next
  restart, chosen by nobody.
- `ghcr.io/base/node` is the only image this stack should pull. Check with
  `docker compose config | grep image:`.
- `baseup` installs release binaries with a piped `curl | bash` — read the
  script first, or download the release asset from the
  [base/base releases](https://github.com/base/base/releases) page and verify it
  against the published checksum.
- **Third-party helper tools are third-party code.** Anything that wraps
  `docker compose`, reads your `.env` and posts health to a Discord webhook has
  your L1 credential in process memory by design. Read it before running it,
  pin the commit, and do not install it from a one-line remote pipe on a
  production host.

---

## 8. Incident checklist

If you believe the node was reached:

1. Do **not** delete anything. There is no key at risk and no clock running.
2. Capture evidence first: `docker compose logs --no-color --since 48h`,
   `ss -tulpn`, `iptables-save`, `docker compose config` redacted, `last -F`,
   auth logs.
3. Rotate what can be rotated: `BASE_NODE_L2_ENGINE_AUTH_RAW`, the L1 provider
   key, SSH keys.
4. Close the exposure, then verify from a second machine that it is closed.
5. If the engine API was reachable, the chain data is untrusted: restore from a
   fresh snapshot rather than continuing.
6. Compare your head against a public reference before declaring recovery —
   `basectl doctor` does this, and the **Monitoring** tab covers what to watch
   afterwards.

---

## Verification summary

You are hardened when all of these are true, checked and not assumed:

- [ ] `ss -tulpn` shows `127.0.0.1` on `8545`, `8546`, `7545`, `7300`, `7301`; `6060` bound or removed
- [ ] `0.0.0.0` appears only on `30303` and `9222`
- [ ] `8551` appears nowhere in any `ports:` block
- [ ] an external `nc -vz` to `8545`, `7545`, `7300` and `6060` fails
- [ ] `BASE_NODE_L2_ENGINE_AUTH_RAW` is your own value, not the committed one
- [ ] `.env` is `0600`, uncommitted, and its L1 URL has never been pasted anywhere
- [ ] `BASE_NODE_L1_TRUST_RPC=false`
- [ ] `NODE_TAG` is a pinned release, not `latest`
- [ ] SSH is key-only and root login is off
- [ ] disk, clock and peer-count alerts exist and have fired at least once in a test
