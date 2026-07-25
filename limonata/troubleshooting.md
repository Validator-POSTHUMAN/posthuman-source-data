# Limonata Testnet — Troubleshooting

## Official genesis fails `validate-genesis`

On `limonata-v0.3.4`, the official genesis can trigger a `burn_bps` range
error because of a dormant-module validation check. Do not replace a
checksum-verified official genesis to work around this message.

Verify the file instead:

```bash
sha256sum "$HOME/.limonatad/config/genesis.json"
```

Expected SHA-256:

```text
bb76a6d8abbb1bdeaa41d92811066b16bd6a48f58f7136e3fcb71226b6af4569
```

## State sync does not start or cannot verify trust data

Use the CometBFT RPC endpoint, not the EVM JSON-RPC endpoint, for `/block`
and `/commit` requests:

```bash
RPC=https://cosmos-rpc.limonata.xyz
curl -fsS "$RPC/status" | jq '.result.sync_info'
curl -fsS "$RPC/block" | jq -r '.result.block.header.height'
```

Recompute a recent trust height and hash, then cross-check them with another
trusted source before restarting a production validator. Do not copy validator
keys or signer state to a second live node.

## Node is running but remains behind

Check local versus official height, whether the local height advances, and the
peer count:

```bash
curl -fsS http://127.0.0.1:26657/status |
  jq '.result.sync_info | {latest_block_height, catching_up}'
curl -fsS https://cosmos-rpc.limonata.xyz/status |
  jq '.result.sync_info | {latest_block_height, catching_up}'
curl -fsS http://127.0.0.1:26657/net_info | jq '.result.n_peers'
```

For a full node, confirm inbound TCP `26656` is allowed by your firewall. Keep
the other node APIs loopback-only unless you have a separately secured public
service design.

## Prebuilt binary does not run

The `limonata-v0.3.4` amd64 release requires glibc 2.38 or newer. Confirm:

```bash
ldd --version | head -1
limonatad version --long
```

Use a supported host or follow the current official build instructions. Verify
the release archive and binary checksums before replacing any executable.

## Validator recovery or DKG issue

Do not delete data, restart a signer mid-round, or move a validator key as a
first response. Preserve the consensus key, monotonic signer state, and
mode-`0600` DKG key; verify signing and current DKG/QUAL state first. Follow
the official validator documentation and a target-specific recovery plan.
