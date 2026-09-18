# XRPL EVM Mainnet monitoring

## The failure that looks healthy

A `exrpd` process can be `active (running)`, report `catching_up=false`, serve
RPC, and still be useless:

- it is following a **different** chain — the app hash diverged and nobody
  noticed, because nothing local can tell;
- it has stopped **signing** — the process is fine and the validator is jailed
  or has zero voting power;
- it is on the **wrong patch** — consensus still agrees, but a `cosmos/evm`
  hotfix has not been applied.

None of the three raises an error in the log you would notice. So:

**Alert on external agreement and on signing, not on the process.**

## The four checks that matter

| Check | Query | Alert when |
|---|---|---|
| Height advancing | `sync_info.latest_block_height` | unchanged across two polls 60 s apart |
| Agreement | `app_hash` at a common height vs an independent RPC | differs, ever |
| Signing | `validator_info.voting_power` | `0` on a node that should be signing |
| Version | `abci_info` local vs fleet | behind the fleet patch level |

```bash
LOCAL=http://127.0.0.1:26657
REMOTE=https://cosmos-rpc.xrplevm.org

H=$(curl -s "$LOCAL/status" | jq -r .result.sync_info.latest_block_height)
A=$(curl -s "$LOCAL/block?height=$H"  | jq -r .result.block.header.app_hash)
B=$(curl -s "$REMOTE/block?height=$H" | jq -r .result.block.header.app_hash)
[ "$A" = "$B" ] || echo "APP HASH DIVERGENCE at $H"

curl -s "$LOCAL/status"    | jq -r .result.validator_info.voting_power
curl -s "$LOCAL/abci_info" | jq -r .result.response.version
```

Use `127.0.0.1` explicitly rather than `localhost` for a high-frequency check.
`localhost` resolves `::1` first; if the service is bound to `0.0.0.0` only,
every request pays an IPv6 timeout before falling back — around 200 ms each,
which turns a fast poll into a slow one for no visible reason.

## Are we in the block we think we are in?

Height and voting power both look fine while a validator quietly misses every
block. The authoritative check is whether your consensus address appears in
the commit:

Your node reports its own consensus identity in `/status`. Compare that hex
address against the signatures in the latest commit:

```bash
ADDR=$(curl -s "$LOCAL/status" | jq -r .result.validator_info.address)
H=$(curl -s "$LOCAL/status" | jq -r .result.sync_info.latest_block_height)
curl -s "$LOCAL/commit?height=$H" \
  | jq -r --arg a "$ADDR" \
    '[.result.signed_header.commit.signatures[].validator_address] | index($a) // "NOT IN LAST COMMIT"'
```

Over a longer window the decisive number is `missed_blocks_counter`, from the
slashing module:

```bash
curl -s https://rest.exrp.posthuman.digital/cosmos/slashing/v1beta1/signing_infos \
  | jq -r '.info[] | select(.address=="<your ethmvalcons…>")
           | {missed_blocks_counter, jailed_until, tombstoned}'
```

`tombstoned: true` is unrecoverable. It is the outcome the anti-double-sign
discipline exists to prevent.

## Prometheus

In `config.toml` — the official page calls it `config.yaml`, which is a typo;
the file is TOML:

```toml
[instrumentation]
prometheus = true
prometheus_listen_addr = "127.0.0.1:26660"
max_open_connections = 3
namespace = "cometbft"
```

Bind the metrics listener to `127.0.0.1` and scrape it over a private network
or an SSH tunnel. The upstream example uses `:26660`, which binds every
interface and publishes your node's internals.

Scrape config:

```yaml
scrape_configs:
  - job_name: "xrplevm"
    static_configs:
      - targets: ["127.0.0.1:26660"]
```

Useful series:

| Metric | Watch for |
|---|---|
| `cometbft_consensus_height` | flat |
| `cometbft_consensus_validator_power` | drops to 0 |
| `cometbft_consensus_missing_validators` | your node appearing |
| `cometbft_consensus_block_interval_seconds` | growing |
| `cometbft_p2p_peers` | below ~5 |

A community dashboard exists at
<https://grafana.com/grafana/dashboards/22701>. Treat an imported dashboard as
a starting layout, not as an alerting policy — it will not know which validator
address is yours.

## Host-level

`node_exporter` for disk, memory and file descriptors. The two that actually
page:

- **disk** — a full disk stops a node in a way that looks like corruption;
- **file descriptors** — `LimitNOFILE=65535` in the unit, and alert before it.

## What not to alert on

- `catching_up` alone — false on a node following the wrong chain too;
- peer count above the floor — ten and six are the same thing operationally;
- single missed blocks — the network tolerates them; a *rate* is the signal;
- restart count on a node that is not a signer.
