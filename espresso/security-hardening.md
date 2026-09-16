# Espresso — Security Hardening

Espresso splits a validator's secrets across two worlds: three **consensus
keys** that live on the node, and an **Ethereum wallet** that owns the
registration, the commission and the stake. They have different threat models
and must be handled differently.

Verified against the official operator documentation on 2026-09-16.

---

## 1. Key inventory

| Key                                          | Where it lives                   | What it controls                                   | Blast radius if leaked                                      |
| -------------------------------------------- | -------------------------------- | -------------------------------------------------- | ----------------------------------------------------------- |
| Staking key (BLS, `BLS_SIGNING_KEY~…`)       | Node, `0.env`                    | Signs consensus messages                           | Impersonation in consensus; equivocation from a second host |
| State key (Schnorr, `SCHNORR_SIGNING_KEY~…`) | Node, `0.env`                    | Signs finalized consensus states                   | Forged state signatures                                     |
| x25519 key (`X25519_SK~…`)                   | Node, `0.env`                    | Encrypts and authenticates P2P connections         | Peer impersonation; loss of inbound connectivity            |
| Node key mnemonic                            | Offline backup only              | Derives all three node keys                        | Everything above                                            |
| **Ethereum wallet**                          | Ledger / dedicated signing host  | Registration, commission, stake, rewards, exit     | **Funds and validator ownership**                           |

The Ethereum wallet that registers the validator is **entirely separate** from
the node key mnemonic, and the address it derives does not exist on the node.
Do not merge them, and do not store the Ethereum mnemonic on the validator host.

---

## 2. Node key custody

```bash
sudo install -d -m 0700 -o "$USER" -g "$USER" /opt/espresso/keys
chmod 600 /opt/espresso/keys/0.env
```

Mount the key directory into the container **read-only**:

```yaml
volumes:
  - /opt/espresso/keys:/mount/espresso/keys:ro
```

Rules:

- Generate keys **inside the container** (`docker run -v ./keys:/keys $IMAGE
  keygen -o /keys`). They never touch the host except through that volume.
- `keygen` writes the mnemonic and index as comments at the top of each `.env`
  file. Move the mnemonic to offline storage, then remove the comment from the
  on-disk copy.
- Never paste a private key on a command line. Read it from the key file into an
  environment variable, as the install guide does; command lines land in shell
  history and in the process table.
- Never commit `0.env`, the mnemonic, or a Compose file containing them.
- Back the key file up encrypted and offline **before** registering. Losing it
  means re-registering keys, which costs 2–3 epochs of participation.

### Never run two nodes with the same key file

Each BLS key can be registered only once, and every validator is expected to
present one consistent consensus identity. Running a second process with the
same staking key — a forgotten test container, a restored VM snapshot, a
half-finished migration — puts two signers behind one identity.

The reviewed Espresso operator documentation published as of 2026-09-16
describes no slashing mechanism. **Do not read that as permission to duplicate
keys.** Treat consensus-key uniqueness as an invariant: prove the old host
cannot sign before the new one starts. Before any migration or restore:

```bash
# On the old host — the process must be gone, not merely stopped.
docker ps -a --filter name=espresso-node
sudo ss -lntp | grep -E '9977|8080'

# From outside — the old P2P address must no longer answer.
nc -d -w3 <old-public-host> 9977 | xxd     # expect: no output
```

Only then start the node on the new host. Migrating the registered P2P address
or x25519 key is a `staking-cli` operation, not a config edit — see section 6.

### Rotation

Rotating consensus keys is **time-shifted and easy to get wrong**:

1. Generate a new key set into a separate file. Do not touch the running one.
2. Run `update-consensus-keys` from the registering Ethereum wallet.
3. The new keys become active in the **third epoch** after the command runs
   (~72 h). Leave the node on the old key file until then.
4. At that point, swap the key file and restart the node.

Swapping the file immediately takes the validator out of consensus. If the
signing keys are held offline, sign in advance and pass the result with
`--node-signatures signatures.json`.

Rotating only the x25519 key (`keygen --scheme x25519`) derives from a **new
random mnemonic** — replace both the public and private x25519 lines and
re-register the public key, or every inbound handshake fails.

---

## 3. Ethereum wallet custody

The registering wallet can change commission, rotate keys, deregister the
validator, move the stake and claim the rewards. Protect it accordingly.

- **Use a Ledger for mainnet**: `staking-cli --ledger --account-index N`.
  Mnemonic and raw private key modes exist for automation and testnets.
- If a hot key is unavoidable, keep it on a **separate signing host** that does
  not run the validator, holds no inbound services, and has its own access
  control.
- Fund it with gas only. It is not a treasury.
- Each Ethereum account can register exactly one validator — running several
  validators means several account indices or mnemonics, each with its own
  custody story.
- Keep an independent record of which account index maps to which validator.
  `claim-validator-exit --validator-address` needs the exact address, and the
  wrong one is a failed or misdirected transaction.

Rehearse every wallet operation on **Decaf** first. The commands are identical;
only the stake table address and RPC change.

---

## 4. Network exposure

