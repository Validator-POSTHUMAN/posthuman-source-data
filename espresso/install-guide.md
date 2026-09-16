# Espresso — Node and Validator Setup

Espresso is a decentralized sequencing network secured by a permissionless,
delegated proof-of-stake validator set. Consensus runs on the Espresso network
itself; **staking, registration and rewards live in contracts on Ethereum**.

Espresso is **not a Cosmos SDK chain**. There is no `valoper` address, no
Tendermint RPC, no genesis/addrbook download, no state-sync, no `unjail` and no
snapshot service. Everything below is Espresso-specific.

Mainnet and Decaf testnet use identical commands and environment variables.
Only contract addresses, endpoints and the genesis file differ — collected in
[Network values](#network-values) and referenced by name throughout.

Verified against the official operator documentation on 2026-09-16
(`docs.espressosys.com`, node release `20260910`). Re-check the release tag and
contract addresses before you deploy.

---

## Network values

|                      | Mainnet                                                           | Decaf testnet                                                     |
| -------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| L1                   | Ethereum                                                          | Ethereum Sepolia                                                  |
| Container image      | `ghcr.io/espressosystems/espresso-network/espresso-node:20260910` | `ghcr.io/espressosystems/espresso-network/espresso-node:20260910` |
| Genesis file         | `/genesis/mainnet.toml`                                           | `/genesis/decaf.toml`                                             |
| Stake table contract | `0xCeF474D372B5b09dEfe2aF187bf17338Dc704451`                      | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037`                      |
| Query service        | `https://query.main.net.espresso.network`                         | `https://query.decaf.testnet.espresso.network`                    |
| Config cache         | `https://cache.main.net.espresso.network`                         | `https://cache.decaf.testnet.espresso.network`                    |
| State relay          | `https://state-relay.main.net.espresso.network`                   | `https://state-relay.decaf.testnet.espresso.network`              |
| Block explorer       | `https://explorer.main.net.espresso.network`                      | `https://explorer.decaf.testnet.espresso.network`                 |
| Staking UI           | `https://stake.espresso.network/`                                 | `https://stake.decaf.espresso.network/`                           |

### Ethereum contracts

| Contract     | Mainnet (Ethereum)                           | Decaf (Sepolia)                              |
| ------------ | -------------------------------------------- | -------------------------------------------- |
| Stake Table  | `0xCeF474D372B5b09dEfe2aF187bf17338Dc704451` | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037` |
| ESP Token    | `0x031De51F3E8016514Bd0963d0B2AB825A591Db9A` | `0xb3e655a030e2e34a18b72757b40be086a8f43f3b` |
| Reward Claim | `0x67c966a0ecdd5c33608be7810414e5b54da878d8` | `0xe81908e34dbb4ba01f27f8769264199727be50c8` |
| Light Client | `0x95ca91cea73239b15e5d2e5a74d02d6b5e0ae458` | `0x303872bb82a191771321d4828888920100d0b3e4` |
| Fee Contract | `0x9fcE21c3F7600Aa63392A5F5713986b39bB98884` | —                                            |

Environment variables use the prefix `ESPRESSO_NODE_` for node settings and
`ESPRESSO_L1_` for L1 client settings, except `ESPRESSO_STATE_RELAY_SERVER_URL`.
The binary inside the image is `espresso-node`.

---

## Hardware

Figures are observed from running nodes, not a guaranteed minimum. Espresso
block data grows over time — provision headroom and the ability to grow the
disk.

|         | Validator with query API, pruned                | Archival node                                   |
| ------- | ----------------------------------------------- | ----------------------------------------------- |
| CPU     | 4 cores, plus 2 for a separate Postgres server  | 4 cores, plus 2 for a separate Postgres server  |
| Memory  | 8 GB, plus 4 GB for a separate Postgres server  | 8 GB, plus 4 GB for a separate Postgres server  |
| Storage | 500 GB SSD                                      | 2.5 TB SSD                                      |

A mainnet archival node measured about 1.7 TB in September 2026 and grows
roughly 215 GB per month. Disk **throughput** matters more than spare capacity
for a query node: database migrations during version upgrades are IO-bound.

Required on the host: 64-bit Linux with Docker and Docker Compose, a stable
public IP or DNS name, and inbound TCP on the P2P port.

---

## 1. Prepare the host

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl jq ca-certificates docker.io docker-compose-v2
sudo systemctl enable --now docker
```

```bash
sudo mkdir -p /opt/espresso/keys /opt/espresso/store
sudo chown -R "$USER":"$USER" /opt/espresso
```

---

## 2. Generate consensus keys

Each validator needs three keypairs:

| Key         | Scheme  | Purpose                                                             |
| ----------- | ------- | ------------------------------------------------------------------- |
| Staking key | BLS     | Signs consensus messages; supports signature aggregation.           |
| State key   | Schnorr | Signs finalized consensus states that drive on-chain state updates. |
| x25519 key  | X25519  | Encrypts and authenticates connections to other validators.         |

```bash
IMAGE=ghcr.io/espressosystems/espresso-network/espresso-node:20260910

docker run --rm -v /opt/espresso/keys:/keys "$IMAGE" keygen -o /keys
```

This writes `/opt/espresso/keys/0.env`:

```
# Mnemonic: ...
# Index: 0
ESPRESSO_NODE_PUBLIC_STAKING_KEY=BLS_VER_KEY~...
ESPRESSO_NODE_PRIVATE_STAKING_KEY=BLS_SIGNING_KEY~...
ESPRESSO_NODE_PUBLIC_STATE_KEY=SCHNORR_VER_KEY~...
ESPRESSO_NODE_PRIVATE_STATE_KEY=SCHNORR_SIGNING_KEY~...
ESPRESSO_NODE_PUBLIC_X25519_KEY=X25519_PK~...
ESPRESSO_NODE_PRIVATE_X25519_KEY=X25519_SK~...
```

```bash
chmod 600 /opt/espresso/keys/0.env
```

Generating the keys inside the container keeps them off the host unless a
volume is mounted, as above. Back the file up offline **before** you register.

- `keygen --mnemonic <PHRASE>` derives all three keys deterministically from a
  BIP-39 phrase instead of fresh OS entropy.
- `keygen -n <N>` writes `0.env` … `<N-1>.env`; each file derives from its own
  file index, and `--index` is ignored.
- `keygen --scheme x25519` rotates only the x25519 key. It derives from a new
  random mnemonic, so replace **both** the public and private x25519 lines and
  re-register the public key on-chain.
- The node can instead be configured with `ESPRESSO_NODE_KEY_MNEMONIC` plus
  `ESPRESSO_NODE_KEY_INDEX`. That conflicts with `ESPRESSO_NODE_KEY_FILE` — use
  one or the other. Print the public keys of such a node with the `pub-key`
  utility from the same image.

Without a persistent `ESPRESSO_NODE_PRIVATE_X25519_KEY` the node generates a
random ephemeral key on every start, which will not match the public key
registered on-chain and breaks every inbound P2P handshake.

---

## 3. Choose the P2P address

The stake table stores the x25519 public key **and** the P2P address; a
validator without them cannot participate in consensus. Decide the address
before registering. It must:

- use the node's public IP address or DNS name — never private or loopback;
- be reachable over **TCP from the public internet** and route to the node's
  P2P bind port (`ESPRESSO_NODE_CLIQUENET_BIND_ADDRESS`, default `9977`);
- if it is an IP address, match the source IP of the node's **outgoing**
  connections — peers check the source IP of every inbound connection.

> **Register a DNS name** when egress and ingress use different IPs (inbound
> load balancer with a separate NAT gateway, egress IP pools, unstable egress).
> A DNS registration disables the source-IP check. Registering an IP while
> egress leaves through a different address produces `party has invalid ip addr`
> on peers and one-directional connectivity.

---

## 4. Run the node

### Environment

`/opt/espresso/.env` — mainnet shown; swap the network values for Decaf:

```bash
# --- identity and storage -------------------------------------------------
ESPRESSO_NODE_KEY_FILE=/mount/espresso/keys/0.env
ESPRESSO_NODE_STORAGE_PATH=/mount/espresso/store/
ESPRESSO_NODE_EMBEDDED_DB=true

# --- network --------------------------------------------------------------
ESPRESSO_NODE_GENESIS_FILE=/genesis/mainnet.toml
ESPRESSO_STATE_RELAY_SERVER_URL=https://state-relay.main.net.espresso.network
ESPRESSO_NODE_STATE_PEERS=https://query.main.net.espresso.network
ESPRESSO_NODE_API_PEERS=https://query.main.net.espresso.network
ESPRESSO_NODE_CLIQUENET_BIND_ADDRESS=0.0.0.0:9977
ESPRESSO_NODE_API_PORT=8080

# --- L1 -------------------------------------------------------------------
ESPRESSO_L1_PROVIDER=https://<your-ethereum-rpc>
ESPRESSO_L1_WS_PROVIDER=wss://<your-ethereum-ws-rpc>

# --- pruning (non-archival query node) ------------------------------------
ESPRESSO_NODE_DATABASE_PRUNE=true
ESPRESSO_NODE_PRUNER_TARGET_RETENTION=14d
ESPRESSO_NODE_PRUNER_MINIMUM_RETENTION=14d
ESPRESSO_NODE_PRUNER_STATE_TARGET_RETENTION=14d
ESPRESSO_NODE_PRUNER_STATE_MINIMUM_RETENTION=14d
ESPRESSO_NODE_PRUNER_PRUNING_THRESHOLD=400GB

# --- logging --------------------------------------------------------------
RUST_LOG=warn
RUST_LOG_FORMAT=json
```

Add more comma-separated `ESPRESSO_NODE_STATE_PEERS` and
`ESPRESSO_NODE_API_PEERS` entries so catch-up does not depend on a single peer.
`ESPRESSO_L1_PROVIDER` is required; a `wss://` endpoint is optional but
recommended — it noticeably reduces load on the L1 provider.

The advertised P2P address is **not** an environment variable: peers learn it
from the stake table contract, so it is set with `staking-cli` in step 5.

### First start only

A node with no saved network configuration must fetch it from a running peer:

```bash
ESPRESSO_NODE_CONFIG_PEERS=https://cache.main.net.espresso.network
```

The node stores the configuration once it joins, so this is not needed on
subsequent restarts. It **is** needed again after any reset or migration that
clears storage.

### Compose file

`/opt/espresso/docker-compose.yml`:

```yaml
services:
  espresso-node:
    image: ghcr.io/espressosystems/espresso-network/espresso-node:20260910
    container_name: espresso-node
    restart: unless-stopped
    env_file: /opt/espresso/.env
    command: ["espresso-node", "--", "http", "--", "query", "--", "light-client"]
    ports:
      - "9977:9977/tcp"
      - "127.0.0.1:8080:8080/tcp"
    volumes:
      - /opt/espresso/keys:/mount/espresso/keys:ro
      - /opt/espresso/store:/mount/espresso/store
    stop_grace_period: 60s
    logging:
      driver: json-file
      options: { max-size: "100m", max-file: "5" }
```

```bash
cd /opt/espresso
docker compose up -d
docker compose logs -f --tail=200
```

Worked Compose files for both networks and both storage backends are published
in [espresso-for-dummies](https://github.com/EspressoSystems/espresso-for-dummies).
Take the file layout from there and the image tag, modules and environment from
this page.

### Modules

| Storage                        | Command                                                         |
| ------------------------------ | --------------------------------------------------------------- |
| SQLite (`EMBEDDED_DB=true`)    | `espresso-node -- http -- query -- light-client`                 |
| Postgres (`EMBEDDED_DB=false`) | `espresso-node -- storage-sql -- http -- query -- light-client`  |

With `ESPRESSO_NODE_EMBEDDED_DB=true` the entrypoint supplies the storage
module itself. Passing `storage-sql` again fails with
`optional module storage-sql can only be started once`; passing `storage-fs`
silently overrides SQLite. With the query module enabled, the catchup, status
and state-signature routes are served without being listed.

**Keep `light-client` enabled.** It serves leaves, headers and stake tables that
clients verify against the light client contract on Ethereum — this is how other
nodes catch up without trusting the node they fetch from. The more operators
serve it, the less catch-up depends on any single provider.

A validator that does not serve the query API uses `-- status -- catchup`
instead of `-- query -- light-client`. It still needs SQL storage. Without
`status` the node exposes **no consensus metrics at all** and none of the alerts
in the monitoring guide work. This configuration is not recommended.

`storage-fs` supports neither pruning nor state catch-up. Use SQL storage for
any node running the query module.

---

## 5. Register the validator

Registration associates the node's consensus keys with an Ethereum address in
the stake table contract. **That address receives commission and does not exist
on the node itself** — the Ethereum wallet is entirely separate from the node
key mnemonic in step 2.

```bash
export L1_PROVIDER=https://<your-ethereum-rpc>
export STAKE_TABLE_ADDRESS=0xCeF474D372B5b09dEfe2aF187bf17338Dc704451
export ACCOUNT_INDEX=0
export COMMISSION=5.00
export METADATA_URI=https://<your-host>/espresso-metadata.json
export P2P_ADDR=<your-host>:9977

# Load consensus material from the key file; never paste it on a command line.
export CONSENSUS_PRIVATE_KEY=$(grep '^ESPRESSO_NODE_PRIVATE_STAKING_KEY=' /opt/espresso/keys/0.env | cut -d= -f2-)
export STATE_PRIVATE_KEY=$(grep '^ESPRESSO_NODE_PRIVATE_STATE_KEY=' /opt/espresso/keys/0.env | cut -d= -f2-)
export X25519_KEY=$(grep '^ESPRESSO_NODE_PUBLIC_X25519_KEY=' /opt/espresso/keys/0.env | cut -d= -f2-)

docker run --rm -e L1_PROVIDER -e STAKE_TABLE_ADDRESS -e MNEMONIC -e ACCOUNT_INDEX \
    -e CONSENSUS_PRIVATE_KEY -e STATE_PRIVATE_KEY \
    -e X25519_KEY -e P2P_ADDR \
    ghcr.io/espressosystems/espresso-network/staking-cli:main \
    staking-cli register-validator \
    --commission "$COMMISSION" \
    --metadata-uri "$METADATA_URI"
```

| Variable                | Meaning                                                                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `L1_PROVIDER`           | RPC endpoint for the network's L1 (Ethereum, or Sepolia for Decaf).                                                                |
| `STAKE_TABLE_ADDRESS`   | Stake table address for the network.                                                                                               |
| `MNEMONIC`              | Ethereum mnemonic; combined with `ACCOUNT_INDEX` to derive the signing wallet.                                                     |
| `CONSENSUS_PRIVATE_KEY` | Node staking key, `BLS_SIGNING_KEY~…`.                                                                                             |
| `STATE_PRIVATE_KEY`     | Node state key, `SCHNORR_SIGNING_KEY~…`.                                                                                           |
| `X25519_KEY`            | Node x25519 **public** key, `X25519_PK~…`.                                                                                         |
| `P2P_ADDR`              | `host:port` peers dial, e.g. `validator.example.com:9977`.                                                                         |
| `COMMISSION`            | Percentage points, up to 2 decimals, `0.00`–`100.00`. `12.34` = 12.34%. The remainder goes proportionally to delegators.           |
| `METADATA_URI`          | URL hosting validator metadata in JSON or OpenMetrics format.                                                                      |

`staking-cli` also accepts a raw private key (`PRIVATE_KEY`) or a Ledger
(`--ledger --account-index N`). **Use a Ledger or a dedicated signing host for
mainnet.**

Constraints:

- the signing account needs L1 gas;
- each BLS key can be registered only once;
- each Ethereum account can register only one validator — a second validator
  requires a different account index or mnemonic;
- the P2P address must be publicly routable; `staking-cli` rejects addresses
  that are not, unless `--skip-reachability-check` is passed.

A successful registration prints the transaction hash and a
`ValidatorRegisteredV3` event. The event shows commission in basis points, so
`1234` is the `12.34` passed on the command line.

**Registered values take 2 to 3 epochs to become active in consensus.** One
epoch is roughly 24 hours.

### Validator metadata

```json
{
  "pub_key": "BLS_VER_KEY~...",
  "name": "POSTHUMAN",
  "description": "Professional validator operations.",
  "company_name": "POSTHUMAN",
  "company_website": "https://posthuman.digital/",
  "client_version": "20260910",
  "icon": {
    "24x24": { "@1x": "https://example.com/icon-24.png" }
  }
}
```

Serve it over HTTPS at a stable URL, then preview it before registering:

```bash
docker run --rm ghcr.io/espressosystems/espresso-network/staking-cli:main \
    staking-cli preview-metadata --metadata-uri "$METADATA_URI"
```

---

## 6. Verify

Service state alone is not evidence. Check consensus movement and the on-chain
registration.

```bash
# Consensus is advancing.
curl -fsS localhost:8080/v1/status/metrics | grep -E '^consensus_(current_view|last_decided_view) '
sleep 30
curl -fsS localhost:8080/v1/status/metrics | grep -E '^consensus_(current_view|last_decided_view) '

# Seconds since the last decide — the single best liveness signal.
curl -fsS localhost:8080/v1/status/time-since-last-decide

# What the stake table actually holds for this validator.
docker run --rm ghcr.io/espressosystems/espresso-network/staking-cli:main \
    staking-cli --network mainnet stake-table-entry --address "$VALIDATOR_ADDRESS"
```

Both views must advance between the two reads. `stake-table-entry` must show
`Status: Active`, the x25519 public key from your key file, and the exact P2P
address you registered. `not set` for either value means the validator predates
the V3 stake table and peers cannot dial it at all.

`/healthcheck` is a static liveness probe for the HTTP server. **It does not
reflect consensus health.** Never use it as the only health signal.

Confirm inbound P2P from outside the host:

```bash
nc -d -w3 <your-public-host> 9977 | xxd     # expect: 0001 0001
```

Four bytes must come back on a bare connection — cliquenet is a server-first
protocol. Empty output means a closed port, a byte-buffering middlebox, or a
node that is not listening. Full triage is in the
[security guide](/node-ops/espresso/security-hardening) and in
[Debug P2P Connectivity](https://docs.espressosys.com/network/developer/operators/run-a-node/p2p-troubleshooting).

---

## 7. Stake, rewards and lifecycle

A registered node participates only once ESP is delegated to it. Participation
is limited to a dynamic, permissionless set of **100 nodes**: in each epoch
(~24 h) the 100 nodes with the most delegated stake form the active set.

On mainnet, delegations come from any ESP holder and operators can bootstrap by
delegating to their own node. On Decaf, ESP is not publicly distributed — ask
the Espresso team for a delegation in `#decaf-node-ops` on Discord once the node
is registered and running.

### Delegation timing

| Event                 | Timing                                                      |
| --------------------- | ----------------------------------------------------------- |
| Delegation active     | 2 epochs after the L1 transaction is finalized              |
| Minimum delegation    | 1 ESP                                                       |
| Undelegation escrow   | ~7 days, then the withdrawal can be claimed                 |
| Effective stake drop  | 2 epochs after L1 finalization                              |
| Pending undelegations | One per validator at a time — claim before starting another |

Delegate, undelegate and claim withdrawals through the staking UI with MetaMask
or Ledger: <https://stake.espresso.network/> (Decaf:
<https://stake.decaf.espresso.network/>).

### Rewards

Validators and delegators accrue rewards every block their validator proposes.
**Rewards do not auto-compound** — claim manually and re-delegate if desired.
The claim transaction interacts with the Reward Claim contract on the L1. The
`staking-cli` equivalents are useful for scripting and multisig flows:

```bash
export ESPRESSO_URL=https://query.main.net.espresso.network

docker run --rm -e MNEMONIC -e ACCOUNT_INDEX -e L1_PROVIDER -e STAKE_TABLE_ADDRESS -e ESPRESSO_URL \
    ghcr.io/espressosystems/espresso-network/staking-cli:main \
        staking-cli unclaimed-rewards

docker run --rm -e MNEMONIC -e ACCOUNT_INDEX -e L1_PROVIDER -e STAKE_TABLE_ADDRESS -e ESPRESSO_URL \
    ghcr.io/espressosystems/espresso-network/staking-cli:main \
        staking-cli claim-rewards
```

The ESP token address is read from the stake table contract.

### Rotate registered values

Everything registered on-chain can be changed later. Each command is signed by
the same Ethereum wallet that registered the validator and takes
`-e MNEMONIC -e ACCOUNT_INDEX -e L1_PROVIDER -e STAKE_TABLE_ADDRESS`.

| Value                      | Command                 |
| -------------------------- | ----------------------- |
| Staking key and state key  | `update-consensus-keys` |
| x25519 key and P2P address | `update-network-config` |
| x25519 key only            | `update-x25519-key`     |
| P2P address only           | `update-p2p-addr`       |
| Commission                 | `update-commission`     |
| Metadata URI               | `update-metadata-uri`   |

> **Consensus key rotation is time-shifted.** New keys become active in the
> **third epoch** after `update-consensus-keys` runs. Update the node's key file
> at that point, **not immediately** — swapping early takes the node out of
> consensus. If the signing keys are held offline, sign in advance and pass the
> result with `--node-signatures signatures.json`.

After rotating the x25519 key or P2P address, the node's
`ESPRESSO_NODE_PRIVATE_X25519_KEY` must match the newly registered public key,
and `ESPRESSO_NODE_CLIQUENET_BIND_ADDRESS` must use the same port as the
registered address.

Commission limits, enforced by the contract and adjustable by its admin:

- one **increase** per `minCommissionIncreaseInterval` (7 days at deployment);
- increases capped at `maxCommissionIncrease` (500 bps = 5 percentage points);
- decreases are neither rate-limited nor capped, and do not reset the timer;
- the new value must differ from the current one, or the call reverts with
  `CommissionUnchanged`.

### Deregister

Two steps, ~7 days apart:

```bash
# 1. Leave the active set immediately and unbond all delegators.
docker run --rm -e MNEMONIC -e ACCOUNT_INDEX -e L1_PROVIDER -e STAKE_TABLE_ADDRESS \
    ghcr.io/espressosystems/espresso-network/staking-cli:main \
        staking-cli deregister-validator

# 2. After the exit escrow, return the principal to the operator address.
docker run --rm -e MNEMONIC -e ACCOUNT_INDEX -e L1_PROVIDER -e STAKE_TABLE_ADDRESS \
    ghcr.io/espressosystems/espresso-network/staking-cli:main \
        staking-cli claim-validator-exit --validator-address "$VALIDATOR_ADDRESS"
```

**Claim accumulated rewards first.** Deregistration does not claim them for you.

---

## 8. Storage and retention

Two independent storage systems with separate lifecycles. Operators normally
configure only the second.

**Consensus storage** is a bounded working set, not accumulating history. Every
validator reconstructs the full block payload for every view, writes it, and
deletes the rows as each view decides. Garbage collection is automatic and
view-based: about 1 GB of database, roughly one week of views retained with a
floor near three days. This applies to every validator, including one running
without the query module — size such a node for **write throughput**, one
full-payload write and delete per view, not for accumulated history.

**Query database** is the historical database added by the query module.
Pruning is **off by default**, so an unconfigured query node retains everything.
Setting both target and minimum retention to `14d`, as above, makes two weeks a
hard window rather than a target; the `STATE_` variables cover the Merklized
state tables, which otherwise prune at the 7-day default.

Durations take one integer and one unit from `ns`, `mc`, `ms`, `s`, `m`, `h`,
`d`, `w`, or a colon form (`hh:mm`, `hh:mm:ss`). A bare number of seconds is
rejected. `14d` and `2w` are equivalent.

| Variable                                 | Default | Meaning                                                             |
| ---------------------------------------- | ------- | ------------------------------------------------------------------- |
| `ESPRESSO_NODE_PRUNER_PRUNING_THRESHOLD` | `3TB`   | Database size above which the pruner deletes past target retention. |
| `ESPRESSO_NODE_PRUNER_MAX_USAGE`         | `8000`  | Basis points of the threshold to prune back to (80%).               |
| `ESPRESSO_NODE_PRUNER_INTERVAL`          | `5400s` | Time between pruner runs; sleeps one interval before the first run. |
| `ESPRESSO_NODE_PRUNER_BATCH_SIZE`        | `1000`  | Block heights deleted per transaction.                              |

> Setting any retention variable **without** `ESPRESSO_NODE_DATABASE_PRUNE=true`
> has no effect — the pruner configuration is only built when pruning is on.

> Pruning does not shrink the database to the retention window. The hash table
> and the aggregate table are never deleted by the pruner, and Merkle state
> pruning keeps the newest node at every path indefinitely. On Postgres the
> pruner skips `VACUUM`, so space returns to Postgres for reuse but not to the
> filesystem. **Provision disk for peak usage, not for the retention window.**

### Backends

|                         | SQLite (`EMBEDDED_DB=true`)                       | Postgres                                 |
| ----------------------- | ------------------------------------------------- | ---------------------------------------- |
| Deployment              | Single container                                  | Requires operating a Postgres server     |
| Reclaiming pruned space | Returns it to the filesystem (incremental vacuum) | Returns it to Postgres for reuse only    |
| Query concurrency       | Shares the node's connection pool                 | Separate tunable query pool              |
| Suited to               | Most validators                                   | Nodes serving heavy external query load  |

`ESPRESSO_NODE_PRUNER_INCREMENTAL_VACUUM_PAGES` (default `8000`) sets how many
pages each SQLite vacuum reclaims; it has no effect on Postgres.

**Archival node:** run the query module with no pruning variables.
`ESPRESSO_NODE_ARCHIVE=true` additionally clears the pruning watermark so the
node backfills missing data from peers — this is what turns a pruned database
into a full one. It conflicts with `ESPRESSO_NODE_DATABASE_PRUNE`.

---

## 9. Upgrades

1. Read the release notes for the new tag in
   [espresso-network/releases](https://github.com/EspressoSystems/espresso-network/releases).
2. Record the running tag:
   `curl -fsS localhost:8080/v1/status/metrics | grep consensus_version`.
3. Pin the new tag in the Compose file — never `:latest` or a floating tag.
4. `docker compose pull && docker compose up -d`.
5. Watch for database migrations; they are IO-bound and can take a while. More
   IOPS temporarily makes them substantially faster.
6. Verify both views advance again and `consensus_version{desc=…}` reports the
   intended tag.

Keep the previous tag and the previous `.env` available for rollback. Do not
delete the storage volume as part of an upgrade.

---

## 10. TCP tuning (optional)

Consensus traffic runs over TCP. The node sets `TCP_NODELAY` and its own
keepalive policy but does not size socket buffers, so kernel autotuning bounds
are the operator's to set. Apply this when the validator connects across
long-haul links.

`/etc/sysctl.d/espresso-opts.conf`:

```
net.ipv4.tcp_congestion_control=bbr
net.ipv4.tcp_rmem=8192 262144 67108864
net.ipv4.tcp_wmem=4096 16384 536870912
net.ipv4.tcp_adv_win_scale=0
net.ipv4.tcp_notsent_lowat=131072
net.ipv4.tcp_slow_start_after_idle=0
```

```bash
sudo sysctl -p /etc/sysctl.d/espresso-opts.conf
```

This affects **all** TCP connections on the machine. To scope it to the node
instead, put the same keys under `sysctls:` in the Compose service.

---

## Next

- [Monitoring](/node-ops/espresso/monitoring) — metrics, alert thresholds and
  participation scoring.
- [Security hardening](/node-ops/espresso/security-hardening) — key custody, exposure, P2P triage
  and safe operational procedure.

## Official resources

- Run a Validator Node: <https://docs.espressosys.com/network/developer/operators/run-a-node>
- Networks & contracts: <https://docs.espressosys.com/network/network/networks>
- Debug P2P connectivity: <https://docs.espressosys.com/network/developer/operators/run-a-node/p2p-troubleshooting>
- `staking-cli` README: <https://github.com/EspressoSystems/espresso-network/blob/main/staking-cli/README.md>
- Compose examples: <https://github.com/EspressoSystems/espresso-for-dummies>
- Discord: <https://discord.gg/espresso>
