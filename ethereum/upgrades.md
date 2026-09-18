# Client Updates and Network Upgrades

Ethereum has no Cosmovisor, no on-chain upgrade proposal and no halt height. A
network upgrade is a slot number compiled into client releases: run a client
that knows about the fork and you follow the chain; run one that does not and
you fork off it at that slot and stop earning.

There are two different procedures here, and confusing them is how operators
miss forks.

| | Routine update | Network upgrade |
|---|---|---|
| Driver | Bug fix, performance, new flags | A fork slot on mainnet |
| Deadline | None | Hard — the slot |
| Scope | One client | **Both** clients, and every node you run |
| Risk of skipping | Low | You leave the network |

---

## 1. Fork status

| Fork | Mainnet | Status |
|---|---|---|
| Deneb | epoch 269568, 2024-03-13 | active |
| Electra (Pectra) | epoch 364032, 2025-05-07 | active |
| Fulu (Fusaka) | epoch 411392, 2025-12-03 21:49:11 UTC | **active** |
| Glamsterdam | not scheduled | next upgrade; no confirmed mainnet slot |

Values come from the `eth-clients/mainnet` config. Fusaka introduced PeerDAS and
Blob Parameter Only (BPO) forks, which raise blob throughput on their own
schedule after the main fork — **a BPO fork still needs a client that knows about
it**, so treat BPO releases as fork-critical, not as routine updates.

Where to watch, in order of authority:

1. [EF Protocol Announcements](https://blog.ethereum.org/category/protocol) —
   the announcement post carries the exact slot and the minimum client versions.
2. [eth-clients](https://github.com/eth-clients) network configuration repos —
   the fork epoch as the clients actually read it.
3. Each client's release notes.
4. [ethereum.org network upgrades](https://ethereum.org/ethereum-forks/).

Do not learn about a fork from a chat message. Subscribe to the first two.

---

## 2. Network upgrade procedure

Start at least a week before the slot.

**1. Read the announcement.** Note the exact slot, the epoch, and the minimum
version for *each* client you run — EL and CL have separate minimums.

**2. Check what you are running.**

````bash
geth version            # or: nethermind --version / besu --version / reth --version
lighthouse --version    # or the equivalent
````

**3. Test on Hoodi first.** Hoodi forks before mainnet, on purpose, and it is
the testnet that exists for exactly this. If you do not have a Hoodi validator,
that is the gap to close before the next fork, not during it.

**4. Upgrade the non-validating node first** if you have one.

**5. Upgrade one client at a time on the validator host**, verifying between
them. Both must be upgraded before the slot; they do not have to be upgraded in
the same minute.

**6. Verify after each restart** — see section 4.

**7. Watch the fork slot itself.** Be at a keyboard. Confirm the node is on the
canonical chain after the transition; a client that forked off looks perfectly
healthy in its own logs.

````bash
curl -s http://127.0.0.1:5052/eth/v1/beacon/headers/head \
  | jq '.data.header.message.slot'
````

Compare against [beaconcha.in](https://beaconcha.in/). Equal, or one behind, is
fine. Diverging is a fork.

---

## 3. Routine client update

Sequence on a validator host, one process at a time:

````bash
# 1. stop the validator client first — no duties are signed while it is down
sudo systemctl stop validator

# 2. update the beacon node or the execution client
sudo systemctl stop consensus
# ... install the new binary ...
sudo systemctl start consensus

# 3. wait for it to be synced and non-optimistic
curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq

# 4. start the validator client last
sudo systemctl start validator
````

Stopping the VC first is the important bit: a VC talking to a restarting beacon
node can miss duties in ways that are harder to diagnose than a clean two-minute
outage.

With eth-docker the whole thing is:

````bash
./ethd update
./ethd up
./ethd version
````

**Do not auto-update client binaries on a validator host.** Pin versions and
upgrade deliberately. `prysm.sh` in particular downloads on every start — pin
the binary instead.

---

## 4. Post-upgrade verification

All four, every time:

````bash
systemctl is-active execution consensus validator

curl -s -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}' http://127.0.0.1:8545

curl -s http://127.0.0.1:5052/eth/v1/node/syncing | jq

curl -s http://127.0.0.1:5052/eth/v1/beacon/headers/head | jq '.data.header.message.slot'
````

Then the one that actually proves it: within two epochs, the validator's
attestations are landing on beaconcha.in. Version numbers and green services do
not prove a validator is working — inclusion does.

---

## 5. Rollback

Keep the previous binary on disk. Rollback is stop, swap the binary, start —
with two conditions:

- **Never roll back across a fork.** A pre-fork client after the fork slot will
  not follow the chain.
- **Never roll back a consensus client to a version with an incompatible
  database format.** Check the release notes; some upgrades migrate the database
  in place and the old binary cannot read the result. When in doubt, resync the
  beacon node with checkpoint sync — it takes minutes.

Chain data is disposable. Keys and the slashing protection database are not.
Rollback never touches them.

---

## 6. Common failures

| Symptom after upgrade | Cause |
|---|---|
| CL logs an unknown fork or refuses to start | Client older than the fork; upgrade |
| Head slot diverges from beaconcha.in | You forked off — you were on an old client at the slot |
| `Unauthorized` on the Engine API | New unit file lost the JWT path |
| VC loads fewer keys than expected | Keystore path or permissions changed |
| Beacon node resyncs from scratch | Database format changed; use checkpoint sync |
| Everything green, no attestations | VC was never restarted, or is pointing at the old beacon port |

## Sources

- [EF Protocol Announcements](https://blog.ethereum.org/category/protocol)
- [Fusaka mainnet announcement](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement)
- `eth-clients/mainnet` and `eth-clients/hoodi` network configs
- [ethereum.org — network upgrades](https://ethereum.org/ethereum-forks/)