| Port                     | Protocol | Direction | Exposure                            |
| ------------------------ | -------- | --------- | ----------------------------------- |
| `9977` (default)         | TCP      | Inbound   | **Public** — required for consensus |
| `ESPRESSO_NODE_API_PORT` | TCP      | Inbound   | Loopback or reverse proxy only      |
| L1 RPC / WS              | TCP      | Outbound  | To your Ethereum provider           |
| Espresso services        | TCP      | Outbound  | Query, config cache, state relay    |

The node serves **plain HTTP**. Terminate TLS in a reverse proxy if the API has
to be reachable at all.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 9977/tcp
sudo ufw enable
sudo ufw status numbered
```

The Compose file in the install guide binds the API port to `127.0.0.1`
deliberately:

```yaml
ports:
  - "9977:9977/tcp"
  - "127.0.0.1:8080:8080/tcp"
```

Publishing `8080:8080` instead exposes metrics, the healthcheck and the query
API to the internet. Docker's published ports bypass `ufw` — the bind address in
the Compose file is the real control, not the firewall rule.

Do not put an inspecting proxy in front of port `9977`. Cliquenet is a
**server-first** protocol: the accepting side writes four bytes before it has
received anything. Anything that waits for the client to speak first — a
protocol sniffer, PERMISSIVE mTLS, `tls_inspector` — deadlocks the connection.
Observing bytes in passing is harmless; buffering them is not.

If you run the query API publicly as a service, treat it as a separate product:
its own hostname, TLS, rate limiting and capacity. It is not required for
validating.

---

## 5. Host and container hardening

- Pin the exact image tag (`espresso-node:20260910`). Never `:latest`, never a
  floating tag. `consensus_version{desc=…}` tells you what is actually running.
- Do not run the container `--privileged`, and do not add capabilities it does
  not need.
- Keep the key volume read-only and the storage volume on a dedicated disk or
  dataset so a full disk cannot take the host with it.
- `stop_grace_period: 60s` so the node shuts down cleanly instead of being
  killed mid-write.
- `RUST_LOG=warn` with `RUST_LOG_FORMAT=json` and bounded log rotation. Debug
  logging on a validator is noise and disk pressure.
- SSH: keys only, no password authentication, no root login, fail2ban.
- Unattended security updates on the host; reboot windows planned, not
  incidental.
- Keep the L1 provider URL out of version control. Provider API keys live in the
  URL, so an `.env` committed by accident leaks a paid credential. Keep `.env`
  at `0600` and outside the repository.

---

## 6. P2P triage

Connectivity failures on Espresso are almost always one of three things: a
blocked or buffered port, a wrong registered value, or the wrong x25519 key.
Work the checks in this order — cheapest first.

### 6.1 Probe the port from outside

A healthy node sends a four-byte version range without being sent anything
first.

```bash
# 1. Control: no input at all — what a real peer sees.
nc -d -w3 $PUBLIC_HOST 9977 | xxd

# 2. Four bytes, as a peer sends.
printf "\x00\x01\x00\x01" | nc -w3 $PUBLIC_HOST 9977 | xxd

# 3. Five bytes: one past the typical sniffer minimum.
printf "\x00\x01\x00\x01\x00" | nc -w3 $PUBLIC_HOST 9977 | xxd
```

Healthy output from all three:

```
00000000: 0001 0001                                ....
```

| Result                                     | Meaning                                                                         |
| ------------------------------------------ | -------------------------------------------------------------------------------- |
| All three print `00 01 00 01`              | Nothing withholds bytes — the port is fine, continue to 6.2                      |
| 1 and 2 empty, 3 prints the version range  | A byte-inspecting filter with a minimum-bytes threshold is in the path           |
| All three empty, connection succeeds       | Something holds the connection without forwarding, or the node is not listening  |
| Connection refused or timeout              | Firewall, security group or port mapping — not a sniffer                         |
| Anything other than a 4-byte version range | The stream is being rewritten: TLS termination or a PROXY protocol header        |

Where `nc` has no `-d`, use `nc -w3 $PUBLIC_HOST 9977 < /dev/null | xxd`.

### 6.2 Check what is registered on-chain

```bash
docker run --rm ghcr.io/espressosystems/espresso-network/staking-cli:main \
    staking-cli --network mainnet stake-table-entry --address $VALIDATOR_ADDRESS
```

`--network` supplies the stake table address and a public Ethereum RPC. Use
`--network decaf` for Decaf and `--rpc-url` (or `L1_PROVIDER`) for your own
endpoint. `--address` defaults to the signer address — pass it explicitly when
running without a wallet configured.

Confirm `Status: Active`, that the P2P address matches the host and port 6.1
succeeded against, and that the port matches
`ESPRESSO_NODE_CLIQUENET_BIND_ADDRESS` after any port mapping. `not set` means
the validator predates the V3 stake table and peers cannot dial it at all.

### 6.3 Check the node's own x25519 key

```bash
docker compose logs espresso-node | grep -E \
  "No x25519 key provided|migrated deprecated env var|noise error: decrypt error"
