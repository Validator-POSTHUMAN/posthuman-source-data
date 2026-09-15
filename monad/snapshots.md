# Monad Mainnet snapshot safety

## Published catalog

| Field | Value |
| --- | --- |
| Network | Monad Mainnet |
| Chain ID | `143` (`0x8f`) |
| POSTHUMAN metadata root | https://snapshots.posthuman.digital/monad/mainnet |
| Official archive guidance | [Archive data](https://docs.monad.xyz/node-ops/archive-data/) |

A snapshot is a recovery/bootstrap artifact, not proof of complete historical coverage or a substitute for an independent backup.

## Import is intentionally not runnable here

Step-3 review found a previously observed `v0.12.x` snapshot metadata label while official node documentation names `0.16.2`. That proves neither compatibility nor incompatibility. Until format, producer/consumer version, exact checksum, chain identity, height/freshness, capacity and rollback are independently proven, this page must not publish a runnable import workflow.

## Read-only acceptance checklist

Verify expected network/chain, record artifact/checksum/height/time/format, prove capacity and rollback, preserve identity/configuration and prove signer uniqueness. After an approved recovery, independently verify identity, advancing state and monitoring before returning to duty. Never mix mainnet and testnet artifacts. This page downloads or imports nothing.
