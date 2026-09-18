# Creating an Ethereum Validator

This guide assumes you already have a synced execution client and a synced
consensus client — see **Installation**. A validator is a third process (the
validator client) plus a deposit. Do not deposit before the node is synced.

**Read this first.** Ethereum staking has exactly one irreversible mistake:
running the same validator key in two places at once. There is no "start it and
see". Two processes signing for one public key produce a slashable double vote,
the stake is cut and the validator is force-exited. Nothing else in this guide
is as dangerous as that one thing.

---

## 1. The three keys, and which one can lose your money

| Key | Lives where | What it does | If leaked |
|---|---|---|---|
| **Mnemonic (seed)** | Offline, on paper, never on the server | Derives every validator key and the withdrawal credential | Total loss of the stake |
| **Validator signing key** (BLS) | On the staking server, inside a keystore | Signs attestations, blocks, voluntary exits | Attacker can get you slashed; cannot steal the stake |
| **Withdrawal address** (EL address) | Your own wallet — hardware wallet recommended | Receives withdrawals; since Pectra can also trigger exits, partial withdrawals and consolidations | Stake can be withdrawn by the attacker |

The mnemonic is not needed to run a validator. Generate keys, copy the
keystores to the server, and keep the mnemonic offline.

### Withdrawal credentials: 0x01 or 0x02

Choose before you generate keys. Changing later is possible but costs a queue
and, for 0x02, is irreversible without a full exit.

| | `0x01` — regular withdrawals | `0x02` — compounding |
|---|---|---|
| Effective balance cap | 32 ETH | 2048 ETH |
| Rewards | Swept to your address every few days | Compound into the stake automatically |
| Deposit amounts | Multiples of 32 ETH | Any amount from 32 to 2048 ETH |
| Partial withdrawal | Automatic | Manual, triggered from the withdrawal address, costs gas |
| Consolidating several validators into one | No | Yes |

`0x00` credentials are BLS-only and predate withdrawals. If you still hold any,
migrate them with `ethdo` or the deposit CLI's BLS-to-execution change — a
`0x00` validator cannot withdraw anything.

**POSTHUMAN default: `0x02` for a professional operator.** Fewer validators to
run for the same stake, no sweep to re-stake manually, and consolidation is
available. Use `0x01` when the stake is exactly 32 ETH and you want the rewards
paid out rather than compounded.

---

## 2. Generate keys — on an offline machine

