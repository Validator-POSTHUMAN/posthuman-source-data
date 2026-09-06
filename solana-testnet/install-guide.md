# Solana Testnet Validator Installation Guide

## About the testnet cluster

Solana's `testnet` cluster is where new releases are exercised before mainnet.
It is not a low-stakes toy: testnet runs the same software under real load, and
operating there is the accepted way to demonstrate competence before taking on
mainnet stake. It is also where the Solana Foundation Delegation Program looks
for a track record.

Differences from mainnet that change what you do:

- **Restarts and cluster restarts are normal.** Testnet is upgraded first and
  occasionally restarted from a snapshot by coordination. Being ready to follow
  a restart announcement is part of the job here in a way it is not on mainnet.
- **Hardware requirements are lower**, but not trivially so — testnet
  frequently runs heavier synthetic load than mainnet.
- **SOL is worthless here**, but the vote account still needs a balance,
  because voting still costs fees. A testnet validator that stops voting has
  usually just run out of test SOL.
- If you intend to apply to a delegation program, note that the client you run
  on testnet and mainnet is expected to match. Switching clients on only one of
  the two can disqualify you.

The install procedure is the mainnet one. This page states the deltas.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 12 cores / 24 threads | 24+ cores |
| RAM       | 128 GB  | 256 GB      |
| Ledger disk | 1 TB NVMe | 1 TB NVMe, dedicated |
| Accounts disk | 500 GB NVMe | 500 GB NVMe, dedicated |
| Network   | 1 Gbps  | 10 Gbps     |

Ledger, accounts and snapshots on separate filesystems, off root — same rule as
mainnet, same consequence when ignored.

## Point the CLI at testnet

````bash
solana config set --url https://api.testnet.solana.com
solana config get
````

## Keys and vote account

Generate a **separate** identity and vote account for testnet. Never reuse the
mainnet identity keypair on testnet — one identity, one running process, per
cluster:

````bash
solana-keygen new -o ~/testnet-validator-keypair.json
solana-keygen new -o ~/testnet-vote-account-keypair.json
solana-keygen new -o ~/testnet-authorized-withdrawer-keypair.json
````

Fund the identity from the faucet, then create the vote account:

````bash
solana airdrop 5 ~/testnet-validator-keypair.json
solana create-vote-account ~/testnet-vote-account-keypair.json \
  ~/testnet-validator-keypair.json ~/testnet-authorized-withdrawer-keypair.json
````

## Unit differences

Use the mainnet unit as the template and change the cluster wiring:

````
  --entrypoint entrypoint.testnet.solana.com:8001 \
  --entrypoint entrypoint2.testnet.solana.com:8001 \
  --entrypoint entrypoint3.testnet.solana.com:8001 \
  --known-validator 5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on \
  --expected-genesis-hash 4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY \
  --only-known-rpc \
  --wal-recovery-mode skip_any_corrupted_record \
  --limit-ledger-size
````

`--expected-genesis-hash` is worth setting explicitly. It is the cheapest
guarantee that a misconfigured entrypoint has not quietly joined you to a
different cluster.

## Verify

````bash
solana catchup --our-localhost
solana validators --url https://api.testnet.solana.com | grep <your-identity-pubkey>
solana vote-account <your-vote-account-pubkey> --url https://api.testnet.solana.com
````

As on mainnet, the only real health signals are external: `delinquent=false`, a
fresh `lastVote`, and an advancing `rootSlot`.

## Following a cluster restart

Testnet restarts are announced with a specific slot and snapshot hash. When one
happens:

1. stop the validator;
2. follow the announced procedure exactly — usually a hard fork at a named slot
   with specific flags;
3. start, then confirm your node is on the announced fork by comparing your
   block hash at a common slot with a public testnet RPC, not just your height.

Equal height on a different fork is the failure that looks like success.

## Monitoring

Same as mainnet, plus: vote account balance (top it up from the faucet before it
empties) and awareness of the release and restart announcements for the cluster.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
