# Solana Testnet CLI Sheet

Same CLI as mainnet, pointed at the testnet cluster. Pass `-ut` or an explicit
`--url` whenever the answer matters — a saved config that silently points at
mainnet is how people read the wrong validator's state during an incident.

````bash
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
solana config set --url https://api.testnet.solana.com
solana config get
````

## Faucet

````bash
solana airdrop 1                                   # 1 SOL per request
solana airdrop 1 <pubkey> --url https://api.testnet.solana.com
solana balance
solana balance --lamports
````

## Keys

````bash
solana-keygen new -o ~/testnet-validator-keypair.json
solana-keygen pubkey ~/testnet-validator-keypair.json
solana-keygen verify <pubkey> ~/testnet-validator-keypair.json
solana-keygen bls_pubkey ~/testnet-validator-keypair.json
````

## Vote account

````bash
solana create-vote-account vote-account-keypair.json validator-keypair.json withdrawer-keypair.json
solana vote-account <vote-account> -ut
solana vote-account <vote-account> -ut | grep "BLS Public Key"
solana vote-authorize-voter-checked <vote-account> <current-keypair> <new-voter-keypair>
solana vote-update-validator <vote-account> <new-identity-keypair> <withdrawer-keypair>
solana withdraw-from-vote-account <vote-account> <recipient> <amount> --authorized-withdrawer <keypair>
````

## Cluster state

````bash
solana epoch-info -ut
solana slot -ut
solana cluster-version -ut
solana gossip -ut | grep <identity-pubkey>
solana gossip -ut | wc -l                          # peer count — watch this after a cluster restart
solana validators -ut | grep <identity-pubkey>
solana block-production -ut | grep <identity-pubkey>
solana leader-schedule -ut | grep <identity-pubkey>
solana catchup <identity-pubkey> -ut
solana catchup --our-localhost
solana stakes <vote-account> -ut
````

## Local node

````bash
agave-validator --ledger /mnt/ledger monitor
agave-validator --ledger /mnt/ledger contact-info
agave-validator --ledger /mnt/ledger exit --max-delinquent-stake 5
agave-validator --ledger /mnt/ledger set-identity ~/testnet-unstaked-identity.json
agave-validator --ledger /mnt/ledger set-identity --require-tower ~/testnet-validator-keypair.json
````

## Local RPC probes

````bash
RPC=http://127.0.0.1:8899
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}'
curl -s $RPC -X POST -H 'content-type:application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getEpochInfo"}'
````

## After a cluster restart

````bash
journalctl -u solana | grep -i 'shred version'
solana gossip -ut | wc -l
solana validators -ut | grep <identity-pubkey>
````

Peer count collapsing to near-nothing while the service looks healthy means the
node is on the wrong shred version. Update `--expected-shred-version` from the
restart announcement and restart.

## Service

````bash
sudo systemctl status solana
sudo systemctl restart solana
systemctl show solana -p NRestarts -p ActiveState
journalctl -u solana -f -o cat
journalctl -u solana --since "30 min ago" | grep -Ei 'panic|error|no space|shred version'
````

`systemctl start` on an already-active unit is a no-op. After replacing a key
file or editing the unit, use `stop` then `start`, or `restart`.

## Host

````bash
df -h | grep -v 'tmpfs\|udev\|loop'
free -h
swapon --show
timedatectl
ip -s link show <nic>
````

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
