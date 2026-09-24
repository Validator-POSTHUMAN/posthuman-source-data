# Logos Blockchain Testnet — Monitoring

A Logos node is not a Cosmos validator. There is no missed-block counter, no
signing window, no jail state and no slashing. Cryptarchia is a private
proof-of-stake protocol: proposer identity and stake are hidden behind
zero-knowledge proofs, block proposal is a probabilistic lottery weighted by
your stake, and a node that is running, synced and funded is participating even
on a day it proposes nothing.

That shape decides what is worth an alert. **Absence of your blocks is not a
fault.** The four things that are: the node stopped, it stopped advancing, it
lost its peers, or its stake stopped counting.

This page lists what to poll, what to page on, and what each signal means. Every
endpoint below is the local HTTP API on `127.0.0.1:8080`, the same one the
[installation guide](install-guide.md) uses.

---

## 1. The four signals that matter

| Signal | Source | Page when |
|---|---|---|
| Service alive | `systemctl is-active logos.service` | not `active` |
| Chain advancing | `/cryptarchia/info` → `height` | unchanged across three consecutive polls |
| Connected | `/network/info` → `n_peers` | `0`, or below your floor for two polls |
| Stake counting | `/wallet/<public-key>/balance` | drops to `0`, or below the amount you funded |

A five-minute poll interval is enough for all four: blocks arrive roughly every
ten seconds, so three polls without a height change is a real stall rather than
jitter.

---

## 2. Sync state and progress

```bash
curl -fsS http://127.0.0.1:8080/cryptarchia/info | jq .
```

```json
{
  "mode": "Online",
  "height": 44812,
  "slot": 118733
}
```

- `mode` is `Bootstrapping` while the node catches up and `Online` once it is
  synced. A node that has been `Bootstrapping` for hours after a restart is
  either short of peers or stuck on a circuit/binary mismatch — check both
  before anything else.
- `height` is confirmed blocks and is the liveness signal. Record the previous
  value and alert on *no change*, not on an absolute number: there is no public
  head height to compare against the way a Cosmos `catching_up` flag gives you.
- `slot` counts elapsed time intervals and always advances, whether or not your
  node is healthy. **Never use `slot` as a liveness signal** — it moves on a
  dead chain view too.

Compare your height against the fleet on the
[Logos Testnet Dashboard](https://testnet.blockchain.logos.co/web/) when you
need an external opinion.

---

## 3. Peers

```bash
curl -fsS http://127.0.0.1:8080/network/info | jq '.n_peers'
```

Cryptarchia gossip runs over QUIC on **UDP 3000**. Two failure modes look
identical from inside the node and are not:

- **Zero peers with a reachable port** — the bootstrap peers you passed to
  `init` are gone or changed. Re-check the current peer list in the official
  release notes before re-initialising anything.
- **Zero peers with an unreachable port** — the far more common case. UDP is
  quietly dropped by many default firewall and cloud security-group setups, and
  nothing in the node logs says so. Prove the port from outside the host:

```bash
# From another machine, not from the node itself.
nc -u -z -w3 <node-public-ip> 3000 && echo "udp/3000 reachable"
```

A node with a handful of peers is normal. Set your alert floor from your own
observed steady state rather than from a number in a document; on a testnet the
fleet size moves.

---

## 4. Stake, which is a balance here

Consensus stake on the testnet *is* the funded faucet balance, and it starts
counting only after UTXO aging — about two epochs, roughly three and a half
hours. So a freshly funded node that proposes nothing for an afternoon is
working correctly.

```bash
PUBKEY=$(grep -A3 known_keys ~/logos-blockchain/user_config.yaml | grep -oE '[0-9a-fx]{16,}' | head -1)
curl -fsS "http://127.0.0.1:8080/wallet/$PUBKEY/balance" | jq .
```

Alert on the balance falling, not on it being below a target. A drop means
either the UTXO moved or the node is reading a different key than the one you
funded — which happens after an unplanned `init`, because `init` writes **fresh
keys**. See the [security guide](security-hardening.md).

---

## 5. Logs worth alerting on

```bash
journalctl -u logos.service -f
```

Grep for the two classes that are always fatal in practice rather than trying to
parse normal output:

- `panic` and `fatal` — the node is down or about to be; the systemd
  `Restart=on-failure` in the installation guide will loop it if the cause is
  persistent, so alert on the restart count as well.
- circuit and version errors mentioning `circuits`, `verifying key` or
  `proof` — the node binary and the ZK circuits are a matched pair. A binary
  upgraded without its circuits produces exactly this and never proposes.

```bash
systemctl show -p NRestarts logos.service
```

`NRestarts` climbing is the cheapest crash-loop detector there is. Page on any
increase; a healthy node sits at a fixed number for weeks.

---

## 6. Release drift

Logos publishes node binaries and ZK circuits as separate archives on the same
[releases page](https://github.com/logos-blockchain/logos-blockchain/releases),
and a testnet release can be breaking — the upgrade procedure in the
installation guide includes deleting state, config and circuits when the release
notes say so.

Check the deployed pair against the published one on a schedule, daily is
enough, and alert on drift rather than upgrading automatically:

```bash
~/logos-blockchain/logos-blockchain-node --version
ls -d ~/.logos-blockchain-circuits
```

Never wire an auto-updater to this. A breaking release wants a read of the
release notes, a decision about state deletion, and a re-init that rewrites your
keys — none of which belongs in a timer.

---

## 7. Disk

The node stores its chain database under its working directory and the circuits
under `~/.logos-blockchain-circuits`. Alert on the filesystem holding both, at
80% and again at 90%, and remember that a breaking-release re-init needs room
for a fresh database beside the old one before you delete anything.

---

## 8. A minimal watchdog

One script, one timer, no dependencies beyond `curl` and `jq`. It holds the
previous height in a state file, which is what makes a stall detectable at all.

```bash
#!/usr/bin/env bash
set -euo pipefail
API=http://127.0.0.1:8080
STATE=/var/lib/logos-watch/height
mkdir -p "$(dirname "$STATE")"

fail() { printf 'LOGOS ALERT: %s\n' "$*" >&2; exit 1; }

systemctl is-active --quiet logos.service || fail "logos.service is not active"

info=$(curl -fsS --max-time 10 "$API/cryptarchia/info") || fail "API unreachable"
height=$(jq -er '.height' <<<"$info")
mode=$(jq -er '.mode' <<<"$info")
peers=$(curl -fsS --max-time 10 "$API/network/info" | jq -er '.n_peers')

previous=$(cat "$STATE" 2>/dev/null || echo 0)
printf '%s\n' "$height" >"$STATE"

[ "$peers" -gt 0 ] || fail "no peers — check udp/3000 from outside the host"
[ "$height" -gt "$previous" ] || fail "height stuck at $height (mode $mode)"
printf 'ok mode=%s height=%s peers=%s\n' "$mode" "$height" "$peers"
```

Route it wherever your other alerts go, and deduplicate: a stalled node
produces the same message every interval, and an alert channel that repeats it
every five minutes is one people stop reading.

**Do not let the watchdog restart the node.** A restart hides the two causes
worth knowing — a circuit mismatch and a dropped UDP port — and neither is fixed
by restarting.
