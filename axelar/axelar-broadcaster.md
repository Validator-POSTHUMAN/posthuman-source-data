# Axelar Broadcaster Proxy

A classic Axelar validator uses a dedicated broadcaster account for `vald` protocol transactions. The broadcaster and validator are separate accounts, and the validator-to-broadcaster proxy mapping is immutable for the lifetime of the validator.

Official sources:

- [Register broadcaster proxy](https://docs.axelar.dev/validator/setup/register-broadcaster/)
- [Create and back up accounts](https://docs.axelar.dev/validator/setup/backup/)
- [External-chain maintenance](https://docs.axelar.dev/validator/external-chains/overview/)
- Reviewed Axelar docs source: `1e9fedd2c70043c612f3febdad94e3da3acb5335`

Refresh the official commands, fees, and chain parameters before use.

## Preconditions

Record and independently verify:

- expected chain ID `axelar-dojo-1`;
- validator operator address and its separately protected signer;
- broadcaster address and its separately protected keyring entry;
- exact `vald` service and every other process able to use the broadcaster;
- current account number, sequence, balance, minimum fee, and gas policy;
- rollback owner and the operator who will review the signed transaction.

Create and back up the validator and broadcaster accounts only through the operator custody runbook. Never paste a mnemonic, keyring password, private key, or credential into the Hub, a shell command line, a ticket, or chat.

## 1. Check the current mapping

Use the public validator operator address only:

```bash
axelard query snapshot proxy <validator-operator-address> \
  --node http://127.0.0.1:26657 \
  --output json
```

Stop if the validator already maps to an unexpected broadcaster. Do not try to overwrite or repair the mapping by broadcasting another transaction.

## 2. Verify funding and sequence ownership

The broadcaster pays for `vald` transactions. Define an alert threshold from observed fee consumption and refill lead time, not from a fixed example amount.

Before registration or another manual broadcaster transaction:

- verify the address and denom from chain state;
- check current balance, account number, and sequence;
- make sure `vald` and maintenance scripts cannot submit concurrently;
- preserve bounded `vald` logs and recent transaction evidence;
- confirm the intended transaction signer is the validator account where required by the current official workflow.

Concurrent use can cause sequence mismatch failures and missed protocol votes. A maintenance command must not race with `vald`.

## 3. Generate an unsigned registration document

This template deliberately retains placeholders and stops at `--generate-only`:

```bash
set -Eeuo pipefail
VALIDATOR_KEY='<validator-key-name>'
BROADCASTER_ADDR='<broadcaster-account-address>'
CHAIN_ID='axelar-dojo-1'

test "$VALIDATOR_KEY" != '<validator-key-name>'
test "$BROADCASTER_ADDR" != '<broadcaster-account-address>'

axelard tx snapshot register-proxy "$BROADCASTER_ADDR" \
  --from "$VALIDATOR_KEY" \
  --chain-id "$CHAIN_ID" \
  --node http://127.0.0.1:26657 \
  --gas auto \
  --gas-adjustment 1.4 \
  --generate-only > register-broadcaster.unsigned.json

jq empty register-broadcaster.unsigned.json
```

Inspect the unsigned document independently. Verify message type, chain ID, validator signer, broadcaster address, fee, gas, account number, and sequence. The Hub does not sign or broadcast it.

## 4. Sign and broadcast separately

Signing and broadcast require the operator-controlled wallet workflow and a separate approval. Keep the reviewed unsigned file immutable between review and signing. Record the resulting transaction hash without exposing key material.

After inclusion, require all of the following:

- successful transaction code at the expected height;
- exact validator-to-broadcaster proxy mapping from a fresh query;
- broadcaster balance above its alert threshold;
- expected account sequence;
- healthy `vald` submission after it resumes;
- no duplicate broadcaster process or recurring sequence error.

## 5. Continuous monitoring

Alert on:

- proxy mapping missing or different from inventory;
- low broadcaster balance and accelerated fee consumption;
- account sequence mismatch or concurrent-account-use evidence;
- out-of-gas, failed inclusion, rejected message, timeout, panic, or fatal errors;
- missing heartbeat, late/missing external-chain votes, or a drop in successful `vald` transactions;
- keyring or `tofnd` reachability faults without reading secret contents.

A replacement broadcaster means creating a new validator identity under the current Axelar protocol. Treat that as validator onboarding, not as routine account rotation.
