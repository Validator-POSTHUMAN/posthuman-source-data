# Mina Mainnet Node Installation — Debian Package and systemd

This is the **package + systemd** path. For the container path see the
**Install (Docker)** guide; the two produce the same node and the choice is
purely operational.

Mina is not a Cosmos SDK chain. There is no Cosmovisor, no `priv_validator_key.json`,
no jailing and no slashing. The validator role is called a **block producer**,
its identity is an ordinary MINA account, and the private key has to be online
and unlocked for the node to produce anything. Host security *is* key security.

## What is current

Read these from the release, not from memory — Mina's package version, chain ID
and commit move together and a mismatch is the usual cause of "my node syncs but
nothing happens".

| Item | Mainnet value |
|---|---|
| Release | `4.0.0-mainnet-mesa` (stable, 2026-09-03) |
| Debian package | `mina-mainnet=4.0.0-6850301` |
| Chain ID | `0718f61ab88f9d0fa643ff4dc3a3d5998dd6d51a6008b2b0339b0dbb26133886` |
| Git SHA-1 | `685030107ff328e59936410a0e72ddaca59cb9d6` |
| Config file | `/var/lib/coda/config_68503010.json` |
| Peer list | `https://bootnodes.minaprotocol.com/networks/mainnet.txt` |

The Mesa upgrade changed consensus timing. Anything you read that says "3-minute
slots" or "14-day epochs" predates it. Live values, read from a synced node on
2026-09-17:

| Parameter | Value |
|---|---|
| Slot duration | 90 s |
| Slots per epoch | 7140 |
| Epoch duration | ~7.44 days |
| `k` (confirmation depth) | 290 blocks |
| Post-fork genesis | 2026-09-03 18:00:00 UTC |

Verify for yourself against any node:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { chainId commitId consensusConfiguration { slotDuration slotsPerEpoch epochDuration k } } }"}' | jq
````

## Requirements

| Role | RAM | CPU | Disk |
|---|---|---|---|
| Block producer | 32 GB | 8 cores, **BMI2 + ADX + AVX required** | 64 GB |
| SNARK coordinator | 32 GB | 8 cores | 64 GB |
| SNARK worker | 32 GB | 4 cores / 8 threads per worker, BMI2 + ADX + AVX | 64 GB |
| Archive node | 32 GB | 8 cores | 64 GB + database growth |

- **x86-64 only.** ARM and Raspberry Pi do not work, and no amount of
  configuration changes that.
- Supported: Debian 11/12, Ubuntu 20.04/22.04/24.04. Ubuntu 20.04 and Debian 11
  are EOL and will be dropped in future releases — start new hosts on 24.04 or
  Debian 12.
- NTP must be running. Consensus is slot-timed; clock drift costs you blocks.
- The official minimum (8 cores / 16 GB) is a floor, not a target. Operators
  who produce reliably run 16 cores / 32 GB or better, because a block that is
  not built and gossiped inside the 90-second slot is simply lost.

## Install

````bash
sudo rm -f /etc/apt/sources.list.d/mina*.list
echo "deb [trusted=yes] http://packages.o1test.net $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/mina.list
sudo apt-get update
sudo apt-get install --yes curl unzip jq
sudo apt-get install --yes --allow-downgrades mina-mainnet=4.0.0-6850301
````

Pin the exact version as shown. An unpinned `mina-mainnet` will follow the
repository and can move your node across a fork boundary during an unattended
`apt upgrade`.

Verify:

````bash
mina version
````

The output must include a `Commit` line matching the SHA-1 in the table above.

## Create the block producer key

Full key handling — hot/cold split, Ledger, backups, the libp2p key — is in the
**Keys** guide. The minimum to get a node running:

````bash
mkdir -p ~/keys && chmod 700 ~/keys
mina advanced generate-keypair --privkey-path ~/keys/my-wallet
chmod 600 ~/keys/my-wallet
````

You are prompted for a password. It is required at every start, it is never
recoverable, and losing it loses the producer identity along with everything
delegated to it. Store the key file and the password separately and offline.

Confirm the key is usable before you build anything on top of it:

````bash
mina advanced validate-keypair --privkey-path ~/keys/my-wallet
````

