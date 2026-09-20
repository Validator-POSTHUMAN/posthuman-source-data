# Solana Testnet Upgrades and Cluster Restarts

Testnet gets new releases first, and it is restarted by coordination in a way
mainnet is not. Two consequences: your upgrade cadence has to be faster here,
and "follow the restart announcement" is a routine operation rather than an
incident response.

## Upgrade cadence

The SFDP minimum version moves **48 hours after the supermajority adopts it**,
and testnet reaches supermajority first. A monthly upgrade rhythm that is fine
on mainnet will drop you below the enforced minimum here.

Practical rule: watch the release feed and the feature-gate schedule, upgrade
within days of a stable testnet release, and always **before** an activation
epoch rather than during it.

- Agave releases — <https://github.com/anza-xyz/agave/releases>
- Feature-gate tracker — <https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule>

## Normal upgrade

Identical mechanics to mainnet: stage the new release beside the old one, switch
`active_release` atomically, exit politely, start, verify externally.

````bash
sh -c "$(curl -sSfL https://release.anza.xyz/v<version>/install)" -- --no-modify-path
sha256sum ~/.local/share/solana/install/releases/<version>/bin/agave-validator

ln -sfn ~/.local/share/solana/install/releases/<version> \
        ~/.local/share/solana/install/active_release.new
mv -T ~/.local/share/solana/install/active_release.new \
      ~/.local/share/solana/install/active_release

agave-validator --ledger /mnt/ledger exit --max-delinquent-stake 5
sudo systemctl start solana
````

Verify:

````bash
agave-validator --version
solana catchup --our-localhost
solana validators --url https://api.testnet.solana.com | grep <identity-pubkey>
````

Keep the previous release directory. Rollback on testnet matters more than on
mainnet, because you are running newer, less-exercised code by design.

## Cluster restarts

A coordinated testnet restart typically means: stop at an announced slot, take
the published snapshot or restart slot, update the **shred version**, start
again.

What to do:

1. **Read the announcement**, and take the restart slot and the new shred
   version from it. Do not infer them.
2. Stop the validator cleanly.
3. If the announcement specifies a snapshot or a hard fork slot, apply exactly
   what it specifies — `--wait-for-supermajority`, `--expected-shred-version`
   and any hard-fork arguments are given in the announcement.
4. Update `--expected-shred-version` in the unit. This is the step that gets
   skipped, and skipping it produces a node that looks perfectly healthy and
   participates in nothing.
5. Start, then confirm gossip peer count recovers and votes resume.

````bash
solana gossip | wc -l
journalctl -u solana | grep -i 'shred version'
solana validators --url https://api.testnet.solana.com | grep <identity-pubkey>
````

## Ledger resets

Testnet may be reset. When that happens the local ledger and accounts are
worthless: clear the ledger and accounts directories, keep the keypairs, and let
the node bootstrap from the new genesis.

Before deleting anything, confirm from the official announcement that a reset
actually occurred. "My node is behind" is not a reset.

Never delete keypairs. Never delete the tower on a node that is still voting on
a live cluster.

## Client consistency with mainnet

SFDP expects the client you run on testnet to match the one you run on mainnet.
If you want to evaluate a fork or an orderflow stack, do it on a **separate,
non-staked** testnet validator with its own identity — not on the SFDP node.

## Checklist

- [ ] release tag resolved to a commit; binary hash recorded
- [ ] previous release retained for rollback
- [ ] feature-gate schedule checked for activation epochs
- [ ] restart announcement read; shred version and restart slot taken from it
- [ ] `--expected-shred-version` updated in the unit
- [ ] unit passes `systemd-analyze verify`
- [ ] after start: gossip peers recovered, votes advancing, not delinquent
- [ ] version at or above the enforced SFDP minimum

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
