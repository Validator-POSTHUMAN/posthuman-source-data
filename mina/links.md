# Mina Endpoints, Explorers and Tools

## POSTHUMAN

| | |
|---|---|
| Block producer public key | `B62qrnPdz8HpsDJfGHirDLpVrN2VeyeitdaTKBaccWtHpeVW9Hgwi75` |
| Delegations | <https://minascan.io/mainnet/validator/B62qrnPdz8HpsDJfGHirDLpVrN2VeyeitdaTKBaccWtHpeVW9Hgwi75/delegations> |
| Website | <https://posthuman.digital> |

## Network identity

Check these against your own node after every version change — they are what
proves which network you joined.

| | Mainnet | Devnet |
|---|---|---|
| Chain ID | `0718f61ab88f9d0fa643ff4dc3a3d5998dd6d51a6008b2b0339b0dbb26133886` | `ebfce0d570bc22eb041e1a7b0a46bbc3ed5d0a1030ef2ab5e36eef908b93eba8` |
| Git SHA-1 | `685030107ff328e59936410a0e72ddaca59cb9d6` | `6965b502ecd7959d50e4a9116529406ed44e85a8` |
| Debian package | `mina-mainnet=4.0.0-6850301` | `mina-devnet=4.0.0-6965b50` |
| Docker daemon | `minaprotocol/mina-daemon:4.0.0-6850301-CODENAME-mainnet` | `minaprotocol/mina-daemon:4.0.0-6965b50-CODENAME-devnet` |

Devnet values come from the `4.0.0-devnet-mesa` release notes. Devnet is reset
and re-forked more often than mainnet — re-read the latest devnet release before
trusting any of it.

## Peer lists

| Network | URL |
|---|---|
| Mainnet | <https://bootnodes.minaprotocol.com/networks/mainnet.txt> |
| Devnet | <https://storage.googleapis.com/o1labs-gitops-infrastructure/devnet/seed-list-devnet.txt> |
| Mainnet (legacy) | `https://storage.googleapis.com/mina-seed-lists/mainnet_seeds.txt` |

The legacy list still works and is what the Debian package bakes into its
systemd unit, but the maintained list is the `bootnodes.minaprotocol.com` one.
Override `PEERS_LIST_URL` in `~/.mina-env` — see the **Installation guide**.

## Public GraphQL endpoints

Useful as an independent second opinion on height, chain ID and epoch. Do not
build production tooling on somebody else's node.

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ syncStatus daemonStatus { blockchainLength chainId commitId } }"}' | jq
````

| Network | Endpoint |
|---|---|
| Mainnet | `https://api.minascan.io/node/mainnet/v1/graphql` |
| Devnet | `https://api.minascan.io/node/devnet/v1/graphql` |

Your own node serves the same API at `http://127.0.0.1:3085/graphql`.

## Explorers

| Explorer | Good for |
|---|---|
| [Minascan](https://minascan.io/mainnet/home) | blocks, accounts, validators and delegations, zkApps, staking UI |
| [Minataur](https://minataur.net/) | fast block and account lookup, uptime leaderboard mirror |

Validator page pattern: `https://minascan.io/mainnet/validator/<PUBLIC_KEY>/delegations`
Account page pattern: `https://minataur.net/account/<PUBLIC_KEY>`

## Delegation program

| | |
|---|---|
| Official uptime leaderboard | <https://uptime.minaprotocol.com> |
| Community leaderboard | <https://minataur.net/uptime> |
| Uptime submission endpoint | `https://uptime-backend.minaprotocol.com/v1/submit` |
| Payout script (mandatory for the Foundation program) | <https://github.com/jrwashburn/mina-pool-payout> |
| Foundation delegation policy | <https://minaprotocol.com/blog/mina-foundation-delegation-policy> |

## Archive data

| | |
|---|---|
| Public archive dumps (hourly, ~1.6 GB compressed) | <https://storage.googleapis.com/mina-archive-dumps/> |
| Archive schema | [`create_schema.sql`](https://github.com/MinaProtocol/mina/blob/4.0.0-mainnet-mesa/src/app/archive/create_schema.sql) |

List what exists rather than guessing a filename:

````bash
curl -s "https://storage.googleapis.com/storage/v1/b/mina-archive-dumps/o?prefix=mainnet-archive-dump-$(date -u +%F)&fields=items(name,size,updated)" | jq -r '.items[].name'
````

## Wallets

| Wallet | Notes |
|---|---|
| [Auro Wallet](https://www.aurowallet.com/) | browser extension and mobile; injects `window.mina` for dApps; `sendStakeDelegation` for staking |
| [Ledger](https://www.ledger.com/) | cold storage and delegation signing; **cannot** run a block producer |

A Ledger cannot produce blocks: the VRF evaluation and the blockchain SNARK both
need the raw private key. See **Keys**.

## Official resources

| | |
|---|---|
| Documentation | <https://docs.minaprotocol.com/node-operators> |
| Releases | <https://github.com/MinaProtocol/mina/releases> |
| Source | <https://github.com/MinaProtocol/mina> |
| Issues | <https://github.com/MinaProtocol/mina/issues> |
| Website | <https://minaprotocol.com> |
| Discord | <https://discord.gg/minaprotocol> |
| X | <https://x.com/MinaProtocol> |

## Ports

| Port | Purpose | Exposure |
|---|---|---|
| `8302/tcp` | libp2p P2P | public |
| `8301/tcp` | client RPC, SNARK coordinator ↔ worker | private only |
| `3085/tcp` | GraphQL / REST | loopback only |
| `3086/tcp` | archive server port | private only |
| `6060` / `6061` | Prometheus daemon / libp2p metrics | private only |

## Related guides

- **Installation guide** / **Install (Docker)**
- **Monitoring**, **Security hardening**, **Upgrades**
- **Delegation program**, **Archive node**
