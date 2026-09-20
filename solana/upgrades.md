# Solana Validator Upgrades

Solana ships often and the cluster expects you to keep up. An upgrade is a
restart, and on Solana a restart is a snapshot load — so the risk is not the new
binary, it is the minutes of downtime around it and the state you restart onto.

Two paths:

- **Restart in place** — simple, costs a few minutes of missed votes.
- **Identity handover to a spare host** — near-zero missed votes, and the only
  approach worth using on a large stake.

## Before you touch anything

1. **Resolve the version to a commit.** Take the official signed tag, resolve it
   to its commit, and record both. "Latest" is not a version.
2. **Verify the artifact.** Check the downloaded archive against the SHA-256
   published with the release, and hash the resulting binary too.
3. **Read the release notes** for feature-gate activations, required flags and
   renamed flags. Flags get renamed between minor versions — a unit that starts
   fine on one release can refuse to start on the next.
4. **Keep the current release directory.** Rollback must be a symlink change.
5. **Check snapshot freshness and free disk** — see the snapshots guide. This is
   what decides whether the restart takes two minutes or two hours.
6. **Pick the window.** Avoid your own leader slots and avoid an epoch boundary.

## Install alongside, do not overwrite

Agave's installer keeps releases in versioned directories with an
`active_release` symlink:

````
~/.local/share/solana/install/releases/<version>/
~/.local/share/solana/install/active_release -> releases/<version>/
````

Stage the new release without switching:

````bash
sh -c "$(curl -sSfL https://release.anza.xyz/v<version>/install)" -- --no-modify-path
ls -l ~/.local/share/solana/install/active_release
sha256sum ~/.local/share/solana/install/releases/<version>/bin/agave-validator
````

Building from source is the supported path on most platforms now, and is
required if your CPU lacks the instruction set the prebuilt binaries target:

````bash
git clone https://github.com/anza-xyz/agave.git && cd agave
git checkout <signed-tag>
git rev-parse HEAD          # record this
./scripts/cargo-install-all.sh --validator-only ~/.local/share/solana/install/releases/<version>
````

If you run a modified client — Jito, Firedancer/Frankendancer — take the tag
from that project, not from Agave, and record the same three facts: tag,
commit, binary hash.

## Path A — restart in place

````bash
# 1. verify there is a recent snapshot pair and free space
ls -lt /mnt/ledger/snapshots | head
df -h /mnt/ledger /mnt/accounts

# 2. switch the release atomically
ln -sfn ~/.local/share/solana/install/releases/<new-version> \
        ~/.local/share/solana/install/active_release.new
mv -T ~/.local/share/solana/install/active_release.new \
      ~/.local/share/solana/install/active_release

# 3. polite exit, then start
agave-validator --ledger /mnt/ledger exit --max-delinquent-stake 5
sudo systemctl start solana
````

`exit --max-delinquent-stake 5` waits for a moment when the cluster can absorb
your absence instead of dropping out mid-slot. Use it rather than `kill`.

Then verify — from outside:

````bash
agave-validator --version
solana catchup --our-localhost
solana validators --url https://api.mainnet-beta.solana.com | grep <identity-pubkey>
solana vote-account <vote-account> --url https://api.mainnet-beta.solana.com
systemctl show solana -p NRestarts -p ActiveState
````

Done means: the running binary is the one you intended, `NRestarts=0` since the
start, local health `ok`, local and public finalized slots converged, and two
external samples a minute apart showing `delinquent=false` with `lastVote` and
`rootSlot` advancing in both.

## Path B — identity handover (near-zero downtime)

Requires a second synced host running the same cluster with the **unstaked**
identity.

````bash
# on the spare, already synced and caught up, running with unstaked-identity.json

# 1. active node gives up the staked identity
agave-validator --ledger /mnt/ledger set-identity /home/sol/unstaked-identity.json

# 2. copy the tower file to the spare
scp /mnt/ledger/tower-1_9-<identity-pubkey>.bin sol@<spare>:/mnt/ledger/

# 3. spare takes the staked identity, refusing without a valid tower
agave-validator --ledger /mnt/ledger set-identity --require-tower /home/sol/validator-keypair.json
````

Then upgrade the now-idle host at leisure and hand the identity back the same
way.

**Never skip `--require-tower`.** It is the only automatic check standing
between you and two hosts voting on one identity. If it refuses, the answer is
to fix the tower copy, not to drop the flag.

## Feature gates and cluster restarts

Some upgrades carry a feature that activates at a specific epoch. Two
consequences:

- run the required version **before** the activation epoch, not during it;
- after a cluster-wide restart the **shred version changes**. A node still on
  the old shred version will look alive, peer with nobody, and vote on nothing.
  Check `--expected-shred-version` against the current cluster value and update
  it as part of the restart.

## Rollback

Rollback is switching `active_release` back and restarting:

````bash
ln -sfn ~/.local/share/solana/install/releases/<previous-version> \
        ~/.local/share/solana/install/active_release.new
mv -T ~/.local/share/solana/install/active_release.new \
      ~/.local/share/solana/install/active_release
sudo systemctl restart solana
````

This works only if you kept the previous release directory. Downgrading across a
feature-gate activation is not always possible — check the release notes before
assuming rollback is available.

## Record what you shipped

After every upgrade write down: release tag, resolved commit, binary SHA-256,
time of restart, snapshot slot it resumed from, and the rollback release. An
incident three weeks later starts from that record or from guesswork.

## Upgrade checklist

- [ ] tag resolved to a commit; archive and binary hashes recorded
- [ ] release notes read for renamed flags and feature gates
- [ ] previous release retained
- [ ] recent snapshot pair confirmed; disk headroom confirmed
- [ ] window avoids leader slots and the epoch boundary
- [ ] unit passes `systemd-analyze verify` after any edit
- [ ] polite `exit` used, not a kill
- [ ] post-restart: version, `NRestarts`, local health, slot convergence
- [ ] two external samples: not delinquent, vote and root advancing
- [ ] result written down

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
