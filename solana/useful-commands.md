# Solana Validator CLI Sheet

Every command below assumes the Solana CLI on `PATH`:

````bash
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
````

Most read commands take `-um` (mainnet-beta), `-ut` (testnet), `-ud` (devnet) or
an explicit `--url`. When the answer matters, pass the cluster explicitly rather
than trusting the saved config.

## Configuration

````bash
solana --version
agave-validator --version
solana config get
solana config set --url https://api.mainnet-beta.solana.com
solana config set --keypair /home/sol/validator-keypair.json
````

## Keys

````bash
solana-keygen new -o validator-keypair.json
solana-keygen new --no-outfile                       # seed phrase only, nothing on disk
solana-keygen pubkey validator-keypair.json
solana-keygen verify <pubkey> validator-keypair.json # non-zero exit on mismatch
solana-keygen grind --starts-with pstmn:1
solana-keygen bls_pubkey validator-keypair.json      # SIMD-0387 BLS key
````

## Balances and transfers

````bash
solana balance <pubkey>
solana balance --lamports <pubkey>
solana transfer <recipient> <amount> --allow-unfunded-recipient
solana confirm -v <signature>
````

## Vote account

````bash
solana vote-account <vote-account>
solana vote-account <vote-account> | grep "Vote Authority"
solana vote-account <vote-account> | grep "BLS Public Key"

solana create-vote-account vote-account-keypair.json validator-keypair.json withdrawer-keypair.json
solana vote-update-validator <vote-account> <new-identity-keypair> <withdrawer-keypair>
solana vote-authorize-voter-checked <vote-account> <current-authority> <new-voter-keypair>
solana vote-authorize-withdrawer-checked <vote-account> <current> <new-withdrawer-keypair>
solana vote-update-commission <vote-account> <percent> <withdrawer-keypair>
solana vote-update-commission-collector <vote-account> block-revenue <collector> <withdrawer-keypair>
solana withdraw-from-vote-account <vote-account> <recipient> <amount> --authorized-withdrawer <keypair>
````

## Stake

````bash
solana create-stake-account stake-keypair.json <amount>
solana delegate-stake stake-keypair.json <vote-account>
solana stake-account <stake-account>
solana deactivate-stake stake-keypair.json
solana withdraw-stake stake-keypair.json <recipient> <amount>
solana stakes <vote-account>                  # all stake delegated to a validator
solana stake-history
````

## Cluster and validator state

````bash
solana epoch-info
solana slot
solana block-height
solana cluster-version
solana gossip | grep <identity-pubkey>
solana validators | grep <identity-pubkey>
solana validators --sort=stake --reverse | head -20
solana block-production | grep <identity-pubkey>
solana leader-schedule | grep <identity-pubkey>
solana catchup <identity-pubkey>
solana catchup --our-localhost
solana ping
solana transaction-count
solana inflation
solana inflation rewards <vote-account> --rewards-epoch <epoch>
````

## Local node

````bash
agave-validator --ledger /mnt/ledger monitor
agave-validator --ledger /mnt/ledger contact-info
agave-validator --ledger /mnt/ledger exit --max-delinquent-stake 5
agave-validator --ledger /mnt/ledger set-identity /home/sol/unstaked-identity.json
agave-validator --ledger /mnt/ledger set-identity --require-tower /home/sol/validator-keypair.json
agave-validator --ledger /mnt/ledger set-log-filter "solana=info"
agave-validator --ledger /mnt/ledger repair-shred-from-peer --slot <slot>
````

`exit --max-delinquent-stake 5` is the polite shutdown: it waits for a
restart-safe moment instead of dropping votes immediately.

## Local RPC probes

````bash
RPC=http://127.0.0.1:8899
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getEpochInfo"}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getVoteAccounts","params":[{"votePubkey":"<vote-account>"}]}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getClusterNodes"}' | jq 'length'
````

## Ledger tools

````bash
agave-ledger-tool --ledger /mnt/ledger bounds
agave-ledger-tool --ledger /mnt/ledger print --starting-slot <slot>
agave-ledger-tool --ledger /mnt/ledger verify --halt-at-slot <slot>
````

These are offline tools. Do not run them against the ledger of a validator that
is currently voting.

## Service control

````bash
sudo systemctl status solana
sudo systemctl stop solana && sudo systemctl start solana   # not `start` alone
sudo systemctl restart solana
systemctl show solana -p NRestarts -p ActiveState -p ExecMainStartTimestamp
journalctl -u solana -f -o cat
journalctl -u solana --since "30 min ago" | grep -Ei 'panic|error|no space'
````

`systemctl start` on an already-active unit is a no-op. After replacing a key
file or a unit, always `stop` then `start`, or `restart`.

## Host checks

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
free -h
swapon --show
timedatectl
ip -s link show <nic>
lscpu | grep -E 'Model name|MHz|Core|Socket'
nvme list
````

## The two-sample health check

The single most useful thing to have in a script:

````bash
V=<vote-account>; U=https://api.mainnet-beta.solana.com
for i in 1 2; do
  solana vote-account "$V" --url "$U" | grep -E 'Recent Timestamp|Credits|Root Slot|Last Vote'
  sleep 60
done
````

Both samples must advance. One sample proves nothing.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
