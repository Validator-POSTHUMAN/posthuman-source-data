# Solana Testnet Troubleshooting

The mainnet troubleshooting guide applies. This page covers the failures that
are specific to testnet, plus the ones people misdiagnose *because* it is
testnet.

## Triage

````bash
solana validators -ut | grep <identity-pubkey>
solana gossip -ut | wc -l
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
journalctl -u solana --since "30 min ago" | grep -Ei 'panic|error|no space|shred version'
````

---

## Healthy service, no peers, no votes

**Almost always the shred version.** Testnet is restarted by coordination and
the shred version changes; a node still on the old value gossips into a void.
There is no error message for this.

````bash
solana gossip -ut | wc -l               # near-zero
journalctl -u solana | grep -i 'shred version'
````

Take the new value from the official restart announcement, update
`--expected-shred-version` in the unit, restart, and confirm peer count recovers.

Add **gossip peer count** to your alerting. It is the earliest signal and it
fires before delinquency does.

## Node re-downloads a snapshot on every start

After a cluster restart or a ledger reset, the local snapshot is unusable and
Agave falls back to a network fetch. That is correct behaviour.

````bash
ls -lt /mnt/ledger/snapshots | head
df -h /mnt/ledger /mnt/accounts
````

Make room **before** the fetch. If the announcement says the cluster was reset
from a new genesis, clear the ledger and accounts directories — and only those.
Keep every keypair.

If no reset was announced, do not clear anything. "Behind" is not "reset".

## Validator stopped voting and nothing is wrong

Check the identity balance. Voting costs fees on testnet too, the faucet gives
1 SOL per request, and an identity that runs dry stops voting without an error
that looks like a failure.

````bash
solana balance <identity-pubkey> -ut
solana airdrop 1 -ut
````

Same for the vote account: it needs its rent-exempt minimum plus the admission
ticket each epoch.

## Failing SFDP epochs while the node looks fine

Three usual causes, none of which show up as an outage:

| Cause | Check |
|---|---|
| Version below the enforced minimum | `agave-validator --version` against the current testnet minimum; testnet moves first and fast |
| Metrics pointed at the wrong cluster | `SOLANA_METRICS_CONFIG` must carry the **testnet** value, not mainnet's |
| Vote credits or skip rate below the cluster grade | `solana validators -ut`, `solana block-production -ut` — graded against cluster average, not against zero |

A node can be non-delinquent every epoch and still fail the 3% vote-credit rule
or the +5 pp skip-rate rule. Grade yourself against the cluster, not against
"up".

## Onboarding number lost

Ten or more epochs without receiving Foundation stake on testnet costs your
onboarding number and sends you to the bottom of the queue. Track "epochs since
last stake" as a metric; by the time you notice it in a dashboard it is usually
already gone.

## Catch-up is slow after a restart

Testnet load is deliberately heavy. Before assuming a host problem:

````bash
solana catchup --our-localhost
iostat -x 2 5
top -H -p "$(pgrep -f agave-validator)"
free -h
````

Usual order of causes: accounts-DB disk latency, CPU contention on the PoH core,
memory pressure without swap, then network loss. Restarting repeatedly makes it
worse — each restart starts the snapshot load again.

## Two hosts, one identity

Same rule as mainnet, and testnet is exactly where operators get sloppy about
it. Stop, determine which host holds the valid tower, shut the other down
completely, then hand over with `--require-tower`. Practising the safe procedure
here is the point of having a testnet node at all.

## Capture before restarting

````bash
systemctl show solana -p NRestarts -p ActiveState -p ExecMainStartTimestamp
journalctl -u solana --since "1 hour ago" > /tmp/incident-$(date +%s).log
df -h > /tmp/incident-host.txt
free -h >> /tmp/incident-host.txt
ls -lt /mnt/ledger/snapshots | head >> /tmp/incident-host.txt
````

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
