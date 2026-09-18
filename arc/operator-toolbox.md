# Arc Network mainnet — operator toolbox

A review of the tooling around this network. Nothing here is operated by
POSTHUMAN.

## Node software

| Tool | What it is |
|---|---|
| `arc-node-execution` | execution layer, Reth-based |
| `arc-node-consensus` | consensus layer, Malachite-based |
| `arc-snapshots` | the only supported bootstrap — genesis sync is not available |
| `arcup` | installer and updater for all three |

`arcup` with no arguments updates to the latest release. Convenient, and also
how a node ends up on a version nobody chose. Pin with `arcup --install <tag>`
on anything that matters. `arcup --self-update` updates the installer,
`arcup --uninstall` removes binaries without touching node data.

Checksum verification is on; **GPG signature verification is disabled until
Circle publishes the release signing key**.

## Explorers

| Tool | Use it for |
|---|---|
| [explorer.arc.io](https://explorer.arc.io) | official view — blocks, transactions, contracts |
| [arc.etherscan.io](https://arc.etherscan.io) | Etherscan's deployment; familiar UI and API shape |
| [arc.exploreme.pro](https://arc.exploreme.pro) | independent third-party explorer |

Three independent views of one chain is useful precisely when they disagree.

## Foundry

The fastest EVM-side check you can type, and worth installing on the node host:

```sh
cast block-number --rpc-url http://127.0.0.1:8545
cast chain-id     --rpc-url http://127.0.0.1:8545
cast block        --rpc-url http://127.0.0.1:8545 <height> --json | jq -r .hash
cast gas-price    --rpc-url https://rpc.mainnet.arc.io
```

<https://book.getfoundry.sh>

## Monitoring

| Tool | Notes |
|---|---|
| Prometheus + Grafana | EL metrics at `/` on `9001`, CL at `/metrics` on `29000` — different paths |
| Dashboards shipped with the node | `deployments/monitoring/config-grafana/provisioning/dashboards-data` in `arc-node` |
| `node_exporter` | disk space, and disk **write latency**, which is what backpressure exists for |

Whatever you use, alert on **block-number progress** and on **divergence from
an independent RPC**. A tool that watches the process will report a healthy
node that stopped following an hour ago.

## Circle's developer tooling — read the boundary

Circle ships an application-development stack for Arc. It is worth knowing
about and it is **not** node-operations tooling:

| Component | What it does | What it does not do |
|---|---|---|
| Circle CLI (`@circle-fin/cli`) | wallets, USDC transfers, CCTP, contract queries | nothing about running a node |
| Circle Skills (`use-arc`) | chain config, Solidity tooling, deployment, bridging | nothing about node operations |
| Circle MCP server | current SDK and contract context for AI tools | not an operational control plane |
| App Kit | bridge, swap, send, unified balance, onramp, earn | application layer |

Adoption posture, and it is not optional:

- **Do not install Circle CLI, wallets, skills or MCP on a node host.** Pilot on
  an isolated developer workstation, testnet first, read-only commands first.
- Do not import validator, treasury or production deployer keys. Local-wallet
  mode bypasses Agent Wallet compliance, policy and audit controls.
- `circle update` is an explicit global npm replacement and prompts on a TTY
  unless `--yes` is passed. Never schedule `circle update --yes` on an
  operational host; pin and review the exact version instead.
- `circle skill update` for non-Claude targets delegates to `npx skills update
  -y`, which can update a broader local skill set. Treat every skill update as
  an untrusted instruction change: capture old and new revisions, inspect the
  diff, review, then promote.

The `use-arc` skill already documents the native/USDC dual view and the 18 vs 6
decimal representation correctly. It remains a development reference, not a
substitute for the operator guides on the other tabs of this card.

## AI operations skill

POSTHUMAN publishes an Arc node-operations skill — see the Skills & MCP tab. It
covers the operational half that `use-arc` deliberately does not.

## What to be careful with

- **`curl … | bash`.** `arcup`'s installer is Circle-published and it is also a
  script that configures a node you will own at three in the morning. Read it.
- **Copying a quickstart.** Circle's published `docker-compose.yml` and every
  example target `arc-testnet`. A mainnet deployment made by changing the RPC
  URLs and not `--chain` is a testnet node pointed at mainnet relays. Always
  finish with `cast chain-id`.
- **Presigned snapshot URLs.** Reth derives component URLs by string
  concatenation, so a query string breaks every one of them. Use `--chain`.
- **Any tool asking for the consensus-layer private key.** Nothing legitimate
  needs it. It is your node's network identity and it is unrecoverable.

*Arc is a trademark of Circle Internet Group, Inc. and/or its affiliates.*
