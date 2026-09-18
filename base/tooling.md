# Base Operator Tooling

Four things are worth installing. One of them is first-party and does most of
the work.

---

## `basectl` — the operator console

First-party, shipped from `base/base`, read-only for everything a follower node
needs. If you install one tool, install this one.

```bash
curl -fsSL https://raw.githubusercontent.com/base/base/main/baseup/install | bash
baseup -i v1.4.0 --bin basectl
basectl --version
```

### What it replaces

| Instead of | Run |
|---|---|
| hand-rolled `optimism_syncStatus` + `eth_syncing` + tip comparison | `basectl sync-status` |
| a checklist of curl commands | `basectl doctor` |
| `eth_getBlockByNumber` with hex decoding | `basectl block latest` |
| grepping logs for peer counts | `basectl p2p info` |
| watching a releases page | `basectl monitor upgrades` |

### `basectl doctor`

The single most useful command on this page. Read-only, one row per check,
exits `1` if any check fails and `0` when checks only pass, warn or **skip**.

```bash
basectl -c mainnet doctor --el-rpc http://127.0.0.1:8545 --cl-rpc http://127.0.0.1:7545 --json
```

It checks declared network against live chain ID, P2P endpoint sanity, canonical
bootnode configuration, telemetry-backed external EL and CL reachability, EL and
CL peer counts, local head against the public tip, safe-head recency, optional
`reth.toml` limits, consensus-node RPC presence, and L1 RPC reachability.

Thresholds, all overridable:

| Flag | Default |
|---|---|
| `--peer-warn-threshold` | `5` |
| `--head-lag-warn-blocks` | `10` |
| `--head-lag-fail-blocks` | `20` |
| `--safe-recency-warn-blocks` | `150` |
| `--safe-recency-fail-blocks` | `300` |
| `--tip-tolerance` | `5` |

**Always pass `--cl-rpc`.** The built-in mainnet preset expects the consensus
node at `http://127.0.0.1:9545`; the Compose stack publishes it on `7545`.
Without the flag, the CL-dependent checks are skipped with a hint — and a cron
job reading only the exit code will report a healthy node while never having
looked at derivation.

### `basectl` in a cron

```bash
#!/usr/bin/env bash
set -euo pipefail
out=$(basectl -c mainnet doctor \
  --el-rpc http://127.0.0.1:8545 \
  --cl-rpc http://127.0.0.1:7545 --json) || {
    echo "$out" | jq -r '.checks[] | select(.status=="fail") | "\(.name): \(.message)"'
    exit 1
  }
echo "$out" | jq -r '.summary'
```

### Commands that mutate

`basectl p2p add-peer`, `remove-peer`, `ban`, `unban`, `unban-all`, and the
whole `conductor`, `sequencer` and `proofs` groups change state. None of them
belong in routine operation of a follower node. `conductor` and `sequencer`
operate HA sequencer clusters — not something a public node runs.

---

## `baseup` — the release installer

```bash
baseup                      # latest — avoid
baseup -i v1.4.0 --bin all  # pinned — do this
baseup verify-release -i v1.4.0
baseup --update
```

Installs `base`, `base-reth-node`, `base-consensus` and `basectl` to
`~/.base/bin` (override with `BASEUP_HOME`). Never uses `sudo`.

It does real verification of every archive: `sha256`, a GPG signature against
the pinned Base Releases key with fingerprint
`5EFE7BCFCD85682711F9FC30904841FFEBD38BAD`, and GitHub SLSA provenance when
`gh` is installed and authenticated. `verify-release` runs those checks without
installing anything.

Two rules: pin with `-i`, and never pass `--unsafe-skip-verify` on a production
host. The residual risk is the bootstrap `curl | bash` from `main` — read
`baseup/install` before running it, or install once on a machine you trust and
copy the binary across.

---

## `base-reth-node download` — the snapshot client

Not a separate tool, but the only supported way to fetch a V2 snapshot. Covered
in full on the **Snapshots** tab.

```bash
base-reth-node download --full --datadir ./reth-data --chain base --resumable
```

Segmented, resumable and idempotent. Do not reach for `wget`.

---

## Third party: `base-node-helper`

A community CLI that wraps `docker compose` with preflight checks and health
notifications. Not maintained by Base.

```
bnh init      bnh doctor    bnh start
bnh stop      bnh status    bnh monitor
bnh upgrade   bnh down
```

`bnh start` refuses to launch on a failed preflight: Docker daemon running,
ports `30303` and `9222` free, ≥ 500 GB disk, disk write speed above a
threshold, NTP offset under 1 s, L1 RPC reachable, peer count above a minimum.
`bnh monitor` polls every 60 s and notifies Discord or a webhook only on state
change.

The preflight idea is sound, and "refuse to start rather than start badly" is
the right default. Three things to weigh before installing it:

- **It reads your `.env`.** That file holds your L1 provider credential and your
  engine JWT. Anything that parses it and also talks to a Discord webhook has
  both in process memory by design.
- **Install by piped remote script.** The published install is
  `curl … | sh` from `main`. On a production host, clone, read, pin a commit and
  build from source with Go 1.23+.
- **Its 500 GB disk threshold is a floor, not a target.** Size from the formula
  in **Pruning & Storage**, not from a tool's minimum.

`basectl doctor` covers most of the same health surface, is first-party, and
never reads your secrets. Prefer it. Use `bnh` if you specifically want the
start-time gating and the change-only notifications, and you have read the
source.

---

## What you still need to build yourself

No tool on this page does these, and all three are on the **Monitoring** tab:

- **An external prober.** Everything above runs on or near the node. A check
  that dies with the host is not a check.
- **A version-drift alert.** Compare the running tag against
  `api.github.com/repos/base/base/releases/latest` daily. There is no
  in-protocol upgrade signal on Base and no governance proposal to watch.
- **A safe-head lag alert.** `basectl doctor` evaluates it at the moment you run
  it. A time series is what shows you derivation degrading before it stops.

---

## Related

- **Monitoring** — thresholds, Prometheus scrape config, the external prober
- **Useful Commands** — the raw RPC calls behind these tools
- **Upgrades** — release watching, and why it is manual
