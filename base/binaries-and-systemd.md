# Base Without Docker: Binaries and systemd

Docker Compose is what Base supports and what the **installation guide**
assumes. Run the binaries under systemd when you want one of these three
things:

- **Ports that bind where you say.** The stock Compose file publishes the RPC,
  both metrics endpoints and pprof on `0.0.0.0`, past `ufw`. systemd units bind
  to the address in the flag and nothing else.
- **A fixed advertised P2P address.** `consensus-entrypoint` resolves the public
  IP from `ifconfig.me` and friends at every start and overwrites whatever you
  set. Behind NAT, a floating IP or a restricted egress policy, that is either
  wrong or fatal — the container exits `8` if it cannot reach any of them.
- **No Docker on the host** at all.

You give up Base's tested composition in exchange. Track upstream changes to the
entrypoints; they are the reference for what these units must do.

---

## 1. Install the binaries

```bash
curl -fsSL https://raw.githubusercontent.com/base/base/main/baseup/install | bash
baseup -i v1.4.0 --bin all
```

Installs to `~/.base/bin` by default; `BASEUP_HOME=/custom/path` moves it.
`baseup` never uses `sudo` and only writes to user-writable directories.

Four binaries are published: `base`, `base-reth-node`, `base-consensus`,
`basectl`.

### The installer verifies its own downloads

Worth knowing, because it changes what you have to do yourself. For each
archive `baseup`:

- checks `<archive>.sha256`
- imports the pinned Base Releases public key into a temporary GPG keyring and
  verifies `<archive>.asc`, requiring fingerprint
  `5EFE7BCFCD85682711F9FC30904841FFEBD38BAD`
- verifies GitHub SLSA provenance when `gh` is installed and authenticated

Never pass `--unsafe-skip-verify` on a production host.

You can verify a release without installing it:

```bash
baseup verify-release -i v1.4.0
```

The residual supply-chain risk is the bootstrap line itself — `curl | bash` from
`main`. On a production host, fetch `baseup/install`, read it, then run it, or
install `baseup` once from a machine you trust and copy the binary.

Pin the version with `-i`. `baseup` with no argument installs "latest", which
is the same anti-pattern as `NODE_TAG=latest`.

---

## 2. Lay out the host

```bash
sudo useradd --system --create-home --home-dir /var/lib/base --shell /usr/sbin/nologin base
sudo install -d -o base -g base -m 0750 /var/lib/base/data
sudo install -d -o root -g base -m 0750 /etc/base
sudo install -m 0755 ~/.base/bin/base-reth-node ~/.base/bin/base-consensus ~/.base/bin/basectl /usr/local/bin/
```

Generate your own engine JWT. Do not reuse the one committed to `.env.mainnet`
— it is public, and every default Base node shares it:

```bash
openssl rand -hex 32 | sudo tee /etc/base/jwt.hex >/dev/null
sudo chown root:base /etc/base/jwt.hex
sudo chmod 0640 /etc/base/jwt.hex
```

---

## 3. Environment file

`/etc/base/base.env`, `0640`, `root:base`. It holds your L1 credential — treat
it as a secret file, not as configuration.

```ini
# Network
RETH_CHAIN=base
BASE_NODE_NETWORK=base
RETH_SEQUENCER_HTTP=https://mainnet-sequencer.base.org

# L1 — required
BASE_NODE_L1_ETH_RPC=http://127.0.0.1:8545
BASE_NODE_L1_BEACON=http://127.0.0.1:5052
BASE_NODE_L1_TRUST_RPC=false

# Engine
BASE_NODE_L2_ENGINE_RPC=ws://127.0.0.1:8551
BASE_NODE_L2_ENGINE_AUTH=/etc/base/jwt.hex

# P2P — the whole reason to run without Docker
BASE_NODE_P2P_ADVERTISE_IP=203.0.113.10
```

For Sepolia: `RETH_CHAIN=base-sepolia`, `BASE_NODE_NETWORK=base-sepolia`,
`RETH_SEQUENCER_HTTP=https://sepolia-sequencer.base.org`.

Set `BASE_NODE_P2P_ADVERTISE_IP` to the address peers should dial — your public
IP, or the NAT's external address. This is the value the container path
overwrites and systemd does not.

---

## 4. Execution layer unit

`/etc/systemd/system/base-reth.service`. The flags mirror the upstream
`execution-entrypoint`, with every listener that is not P2P moved to loopback.

