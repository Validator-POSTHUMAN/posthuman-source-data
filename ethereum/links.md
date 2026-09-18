# Ethereum Endpoints and References

**POSTHUMAN does not currently operate a public Ethereum RPC endpoint.**
Everything listed below is third-party. Verify a provider yourself before
pointing production infrastructure at it, and never point a validator's Engine
API at anything but your own local execution client.

---

## Network identity

| | Mainnet | Hoodi | Sepolia |
|---|---|---|---|
| Chain ID | `1` | `560048` | `11155111` |
| Deposit contract | `0x00000000219ab540356cBB839Cbe05303d7705Fa` | `0x00000000219ab540356cBB839Cbe05303d7705Fa` | `0x7f02C3E3c98b133055B8B348B2Ac625669Ed295D` |
| Config | [eth-clients/mainnet](https://github.com/eth-clients/mainnet) | [eth-clients/hoodi](https://github.com/eth-clients/hoodi) | [eth-clients/sepolia](https://github.com/eth-clients/sepolia) |

Pectra system contracts, used for exits, partial withdrawals and consolidations:

| Purpose | Address | EIP |
|---|---|---|
| Withdrawal request | `0x00000961Ef480Eb55e80D19ad83579A64c007002` | [EIP-7002](https://eips.ethereum.org/EIPS/eip-7002) |
| Consolidation request | `0x0000BBdDc7CE488642fb579F8B00f3a590007251` | [EIP-7251](https://eips.ethereum.org/EIPS/eip-7251) |

---

## Public JSON-RPC

Free, keyless, rate-limited. Fine for a script or a health check; not something
to build a product on without an agreement.

| Endpoint | Operator |
|---|---|
| `https://ethereum-rpc.publicnode.com` | Allnodes |
| `https://eth.llamarpc.com` | LlamaNodes |
| `https://rpc.ankr.com/eth` | Ankr |
| `https://cloudflare-eth.com` | Cloudflare |

The maintained community list is
[chainlist.org](https://chainlist.org/chain/1), which reports latency and
privacy policy per endpoint.

**Do not use a public RPC as a validator's execution client.** The Engine API is
not a public interface, the trust model is wrong, and the latency will cost you
attestations.

---

## Checkpoint sync

Used once, at first start of a beacon node, to fetch a finalised state. This is
a trust assumption for one state root — take the checkpoint from one provider
and verify the resulting head against another.

The maintained list is
[eth-clients/checkpoint-sync-endpoints](https://github.com/eth-clients/checkpoint-sync-endpoints).
Commonly used mainnet providers include `beaconstate.info`,
`mainnet.checkpoint.sigp.io` and `sync-mainnet.beaconcha.in`; Hoodi's is
`checkpoint-sync.hoodi.ethpandaops.io`.

---

## Explorers

| Explorer | Use |
|---|---|
| [etherscan.io](https://etherscan.io/) | The default execution-layer explorer: transactions, contracts, verified source |
| [beaconcha.in](https://beaconcha.in/) | **The one an operator needs** — validators, attestation effectiveness, proposals, watchlists and alerts |
| [blockscout.com](https://eth.blockscout.com/) | Open-source explorer; self-hostable |
| [otterscan.io](https://otterscan.io/) | Lightweight explorer that runs against your own Erigon/Reth archive node |
| [ethplorer.io](https://ethplorer.io/) | Token-centric views and holder distribution |
| [ethernodes.org](https://ethernodes.org/) | Execution client and hosting distribution |
| [nodewatch.io](https://www.nodewatch.io/) | Consensus-layer crawler |
| [rated.network](https://www.rated.network/) | Operator-level validator performance ratings |
| [clientdiversity.org](https://clientdiversity.org/) | Client share against the 33% and 66% thresholds |

---

## Official documentation

- [ethereum.org — Nodes and clients](https://ethereum.org/developers/docs/nodes-and-clients/)
- [ethereum.org — Run a node](https://ethereum.org/run-a-node/)
- [ethereum.org — Home staking](https://ethereum.org/staking/solo/)
- [Staking Launchpad](https://launchpad.ethereum.org/)
- [EF Protocol Announcements](https://blog.ethereum.org/category/protocol)
- [Ethereum Improvement Proposals](https://eips.ethereum.org/)
- [Execution specs](https://github.com/ethereum/execution-specs) · [Consensus specs](https://github.com/ethereum/consensus-specs)

## Client documentation

| Client | Docs |
|---|---|
| Geth | [geth.ethereum.org](https://geth.ethereum.org/docs) |
| Nethermind | [docs.nethermind.io](https://docs.nethermind.io/) |
| Besu | [besu.hyperledger.org](https://besu.hyperledger.org/) |
| Reth | [reth.rs](https://reth.rs/) |
| Erigon | [docs.erigon.tech](https://docs.erigon.tech/) |
| Lighthouse | [lighthouse-book.sigmaprime.io](https://lighthouse-book.sigmaprime.io/) |
| Prysm | [docs.prylabs.network](https://docs.prylabs.network/) |
| Teku | [docs.teku.consensys.net](https://docs.teku.consensys.net/) |
| Nimbus | [nimbus.guide](https://nimbus.guide/) |
| Lodestar | [chainsafe.github.io/lodestar](https://chainsafe.github.io/lodestar/) |
| eth-docker | [ethdocker.com](https://ethdocker.com/) |
