# Solana Testnet Keys

The key model is identical to mainnet — identity, vote account, authorized
withdrawer, plus an unstaked spare identity. What changes on testnet is the
temptation to be careless, and the two rules that exist to stop it.

## Rule 1 — never reuse the mainnet identity

Generate a separate set for testnet:

````bash
solana-keygen new -o ~/testnet-validator-keypair.json
solana-keygen new -o ~/testnet-vote-account-keypair.json
solana-keygen new -o ~/testnet-authorized-withdrawer-keypair.json
solana-keygen new -o ~/testnet-unstaked-identity.json
````

Reusing one identity across clusters means one file on one host is the single
point of failure for both, and it makes the "one identity, one running process"
rule impossible to reason about during an incident.

## Rule 2 — testnet keys are still keys

Testnet SOL is worthless. The habits are not.

- withdrawer generated on a workstation, not on the validator;
- key files `chmod 600`, owned by the service user;
- no keypair in a repository, a chat message, a ticket or a screenshot;
- identity backup restore-tested against its pubkey.

Every bad habit formed on testnet gets carried to mainnet by the same hands.

## The spare identity and the tower

Testnet is where you practise the handover you will one day do under pressure on
mainnet. Do it deliberately, more than once:

````bash
# node currently voting gives up the staked identity
agave-validator --ledger /mnt/ledger set-identity ~/testnet-unstaked-identity.json

# copy the tower to the receiving node
scp /mnt/ledger/tower-1_9-<identity-pubkey>.bin sol@<spare>:/mnt/ledger/

# receiving node takes the staked identity, refusing without a valid tower
agave-validator --ledger /mnt/ledger set-identity --require-tower ~/testnet-validator-keypair.json
````

`--require-tower` refusing is the protection working. Learn what a refusal looks
like here, where it costs nothing.

## Funding

The identity pays vote fees, so it needs test SOL:

````bash
solana config set --url https://api.testnet.solana.com
solana airdrop 1
solana balance
````

One SOL per faucet request. A validator burns it; set an alert on the identity
balance rather than discovering it through delinquency.

## Vote account

````bash
solana create-vote-account \
  --fee-payer ~/testnet-validator-keypair.json \
  ~/testnet-vote-account-keypair.json \
  ~/testnet-validator-keypair.json \
  ~/testnet-authorized-withdrawer-keypair.json
````

Then set the BLS public key for the authorized voter, the same as on mainnet:

````bash
solana-keygen bls_pubkey ~/testnet-validator-keypair.json
solana vote-authorize-voter-checked <vote-account> ~/testnet-validator-keypair.json ~/testnet-validator-keypair.json
solana vote-account <vote-account> | grep "BLS Public Key"
````

There is no commission cap on testnet, but SFDP still grades vote credits and
skip rate here — the commission is the only criterion that is genuinely relaxed.

## Verify a backup

````bash
solana-keygen pubkey /path/to/restored/testnet-validator-keypair.json
solana-keygen verify <expected-pubkey> /path/to/restored/testnet-validator-keypair.json
````

Non-zero exit on mismatch, so it belongs in a check script — on both clusters.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
