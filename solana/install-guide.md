# Solana Validator Installation Guide

## About Solana

Solana validators run the Agave client (or a compatible client such as Jito or
Firedancer). A validator keeps the full ledger, replays every block and votes
on the fork it believes is canonical. Voting costs SOL in transaction fees, so
a validator has a running cost from the first slot it votes on.

**Facts that shape the setup:**
- Solana is the most hardware-hungry network in common validator practice.
  Under-provisioning does not degrade gracefully — the node falls behind,
  becomes delinquent and stops earning.
- The **identity** keypair and the **vote account** are different things. The
  identity signs blocks and votes; the vote account holds the stake
  relationship and the reward. Losing the identity key means losing the node;
  running two nodes with the same identity at the same time will get you
  slashed by the network's duplicate-block detection in practice, so treat it
  as a hard rule: one identity, one running process.
- Restarts are routine and expensive. Plan for them: snapshots, swap and fast
  disks are what make a restart minutes instead of hours.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 16 cores / 32 threads | 32 cores, high single-core clock |
| RAM       | 256 GB  | 384–512 GB  |
| Ledger disk | 1 TB NVMe | 2 TB NVMe, dedicated |
| Accounts disk | 500 GB NVMe | 1 TB NVMe, dedicated |
| Network   | 1 Gbps  | 10 Gbps+ |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

Put the ledger and the accounts database on **separate** NVMe devices, and keep
both off the root filesystem. Snapshots belong on the ledger filesystem, not on
root — a root filesystem that fills up during snapshot creation takes the node
down.

## Prepare the system

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install build-essential pkg-config libssl-dev libudev-dev llvm clang jq curl
````

Raise the kernel limits Solana needs:

````bash
sudo tee /etc/sysctl.d/99-solana.conf > /dev/null <<'EOF'
net.core.rmem_default = 134217728
net.core.rmem_max = 134217728
net.core.wmem_default = 134217728
net.core.wmem_max = 134217728
vm.max_map_count = 1000000
fs.nr_open = 1000000
EOF
sudo sysctl -p /etc/sysctl.d/99-solana.conf
````

````bash
sudo tee /etc/security/limits.d/99-solana.conf > /dev/null <<'EOF'
* - nofile 1000000
EOF
````

Add swap even on a large-memory host. A validator that hits memory pressure
without swap dies; with swap it slows down and survives:

````bash
sudo fallocate -l 64G /mnt/ledger/swapfile
sudo chmod 600 /mnt/ledger/swapfile
sudo mkswap /mnt/ledger/swapfile
sudo swapon /mnt/ledger/swapfile
echo '/mnt/ledger/swapfile none swap sw,pri=10 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-solana-swap.conf
````

## Install the client

Install the Agave release you intend to run:

````bash
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
agave-validator --version
````

Jito's build is a drop-in alternative that adds MEV tips; it is installed from
its own tag and reports itself as `agave-validator` with a Jito suffix. Whatever
you choose, record the exact tag and the binary SHA-256 you deployed — you will
need it to prove what is running after an incident:

````bash
sha256sum "$(command -v agave-validator)"
````

## Create the keys

````bash
solana-keygen new -o ~/validator-keypair.json
solana-keygen new -o ~/vote-account-keypair.json
solana-keygen new -o ~/authorized-withdrawer-keypair.json
````

Back up all three offline **before** funding anything. The authorized
withdrawer controls the stake and should never live on the validator host.

Create the vote account once, from a funded wallet:

````bash
solana create-vote-account ~/vote-account-keypair.json ~/validator-keypair.json ~/authorized-withdrawer-keypair.json
````

## Create the systemd unit

````bash
sudo tee /etc/systemd/system/solana.service > /dev/null <<'EOF'
[Unit]
Description=Solana Validator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
LimitNOFILE=1000000
Environment=PATH=/home/ubuntu/.local/share/solana/install/active_release/bin:/usr/bin:/bin
ExecStart=/home/ubuntu/.local/share/solana/install/active_release/bin/agave-validator \
  --identity /home/ubuntu/validator-keypair.json \
  --vote-account /home/ubuntu/vote-account-keypair.json \
  --ledger /mnt/ledger \
  --accounts /mnt/accounts \
  --snapshots /mnt/ledger/snapshots \
  --log /home/ubuntu/solana-validator.log \
  --rpc-port 8899 \
  --private-rpc \
  --dynamic-port-range 8000-8050 \
  --entrypoint entrypoint.mainnet-beta.solana.com:8001 \
  --entrypoint entrypoint2.mainnet-beta.solana.com:8001 \
  --entrypoint entrypoint3.mainnet-beta.solana.com:8001 \
  --known-validator 7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2 \
  --only-known-rpc \
  --wal-recovery-mode skip_any_corrupted_record \
  --limit-ledger-size
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now solana
````

## Open the ports

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8000:8050/tcp
sudo ufw allow 8000:8050/udp
sudo ufw enable
````

Keep the RPC port closed to the internet. `--private-rpc` restricts it, but the
firewall is what enforces it.

## Verify

````bash
solana catchup --our-localhost
solana-validator --ledger /mnt/ledger monitor
curl -s http://127.0.0.1:8899 -X POST -H 'content-type:application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
````

Then check what the **network** sees, which is the only view that matters:

````bash
solana validators --url https://api.mainnet-beta.solana.com | grep <your-identity-pubkey>
solana vote-account <your-vote-account-pubkey> --url https://api.mainnet-beta.solana.com
````

`delinquent=false`, a fresh `lastVote` and an advancing `rootSlot` are the three
signals that say the validator is genuinely working. "The service is running" is
not one of them.

## Restart discipline

A restart replays from the last snapshot. Before every planned restart:

1. confirm a recent snapshot exists under `--snapshots`;
2. confirm free space on both the ledger and accounts filesystems;
3. stop the service, wait for the process to exit fully, then start it;
4. watch `solana catchup --our-localhost` until the gap closes;
5. confirm `delinquent=false` from an external RPC before calling it done.

## Upgrade

Solana upgrades are frequent and coordinated with the cluster. Upgrade during a
low-stake window, keep the previous release directory in place so a rollback is
a symlink change, and record the new version and binary hash. After restarting,
run the same external checks as above — version, delinquency, last vote, root
slot.

## Monitoring

Watch: service state and restart count, local `getHealth`, local slot against
public slot, `delinquent`, last vote and root slot from an external RPC, disk
free on ledger and accounts, memory and swap usage, and the vote account
balance — a vote account that runs out of SOL stops voting.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
