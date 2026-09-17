# Mina CLI and GraphQL Cheat Sheet

Everything below assumes a running daemon on the same host. Under Docker prefix
with `docker exec -it mina`, or run the same command inside the container.

Most commands talk to the daemon over `--rest-server` (GraphQL, default `3085`)
or `--daemon-port` (client RPC, default `8301`). If a command hangs or refuses
to connect, the daemon is not up yet, or you are outside the client trustlist.

## Status and health

````bash
mina client status                  # the one command to know
mina client status --json | jq
mina client status --performance    # include performance histograms
mina version                        # build and commit
mina advanced get-peers             # currently connected peers
mina advanced node-status           # node status of a peer set
mina advanced runtime-config        # effective runtime configuration
mina advanced compile-time-constants
mina client stop-daemon
````

Scriptable checks:

````bash
mina client status --json | jq -r '.syncStatus'
mina client status --json | jq -r '.blockchainLength, .highestBlockLengthReceived'
````

## Accounts and keys

````bash
mina advanced generate-keypair  --privkey-path ~/keys/my-wallet
mina advanced validate-keypair  --privkey-path ~/keys/my-wallet
mina advanced dump-keypair      --privkey-path ~/keys/my-wallet

mina accounts list
mina accounts import  --privkey-path ~/keys/my-wallet
mina accounts export  --privkey-path ~/keys/out --public-key B62q…
mina accounts unlock  --public-key B62q…
mina accounts lock    --public-key B62q…
````

`MINA_PRIVKEY_PASS` makes `import`/`export` non-interactive. Quote passwords
containing shell metacharacters.

Unlock only for as long as you need to send something, then lock. An unlocked
account plus an exposed GraphQL endpoint is a funds-loss path — see **Security
hardening**.

## Transactions

````bash
mina client get-balance --public-key B62q…
mina client get-tokens  --public-key B62q…
mina advanced get-nonce --public-key B62q…

mina client send-payment \
  --sender B62q… --receiver B62q… --amount 10 --fee 0.01 --memo "note"

mina client delegate-stake \
  --sender $COLD_PUBLIC_KEY --receiver $HOT_PUBLIC_KEY --fee 0.1

mina client cancel-transaction --id <TRANSACTION_ID>
mina advanced batch-send-payments <file>
mina advanced pooled-user-commands --public-key B62q…
````

Fee default is `0.25`, minimum `0.001`. `cancel-transaction` works by submitting
a replacement with a higher fee — it is a race, not a guarantee.

## Block production

````bash
mina client status | grep -i "block producer"
mina advanced set-coinbase-receiver --public-key $COLD_PUBLIC_KEY
mina advanced set-coinbase-receiver --reset
````

## SNARK work

````bash
mina client set-snark-worker --address B62q…   # start
mina client set-snark-worker                   # stop
mina client set-snark-work-fee 0.001

mina advanced snark-pool-list      | jq        # completed work in the pool
mina advanced snark-job-list       | jq        # jobs not yet in blocks
mina advanced pending-snark-work   | jq        # work not yet in the pool
````

## Ledgers

````bash
mina ledger export staking-epoch-ledger > staking.json
mina ledger export next-epoch-ledger    > next.json
mina ledger export staged-ledger        > staged.json
mina ledger currency --ledger-file staking.json
mina ledger hash     --ledger-file staking.json
````

Total stake delegated to you, from your own node rather than an explorer:

````bash
jq --arg pk "$YOUR_PUBLIC_KEY" '
  [ .[] | select(.delegate == $pk) | (.balance | tonumber) ] | add
' staking.json
````

Your delegator list, largest first:

````bash
jq -r --arg pk "$YOUR_PUBLIC_KEY" '
  [ .[] | select(.delegate == $pk) | {pk: .pk, balance: (.balance | tonumber)} ]
  | sort_by(-.balance)[] | "\(.balance)\t\(.pk)"
' staking.json | head -20
````

Exporting the snarked ledger is expensive and takes seconds — do not put it in a
one-minute monitoring loop.

## libp2p

````bash
mina libp2p generate-keypair --privkey-path ~/keys/libp2p
mina libp2p dump-keypair     --privkey-path ~/keys/libp2p
````

## Trustlist

````bash
mina advanced client-trustlist list
mina advanced client-trustlist add    --cidr 10.0.0.0/8
mina advanced client-trustlist remove --cidr 10.0.0.0/8
````

## Logs

````bash
mina client export-logs       -tarfile incident-$(date +%Y%m%dT%H%M%SZ)
mina client export-local-logs -tarfile incident-offline    # daemon stopped
journalctl --user -u mina -n 1000 -f
docker logs --follow mina
tail -f ~/.mina-config/mina.log
````

## GraphQL

Sandbox: `http://localhost:3085/graphql` in a browser. From the shell:

````bash
gql() {
  curl -s http://127.0.0.1:3085/graphql \
    -H 'Content-Type: application/json' \
    -d "{\"query\":\"$1\"}" | jq
}
````

Node health:

````graphql
{ syncStatus daemonStatus { blockchainLength chainId commitId numAccounts peers { host } } }
````

Consensus position and parameters:

````graphql
{ daemonStatus {
    consensusTimeNow { epoch slot globalSlot startTime endTime }
    consensusConfiguration { slotDuration slotsPerEpoch epochDuration k delta }
} }
````

Account balance and delegation:

````graphql
{ account(publicKey: "B62q…") {
    balance { total blockHeight stateHash }
    nonce
    delegateAccount { publicKey }
} }
````

`delegateAccount.publicKey` null means the account stakes for itself.

Recent blocks and their transactions:

````graphql
{ bestChain(maxLength: 10) {
    stateHash
    protocolState { consensusState { blockHeight epoch slot } }
    transactions {
      coinbase
      userCommands { hash kind amount fee isDelegation memo
                     feePayer { publicKey } receiver { publicKey } }
    }
} }
````

`bestChain` only reaches back about 290 blocks — roughly 7 hours at 90-second
slots. Anything older needs an **archive node**.

Public endpoints, for comparing your node against something independent:

````bash
curl -s https://api.minascan.io/node/mainnet/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ daemonStatus { blockchainLength chainId } }"}' | jq
````

## Docker equivalents

````bash
docker exec -it mina mina client status
docker exec -it mina mina accounts list
docker exec -it mina mina ledger export staking-epoch-ledger > staking.json
docker logs --follow mina
docker inspect mina --format '{{.Config.Image}}'
docker stats --no-stream mina
````

## Related guides

- **Monitoring** — which of these belong in alerting
- **Block producer** — stake and production checks
- **Archive node** — history beyond the 290-block window
- **Security hardening** — unlock/lock discipline and endpoint exposure

## Sources

- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
- [docs.minaprotocol.com — querying data](https://docs.minaprotocol.com/node-operators/validator-node/querying-data)
- [docs.minaprotocol.com — logging](https://docs.minaprotocol.com/node-operators/validator-node/logging)
