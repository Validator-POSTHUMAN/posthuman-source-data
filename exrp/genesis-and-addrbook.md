# XRPL EVM Mainnet bootstrap files

Two files decide which chain your node joins. Both come from the official
`xrplevm/networks` repository; neither is interchangeable with the testnet
equivalent.

## Genesis

```bash
NODE_HOME=/var/lib/exrpd/.exrpd

curl -fsSL \
  https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/mainnet/genesis.json \
  -o "$NODE_HOME/config/genesis.json"

sha256sum "$NODE_HOME/config/genesis.json"
exrpd validate-genesis --home "$NODE_HOME"
```

`validate-genesis` checks structure, not identity. To check identity, confirm
the chain ID inside the file is the one you intend to join:

```bash
jq -r .chain_id "$NODE_HOME/config/genesis.json"
# xrplevm_1440000-1
```

| Network | Genesis |
|---|---|
| Mainnet | <https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/mainnet/genesis.json> |
| Testnet | <https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/testnet/genesis.json> |
| Devnet | <https://raw.githubusercontent.com/xrplevm/networks/refs/heads/main/devnet/genesis.json> |

Record the genesis SHA-256 you installed. During a later incident, "the genesis
file is correct" is a claim you want to be able to re-prove in one command
rather than re-derive from a browser tab.

## Peers

XRPL EVM publishes a plain peer list rather than a seed-node service. Sample it
rather than pasting all of it:

```bash
PEERS="$(curl -fsSL https://raw.githubusercontent.com/xrplevm/networks/main/mainnet/peers.txt \
  | awk '{print $1}' | sort -R | head -n 10 | paste -sd, -)"

sudo sed -i "s|^persistent_peers *=.*|persistent_peers = \"${PEERS}\"|" \
  "$NODE_HOME/config/config.toml"
```

Add the POSTHUMAN non-signing peer:

```
71891d3e4790ca8187d38d7acf40ca881074a06b@peer.exrp.posthuman.digital:62656
```

## Address book

There is no published `addrbook.json` for this network. CometBFT builds one
from the peers it meets, at `$NODE_HOME/config/addrbook.json`. It is
disposable: deleting it costs a slower first connection and nothing else.

A stale address book full of dead peers is a real cause of a node that starts
and then finds nobody. If `net_info` shows a low peer count that does not
recover:

```bash
curl -s http://127.0.0.1:26657/net_info | jq -r .result.n_peers
sudo systemctl stop exrpd
sudo -u exrpd rm -f "$NODE_HOME/config/addrbook.json"
sudo systemctl start exrpd
```

A healthy node on this network holds roughly ten peers.

## Peering settings worth setting

From the official validator-security guidance, in `config.toml`:

```toml
max_num_inbound_peers = 100
max_num_outbound_peers = 10
flush_throttle_timeout = "100ms"
```

A validator should additionally use `persistent_peers` it controls or trusts,
rather than depending only on whatever discovery finds.
