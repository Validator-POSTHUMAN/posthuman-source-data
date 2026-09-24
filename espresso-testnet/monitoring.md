# Espresso Decaf Testnet — Monitoring

Decaf runs the same node software as mainnet, so the mechanics of monitoring an
Espresso validator are the mainnet ones and are not repeated here. Read
[Espresso — Monitoring](/node-ops/espresso/monitoring) for the metrics endpoint,
what a consensus view is, the participation score, and which signals deserve a
page.

This page is only the differences, and there are four that matter.

---

## 1. Point every probe at Decaf, not at mainnet

The metrics path, the scrape config and the alert expressions are identical. The
endpoints they compare against are not:

|                | Decaf |
|---|---|
| Query service  | `https://query.decaf.testnet.espresso.network` |
| Config cache   | `https://cache.decaf.testnet.espresso.network` |
| State relay    | `https://state-relay.decaf.testnet.espresso.network` |
| Block explorer | `https://explorer.decaf.testnet.espresso.network` |
| Staking UI     | `https://stake.decaf.espresso.network/` |
| L1             | Ethereum **Sepolia** |
| Stake table    | `0x40304fbe94d5e7d1492dd90c53a2d63e8506a037` |

A dashboard that reads a mainnet query service while pointing at a Decaf node is
the classic mistake here: every panel renders, every number is plausible, and
none of them describes your node. Put the network name in the dashboard title and
in every alert message.

---

## 2. Watch the L1 provider, because it is Sepolia

The node reads its L1 through `ESPRESSO_L1_PROVIDER` and
`ESPRESSO_L1_WS_PROVIDER`, and on Decaf that is a Sepolia endpoint. Sepolia
endpoints are less reliable than mainnet ones, free tiers are throttled harder,
and the websocket is the half that fails first and most quietly.

Alert on L1 errors in the node log as a first-class signal rather than treating
them as noise:

```bash
journalctl -u espresso-node -n 500 --no-pager \
  | grep -Ei 'l1|provider|websocket|reconnect|rate.?limit' | tail -20
```

A node whose L1 websocket has been dropping and reconnecting for an hour is not
healthy, whatever the consensus metrics say.

---

## 3. A registered node with no delegation is expected

Decaf ESP is not publicly distributed, so a correctly registered Decaf validator
stays **out of the active set** until someone delegates to it. Do not alert on
absence from the active set on this network; it is the normal state, and the
mainnet alert for it is one to disable here explicitly rather than leave enabled
and mute.

What is worth checking, once, after registration:

```bash
staking-cli --network decaf stake-table-entry --address "$VALIDATOR_ADDRESS"
```

and then again after any key rotation, because the registration is what your
delegation is attached to.

---

## 4. Rehearsal is the point, so measure the rehearsal

Decaf exists to catch things before they reach mainnet. That makes two checks
worth more here than they are on mainnet:

- **Alert-path proof.** Fire a real alert through the whole chain — node,
  scraper, rule, notification — and confirm a human received it. An alert path
  proven on Decaf is the only kind worth trusting on mainnet.
- **Upgrade rehearsal.** Run the mainnet upgrade procedure here first and time
  it. The commands are identical, so an upgrade that goes wrong on Decaf would
  have gone wrong on mainnet.

Everything else — what to scrape, what the numbers mean, what to page on — is in
the [mainnet monitoring guide](/node-ops/espresso/monitoring).
