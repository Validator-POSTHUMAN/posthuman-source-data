# Ethereum Testnets for Operators

There is one testnet a staking operator should care about, and it is **Hoodi**.
Everything else on this page is context.

| Network | Chain ID | For | Validator set |
|---|---|---|---|
| **Hoodi** | `560048` | Staking, validator lifecycle, protocol upgrades | **Open** — anyone can run one |
| Sepolia | `11155111` | Contract and application development | Permissioned |
| Ephemery | rotating | Throwaway testing; resets every 28 days | Open |
| Holesky | — | **Deprecated since September 2025** | — |

Holesky is shut down. Any runbook, script or dashboard still pointing at it is
stale and should be repointed at Hoodi.

---

## Hoodi

The testnet that exists so stakers can rehearse. It forks before mainnet, it has
an open validator set, and it is where a fork upgrade should be tested a week
before the mainnet slot.

| | |
|---|---|
| Chain ID / network ID | `560048` |
| Deposit contract | `0x00000000219ab540356cBB839Cbe05303d7705Fa` |
| Launchpad | `hoodi.launchpad.ethereum.org` |
| Explorer | [hoodi.etherscan.io](https://hoodi.etherscan.io/) · [explorer.hoodi.ethpandaops.io](https://explorer.hoodi.ethpandaops.io/) · [hoodi.otterscan.io](https://hoodi.otterscan.io/) |
| Checkpoint sync | `https://checkpoint-sync.hoodi.ethpandaops.io/` |
| Faucets | [hoodi.ethpandaops.io](https://hoodi.ethpandaops.io/) · [hoodi-faucet.pk910.de](https://hoodi-faucet.pk910.de/) |
| Config | [eth-clients/hoodi](https://github.com/eth-clients/hoodi) |

Running a node on Hoodi is the mainnet procedure with the network name changed:

````bash
# execution
--hoodi                      # Geth
--config hoodi               # Nethermind
--network=hoodi              # Besu
--chain hoodi                # Reth

# consensus
--network hoodi              # Lighthouse, Lodestar
--hoodi                      # Prysm
--network=hoodi              # Teku, Nimbus
````

eth-docker: choose `hoodi` in `./ethd config`.

**Keep a Hoodi validator running permanently.** It is the only way to test a
fork, a client swap, a key migration or an exit before doing it with real money,
and the cost is one small VPS. POSTHUMAN has operated Hoodi validators and SSV
operators for exactly this purpose.

### What to rehearse there

- The full key generation → deposit → activation flow
- A client swap in both directions
- A host migration, including the slashing protection export and import
- A voluntary exit, and an execution-layer triggered exit (EIP-7002)
- A `0x01` → `0x02` credential change and a consolidation (EIP-7251)
- Every network upgrade, before mainnet

---

## Sepolia

For contract and application work, not for staking — the validator set is
permissioned and you cannot join it.

| | |
|---|---|
| Chain ID | `11155111` |
| Deposit contract | `0x7f02C3E3c98b133055B8B348B2Ac625669Ed295D` |
| Explorer | [sepolia.etherscan.io](https://sepolia.etherscan.io/) · [eth-sepolia.blockscout.com](https://eth-sepolia.blockscout.com/) |
| Config | [eth-clients/sepolia](https://github.com/eth-clients/sepolia) |

Sepolia's state is small, so a node syncs quickly — it is a good place to test an
RPC integration without waiting a day.

---

## Ephemery

Resets to genesis every 28 days. Useful when you want a clean chain, a fast
bootstrap and free funds, and you do not care about anything persisting.
Under 5 GB.

- [ephemery.dev](https://ephemery.dev/) · [ephemery-testnet resources](https://github.com/ephemery-testnet/ephemery-resources)

---

## Rules that apply to all of them

- **Never reuse a mainnet mnemonic on a testnet, or a testnet mnemonic on
  mainnet.** Generate separate key material.
- Testnet ETH has no value. Anyone offering to sell it is running a scam.
- A testnet validator can be slashed the same way a mainnet one can. Rehearse
  the safe procedure, not a sloppy one — the point is to build the habit.

## Sources

- [ethereum.org — Networks](https://ethereum.org/developers/docs/networks/)
- [eth-clients/hoodi](https://github.com/eth-clients/hoodi) · [eth-clients/sepolia](https://github.com/eth-clients/sepolia)
- [Holesky shutdown announcement](https://blog.ethereum.org/2025/09/01/holesky-shutdown-announcement)
