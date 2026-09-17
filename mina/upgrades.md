# Mina Node Upgrades and Hard Forks

There is no Cosmovisor on Mina, no on-chain upgrade proposal and no halt height
you can query. Upgrades are announced by o1Labs as GitHub releases, and it is on
you to be running the right build when the network changes.

Two different things are called "an upgrade":

| Kind | What changes | Coordination |
|---|---|---|
| Ordinary release | binary only, same chain | upgrade when convenient |
| Hard fork | consensus rules, chain ID, often genesis | must happen at the fork point |

Getting the second one wrong does not slash you — Mina has no slashing. It
leaves you on a dead chain, producing nothing, while your own node reports
`Synced`. That is the failure to design against.

## Two hard-fork mechanisms

The Mesa upgrade (3 September 2026) introduced hard-fork automation, so both
exist today:

**Automode.** One build carries both pre-fork and post-fork logic and switches
itself at the fork slot. Nothing to do on the night.

- Debian: `mina-mainnet-automode=4.0.0-mainnet-893c877`
- Docker: `minaprotocol/mina-daemon-auto-hardfork:4.0.0-mainnet-893c877-CODENAME-mainnet`

**Legacy stop slot.** The pre-fork build runs to a fixed slot, then exits
cleanly. You install the post-fork build and start again.

- Pre-fork: `3.5.0-mainnet-stop-slot`
- Post-fork stable: `mina-mainnet=4.0.0-6850301`, Docker
  `minaprotocol/mina-daemon:4.0.0-6850301-CODENAME-mainnet`

The stop-slot exit is a **clean** exit, not a crash. With `Restart=always` the
supervisor immediately restarts the old binary, which exits again — a tidy loop
that looks like flapping. That is expected: the loop is the signal that the
binary swap is now due.

Today's mainnet state: the network is past Mesa. `4.0.0-mainnet-mesa` stable is
what you install if you are joining for the first time or still on the legacy
stop-slot build. Nodes that crossed the fork on automode do **not** need it.

## Before any upgrade

1. Read the release notes for the exact tag. Package version, Docker tag, config
   file name, chain ID and Git SHA-1 all move together.
2. Note the **rollback point**: the exact package version or image tag you are
   on now. `mina version`, or `docker inspect <container> --format '{{.Config.Image}}'`.
3. Back up `~/.mina-env` (or the compose file) and confirm your key backup is
   current. Chain data in `~/.mina-config` is disposable; the key is not.
4. Check whether the release also changes `mina-archive`. Archive and daemon
   versions must match — Mesa shipped a daemon and archive with *different*
   version strings, so read, do not assume.
5. Pin. An unpinned `mina-mainnet` under unattended upgrades can move you across
   a fork boundary at 04:00 with nobody watching.

## Debian / systemd

````bash
# rollback point
mina version
systemctl --user stop mina

sudo apt-get update
sudo apt-get install --yes --allow-downgrades mina-mainnet=4.0.0-6850301

systemctl --user daemon-reload
systemctl --user start mina
````

`--allow-downgrades` is what lets you move to an explicitly older build if the
new one misbehaves. Nothing in the package manager stops you from crossing a
fork boundary in the wrong direction, so the version string is your only guard.

## Docker

````bash
docker inspect mina --format '{{.Config.Image}}'     # rollback point
docker pull minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet
docker stop mina && docker rm mina
# recreate with the SAME volumes, key mount and flags, new tag
````

Or, with Compose: edit the `image:` line, then

````bash
docker compose up -d
````

Keep `/root/.mina-config` on its persistent volume. Losing it turns a two-minute
restart into a ~30-minute bootstrap, and across a hard fork it can mean
re-downloading state you already had.

## Verify — every field, every time

````bash
mina client status
mina version
````

| Check | Expected |
|---|---|
| `mina version` commit | matches the Git SHA-1 in the release notes |
| `Chain id` | matches the release notes for the network you intend to be on |
| `Sync status` | `Synced` (after bootstrap/catchup) |
| `Block height` | equals `Max observed block length`, and matches an external node |
| `Block producers running` | `1 (B62q…)` on a producer |
| peers | non-trivial |

Confirm height against something that is not your node:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { blockchainLength chainId commitId } }"}' | jq
````

**An upgrade is not complete until the chain ID and an external height both
check out.** A node that syncs happily to the wrong chain ID is the specific
outcome this whole procedure exists to prevent.

Then confirm from outside that a block you were scheduled to produce actually
landed — see **Monitoring**.

## Rollback

Reinstall the recorded previous version (`--allow-downgrades`) or restart the
previous image tag with the same volumes, then re-run the verification table.

Two limits to know before you rely on it:

- **After a hard fork, rollback is not a real option.** The old binary cannot
  follow the new chain. The rollback path applies to ordinary releases and to
  pre-fork mistakes.
- A newer daemon may have written state the older one does not understand. If
  the old binary refuses to start against the existing `~/.mina-config`, the
  recovery is to clear the chain cache and re-bootstrap — which is why the key
  and `.mina-env`, not the chain data, are what you back up.

## Fleet sequencing

With multiple producers on the same key — permitted on Mina, see **Block
producer** — upgrade them one at a time and let each reach `Synced` with the
correct chain ID before touching the next. There is no double-sign risk, so the
only thing that matters is never having zero healthy producers.

## Related guides

- **Installation guide** / **Install (Docker)** — the baseline both paths upgrade
- **Monitoring** — external verification and the weekly self-restart
- **Security hardening** — pinning and unattended-upgrade policy
- **Archive node** — keeping schema and daemon versions aligned

## Sources

- [Mina 4.0.0 Mesa mainnet release notes](https://github.com/MinaProtocol/mina/releases/tag/4.0.0-mainnet-mesa)
- [Mina 4.0.0 Mesa automode release notes](https://github.com/MinaProtocol/mina/releases/tag/4.0.0-mainnet)
- [Mina 3.5.0 mainnet stop-slot release notes](https://github.com/MinaProtocol/mina/releases/tag/3.5.0-mainnet-stop-slot)
- [docs.minaprotocol.com — connect to Mainnet or Devnet](https://docs.minaprotocol.com/node-operators/validator-node/connecting-to-the-network)
- [github.com/MinaProtocol/mina/releases](https://github.com/MinaProtocol/mina/releases)
