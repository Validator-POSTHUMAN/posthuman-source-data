# Monad FastLane Sidecar

POSTHUMAN maintains a public validator-facing guide and AI-agent skill for
FastLane / shMonad MEV sidecar operations on Monad validators.

## Validator Guide

- [Monad FastLane Sidecar Guide for Validators](https://github.com/Validator-POSTHUMAN/contributions/blob/main/guides/monad-fastlane-sidecar-guide.md)

## AI Skill

- [FastLane Sidecar Ops Skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fastlane-sidecar/SKILL.md)
- [Inventory schema](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fastlane-sidecar/references/inventory.schema.json)
- [Example inventory](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fastlane-sidecar/examples/inventory.example.json)
- [Healthcheck helper](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/fastlane-sidecar/scripts/fastlane-sidecar-healthcheck.sh)

## Scope

The guide and skill cover:

- shMonad onboarding order;
- beneficiary / coinbase prerequisites;
- FastLane dedicated fullnodes;
- segregated Monad mempool IPC socket;
- rootless Docker isolation;
- release digest, signature, and provenance verification;
- health checks, monitoring, upgrades, and rollback.

Operators should always re-read the current official shMonad / FastLane docs
before production installation or upgrade.
