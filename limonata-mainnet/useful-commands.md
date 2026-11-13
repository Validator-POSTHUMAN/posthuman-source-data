# Read-only mainnet commands

Assumes installation above, explicit home, local Comet RPC on 26657 and jq. Adapt local ports only to your reviewed configuration. These commands never broadcast or print secret files.

```bash
"$HOME/.local/bin/limonatad" version
curl --fail --silent --show-error http://127.0.0.1:26657/status | jq -e '.result | {chain: .node_info.network, height: .sync_info.latest_block_height, catching_up: .sync_info.catching_up}'
curl --fail --silent --show-error http://127.0.0.1:26657/net_info | jq '.result.n_peers'
"$HOME/.local/bin/limonatad" comet show-node-id --home "$HOME/.limonata-mainnet"
"$HOME/.local/bin/limonatad" query staking params --node tcp://127.0.0.1:26657 --home "$HOME/.limonata-mainnet" --output json
"$HOME/.local/bin/limonatad" query slashing params --node tcp://127.0.0.1:26657 --home "$HOME/.limonata-mainnet" --output json
"$HOME/.local/bin/limonatad" query upgrade plan --node tcp://127.0.0.1:26657 --home "$HOME/.limonata-mainnet" --output json
"$HOME/.local/bin/limonatad" query feemarket params --node tcp://127.0.0.1:26657 --home "$HOME/.limonata-mainnet" --output json
```

Expected chain: `limonata_20777-1`. Sample status twice to prove advancement. Compare an identical height's block ID hash on the local node and two independent mainnet Comet RPCs. Latest heights may differ normally; do not compare different heights' hashes.

For validator checks, inspect `query staking validator --help` and `query slashing signing-info --help`, then supply your own public operator/consensus identifiers. Never print private validator/P2P keys, wallet exports or DKG key contents. The approved binary has no `query encmempool` CLI subcommand: use documented events and current reviewed module API/source instead.

## Provenance

Reviewed 2026-11-13 against the [official final mainnet release](https://github.com/Limonata-Blockchain/limonata/releases/tag/v0.4.0-mainnet.3), its startup instructions, configurations and checksums. Refresh official requirements before use. Publisher hashes provide integrity, not independent publisher certification. These guides do not enable a Hub installer or wallet signing.