## Configure the service

The package installs a **user** unit at `/usr/lib/systemd/user/mina.service`.
It reads `~/.mina-env`, and everything you want to pass to the daemon goes into
`EXTRA_FLAGS` in that file.

````bash
cat > ~/.mina-env <<'EOF'
PEERS_LIST_URL=https://bootnodes.minaprotocol.com/networks/mainnet.txt
MINA_PRIVKEY_PASS="your-key-password"
LOG_LEVEL=Info
FILE_LOG_LEVEL=Debug
EXTRA_FLAGS="--block-producer-key /home/YOUR_USER/keys/my-wallet --metrics-port 6060"
EOF
chmod 600 ~/.mina-env
````

Three things about this file that cost people time:

- **Override `PEERS_LIST_URL`.** The package bakes in the legacy
  `storage.googleapis.com/mina-seed-lists/mainnet_seeds.txt`. It still resolves,
  but the maintained list is the `bootnodes.minaprotocol.com` one. The unit sets
  the default with `Environment=` and then reads `~/.mina-env`, so your line wins.
- **Passwords with shell metacharacters must be quoted.** A `$` in an unquoted
  password is the most common "my node crashes every few minutes" cause.
- `--block-producer-key` is deprecated in favour of the `MINA_BP_PRIVKEY`
  environment variable. Both work today; the flag is what most existing tooling
  still emits. Do not pass both `--block-producer-key` and
  `--block-producer-pubkey`.

Start it:

````bash
systemctl --user daemon-reload
systemctl --user enable --now mina
sudo loginctl enable-linger "$USER"
````

`enable-linger` is not optional. Without it the user manager — and your node —
stops when you log out.

## Open the firewall

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8302/tcp
sudo ufw enable
````

`8302/tcp` is the only port that belongs on the public internet. Port `8301`
(client RPC and SNARK coordinator) and port `3085` (GraphQL) must never be
reachable from outside the host. Details, including the Hetzner "netscan
detected" egress rules, are in the **Security hardening** guide.

## Verify

````bash
mina client status
````

Bootstrap timeline on a fresh host:

| Time after start | Expected |
|---|---|
| 0 – 5 min | `mina client status` may refuse to connect while the daemon initialises |
| 5 – 25 min | `Sync status: Bootstrap`, then `Catchup` |
| ~30 min | `Sync status: Synced` |

Check four fields, not one:

- `Sync status: Synced`
- `Chain id` equals the mainnet chain ID above — this is the only proof you
  joined the network you intended to join
- `Block height` equals `Max observed block length`
- a non-trivial peer count

During catchup the block height does **not** climb steadily; it stays flat and
then jumps. That is normal and is not a stuck node. See **Troubleshooting**.

Confirm the daemon actually loaded your producer key:

````bash
mina client status | grep -i "block producer"
mina accounts list
````

`Block producers running: 1 (B62q...)` is the line that matters. A synced node
with `0` producers is a spectator.

## Follow the logs

````bash
journalctl --user -u mina -n 200 -f
tail -f ~/.mina-config/mina.log
````

## Next steps

- **Keys** — hot/cold split, libp2p key, backups, Ledger
- **Block producer** — coinbase receiver, stake latency, proving production
- **SNARK worker** — the second, independent earning role
- **Delegation program** — uptime tracking and the payout obligation you take on
- **Monitoring**, **Security hardening**, **Upgrades**

## Sources

- [docs.minaprotocol.com — installing on Ubuntu and Debian](https://docs.minaprotocol.com/node-operators/validator-node/installing-on-ubuntu-and-debian)
- [docs.minaprotocol.com — connect to Mainnet or Devnet](https://docs.minaprotocol.com/node-operators/validator-node/connecting-to-the-network)
- [docs.minaprotocol.com — requirements](https://docs.minaprotocol.com/node-operators/validator-node/requirements)
- [Mina 4.0.0 Mesa mainnet release notes](https://github.com/MinaProtocol/mina/releases/tag/4.0.0-mainnet-mesa)
- [MinaProtocol/mina — `scripts/mina.service`](https://github.com/MinaProtocol/mina/blob/4.0.0-mainnet-mesa/scripts/mina.service)
