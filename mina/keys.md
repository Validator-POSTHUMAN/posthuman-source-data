# Mina Keys and Custody

Mina has no consensus key separate from the wallet, no remote signer and no
slashing. That combination is not a relaxation — it moves the entire risk onto
one place: a private key that must sit unlocked on an internet-connected
machine.

| Secret | Location | What it controls | If leaked |
|---|---|---|---|
| Block producer key | `~/keys/my-wallet` (+ `.pub`) | block production **and** the funds in that account | funds drained; producer identity taken over |
| Key password | your password manager | decrypts the key file | with the file, total loss |
| libp2p keypair | `~/.mina-config/libp2p-keys/…` | the node's P2P identity | peer impersonation, no fund authority |
| Uptime submitter key | usually the same file as the BP key | signs delegation-program uptime submissions | same blast radius as whichever key you used |
| SNARK worker fee key | public key only on the node | where SNARK fees are paid | nothing — only a public key is configured |

Two consequences follow, and everything else in this guide is downstream of them:

1. The key on the producer is a **hot** key. Keep the stake elsewhere.
2. There is no double-sign penalty, so running a second node with the same key
   is safe for the chain. It is a legitimate redundancy strategy, and the
   delegation program explicitly allows it.

## Generate the block producer key

````bash
mkdir -p ~/keys && chmod 700 ~/keys
mina advanced generate-keypair --privkey-path ~/keys/my-wallet
chmod 600 ~/keys/my-wallet
````

Under Docker, generate with the image you will run so the format matches:

````bash
docker run --rm -it -v ~/mina/keys:/keys \
  minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet \
  mina advanced generate-keypair --privkey-path /keys/my-wallet
````

Two files appear:

- `my-wallet` — the encrypted private key, mode `600`
- `my-wallet.pub` — the public key in plain text, safe to publish

Permissions are enforced by the daemon, not suggested: `700` on the directory
and `600` on the key file. Anything looser and the node exits at startup. This
is the most common cause of a node that "crashes every few minutes".

Set `MINA_PRIVKEY_PASS` to use the tools non-interactively. Passwords containing
shell metacharacters must be quoted — an unquoted `$` is silently mangled and
produces a wrong-password failure that reads like a corrupt key.

Always validate before you depend on it:

````bash
mina advanced validate-keypair --privkey-path ~/keys/my-wallet
````

## Hot and cold

The block producer needs its private key in plaintext memory to evaluate the
VRF for every slot and to build the blockchain SNARK. Neither operation can be
delegated to a Ledger or an HSM — this is a protocol property, not a missing
feature. So the pattern is:

1. **Hot wallet** — generated on the producer host. Holds a minimal balance.
   Runs the node.
2. **Cold wallet** — generated offline or on a Ledger. Holds the stake.
3. **Delegate cold → hot.** The hot key then produces blocks backed by the cold
   key's stake, and a compromise of the producer costs you the hot balance and
   the identity, not the stake.

````bash
mina client delegate-stake \
  --sender  $COLD_PUBLIC_KEY \
  --receiver $HOT_PUBLIC_KEY \
  --fee 0.1
````

Both accounts must exist in the consensus ledger before any of this counts: an
address that has never received funds is not in the ledger, and stake delegated
to or from it is invisible to consensus. Fund each account at least once —
the account-creation fee is enough to create it.

Delegation is an on-chain transaction, so it costs a fee, and it is
all-or-nothing: your entire balance is delegated, there is no partial
delegation. Changes take effect after 1–2 epochs; see **Block producer** for
why that latency is not a bug.

### Ledger hardware wallet

A Ledger can hold the cold key and sign the delegation. It cannot run the
producer. Install the Mina app and use the Mina command-line wallet or the
Ledger app's delegate flow.

### mina-signer

`mina-signer` (npm) generates key pairs and signs payments and delegations
offline, in Node.js. Useful for air-gapped cold-key ceremonies and for scripted
payout tooling that must not have an unlocked account on a live daemon.

## The libp2p key

Generated automatically on first start under the config directory, or explicitly:

````bash
mina libp2p generate-keypair --privkey-path ~/keys/libp2p
mina libp2p dump-keypair      --privkey-path ~/keys/libp2p
````

Pass it with `--libp2p-keypair` to keep a stable peer ID across rebuilds.
It carries no fund authority. Do **not** copy it to a second host that runs on
the same network at the same time — duplicate peer IDs produce unstable
connectivity that looks like a networking fault for days before anyone suspects
the key.

## The uptime submitter key

The delegation program's SNARK-based uptime system signs its submissions with a
key you nominate:

````
EXTRA_FLAGS="--block-producer-key /home/YOUR_USER/keys/my-wallet \
             --uptime-submitter-key /home/YOUR_USER/keys/my-wallet \
             --uptime-url https://uptime-backend.minaprotocol.com/v1/submit"
UPTIME_PRIVKEY_PASS="your-key-password"
MINA_PRIVKEY_PASS="your-key-password"
````

`UPTIME_PRIVKEY_PASS` must be its own line in `~/.mina-env` — not inside
`EXTRA_FLAGS`. Most operators point it at the block producer key, which is what
the program expects; using a separate key means submissions are attributed to
that other public key. See the **Delegation program** guide.

## Backup and rotation

Back up, encrypted and off-host:

- `my-wallet` and `my-wallet.pub`
- the password, stored **separately** from the key file
- the libp2p key, if you pinned one

`~/.mina-config` chain data is disposable — it re-syncs. The key files are not.

There is no on-chain key rotation for a Mina block producer: the producer *is*
the account. "Rotating" means creating a new account, having every delegator
re-delegate to it, and waiting out the epoch latency. Plan the key to last, and
treat suspected compromise as an incident with a funds-movement step, not a
config change:

1. Move the cold wallet's delegation away from the compromised hot key
   immediately — that is the only action that takes effect without the
   attacker's cooperation.
2. Sweep any balance still on the hot key.
3. Stand up a new hot key, publish it, and ask delegators to re-delegate.

## Related guides

- **Installation guide** / **Install (Docker)** — where these files are created
- **Block producer** — coinbase receiver and stake latency
- **Security hardening** — host and port rules around the key
- **Delegation program** — uptime submission and payout obligations

## Sources

- [docs.minaprotocol.com — generating a key pair](https://docs.minaprotocol.com/node-operators/validator-node/generating-a-keypair)
- [docs.minaprotocol.com — hot and cold block production](https://docs.minaprotocol.com/node-operators/block-producer-node/hot-cold-block-production)
- [docs.minaprotocol.com — staking and snarking](https://docs.minaprotocol.com/node-operators/validator-node/staking-and-snarking)
- [docs.minaprotocol.com — uptime tracking system](https://docs.minaprotocol.com/node-operators/delegation-program/uptime-tracking-system)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