Use the maintained CLI. `ethereum/staking-deposit-cli` is **deprecated**; the
successor is [`ethstaker/ethstaker-deposit-cli`](https://github.com/ethstaker/ethstaker-deposit-cli),
`v1.3.0` at the time of writing.

Do this on a machine that is not the staking server and ideally has never been
online. A live USB is fine.

````bash
# on the offline machine
DEPOSIT_CLI=v1.3.0
curl -fsSLO https://github.com/ethstaker/ethstaker-deposit-cli/releases/download/${DEPOSIT_CLI}/ethstaker_deposit-cli-linux-amd64.tar.gz
curl -fsSLO https://github.com/ethstaker/ethstaker-deposit-cli/releases/download/${DEPOSIT_CLI}/checksums.txt
sha256sum -c checksums.txt --ignore-missing
tar xzf ethstaker_deposit-cli-linux-amd64.tar.gz
````

Verify the checksum. A tampered deposit CLI is the classic way stakers lose a
mnemonic.

````bash
./deposit new-mnemonic \
  --num_validators 1 \
  --chain mainnet \
  --withdrawal_address 0xYourWithdrawalAddress \
  --compounding
````

- `--withdrawal_address` sets `0x01` credentials. Adding `--compounding` makes
  them `0x02`. Omit both and you get `0x00`, which you do not want.
- The address must be one **you control the private key for**. An exchange
  deposit address is not a withdrawal address.
- Write the 24 words on paper. Twice. Do not photograph them, do not put them in
  a password manager that syncs, do not type them into anything that is online.

Output, in `validator_keys/`:

| File | Contains | Goes to |
|---|---|---|
| `keystore-m_12381_3600_*.json` | Encrypted signing key, one per validator | The staking server |
| `deposit_data-*.json` | Public keys, signatures, withdrawal credentials | The Launchpad — **public, no secrets** |

Verify what you generated before depositing anything:

````bash
jq -r '.[] | "\(.pubkey) \(.withdrawal_credentials) \(.amount)"' validator_keys/deposit_data-*.json
````

The credential must start with `02` (compounding) or `01` (regular) followed by
your address, zero-padded. If it starts with `00`, stop and regenerate.

---

## 3. Deposit

Use the [Staking Launchpad](https://launchpad.ethereum.org/). It walks the
checklist, uploads `deposit_data-*.json`, and builds the transaction to the
deposit contract.

| | Mainnet | Hoodi (testnet) |
|---|---|---|
| Launchpad | `launchpad.ethereum.org` | `hoodi.launchpad.ethereum.org` |
| Chain ID | `1` | `560048` |
| Deposit contract | `0x00000000219ab540356cBB839Cbe05303d7705Fa` | `0x00000000219ab540356cBB839Cbe05303d7705Fa` |

**Verify the deposit contract address on the Launchpad page against the value
above before signing.** Phishing clones of the Launchpad exist and the only
thing that distinguishes them is the contract address in the transaction.

After the transaction confirms:

- the beacon chain notices the deposit after roughly 13 minutes;
- the validator then sits in the **activation queue**, whose length varies with
  demand — hours to weeks;
- track it at [beaconcha.in](https://beaconcha.in/) by public key.

Start the validator client while you wait. A VC whose keys are not yet active
has no duties and signs nothing, so there is no risk — and it proves the keys
loaded, the beacon connection works and the fee recipient is set before the
first duty arrives.

---

## 4. Validator client

The VC holds the keystores and signs. It talks to your beacon node over the
Beacon API on `127.0.0.1:5052`. It never needs internet access of its own.

Move `validator_keys/` to the server over `scp`, set ownership to a dedicated
user, and **delete the copy from the offline machine only after the validator is
attesting**.

````bash
sudo useradd --no-create-home --shell /bin/false validator
sudo mkdir -p /var/lib/validator
sudo chown -R validator:validator /var/lib/validator
sudo chmod 700 /var/lib/validator
````

### Fee recipient — set it, or you donate your tips

Every client requires a fee recipient address for execution-layer tips. Set it
to an address you control. Several clients refuse to start without it; the ones
that do not will burn your priority fees to a zero address.

### Lighthouse

````bash
sudo -u validator lighthouse account validator import \
  --network mainnet \
  --datadir /var/lib/validator \
  --directory /path/to/validator_keys
````

````ini
# /etc/systemd/system/validator.service
[Unit]
Description=Lighthouse validator client
After=network-online.target consensus.service
Wants=network-online.target

[Service]
User=validator
Group=validator
Type=simple
Restart=always
RestartSec=5
ExecStart=/usr/local/bin/lighthouse vc \
  --network mainnet \
  --datadir /var/lib/validator \
  --beacon-nodes http://127.0.0.1:5052 \
  --suggested-fee-recipient 0xYourFeeRecipient \
  --metrics --metrics-address 127.0.0.1 --metrics-port 5064 \
  --graffiti "POSTHUMAN"

[Install]
WantedBy=multi-user.target
````

### Prysm

````bash
sudo -u validator prysm.sh validator accounts import \
  --mainnet \
  --wallet-dir=/var/lib/validator \
  --keys-dir=/path/to/validator_keys
````

````ini
ExecStart=/usr/local/bin/prysm.sh validator \
  --mainnet \
  --wallet-dir=/var/lib/validator \
  --wallet-password-file=/var/lib/validator/password.txt \
  --beacon-rpc-provider=127.0.0.1:4000 \
  --suggested-fee-recipient=0xYourFeeRecipient \
  --accept-terms-of-use
````

### Teku

Teku can run the beacon node and validator in one process
(`--validator-keys=<dir>:<passdir>` on the beacon command) or separately with
`teku validator-client`. One process is simpler; two let you restart the beacon
node without restarting the signer.

### Nimbus

````bash
sudo -u validator /usr/local/bin/nimbus_beacon_node deposits import \
  --data-dir=/var/lib/consensus /path/to/validator_keys
````

Nimbus runs the validator inside the beacon node by default.

### Lodestar

````bash
sudo -u validator lodestar validator import \
  --network mainnet --dataDir /var/lib/validator \
  --importKeystores /path/to/validator_keys
````

### Start and verify

````bash
sudo systemctl daemon-reload
sudo systemctl enable --now validator
sudo journalctl -fu validator
````

You are looking for the client logging the number of keys it loaded. **If that
number is not the number you expect, stop and fix it** — a silently skipped
keystore is a validator that is not attesting and will accrue inactivity
penalties.

Then, once activated, confirm from outside: the validator's page on
[beaconcha.in](https://beaconcha.in/) must show attestations landing with a high
inclusion rate within two epochs (about 13 minutes).

---

## 5. Doppelganger protection — turn it on

Every major client has a flag that makes the VC sit out two to three epochs on
startup and listen for its own keys attesting elsewhere. If it hears them, it
refuses to start.

| Client | Flag |
|---|---|
| Lighthouse | `--enable-doppelganger-protection` |
| Prysm | `--enable-doppelganger-protection` |
| Nimbus | `--doppelganger-detection=on` (default) |
| Lodestar | `--doppelgangerProtection` |
| Teku | `--doppelganger-detection-enabled=true` |

It costs a few minutes of missed attestations on every restart and it is the
cheapest slashing insurance that exists. Use it.

It is **not** a substitute for the slashing protection database. When moving
keys between machines, export and import that database:

````bash
# on the old host, after stopping the VC
lighthouse account validator slashing-protection export slashing.json
# on the new host, before starting the VC
lighthouse account validator slashing-protection import slashing.json
````

The interchange format is standard (EIP-3076) and every client reads it.

---

## 6. MEV-Boost — optional, and a real tradeoff

`mev-boost` (`v1.12`) sits between the beacon node and a set of relays and
auctions your block space. It typically raises rewards on the blocks you
propose. It also means your blocks come from a relay, with the censorship and
liveness properties of that relay.

````ini
ExecStart=/usr/local/bin/mev-boost \
  -mainnet \
  -relay-check \
  -relays <relay-url-1>,<relay-url-2> \
  -addr 127.0.0.1:18550
````

Then point the beacon node at it — `--builder http://127.0.0.1:18550` on
Lighthouse, `--builder-endpoint` on Teku, `--payload-builder-*` on Nimbus — and
add the builder flag on the VC.

Choose relays deliberately: check censorship policy and reliability at
[mevboost.pics](https://www.mevboost.pics/) and
[relayscan.io](https://relayscan.io/). Run with `-relay-check` so a dead relay
does not cost you a proposal, and make sure the client falls back to a locally
built block rather than missing the slot.

---

## 7. Exiting, consolidating, withdrawing

Since Pectra these are execution-layer operations triggered from the withdrawal
address, not only from the signing key.

| Operation | How | Contract |
|---|---|---|
| Voluntary exit (signing key) | `lighthouse account validator exit`, `ethdo validator exit`, or the client equivalent | — |
| Triggered exit (withdrawal address) | Transaction to the withdrawal-request predeploy | `0x00000961Ef480Eb55e80D19ad83579A64c007002` |
| Partial withdrawal (0x02 only) | Same predeploy, non-zero amount | `0x00000961Ef480Eb55e80D19ad83579A64c007002` |
| Consolidate validators / switch 0x01 → 0x02 | Transaction to the consolidation predeploy | `0x0000BBdDc7CE488642fb579F8B00f3a590007251` |

Exit is not instant: the validator waits in the exit queue, then serves a
withdrawal delay, then the balance is swept. Budget days, not hours, and keep
the validator online and attesting the whole time — an exiting validator is
still penalised for missed duties.

Switching `0x01` → `0x02` cannot be reversed without exiting and depositing
again. Consolidation requires both source and target to already be `0x02`.

---

## 8. Distributed validators (DVT)

If a single host is not an acceptable failure domain, the stake can be split
across operators with threshold signing — no single machine holds a complete
key.

- [SSV Network](https://ssv.network/) — operator registry, DKG, used by Lido.
  POSTHUMAN has run SSV operators on mainnet and Hoodi.
- [Obol](https://obol.org/) — Charon middleware, distributed validator clusters.
- [Anchor](https://github.com/sigp/anchor) — Sigma Prime's SSV client, Rust.

DVT removes the single-host risk and adds a cluster to operate. It does not
remove the double-signing rule; it moves it to the cluster level, where a
mis-restored key share is still a slashing event.

---

## 9. Before you deposit — checklist

- [ ] EL synced: `eth_syncing` returns `false`
- [ ] CL synced: `is_syncing: false`, `is_optimistic: false`
- [ ] Clock synced with `chrony`
- [ ] Tested the whole flow on **Hoodi** first
- [ ] Mnemonic on paper, offline, in two locations
- [ ] Withdrawal address is a wallet you control, verified on-chain
- [ ] Deposit contract address checked against this page
- [ ] Fee recipient set on the VC
- [ ] Doppelganger protection enabled
- [ ] Monitoring and alerting live *before* activation, not after
- [ ] You know where the slashing protection database is and how to export it

## Sources

- [ethereum.org — Home staking](https://ethereum.org/staking/solo/)
- [Staking Launchpad](https://launchpad.ethereum.org/)
- [ethstaker-deposit-cli](https://github.com/ethstaker/ethstaker-deposit-cli)
- [EIP-7002 — Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002)
- [EIP-7251 — Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251)
- [EIP-3076 — Slashing protection interchange format](https://eips.ethereum.org/EIPS/eip-3076)
- `eth-clients/mainnet` and `eth-clients/hoodi` network configs
