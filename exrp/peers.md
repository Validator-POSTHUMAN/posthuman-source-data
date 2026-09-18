# XRPL EVM Mainnet peers

## POSTHUMAN public peer

```
71891d3e4790ca8187d38d7acf40ca881074a06b@peer.exrp.posthuman.digital:62656
```

Verified 2026-09-18 against `/status` on the node itself: network
`xrplevm_1440000-1`, voting power `0`. It is a non-signing node, which is the
only kind of node whose P2P address belongs in public documentation.

## Official peer list

XRPL EVM has no seed-node service. It publishes a flat list instead:

<https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/peers.txt>

```bash
curl -fsSL https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/peers.txt \
  | awk '{print $1}' | sort -R | head -n 10 | paste -sd, -
```

Sample it. Pasting the whole list into `persistent_peers` makes every node in
the network dial the same set, which is worse for the network and no better
for you.

## `seeds` versus `persistent_peers`

| | `seeds` | `persistent_peers` |
|---|---|---|
| Purpose | address discovery, then disconnect | stay connected |
| Reconnects | no | yes, indefinitely |
| Right for | a new node finding the network | a validator that wants a known path |

XRPL EVM's `peers.txt` entries are ordinary nodes, so `persistent_peers` is
the correct field for them. Some published guides put them in `seeds`; that
works for discovery but does not give a validator the stable path it wants.

A validator should keep a small `persistent_peers` set it controls or trusts —
its own sentries first — and let discovery fill the rest.

## Check what you actually have

```bash
curl -s http://127.0.0.1:26657/net_info | jq -r '.result.n_peers'
curl -s http://127.0.0.1:26657/net_info \
  | jq -r '.result.peers[] | "\(.node_info.moniker)\t\(.remote_ip)\t\(.is_outbound)"'
```

Around ten peers is normal here. A node with one or two peers is one
disconnection away from stopping, whatever its height says.

## Your own node's dialable address

```bash
curl -s http://127.0.0.1:26657/status \
  | jq -r '"\(.result.node_info.id)@\(.result.node_info.listen_addr)"'
```

The `id` comes from `config/node_key.json`. Replacing that file changes your
node's identity and invalidates every peer string anyone published for you —
which is exactly why `node_key.json` belongs in the backup set alongside the
configuration, and never in a snapshot archive you publish.

## Firewall

The P2P port must be reachable inbound. RPC, REST, gRPC and EVM JSON-RPC must
not be, unless they are behind a reviewed reverse proxy with rate limiting. See
the Security tab.
