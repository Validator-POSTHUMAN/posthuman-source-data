# Celestia Mainnet Fibre Server

For **mainnet chain ID `celestia`**. Use this with the [Celestia skill](skill.md), [consensus-node installation guide](installation-guide.md), and [official Fibre guide](https://docs.celestia.org/operate/consensus-validators/fibre/). This is a same-host, local-disk procedure for an existing bonded validator, not a validator-key migration or a Bridge/Light node install. The release below was checked on 2026-10-29; refresh official release and chain state before acting.

The matching mainnet app/Fibre release is **`v10.5.0`**. Active app version must be 10 or later before Fibre starts or a provider is registered. Installing a v10 multiplexer binary alone does not activate app v10.

## 1. Preflight

Record the exact host, chain, validator service/home, consensus address, account-key reference, existing provider record, binary versions, service restarts, height/sync, bonded/jailed state, and independent recent signatures. Prove the consensus key cannot sign on another host. Do not inspect, export, copy, replace, or reset the consensus key or signer state. Stop if the validator is unhealthy or identity is ambiguous.

Size a dedicated Fibre data disk separately from celestia-app data and stake-based storage/bandwidth demand. Default receive-buffer upper bound is `16 × 13 × 132 MiB`, about 27 GiB, *in addition* to app and OS memory. Run the official CPU benchmark after the baseline and recheck sync/signing; do not turn an idle trial into a capacity claim. Any shared-disk exception needs a separate resource/alert plan and explicit operator decision. Local app and signing links must stay on loopback. Remote signing requires mTLS and a separately reviewed private app-gRPC path; never use insecure remote-signing overrides in production.

## 2. Stage the matching Fibre binary

If the consensus key is held in an external KMS, verify the exact release's KMS policy and `SignRawBytes` support before Fibre starts. Confirm median signing latency at the celestia-app node is <=10 ms across the last 50 signatures (use `cometbft_privval_signing_latency_*` metrics for a remote signer). Ordinary consensus signatures alone do not prove Fibre endorsement support. Stop if support or latency is unverified.

Select the version for the exact chain above. The host must meet the published release's OS requirements; Fibre's Linux archive requires glibc >=2.34. Stage in a fresh empty directory (do not reuse an app home):

```bash
# Recheck the current mainnet release before use.
FIBRE_VERSION=v10.5.0
STAGE_DIR=$(mktemp -d -p /tmp celestia-fibre.XXXXXX)
cd "$STAGE_DIR"
curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${FIBRE_VERSION}/fibre_Linux_x86_64.tar.gz"
curl -fLO "https://github.com/celestiaorg/celestia-app/releases/download/${FIBRE_VERSION}/checksums.txt"
sha256sum --ignore-missing --check checksums.txt
tar -tzf fibre_Linux_x86_64.tar.gz
```

Require the checksum output for `fibre_Linux_x86_64.tar.gz` to say `OK` and inspect archive members before extraction. Only then run `tar -xzf fibre_Linux_x86_64.tar.gz` and `./fibre version`; require the binary version to match the chosen release. Keep the prior binary for rollback. Never overwrite the running app binary as part of a Fibre-only install. For arm64 or source builds, follow the matching official release instead of relabeling this x86_64 example.

Use the [official hardware requirements and CPU benchmark](https://docs.celestia.org/operate/getting-started/hardware-requirements/) for the pass criteria.

## 3. Enable private app and signer connections

Back up the existing non-secret configuration and preserve its owner/mode. In the validator's *existing* `config/app.toml` `[grpc]` section, set `enable = true` and `address = "127.0.0.1:<APP_GRPC_PORT>"`. In the top level of `config/config.toml`, set `priv_validator_grpc_laddr = "127.0.0.1:<SIGNER_GRPC_PORT>"`. Both are bare `host:port` addresses without `tcp://`. Use literal loopback IPs, not `localhost`. Do not append duplicate TOML sections or alter the separate CometBFT `[rpc] grpc_laddr`. Validate the exact file owner/mode and service-user readability before a controlled app restart. After restarting, prove both listeners are loopback-only, the node has caught up, the restart count is stable, and independent RPC shows fresh signatures. Do not proceed if signing fails.

## 4. Install the Fibre service

Immediately before the first Fibre start, query the existing node's `/abci_info` and require `result.response.app_version >= 10`. The installed binary version is not evidence of active app version; an app-v9 chain lacks `x/fibre` and `x/valaddr`. Keep Fibre stopped if the gate fails.

```bash
# Replace the RPC port if this node does not use the default.
curl -fsS 'http://127.0.0.1:26657/abci_info' | jq -e '(.result.response.app_version | tonumber) >= 10'
```

Create a dedicated non-login service account and persistent Fibre home on the planned data disk, separate from the app home. Use the verified release-matched `fibre` binary. Configure a dedicated service to require/order after the validator, restart only on failure, and start with the reviewed values:

```text
fibre start --home <FIBRE_HOME> \
  --app-grpc-address 127.0.0.1:<APP_GRPC_PORT> \
  --signer-grpc-address 127.0.0.1:<SIGNER_GRPC_PORT> \
  --server-listen-address 127.0.0.1:<FIBRE_PORT>
```

Example systemd unit template (replace every placeholder from your own inventory before installing it):

```ini
[Unit]
Description=Celestia Fibre server
Requires=<VALIDATOR_UNIT>.service
After=network-online.target <VALIDATOR_UNIT>.service

[Service]
User=<FIBRE_USER>
ExecStart=<VERIFIED_FIBRE_BINARY> start --home <FIBRE_HOME> --app-grpc-address 127.0.0.1:<APP_GRPC_PORT> --signer-grpc-address 127.0.0.1:<SIGNER_GRPC_PORT> --server-listen-address 127.0.0.1:<FIBRE_PORT>
Restart=on-failure
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Keep the data-plane listener local during the first start. Confirm the log reports the expected chain ID, app connection, `signer ready`, and no restart loop. Fibre creates `<FIBRE_HOME>/config/server_config.toml`; CLI flags override it. Its config rejects unknown fields. Do not put keys or passphrases in the unit or environment. When stable, change only the data-plane bind to the approved public address/port, open only that TCP port, and verify TLS reachability from an independent host. Keep app and signer gRPC private. Enable at boot only after these checks and monitoring are in place.

## 5. Register and verify

Registration is a fee-bearing account-key transaction and needs explicit approval for the *exact* public `host:port`. First verify the active app version is >=10 via `/abci_info`, bonded status, independent signing, public Fibre reachability, and the current `x/valaddr` record. In a protected local terminal, review the unsigned `celestia-appd tx valaddr set-host <HOST:PORT> --from <ACCOUNT> --chain-id <CHAIN_ID> --home <APP_HOME> --node <TRUSTED_RPC>` transaction: message, chain ID, signer, account sequence, fee, host and port. Keep keyring passphrases out of chat, argv, logs, units, and env files. Broadcast once only after approval. Require a committed `code=0`, then run `celestia-appd query valaddr provider <VALCONS> --node <TRUSTED_RPC>`; require `found=true` and the exact approved host. A provider record persists across restarts; do not resend the transaction as a status check.

## 6. Postflight and rollback

Require Fibre readiness and liveness `SERVING` after registration. A successful probe is not a successful upload; verify an upload canary separately when an approved funded client is available.

With a reviewed `grpc_health_probe` binary, check Fibre's local TLS port. Before registration, readiness may correctly fail with `provider_not_registered`; liveness should be `SERVING`. After registration, require both probes to exit 0 and report `SERVING`:

```bash
grpc_health_probe -addr=127.0.0.1:<FIBRE_PORT> -tls -tls-no-verify
grpc_health_probe -addr=127.0.0.1:<FIBRE_PORT> -tls -tls-no-verify -service=fibre-liveness
```

The readiness signer check proves signer reachability and key continuity, not a successful signature.

Prove app sync/height advance, bonded/unjailed state, fresh independent signatures, stable app/Fibre restart counts, private control listeners, external Fibre TLS reachability, matching on-chain provider, free disk, memory/I/O/thermal headroom, and actual upload/readiness when available. Monitor Fibre liveness/restarts, public port, shard storage, signing, and the guard; only claim metrics coverage if a collector is verified. If Fibre overloads a shared signer, stop *Fibre only* and preserve the validator. Before registration, revert the listener/firewall and Fibre service separately; after registration, update the on-chain record only through a separately approved transaction. Never roll signer state back.

Sources: [official Fibre guide](https://docs.celestia.org/operate/consensus-validators/fibre/), [v10.5.0 release](https://github.com/celestiaorg/celestia-app/releases/tag/v10.5.0), and [Fibre CLI reference](https://github.com/celestiaorg/celestia-app/blob/v10.5.0/fibre/cmd/README.md).
