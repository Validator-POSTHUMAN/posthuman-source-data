# Bitcoin CLI Sheet

Assumes `alias bcli='bitcoin-cli -datadir=/var/lib/bitcoind'`. Everything here
is read-only unless marked otherwise.

## Health in one screen

````bash
bcli getblockchaininfo | jq '{chain, blocks, headers, verificationprogress, initialblockdownload, size_on_disk, pruned}'
bcli getnetworkinfo    | jq '{version, subversion, connections_in, connections_out, networkactive, warnings}'
bcli getmempoolinfo    | jq '{size, bytes, mempoolminfee}'
bcli uptime
````

Tip agreement — the check that matters:

````bash
bcli getbestblockhash
curl -s https://mempool.space/api/blocks/tip/hash
curl -s https://blockstream.info/api/blocks/tip/hash
````

## Blocks

````bash
bcli getblockcount
bcli getblockhash 900000
bcli getblock <hash>            # verbosity 1: header + txids
bcli getblock <hash> 2          # + decoded transactions
bcli getblockheader <hash>
bcli getblockstats <height> '["avgfeerate","totalfee","txs","subsidy","utxo_increase"]'
bcli getchaintips               # forks your node has seen
bcli getchainstates             # assumeutxo: snapshot + background chainstate
bcli getdifficulty
````

## Transactions

````bash
bcli getrawtransaction <txid> true            # needs txindex=1 for arbitrary txids
bcli decoderawtransaction <hex>
bcli decodescript <hex>
bcli gettxout <txid> <n>                      # UTXO lookup; null means spent or unknown
bcli gettxspendingprevout '[{"txid":"<txid>","vout":0}]'
bcli estimatesmartfee 6                       # sat/kvB for a 6-block target
bcli testmempoolaccept '["<hex>"]'            # will it relay, without sending it
````

`gettxspendingprevout` gained `mempool_only` and `return_spending_tx` in v31.0,
and finds confirmed spenders when `txospenderindex=1` is set.

## Mempool

````bash
bcli getrawmempool                            # txids
bcli getrawmempool true | jq 'length'
bcli getmempoolentry <txid>                   # includes chunk size and chunk fees since v31.0
bcli getmempoolcluster <txid>                 # v31.0: the connected cluster and its chunks
bcli getmempoolfeeratediagram                 # v31.0: feerate diagram of the whole mempool
bcli savemempool                              # persist to disk now
````

Cluster mempool replaced ancestor/descendant limits in v31.0: a cluster is
capped at 64 transactions and 101 kvB. Tooling that parses the old limits needs
retesting.

## Peers and network

````bash
bcli getpeerinfo | jq '.[] | {addr, subver, inbound, conntime, synced_blocks, relaytxes}'
bcli getpeerinfo | jq 'group_by(.network) | map({network: .[0].network, n: length})'
bcli getnettotals | jq '{totalbytesrecv, totalbytessent}'
bcli getnodeaddresses 10
bcli getaddrmaninfo                           # addrman bucket occupancy
bcli addnode "<ip>:8333" onetry               # mutating
bcli disconnectnode "<ip>:8333"               # mutating
bcli setnetworkactive false                   # mutating — cuts all P2P, remember to re-enable
````

`getpeerinfo` no longer returns `startingheight` unless
`-deprecatedrpc=startingheight` is set; the field is removed in the next major
release.

## Wallet — read-only

````bash
bcli listwallets
bcli -rpcwallet=<name> getwalletinfo
bcli -rpcwallet=<name> getbalances
bcli -rpcwallet=<name> listunspent 1 9999999 | jq 'length'
bcli -rpcwallet=<name> listtransactions "*" 25
bcli -rpcwallet=<name> listdescriptors           # public descriptors only
bcli deriveaddresses "<descriptor>" '[0,10]'
bcli getaddressinfo <address>
bcli validateaddress <address>
````

`listdescriptors true` includes **private keys** — that output is key material.

## Wallet — mutating

````bash
bcli -rpcwallet=<name> walletpassphrase "<pass>" 60
bcli -rpcwallet=<name> send '{"<address>": 0.001}' null "unset" 5      # fee_rate 5 sat/vB
bcli -rpcwallet=<name> bumpfee <txid>
bcli -rpcwallet=<name> walletlock
````

`-paytxfee` and `settxfee` were **removed in v31.0**. Pass `fee_rate` per
transaction, or rely on estimation.

## Indexes and maintenance

````bash
bcli getindexinfo                              # sync state of every enabled index
bcli gettxoutsetinfo                           # slow without coinstatsindex=1
bcli pruneblockchain <height>                  # mutating, pruned nodes only
bcli dumptxoutset /path/utxo.dat rollback=880000   # mutating: node unusable while it runs
bcli loadtxoutset /path/utxo.dat               # mutating: assumeutxo fast start
bcli stop                                      # mutating: the only correct way to stop
````

Always `bcli stop` or `systemctl stop`, never `kill -9`. An interrupted flush
costs a reindex.

## Logging and diagnostics

````bash
bcli logging                                   # active categories
bcli logging '["net","mempool"]' '[]'          # enable at runtime
bcli getrpcinfo | jq '.active_commands'
bcli getmemoryinfo
bcli getdeploymentinfo                         # soft-fork status
journalctl -u bitcoind -f
````

## Signing and verification

````bash
bcli -rpcwallet=<name> signmessage <address> "text"
bcli verifymessage <address> <signature> "text"
bcli -rpcwallet=<name> walletprocesspsbt <psbt>
bcli finalizepsbt <psbt>
bcli analyzepsbt <psbt>
bcli submitpackage '["<parent-hex>","<child-hex>"]'
````

## Lightning

````bash
# LND
lncli getinfo | jq '{version, synced_to_chain, synced_to_graph, num_active_channels}'
lncli listchannels | jq '.channels[] | {remote_pubkey, capacity, local_balance, active}'
lncli walletbalance && lncli channelbalance
lncli wtclient towers

# Core Lightning
lightning-cli getinfo
lightning-cli listfunds
lightning-cli listpeerchannels
````

## The `bitcoin` wrapper

Since v30.0:

````bash
bitcoin help          # list subcommands
bitcoin node          # = bitcoind
bitcoin rpc getblockchaininfo   # = bitcoin-cli -named
bitcoin gui           # = bitcoin-qt
````

It calls the existing binaries and implements nothing itself. Nothing is
deprecated by it.

## Sources

- [developer.bitcoin.org — RPC reference](https://developer.bitcoin.org/reference/rpc/)
- [bitcoincore.org — v31.0 release notes](https://bitcoincore.org/en/releases/31.0/)
- [bitcoincore.org — v30.0 release notes](https://bitcoincore.org/en/releases/30.0/)
