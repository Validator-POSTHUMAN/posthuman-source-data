# XRPL EVM Mainnet — operator toolbox

A review of the third-party tooling around this network: what is worth running,
what is worth reading, and what to be careful with. Nothing here is operated by
POSTHUMAN unless it says so.

## Explorers

| Tool | Use it for | Caveat |
|---|---|---|
| [explorer.xrplevm.org](https://explorer.xrplevm.org) | official, EVM-side view: transactions, contracts, tokens | EVM representation only |
| [governance.xrplevm.org](https://governance.xrplevm.org) | validator set, proposals, votes, uptime | the Cosmos-side view, and the one that matters to an operator |
| [ITRocket](https://itrocket.net/services/mainnet/xrplevm/) | public RPC, sync services, state-sync helper | independent operator; useful precisely because it is not us |

`governance.xrplevm.org/validators` is the page to check before claiming your
validator is healthy. It shows the set's view of you, which is the only view
that decides anything.

## Public endpoints worth knowing

Health checking against your own node proves nothing. These are the second
opinions:

| | |
|---|---|
| Official Cosmos RPC | <https://cosmos-rpc.xrplevm.org> |
| Official EVM JSON-RPC | <https://rpc.xrplevm.org> |
| ITRocket RPC | <https://xrplevm-mainnet-rpc.itrocket.net> |
| POSTHUMAN RPC | <https://rpc.exrp.posthuman.digital> |

## Remote signing

| Tool | What it buys you |
|---|---|
| [TMKMS](https://github.com/iqlusioninc/tmkms) | the signing key leaves the node; HSM/YubiHSM support |
| [Horcrux](https://github.com/strangelove-ventures/horcrux) | threshold signing across hosts; two hosts cannot double-sign by construction |

XRPL EVM documents a Horcrux path at
<https://docs.xrplevm.org/pages/operators/advanced/adding-horocrux>.

This is the single highest-value change available to a validator here. The
anti-double-sign rule is a procedure you can get wrong under pressure; a
threshold signer makes it a property of the system.

## Monitoring

| Tool | What it does |
|---|---|
| [Tenderduty](https://github.com/blockpane/tenderduty) | per-validator missed-block and jail alerting across many Cosmos chains; the closest thing to a default |
| Prometheus + Grafana | node internals; dashboard `22701` is a reasonable starting layout |
| `node_exporter` | disk, memory, file descriptors — where outages actually start |

Whatever you use, alert on *agreement with the network* and *presence in the
commit*. A tool that only watches the process will report a healthy node
following the wrong chain.

## Cosmovisor

<https://docs.cosmos.network/main/build/tooling/cosmovisor>

Worth running, with two settings that are not defaults:

- `DAEMON_ALLOW_DOWNLOAD_BINARIES=false` — an upgrade you staged and checked,
  not one the chain handed you;
- `UNSAFE_SKIP_BACKUP=false` — the first start after an upgrade takes minutes
  because it is copying your data. That is the point.

And: `cosmovisor run start`, not `cosmovisor start`.

## Wallets and EVM tooling

Standard Ethereum tooling works against `1440000`:

- **MetaMask** and any EVM wallet — add the network with chain ID `1440000`
  and an RPC from the list above;
- **Foundry** (`cast`, `forge`) — `cast block-number --rpc-url …` is the
  fastest EVM-side health check you can type;
- **viem / ethers** — ordinary EVM clients.

One account has two representations: `ethm1…` on the Cosmos side and `0x…` on
the EVM side. Same key, same balance. Do not display them as two assets and do
not add them together.

## POSTHUMAN services

| | |
|---|---|
| Snapshots | <https://snapshots.exrp.posthuman.digital> |
| RPC / REST / gRPC / EVM | see the Endpoints tab |
| Peer | `71891d3e4790ca8187d38d7acf40ca881074a06b@peer.exrp.posthuman.digital:62656` |

## What to be careful with

- **Any tool that wants your mnemonic or key file.** There is no legitimate
  monitoring tool in this list that needs either.
- **Community snapshot mirrors with no published metadata.** If you cannot see
  the height and the time before downloading, you cannot tell a current
  snapshot from a month-old one.
- **Dashboards imported wholesale.** A dashboard does not know which validator
  address is yours, so its alerts are about a generic node, not about you.
- **One-liner installers.** Read them. They configure a node you will be
  responsible for at three in the morning.