```

| Log line                                                         | Cause                                                                         |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `No x25519 key provided…`                                        | No persistent key: a random ephemeral key is generated on every start         |
| `migrated deprecated env var  old="ESPRESSO_SEQUENCER_KEY_FILE"` | A legacy key file silently took over x25519 configuration                     |
| `handshake failed  err="noise error: decrypt error"` (many peers) | The node holds a different key than the one registered on-chain              |

A key file takes over x25519 configuration entirely: the key must be an
`ESPRESSO_NODE_PRIVATE_X25519_KEY=…` line **inside that file**. Setting it in
the environment instead does not work, and a key file without that line starts
with no error. A leftover `ESPRESSO_SEQUENCER_KEY_FILE` has caused exactly this
failure on mainnet — check for it even when no key file appears to be
configured.

### 6.4 Read the cliquenet metrics

See the [monitoring guide](/node-ops/espresso/monitoring) §3 for the full metric
table and how to read the numbers. The decisive question is whether the node has
**inbound** hellos: your own outbound dials can keep `peer_tasks` looking
healthy while the inbound path is completely broken.

### 6.5 Log reference

Accept-side (connections this node received):

| Message                     | Meaning                                                                            |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `handshake failed`          | Accept-side failure before the peer was identified; read `err`                      |
| `incompatible versions`     | Version ranges do not overlap, or bytes were prepended (PROXY protocol header)      |
| `party has invalid ip addr` | Source IP does not match that peer's registered P2P address — split ingress/egress  |
| `hello failed`              | Peer identified but the hello was not OK; accompanies the previous line one for one |
| `unknown party` (INFO)      | Connection from an x25519 key that is not in the stake table                        |
| `peer failure`              | An established peer connection dropped                                              |

Dial-side (connections this node initiated):

| Message                     | Meaning                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------- |
| `connect/handshake error`   | Dial failed; `err` distinguishes refused, timeout, unexpected EOF, unreachable, DNS failure |
| `hello response was not ok` | The remote identified this node and refused it — its logs carry the reason                  |
| `failed to exchange hello`  | Hello exchange timed out or errored after connecting                                        |

A middlebox holding the connection without forwarding it shows as `timeout`, not
as a refusal. That distinction is usually the whole diagnosis.

---

## 7. Operational safety rules

- **Registered values are on-chain state, not configuration.** Changing the P2P
  address or x25519 key means a `staking-cli` transaction. Editing `.env` alone
  desynchronizes the node from the stake table and breaks connectivity.
- **Changes take 2–3 epochs to take effect** (~24 h per epoch). Plan around that
  window; do not stack a second change while the first is pending.
- **Commission increases are rate-limited**: one increase per 7 days, capped at
  5 percentage points. Decreases are free and do not reset the timer. Getting
  this wrong is publicly visible to delegators.
- **Deregistration is not reversible on a whim.** It removes the node from the
  active set immediately, unbonds all delegators, and starts a ~7-day exit
  escrow before `claim-validator-exit` returns the principal. Claim accrued
  rewards **before** deregistering — deregistration does not claim them.
- **Only one undelegation can be pending per validator.** Claim each withdrawal
  before starting another from the same validator.
- **Verify before you believe.** A green `/healthcheck` and a running container
  prove nothing about consensus. Use `time-since-last-decide`, the two view
  metrics, and the participation score.

---

## 8. Metadata URI hygiene

The metadata URI is public and fetched by third parties.

- Serve it over HTTPS from a host you control, with a stable URL.
- Publish only what you intend to be public: validator name, description,
  company, website, icon, client version. No internal hostnames, no node IPs
  beyond the already-public P2P address, no contact addresses you do not want
  scraped.
- `staking-cli preview-metadata --metadata-uri …` validates before you spend
  gas. `update-metadata-uri` requires `CONSENSUS_PUBLIC_KEY` to validate the
  content at the new URL; `--skip-metadata-validation` submits without that
  check — use it only when you know why.
- Pointing the URI at the node's own `/status/metrics` publishes the metrics
  endpoint to the world. Prefer a static JSON document on a separate host.

---

## 9. Incident checklist

1. **Do not restart first.** Capture `time-since-last-decide`, both view
   metrics, `consensus_cliquenet_*` and the last 500 log lines.
2. Determine scope: current view moving while decides stall is network-wide;
   check other operators before touching your node.
3. If local: work sections 6.1 → 6.4 in order.
4. Never move, copy or re-register consensus keys during an incident without
   first proving the previous process cannot sign (section 2).
5. If a rollback is needed, roll back the **image tag and `.env`**, never the
   storage volume, and never by restoring a snapshot that also restores a key
   file onto a second live host.
6. Record what was checked, what was found, what changed and the exact
   transaction hashes of any `staking-cli` call.

---

## Official resources

- Run a Validator Node: <https://docs.espressosys.com/network/developer/operators/run-a-node>
- Debug P2P connectivity: <https://docs.espressosys.com/network/developer/operators/run-a-node/p2p-troubleshooting>
- Networks & contracts: <https://docs.espressosys.com/network/network/networks>
- `staking-cli` README: <https://github.com/EspressoSystems/espresso-network/blob/main/staking-cli/README.md>
