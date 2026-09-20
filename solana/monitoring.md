# Solana Validator Monitoring

"The service is running" is worth almost nothing on Solana. A validator process
can be up, healthy locally, peered in gossip, and still be delinquent, skipping
every leader slot, or voting on a fork nobody else is on.

Monitor four layers. Alert on the ones that cost money.

1. **Consensus** — is the cluster counting our votes?
2. **Leader performance** — are we producing the blocks we were scheduled?
3. **Node health** — slot distance, health endpoint, catchup.
4. **Host capacity** — disk, memory, swap, clock, NIC.

## 1. Consensus — the only view that matters

Everything here must be read from an **external** RPC. Asking your own node
whether it is healthy is asking the patient for the diagnosis.

````bash
solana validators --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
solana vote-account <vote-account-pubkey> --url https://api.mainnet-beta.solana.com
````

| Signal | Healthy | Page when |
|---|---|---|
| `delinquent` | `false` | `true` for more than ~2 minutes |
| `lastVote` | advancing between samples | unchanged across two samples 60 s apart |
| `rootSlot` | advancing, ~32 slots behind `lastVote` | stalls, or falls far behind `lastVote` |
| `activatedStake` | matches expectation | unexplained drop — stake left, or you were not admitted |
| credits this epoch | rising | flat while the epoch advances |

Two samples, sixty seconds apart, with both `lastVote` and `rootSlot` advancing
in each — that is the check. A single sample cannot distinguish a voting
validator from a frozen one.

### Vote account balance — the alert most operators do not have

Under Alpenglow the **Validator Admission Ticket** is burned from the vote
account every epoch, and a vote account that cannot pay it is simply not
admitted next epoch. Nothing crashes. The node just stops being a validator.

````bash
solana balance <vote-account-pubkey> --url https://api.mainnet-beta.solana.com
````

Alert below *rent-exempt minimum + next VAT + a buffer* — in practice keep
several epochs of ticket on it. Also alert on the **identity** balance: it pays
roughly 1 SOL/day in vote fees and an empty identity stops voting just as hard.

## 2. Leader performance

Votes keep you in consensus; blocks are where the revenue is. Skipped leader
slots are the clearest signal that the host is under-provisioned or
mis-tuned.

````bash
solana block-production --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
solana leader-schedule --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
````

`block-production` prints leader slots, blocks produced and skipped for the
current epoch. A skip rate meaningfully above the cluster average is a defect,
not bad luck — look at CPU contention on the PoH core, disk latency on the
accounts volume, and network loss before anything else.

## 3. Node health

````bash
# is the local RPC alive and caught up
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'

# local vs network slot
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}'

solana catchup --our-localhost
agave-validator --ledger /mnt/ledger monitor
````

The useful derived metric is **slot distance**: local finalized slot minus the
same figure from a public RPC. Zero or one is healthy. A distance that grows
monotonically is the earliest warning you get, and it appears well before
`delinquent` flips.

Also watch the shred version after any cluster restart — a node on the wrong
shred version will look busy and talk to nobody.

## 4. Agave Watchtower

`agave-watchtower` is the purpose-built delinquency monitor and the cheapest
useful alerting you can deploy.

````bash
agave-watchtower \
  --url https://api.mainnet-beta.solana.com \
  --monitor-active-stake \
  --validator-identity <identity-pubkey>
````

Notifications come from environment variables — Telegram, Slack, Discord or
Twilio. For Telegram:

````
TELEGRAM_BOT_TOKEN=<token from @BotFather>
TELEGRAM_CHAT_ID=<negative group id>
````

**Run it on a different host from the validator.** A watchtower on the validator
goes silent in exactly the failure it exists to report — power loss, kernel
panic, network cut. Run it as its own systemd unit with the environment in an
`EnvironmentFile` mode `600`, not in a shell history.

````ini
[Unit]
Description=Agave Watchtower
After=network-online.target

[Service]
Type=simple
User=watchtower
EnvironmentFile=/etc/agave-watchtower.env
ExecStart=/usr/local/bin/agave-watchtower --url https://api.mainnet-beta.solana.com --monitor-active-stake --validator-identity <identity-pubkey>
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
````

## 5. Metrics and dashboards

### Cluster metrics

Setting `SOLANA_METRICS_CONFIG` in the validator environment publishes node
metrics to the public cluster dashboard. **Participation in the Solana
Foundation Delegation Program requires it.** The value is per-cluster and is
published in the Anza cluster documentation.

### Host and process metrics

There is no first-party Prometheus exporter. The normal stack is:

- `node_exporter` for CPU, memory, swap, disk, filesystem and NIC counters;
- a small exporter or scrape script that turns the RPC answers above into
  gauges: slot distance, delinquency, last vote, root slot, credits, vote
  account balance, identity balance, skip rate;
- `process-exporter` or systemd metrics for restart count and RSS.

The community `solana-exporter` projects do most of this; whichever you pick,
pin the version and read what it queries — some hammer a public RPC hard enough
to get rate-limited, which then looks like an outage in your own dashboard.

### What to graph

| Panel | Why |
|---|---|
| slot distance (local vs public) | earliest warning of trouble |
| delinquent (0/1) | the thing that costs rewards |
| skip rate vs cluster average | leader-side health |
| vote credits per epoch | earning rate |
| vote account + identity balance | silent-death alerts |
| disk free: ledger / accounts / snapshots | the most common real outage |
| memory + swap in use | restart survivability |
| CPU per core, with the PoH core highlighted | contention shows here first |
| NIC errors / drops | shreds lost is skipped blocks |
| systemd `NRestarts` | a restarting validator is not a healthy one |

## 6. Logs

````bash
journalctl -u solana -f -o cat
tail -f /home/sol/agave-validator.log
````

Alert on these patterns:

| Pattern | Meaning |
|---|---|
| `No space left on device` | snapshot packaging or ledger write failed — replay stops |
| `Panic` / `panicked at` | process fault; capture the log before restarting |
| `Error: failed to start validator` | startup misconfiguration |
| `Waiting for a snapshot` / `downloading snapshot` outside a planned restart | local snapshot was rejected |
| `duplicate` / `dead slot` bursts | fork or hardware trouble |
| gossip table growth warnings | usually benign; do not page on them alone |

Rotate the log. The validator reopens its log file on `SIGUSR1`, which is what
makes logrotate safe — and it only works if the start script used `exec`:

````
/home/sol/agave-validator.log {
  rotate 7
  daily
  missingok
  postrotate
    systemctl kill -s USR1 sol.service
  endscript
}
````

## 7. Third-party monitoring surfaces

Useful as an outside opinion, never as your only alerting:

- **validators.app** — validator scoring, delinquency and a notification API.
- **Trillium** — epoch-level rewards, MEV and block-production analytics.
- **Stakewiz / stakeutils** — scoring, commission history, stake movement.
- **Solana Compass, solanabeach.io** — validator pages and epoch state.
- **Pumpkin's Pool watchtower** — stake-concentration and pool views.

They lag, they go down, and they disagree with each other. Use them to explain a
number, not to discover an outage.

## Alert policy that actually works

Page on: delinquency > 2 min, slot distance growing for > 5 min, disk free
below one snapshot's worth, vote or identity balance below threshold, service
restart, `No space left on device`, panic.

Ticket on: skip rate above cluster average, credits below peers, NIC errors,
memory trend, new client version available.

Ignore: transient gossip warnings, single-sample slot jitter, third-party
dashboards disagreeing by a slot.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
