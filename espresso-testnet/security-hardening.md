# Espresso Decaf Testnet — Security Hardening

Decaf runs the same node software as mainnet with the same key inventory, so the
substance of hardening an Espresso node is the mainnet document and is not
repeated here. Read
[Espresso — Security Hardening](/node-ops/espresso/security-hardening) for the
key inventory, node-key custody, the rotation timing, wallet custody and the port
table.

This page is the differences, plus the one habit a testnet makes it easy to lose.

---

## 1. Separate keys, separate wallet, separate everything

Use a **different key set and a different Ethereum account for Decaf than for
mainnet.** Not a derivation of the same mnemonic at another index — a different
mnemonic.

The reason is specific rather than general: `staking-cli` takes `--network decaf`
where the mainnet command takes `--network mainnet`, and the stake table address
changes with it. Every other flag is identical. A wallet that can act on both
networks turns one mistyped flag into a mainnet transaction you did not intend,
and the mainnet wallet is the one that controls the stake, the commission and the
exit.

If the same Ledger is convenient, use a different account index and write down
which index is which. `claim-validator-exit --validator-address` needs the exact
address and the wrong one is a failed or misdirected transaction.

---

## 2. The L1 is Sepolia, and the RPC key is still a secret

`ESPRESSO_L1_PROVIDER` and `ESPRESSO_L1_WS_PROVIDER` point at a Sepolia endpoint,
usually a commercial provider with an API key in the URL. That key is a secret
even though the chain it reaches is a testnet:

- keep it in the env file at `0600`, never on a command line, never in a compose
  file that gets committed
- use a key scoped to this node, separate from the mainnet node's key, so
  rotating one does not take the other down
- treat provider spend as a monitoring signal — an unexpected bill is the first
  sign the key leaked

---

## 3. Network exposure is identical, so do not relax it

The port table is the mainnet one: `9977/TCP` inbound and public for consensus,
the node API on loopback or behind a reverse proxy, L1 and Espresso services
outbound only.

It is tempting to leave the API port open on a testnet box because nothing there
has value. Do not. The host is on your network, the API surface is the same code
you will run on mainnet, and the habit is the thing being rehearsed.

```bash
sudo ss -lntp | grep -E ':(9977|8080)'
```

Verify listeners rather than firewall rules — Docker publishes past `ufw` here
exactly as it does on mainnet.

---

## 4. Key uniqueness still applies, and is easier to get wrong here

The reviewed operator documentation describes no slashing on Espresso, and that
is as true on Decaf as on mainnet. It is still not permission to run two nodes on
one key file, and Decaf is where duplication actually happens: a snapshot of a
test VM, a forgotten container from a rehearsal, a half-finished migration left
running over a weekend.

Before starting a node on a new host, prove the old one is gone:

```bash
# On the old host — the process must be absent, not merely stopped.
docker ps -a --filter name=espresso-node
sudo ss -lntp | grep -E '9977|8080'

# From outside — the old P2P address must answer nothing.
nc -d -w3 <old-public-host> 9977 | xxd     # expect no output
```

---

## 5. What Decaf is for

Rehearse the operations that are expensive to get wrong on mainnet, in this
order, because each one has bitten someone:

1. **Key rotation.** `update-consensus-keys` takes effect in the **third epoch**,
   about 72 hours. Swapping the key file immediately takes the validator out of
   consensus. Do that here once and the timing stops being theoretical.
2. **Exit.** `claim-validator-exit` against the right address, with the right
   account index.
3. **Migration.** Old host proven dead, then new host started — the sequence
   above, executed rather than read.
4. **Restore from backup.** Losing the node key file costs two to three epochs of
   participation. Find out here whether your backup actually restores.

Decaf ESP is not publicly distributed and a registered node stays out of the
active set until someone delegates, so none of these rehearsals costs anything —
which is the entire argument for doing them here rather than discovering the
behaviour on mainnet.
