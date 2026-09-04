# Axelar Amplifier Verifier Setup

Amplifier is a separate verification plane from the classic Axelar validator. Build and monitor it as an independent stack:

- a dedicated Axelar full node;
- a dedicated `tofnd` instance that is never shared with classic `vald`;
- `ampd`;
- one independently supervised handler/client process per supported chain.

Official sources:

- [Amplifier verifier onboarding](https://docs.axelar.dev/validator/amplifier/verifier-onboarding/)
- [Axelar Amplifier documentation](https://docs.axelar.dev/dev/amplifier/)
- [Axelar deployments registry](https://github.com/axelarnetwork/axelar-contract-deployments)
- Reviewed Axelar docs source: `1e9fedd2c70043c612f3febdad94e3da3acb5335`

Amplifier evolves independently from Axelar Core. Refresh current `tofnd`, `ampd`, handler, chain-registry, contract-deployment, funding, bonding, key-registration, chain-support, and authorization requirements before each deployment.

## 1. Inventory and isolation

Record:

- environment and Axelar chain ID;
- dedicated Axelar node host, service, RPC, gRPC, home, and version;
- dedicated Amplifier `tofnd` host, service, state path, key-custody reference, and private listener;
- `ampd` source commit, binary/container digest, service, config path, state path, and private gRPC listener;
- one handler/client source commit, config, service, source-chain endpoint, finality policy, and metrics endpoint for each supported chain;
- service-registry, voting-verifier, multisig, and rewards contract addresses from the exact deployment registry;
- operator address, fee balance policy, expected key types, expected supported chains, and authorization status;
- backup, rollback, monitoring, and alert owners.

Reject a design that shares the classic validator's node or `tofnd`, exposes signer or handler control ports publicly, uses moving container tags, or cannot identify every handler failure independently.

## 2. Prepare the dedicated Axelar node

Install and synchronize the node through the normal Axelar Node Ops flow. Before connecting `ampd`, prove:

- exact expected chain ID and release;
- fresh advancing height and `catching_up=false`;
- healthy peers and stable restart count;
- private RPC/gRPC reachability from only the intended `ampd` host;
- disk and inode headroom for the observation period;
- no classic consensus or `vald` signer state is present on this host.

## 3. Prepare Amplifier `tofnd`

Use a separate binary and state directory from classic `tofnd`. Verify release provenance and checksum, restrict the listener to loopback or the approved private network, and allow only the intended `ampd` client.

Create, back up, and restore-test its encrypted mnemonic through the operator custody runbook. Do not publish key-creation commands, password values, mnemonics, export files, or private listener addresses.

## 4. Configure `ampd`

Bind `ampd` to:

- the exact Axelar node RPC/gRPC interfaces;
- the dedicated Amplifier `tofnd` endpoint;
- the current service-registry deployment;
- the reviewed broadcast and fee policy;
- the exact chain registry consumed by the handlers;
- private status, metrics, and handler gRPC interfaces.

Pin source and binary/container digests. Validate configuration syntax before starting. Supervise `ampd` independently from its node, `tofnd`, and every handler so that one crash does not restart unrelated components.

## 5. Configure one handler per chain

Each supported chain needs a one-to-one match across:

1. on-chain verifier support;
2. `ampd` chain registry;
3. handler configuration;
4. supervised handler/client process;
5. source-chain full node, light client, or reviewed RPC;
6. finality and reorg policy;
7. monitoring and alert ownership.

The handler's chain name, network identity, contracts, RPC methods, finality depth, start height, and expected key type must match current official deployment data. Never reuse a devnet/testnet address on mainnet.

Source-chain RPC options follow the same production criteria as classic external-chain maintenance:

- self-host when control and reliability justify the hardware/operations cost;
- use a paid provider when its methods, limits, history, finality, redundancy, and fallback are proven;
- use public RPC only as a bounded comparison or emergency source unless its service contract and observed capacity support production duties.

Keep credentials outside the repository and Hub.

## 6. On-chain activation

Funding, bonding, ECDSA/Ed25519 public-key registration, chain-support registration, and authorization are signed or governance-controlled actions. Prepare them from current official documentation, review every field, and execute them only through the operator-controlled approval and wallet workflow.

After activation, query public chain state and prove:

- expected verifier identity is bonded and authorized;
- registered key types match every intended chain;
- registered chain support exactly matches configuration and running handlers;
- fee balance is above threshold;
- no stale or duplicate verifier process is active elsewhere.

## 7. Read-only health inventory

This diagnostic reads process and loopback-listener state only. Adapt exact service and port names to inventory:

```bash
set -Eeuo pipefail
systemctl show ampd tofnd-amplifier \
  -p ActiveState -p SubState -p NRestarts --no-pager
systemctl list-units --type=service --all --no-pager | grep -E '(ampd|handler)' || true
ss -lnt | grep -E '127\.0\.0\.1:(50051|9090)' || true
```

It does not create keys, register support, authorize, start, stop, restart, sign, or broadcast.

## 8. Monitoring and acceptance

Require independent evidence for:

- dedicated Axelar node identity, height movement, block age, sync state, peers, RPC/gRPC, disk, and restarts;
- Amplifier `tofnd` process, private reachability, restarts, and bounded signing-session errors without reading key material;
- `ampd` process/state progression, private gRPC, broadcast queue, fee balance, transaction inclusion, votes, and multisig proofs;
- each handler process, `ampd` connection, exact chain name, source RPC identity/finality/latency, and last successful vote/signing activity;
- on-chain bonded/authorized state, key registrations, chain-support parity, and expected verifier coverage;
- reward distributions, missed/unsubmitted votes and proofs, source-chain reorg/finality faults, CPU/RAM, disk/inodes, clock sync, backups, and alert delivery.

Test failure isolation: one handler incident must not stop `ampd`, `tofnd`, another handler, the dedicated Axelar node, or the classic validator stack.

## Rollback boundary

Retain previous binaries, digests, configuration, state backups, and contract-registry references until the observation window passes. If chain identity, signer uniqueness, contract deployment, handler parity, or authorization cannot be proved, keep the affected verifier duty inactive and restore the exact reviewed rollback point.
