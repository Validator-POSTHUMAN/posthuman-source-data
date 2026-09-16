# Starknet snapshots

Syncing Starknet mainnet from genesis takes days. A database snapshot brings a
node to recent state in hours. Both clients publish official snapshots.

> **Order matters.** Download and extract **first**; stop the node **last**.
> If you stop the node before downloading, your downtime equals the download
> time instead of the few minutes it takes to swap a directory. For a live
> validator this is the difference between one missed epoch and ten.

## Restore checklist

Run this in order, every time:

1. Check free disk: you need the extracted database, plus the old one you keep
   until verification, plus headroom. `df -h` on the actual data mount.
2. Download and verify the snapshot checksum.
3. Extract to a **new** directory next to the live one.
4. Stop the node (and the attestation service).
5. **Move** the old data directory aside — never `rm -rf` it.
6. Move the new directory into place, fix ownership.
7. Start the node, verify sync and chain ID.
8. Start attestation, verify a confirmed attestation.
9. Only after that, delete the old directory.

Never restore a snapshot from a different network or a different client.
Never restore while the node is running.

## Pathfinder

Equilibrium publishes snapshots over an S3-compatible endpoint; the index with
filenames and checksums is at
[rpc.pathfinder.equilibrium.co/snapshots/latest](https://rpc.pathfinder.equilibrium.co/snapshots/latest).

### 1. Install rclone and zstd

```bash
sudo -v ; curl https://rclone.org/install.sh | sudo bash
sudo apt-get install -y zstd
```

### 2. Configure the remote

```bash
mkdir -p $HOME/.config/rclone
$EDITOR $HOME/.config/rclone/rclone.conf
```

The public read credentials for the snapshot bucket are published on the
snapshot index page linked above. Copy the `[pathfinder-snapshots]` block from
there — do not guess the values, and refresh them if a download starts failing.

### 3. Download

```bash
mkdir -p $HOME/pathfinder-restore
cd $HOME/pathfinder-restore
rclone copy -P pathfinder-snapshots:pathfinder-snapshots/<FILENAME> .
```

### 4. Verify the checksum

```bash
sha256sum <FILENAME>
```

Compare against the value published on the snapshot index page. A mismatch
means a corrupt or truncated download — delete it and retry. Do not restore an
unverified database.

### 5. Extract

```bash
zstd -T0 -d <FILENAME> -o mainnet.sqlite
```

### 6. Swap it in

```bash
cd ~/starknet
docker compose stop attestation pathfinder

mv ./data/mainnet.sqlite ./data/mainnet.sqlite.old
mv $HOME/pathfinder-restore/mainnet.sqlite ./data/mainnet.sqlite
chown -R $(id -u):$(id -g) ./data

docker compose up -d pathfinder
docker compose logs -f pathfinder
```

Pathfinder keeps a single SQLite database file per network, so the swap is one
file. Start the attestation service only once the node reports head.

## Juno

Nethermind publishes `.tar.zst` snapshots, full and pruned:

| Network | Archive |
|---|---|
| Mainnet | `https://juno-snapshots.nethermind.io/files/mainnet/latest` |
| Mainnet (pruned) | `https://juno-snapshots.nethermind.io/files/mainnet-pruned/latest` |
| Sepolia | `https://juno-snapshots.nethermind.io/files/sepolia/latest` |
| Sepolia (pruned) | `https://juno-snapshots.nethermind.io/files/sepolia-pruned/latest` |

Pruned snapshots contain only recent data and are much smaller. They are
sufficient for a validator: attestation needs recent block hashes, not full
history. Use a full snapshot only if you also serve historical RPC queries.

### Check the size before you start

```bash
curl -s -I -L https://juno-snapshots.nethermind.io/files/mainnet/latest \
  | gawk -v IGNORECASE=1 '/^Content-Length/ { printf "%.2f GB\n", $2/1024/1024/1024 }'
```

### Stream and extract in one step (recommended)

Streaming avoids needing disk space for the compressed archive as well as the
extracted database.

```bash
sudo apt-get install -y zstd wget
mkdir -p $HOME/juno-restore/juno_mainnet

wget --tries=0 --retry-connrefused \
     --retry-on-http-error=500,502,503,504 --read-timeout=60 \
     -O - https://juno-snapshots.nethermind.io/files/mainnet/latest \
  | zstd -d | tar -xf - -C $HOME/juno-restore/juno_mainnet
```

`--tries=0 --retry-connrefused` matters: a multi-hundred-gigabyte transfer will
hit a transient network error, and without retries you start over.

### Download then extract (alternative)

```bash
wget -c -O juno_mainnet.tar.zst https://juno-snapshots.nethermind.io/files/mainnet/latest
zstd -d juno_mainnet.tar.zst -c | tar -xf - -C $HOME/juno-restore/juno_mainnet
```

### Swap it in

```bash
cd ~/starknet
docker compose stop attestation juno

mv ./juno_mainnet ./juno_mainnet.old
mv $HOME/juno-restore/juno_mainnet ./juno_mainnet
chown -R $(id -u):$(id -g) ./juno_mainnet

docker compose up -d juno
docker compose logs -f juno
```

## Verify after restore

```bash
# Pathfinder
curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}'
curl -s -X POST http://127.0.0.1:9545/rpc/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_chainId","params":[],"id":1}'

# Juno
curl -s -X POST http://127.0.0.1:6060/v0_9 -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"starknet_blockNumber","params":[],"id":1}'
```

Checks that must all pass before you call the restore done:

1. Chain ID is the network you intended (`SN_MAIN` / `SN_SEPOLIA`).
2. Block number advances over a minute of observation.
3. `starknet_syncing` reaches `false`, or the gap to a public RPC shrinks.
4. No repeated database, trie or L1 errors in the logs.
5. The attestation service logs `Attestation confirmed` in the next epoch.

## Rollback

If the restored database is incompatible or corrupt:

```bash
cd ~/starknet
docker compose stop attestation pathfinder    # or juno
mv ./data/mainnet.sqlite ./data/mainnet.sqlite.failed
mv ./data/mainnet.sqlite.old ./data/mainnet.sqlite
docker compose up -d
```

This only works because step 5 of the checklist moved the old data instead of
deleting it. Keep the old directory until the new one has produced a confirmed
attestation.

## Reference

- [Pathfinder snapshot index](https://rpc.pathfinder.equilibrium.co/snapshots/latest)
- [Juno snapshot documentation](https://juno.nethermind.io/snapshots/)
- Starknet docs — [Running a full node](https://docs.starknet.io/secure/quickstart/running-a-node)