```ini
[Unit]
Description=Base execution client (base-reth-node)
After=network-online.target
Wants=network-online.target

[Service]
User=base
Group=base
Type=simple
Restart=always
RestartSec=5
EnvironmentFile=/etc/base/base.env
ExecStart=/usr/local/bin/base-reth-node node \
  -vvv \
  --datadir=/var/lib/base/data \
  --log.stdout.format json \
  --chain ${RETH_CHAIN} \
  --rollup.sequencer-http=${RETH_SEQUENCER_HTTP} \
  --http \
  --http.addr=127.0.0.1 \
  --http.port=8545 \
  --http.api=web3,eth,net \
  --ws \
  --ws.addr=127.0.0.1 \
  --ws.port=8546 \
  --ws.api=web3,eth,net \
  --authrpc.addr=127.0.0.1 \
  --authrpc.port=8551 \
  --authrpc.jwtsecret=/etc/base/jwt.hex \
  --metrics=127.0.0.1:7301 \
  --ipcpath=/var/lib/base/data/reth.ipc \
  --max-outbound-peers=100 \
  --port=30303 \
  --discovery.port=30303 \
  --discovery.v5.port=9200
LimitNOFILE=1000000
TimeoutStopSec=300
KillSignal=SIGINT

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/base/data
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
```

Three deliberate differences from the upstream entrypoint:

| Upstream | Here | Why |
|---|---|---|
| `--http.api=web3,debug,eth,net,txpool,miner` | `web3,eth,net` | `debug_*` is a free remote DoS; add it back only for a loopback-only debugging session |
| `--http.corsdomain="*"`, `--ws.origins="*"` | omitted | wildcard CORS is a local-development convenience, not a server setting |
| `--http.addr=0.0.0.0` | `127.0.0.1` | the container relies on the port not being published; a unit does not have that safety net |

Add `--websocket-url=wss://mainnet.flashblocks.base.org/ws` for Flashblocks, and
the `--prune.*.distance=` flags for custom pruning — see **Pruning & Storage**
for why the distance must exceed 10,064 and why the archive snapshot has to come
first.

---

## 5. Consensus layer unit

`/etc/systemd/system/base-consensus.service`.

```ini
[Unit]
Description=Base rollup node (base-consensus)
After=network-online.target base-reth.service
Wants=network-online.target
BindsTo=base-reth.service

[Service]
User=base
Group=base
Type=simple
Restart=always
RestartSec=5
EnvironmentFile=/etc/base/base.env
ExecStart=/usr/local/bin/base-consensus node
LimitNOFILE=1000000
TimeoutStopSec=120

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/base/data
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
```

`base-consensus` is configured almost entirely through `BASE_NODE_*`
environment variables — that is all the upstream entrypoint does before
`exec`-ing it. **Confirm the RPC listen address, metrics address and P2P port
variable names against your installed version** before trusting the defaults:

```bash
base-consensus node --help
```

Set the RPC listener to `127.0.0.1:7545` and the metrics listener to
`127.0.0.1:7300` so the rest of the Base documentation's port numbers still
describe your node. Add `BASE_NODE_SOURCE_L2_RPC=<trusted-l2-rpc>` and run
`base-consensus follow` instead of `node` for follow mode.

---

## 6. Start and verify

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now base-reth base-consensus
systemctl status base-reth base-consensus --no-pager
journalctl -u base-reth -f
```

Then run the four checks from the **installation guide** in order, and confirm
the bindings are what you asked for:

```bash
sudo ss -tulpn | grep -E '8545|8546|8551|7545|7300|7301|30303|9200'
```

Everything except `30303` and the CL P2P port must show `127.0.0.1`. If any of
them shows `0.0.0.0`, the flag did not take — fix it before the node is
reachable.

---

## 7. What you now own

Running outside Compose means these are yours to track:

- **Entrypoint drift.** When Base changes `execution-entrypoint` or
  `consensus-entrypoint`, your units do not change with it. Diff them at every
  upgrade.
- **Flag deprecations.** `v1.4.0` removed `--rollup.disable-tx-pool-gossip`.
  A removed flag in a unit file is a service that will not start.
- **Version pinning.** `baseup -i vX.Y.Z` at each upgrade, then restart both
  units. See **Upgrades**.

---

## Related

- **Installation Guide** — the supported Docker path and the verification sequence
- **Security Hardening** — the published-port problem this page avoids
- **Upgrades** — release cadence and fork deadlines
