# Solana Testnet Monitoring

Everything in the mainnet monitoring guide applies here. This page covers what
is different, and the three testnet-specific failures that silently cost you
SFDP epochs.

## Read consensus from an external RPC

````bash
solana validators --url https://api.testnet.solana.com | grep <identity-pubkey>
solana vote-account <vote-account> --url https://api.testnet.solana.com
solana block-production --url https://api.testnet.solana.com | grep <identity-pubkey>
````

Two samples sixty seconds apart, both showing `delinquent=false` with `lastVote`
and `rootSlot` advancing. Same rule as mainnet.

## Three testnet-specific silent failures

### 1. Wrong shred version after a cluster restart

Testnet is restarted by coordination. The shred version changes, and a node
still carrying the old value peers with nobody, votes on nothing, and shows no
error.

````bash
solana gossip | wc -l                      # collapses to near-nothing
journalctl -u solana | grep -i 'shred version'
````

Alert on **gossip peer count** as well as delinquency. Peer count falling off a
cliff is the first visible symptom and it appears before delinquency does.

### 2. Empty identity account

Voting costs fees on testnet too. The faucet gives 1 SOL per request, and a
validator burns through that. An identity that runs dry stops voting.

````bash
solana balance <identity-pubkey> --url https://api.testnet.solana.com
solana airdrop 1 --url https://api.testnet.solana.com
````

Alert well above zero — you want the page while there is still runway, not at
the moment voting stops.

### 3. Metrics pointed at the wrong cluster

SFDP checks metric reporting **per cluster**. The testnet
`SOLANA_METRICS_CONFIG` value differs from mainnet's. Setting the mainnet value
on a testnet node produces no local symptom and fails the criterion every
epoch.

Verify the variable is present in the validator's environment and carries the
testnet database, then confirm the node appears on the cluster metrics
dashboard.

## Grade yourself against the criteria, not against "up"

SFDP grades vote credits and skip rate against the **cluster average**. Track
both as ratios, every epoch:

````bash
# your credits and the cluster picture
solana validators --url https://api.testnet.solana.com | grep <identity-pubkey>
solana block-production --url https://api.testnet.solana.com | grep <identity-pubkey>
solana epoch-info --url https://api.testnet.solana.com
````

Useful derived alerts:

| Alert | Threshold |
|---|---|
| vote credits below cluster average | more than 3% below → SFDP failure for that epoch |
| skip rate above network average | more than +5 pp → SFDP failure for that epoch |
| running version below enforced minimum | testnet minimum moves first, and fast |
| epochs since last Foundation stake | approaching 10 → onboarding number at risk |

## Watchtower

`agave-watchtower` works the same way, pointed at testnet, and should still run
on a **different host**:

````bash
agave-watchtower \
  --url https://api.testnet.solana.com \
  --monitor-active-stake \
  --validator-identity <identity-pubkey>
````

Run a separate instance per cluster, with separate notification targets or a
clear cluster label in the message. A delinquency alert that does not say which
cluster it came from will eventually be acted on against the wrong node.

## Host metrics

Identical to mainnet: disk free on ledger, accounts and snapshots; memory and
swap; CPU per core with the PoH core watched; NIC errors; systemd `NRestarts`.
Testnet's heavier synthetic load means host limits show up here first — which is
exactly why running testnet is worth the hardware.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
