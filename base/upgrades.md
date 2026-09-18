# Base Node Upgrades

Base has no on-chain governance to watch, no upgrade proposal to vote on and no
`upgrade-info.json` to poll. Forks activate at a **timestamp hard-coded in the
client release**. If your node is on an older release when that timestamp
passes, it derives a different chain from everyone else and stops following
Base. Nothing warns you first.

So the operational question is not "how do I upgrade" — it is "how do I find out
that I must".

---

## Right now: Cobalt

| Network | Activation | Required release |
|---|---|---|
| Base Sepolia | **23 September 2026** | `v1.4.0` |
| Base Mainnet | **30 September 2026** | `v1.4.0` |

`v1.4.0` shipped on 16 September 2026 with Cobalt support in both
`base-reth-node` and `base-consensus`.

It also **deprecates `--rollup.disable-tx-pool-gossip`** as a CLI flag on
`base-reth-node`. If your entrypoint or `ADDITIONAL_ARGS` still passes it,
remove it — the flag is no longer accepted and the node will not start.

Confirm both dates against
[docs.base.org/upgrades/cobalt/overview](https://docs.base.org/upgrades/cobalt/overview)
before acting on them; activation schedules move.

What Cobalt contains, for context rather than action: B20 token-standard
improvements, validity transactions, dynamic upgrades in metrics-only mode, and
the start of the TEE migration.

### Dynamic upgrades will change this — but not yet

Cobalt introduces an Ethereum contract holding upgrade timestamps, which the EL
and CL poll over L1 RPC and apply without a restart. The intent is that future
forks no longer require a release.

It ships **in metrics-only mode** while the data is validated. Do not plan
around it. Until Base says otherwise, a fork still means a new binary, and
treating it as solved is how you miss the one after next.

---

## Watching for releases

There is exactly one authoritative source:
[github.com/base/base/releases](https://github.com/base/base/releases).

Wire it into something you actually read:

```bash
# Current running tag
docker compose config | grep -m1 'image:'

# Latest published release
curl -fsS https://api.github.com/repos/base/base/releases/latest | jq -r .tag_name
```

A daily cron comparing those two and alerting on a difference costs nothing and
is the only upgrade monitor that exists. Subscribe to the repository's release
notifications as a second channel, and join the `🛠｜node-operators` channel in
the [Base Discord](https://discord.gg/buildonbase) — fork coordination happens
there first.

`basectl monitor upgrades` shows the activation countdown and history
interactively.

### Two classes of upgrade, and the difference matters

| Class | Deadline | If you are late |
|---|---|---|
| **Fork-critical** — a release carrying a hardfork activation | hard, a wall-clock timestamp | your node leaves the canonical chain and serves wrong data to everything downstream |
| **Routine** — bug fixes, performance, features | none | nothing breaks; upgrade when convenient |

Release notes say which. `v1.4.0`'s notes open with an `IMPORTANT` block naming
the Sepolia deadline — that is what a fork-critical release looks like. Read
them; do not infer urgency from the version number.

---

## The upgrade procedure

A Base node upgrade is a container restart. There is no key to move, no state to
preserve beyond the data directory, no double-sign risk and no unbonding clock.
This is genuinely low-stakes work — the only real failure mode is doing it
late.

### 1. Read the release notes

Specifically: is it fork-critical, what is the deadline, and are any flags or
environment variables deprecated? `v1.4.0` removed a CLI flag. That class of
change turns a restart into a container that will not boot.

### 2. Upgrade Sepolia first

Base activates every fork on Sepolia roughly a week before mainnet. That week is
free rehearsal and the reason to run a Sepolia node at all. See the **Testnets**
tab.

### 3. Pin the new tag

```bash
cd /path/to/base
git pull                                  # if you build from source
export NODE_TAG=v1.4.0
docker compose pull
docker compose up -d
```

Pinning matters more than usual here. With `NODE_TAG=latest`, your node's
version changes on any restart — including an unplanned one at 3am — and you
lose the ability to say what is running. Record the tag alongside the change.

### 4. Confirm the containers actually came back

```bash
docker compose ps
docker compose logs --since 5m execution | head -40
docker compose logs --since 5m node | head -40
```

A container that exits immediately after an upgrade is almost always a removed
flag or a changed environment variable. The log line names it.

### 5. Verify against the network, not against itself

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}' \
  http://127.0.0.1:8545

curl -s -d '{"id":0,"jsonrpc":"2.0","method":"optimism_syncStatus"}' \
  -H 'Content-Type: application/json' http://127.0.0.1:7545 \
  | jq '{unsafe: .result.unsafe_l2.number, safe: .result.safe_l2.number}'

basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545
```

The check that matters after a fork is the **safe head advancing**, not the head
height. A node that fell out of consensus still receives the sequencer feed and
still increments its unsafe head; only its safe head stops. Watch it for ten
minutes before calling the upgrade done.

Also compare your head hash against a public reference. Agreeing with yourself
is not evidence.

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["safe",false]}' \
  https://mainnet.base.org | jq -r '.result.number, .result.hash'
```

### 6. Rollback

Set `NODE_TAG` back to the previous tag and `docker compose up -d`. The data
directory is compatible in both directions for routine releases.

**A fork-critical release is not rollback-able past activation.** Once the fork
is live, the old binary cannot follow the chain. Rolling back after activation
buys you nothing except a node that is definitely broken instead of possibly
broken.

---

## Missing a fork

If you find out late:

1. Upgrade immediately. Do not investigate first; the node is producing wrong
   answers for every consumer while you read logs.
2. After the upgrade, check whether the safe head recovers on its own. Usually
   it does — the node re-derives from L1 and catches up.
3. If the safe head does not advance within 30 minutes, the local database
   followed the wrong chain past the fork. Restore from a current snapshot. See
   **Snapshots**.
4. Tell whoever consumed the RPC during the gap. They cached wrong data.

There is no slashing, no penalty and no jail. The cost of a missed fork on Base
is entirely downstream: wrong answers served with full confidence.

---

## Keeping `basectl` and `baseup` current

`baseup` installs release binaries from the same repository, so they track the
node version:

```bash
curl -fsSL https://raw.githubusercontent.com/base/base/main/baseup/install | bash
basectl --version
```

A stale `basectl` compares your node against stale expectations. Update it in
the same change window as the node.

---

## Related

- **Installation Guide** — `NODE_TAG` pinning and the verification sequence
- **Monitoring** — the version-drift alert, and safe-head lag
- **Testnets** — why Sepolia earns its keep one week per fork
- **Troubleshooting** — a container that will not start after an upgrade
