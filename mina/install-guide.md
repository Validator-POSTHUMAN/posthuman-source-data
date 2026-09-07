# Mina Block Producer Installation Guide

## About Mina

Mina keeps a constant-size chain — about 22 kB — using recursive zk-SNARKs, so
a node verifies the whole chain without storing it. Consensus is Ouroboros
Samasika, and the validator role is called a **block producer**: your node is
selected to produce blocks in proportion to the stake delegated to it, checked
against a staking ledger that is fixed one epoch in advance.

**Facts that shape the setup:**
- Stake for the current epoch was snapshotted an epoch ago. New delegations do
  not affect your block production until the relevant epoch begins — there is
  nothing wrong with your node if a fresh delegation changes nothing today.
- Block production requires the private key to be online and unlocked. There
  is no remote-signer split in the standard setup, so host security is the
  whole of key security.
- Delegators are paid by the block producer. Mina does not distribute rewards
  to delegators on-chain; payouts are an off-chain obligation you take on when
  you accept delegation.
- SNARK work is a separate role. A block producer buys completed SNARK work
  from a marketplace; running a SNARK coordinator/worker is optional and is a
  different job from producing blocks.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8 cores     |
| RAM       | 16 GB   | 32 GB       |
| Disk      | 256 GB SSD | 512 GB SSD |
| Network   | 100 Mbps, public IP | 1 Gbps, static IP |
| OS        | Ubuntu 22.04 | Ubuntu 24.04 |

## Prepare the host

````bash
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install docker.io jq curl
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
````

Log out and back in so the group membership applies.

## Open the P2P port

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8302/tcp
sudo ufw enable
````

`8302/tcp` must be reachable inbound. A block producer that cannot be dialled
still syncs, but it gossips poorly and can miss its own block slots.

## Create the key

Generate the block producer key with the same image you will run, so the key
format matches the daemon:

````bash
mkdir -p ~/mina/keys && chmod 700 ~/mina/keys
docker run --rm -it -v ~/mina/keys:/keys minaprotocol/mina-daemon:latest \
  mina advanced generate-keypair --privkey-path /keys/my-wallet
sudo chmod 600 ~/mina/keys/my-wallet
````

The passphrase you set here is required at every start. Back up
`~/mina/keys/my-wallet`, `my-wallet.pub` and the passphrase separately and
offline. Losing the key means losing the producer identity and everything
delegated to it.

## Run the daemon

````bash
docker run --name mina -d --restart=always \
  -p 8302:8302 \
  -p 127.0.0.1:3085:3085 \
  -v ~/mina/keys:/keys:ro \
  -v ~/mina/.mina-config:/root/.mina-config \
  -e MINA_PRIVKEY_PASS="<your-passphrase>" \
  minaprotocol/mina-daemon:latest \
  daemon \
    --block-producer-key /keys/my-wallet \
    --peer-list-url https://bootnodes.minaprotocol.com/networks/mainnet.txt \
    --external-port 8302 \
    --insecure-rest-server
````

Bind the GraphQL port to `127.0.0.1` as shown. Port `3085` can read node state
and must never be exposed publicly.

Pin the image to an explicit release tag rather than `latest` for anything you
intend to keep running, and record the tag and the chain ID the node reports —
that pair is what proves which network you actually joined.

## Verify

````bash
docker exec -it mina mina client status
````

Check in the output:
- `Sync status: Synced`;
- `Chain id` matches the network you intended to join;
- `Block producers running: 1`;
- a non-trivial peer count.

Confirm the daemon sees your key as a producer:

````bash
docker exec -it mina mina accounts list
````

## Confirm from outside

Your node's own view is not proof of participation. Once the node is synced and
your public key holds or has been delegated stake, check the public explorer:

`https://minascan.io/mainnet/validator/<your-public-key>/delegations`

If you need the exact staking-ledger picture rather than an explorer's view,
export the ledger from your own synced node and sum the balances that delegate
to your key:

````bash
docker exec -it mina mina ledger export staking-epoch-ledger > staking-ledger.json
````

## Delegator payouts

Mina pays block rewards to the producer, not to delegators. If you accept
delegation you are taking on a manual payout obligation: compute each epoch's
rewards from the staking ledger, apply your published fee, and send the
transfers. Publish your fee and schedule before you accept delegation, and
treat every payout batch as an operation that needs a fresh preflight and an
explicit confirmation — an automated payout loop with an unlocked key is a
standing risk that is hard to bound.

## Upgrade

Mina hard forks are coordinated and require running the release built for the
new chain. Pull the announced tag, stop the container, start it with the same
volumes and key, then re-check sync status, chain ID and producer count before
considering the upgrade complete.

## Monitoring

Watch: container state and restart count, sync status, chain ID, peer count,
block producer count, disk free, and — from outside — whether blocks you were
scheduled to produce actually landed.

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
