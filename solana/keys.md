# Solana Validator Keys

Solana gives a validator three keypairs with three completely different risk
profiles. Treating them as one bundle is the most common and most expensive
mistake an operator makes.

| Keypair | Lives on | If stolen | If lost |
|---|---|---|---|
| **Identity** | the validator host, readable by the service user | attacker can run a node as you and get you into duplicate-block trouble | you cannot sign votes or blocks; recover from backup |
| **Vote account** | nowhere after creation — only its pubkey matters | nothing directly | nothing; the account already exists on chain |
| **Authorized withdrawer** | offline, never on the validator | **total loss of the vote account and its rewards** | you can never withdraw rewards or change the vote account again |

The withdrawer is the only one that is irrecoverable and the only one that
carries value. It must never be copied to the validator host, not even briefly.

## Generate

Generate on a trusted workstation, not on the server.

````bash
solana-keygen new -o validator-keypair.json
solana-keygen new -o vote-account-keypair.json
solana-keygen new -o authorized-withdrawer-keypair.json
````

Read the public keys back:

````bash
solana-keygen pubkey validator-keypair.json
solana-keygen pubkey vote-account-keypair.json
solana-keygen pubkey authorized-withdrawer-keypair.json
````

A vanity identity is cosmetic but common. Grinding a 5-character prefix is
minutes; longer prefixes escalate quickly:

````bash
solana-keygen grind --starts-with pstmn:1
solana-keygen grind --use-mnemonic --starts-with pstmn:1   # recoverable, much slower
````

`--no-outfile` prints a seed phrase and writes nothing to disk, which is the
right choice for the withdrawer if you intend to hold it on paper or in a
hardware wallet.

## Verify before you trust a backup

A backup you have never restored is a hope, not a backup. Restore into a scratch
directory and compare the pubkey:

````bash
solana-keygen pubkey /path/to/restored/validator-keypair.json
solana-keygen verify <expected-pubkey> /path/to/restored/validator-keypair.json
````

`verify` exits non-zero on a mismatch, so it is safe to put in a check script.

## Put them in place

Only two files belong on the validator:

````bash
scp validator-keypair.json  sol@<host>:/home/sol/
scp vote-account-keypair.json sol@<host>:/home/sol/
````

````bash
chmod 600 /home/sol/validator-keypair.json /home/sol/vote-account-keypair.json
chown sol:sol /home/sol/*.json
````

The vote account keypair is not secret after creation — the validator uses only
its public key — but there is no reason to leave it world-readable.

## The unstaked spare identity

Every production Solana validator should have a second identity keypair that
holds **no stake**. It is the mechanism behind every safe restart and every
zero-downtime upgrade:

````bash
solana-keygen new -o /home/sol/unstaked-identity.json
````

The pattern is:

1. the running node is switched to the unstaked identity, and it stops voting;
2. the tower file is copied to the target node;
3. the target node takes over the staked identity and resumes voting.

````bash
agave-validator --ledger /mnt/ledger set-identity /home/sol/unstaked-identity.json
agave-validator --ledger /mnt/ledger set-identity --require-tower /home/sol/validator-keypair.json
````

`--require-tower` refuses to take the staked identity without a valid tower
file. That refusal is the protection: it is what stops two hosts voting on the
same identity. Never bypass it to "save time" during an incident.

**One identity, one voting process. Ever.** Two nodes voting with the same
identity on different forks produce duplicate votes, and the cluster treats that
as misbehaviour. There is no uptime target that justifies the risk.

## Tower file

`tower-1_9-<identity-pubkey>.bin` in the ledger directory is the validator's
record of what it has already voted on. It is small, it is local, and it is the
thing that makes an identity transfer safe.

- do not delete it to "fix" a stuck node;
- do copy it when you move an identity between hosts;
- do not copy it anywhere else.

## Vote account authorities

The vote account has two authorities and they rotate independently:

````bash
# rotate the voter (routine, e.g. new identity)
solana vote-authorize-voter-checked <vote-account> <current-authority> <new-voter-keypair>

# rotate the withdrawer (rare, high consequence)
solana vote-authorize-withdrawer-checked <vote-account> <current-withdrawer> <new-withdrawer-keypair>
````

The `-checked` variants require the new authority to sign as well, which makes
it impossible to hand authority to a key you do not actually hold. Use them.
Never use the unchecked forms on mainnet.

Read the current state before and after any rotation:

````bash
solana vote-account <vote-account-pubkey>
````

## Commission

Commission changes are rate-limited by the cluster and visible to every
delegator. Announce them; do not surprise stake.

````bash
solana vote-update-commission <vote-account> <percent> <withdrawer-keypair>
````

## Custody checklist

- [ ] withdrawer generated on a trusted machine, never on the validator
- [ ] withdrawer held offline — hardware wallet, paper, or multisig
- [ ] identity backed up, and the backup **restore-tested** against its pubkey
- [ ] unstaked spare identity generated and present on the host
- [ ] key files mode `600`, owned by the service user
- [ ] no keypair in a git repository, a chat message, a ticket or a screenshot
- [ ] documented who holds the withdrawer and how a second person reaches it

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
