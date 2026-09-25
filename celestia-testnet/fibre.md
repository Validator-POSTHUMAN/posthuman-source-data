# Celestia Mocha-5 Fibre Server

**Mocha-5 / celestia-app v10 only.** Reviewed 2026-09-25. Fibre is a validator-operated data service; it is not a Celestia Bridge or Light node. Follow the exact release-compatible upstream instructions before changing a running validator.

## Scope and safety boundary

- Run Fibre only for a bonded Mocha-5 validator on a released v10-compatible `celestia-app` binary.
- Celestia currently recommends co-locating Fibre with the validator. A remote deployment needs an explicitly reviewed private transport design because the app and signer gRPC links are not TLS-protected.
- Never copy, export, or substitute `priv_validator_key.json`. Fibre requests endorsements through the validator's PrivValidator gRPC API; it must not be given the consensus key file.
- Keep the app gRPC and PrivValidator gRPC endpoints bound to loopback. The Fibre data-plane listener is the only endpoint that should be public.
- `tx valaddr set-host` is an account-key, fee-bearing on-chain transaction. It needs a separate explicit approval for the exact public `host:port`.

## Capacity and prerequisites

Before installing, record the service state, current height, sync state, bonded/jailed state, restart count, free disk, and fresh external signatures. Do not add Fibre to a validator that is unhealthy or has unresolved signing ambiguity.

Require:

1. At least 32 GiB RAM and a CPU that passes the official Fibre CPU test, including GFNI and SHA-NI where the test requires them.
2. Disk and bandwidth sized from the current Celestia Fibre calculator for the validator's voting power. Reserve capacity for the validator database, metadata, download bursts, and retention/pruning overhead. Prefer a separate Fibre data disk.
3. A reachable public TCP listener (default `7980`) and a firewall rule limited to that data-plane port.
4. An app-node gRPC endpoint and a PrivValidator gRPC endpoint, both local to the Fibre process. Do not expose either through a public address, reverse proxy, or load balancer.

Run the official CPU test before deployment. It is workload-intensive, so take a validator health baseline first and recheck sync, restart count, height advance, and external signatures after it completes.

## Configuration

Use dedicated homes for the app node and Fibre. Do not use a default home that could point at another Celestia network.

In the app-node configuration, bind application gRPC locally. In the CometBFT configuration, set the PrivValidator gRPC listener to a **bare** loopback `host:port`:

```toml
# app configuration
[grpc]
address = "127.0.0.1:<APP_GRPC_PORT>"

# CometBFT config.toml
priv_validator_grpc_laddr = "127.0.0.1:<PRIVVAL_GRPC_PORT>"
```

Do **not** prefix `priv_validator_grpc_laddr` with `tcp://`: this field is a bare address and an invalid prefix can prevent the app multiplexer from starting. Treat any app configuration change as validator maintenance: retain the prior file, restart only the reviewed service, and verify signing after.

The Fibre server configuration should use only loopback control links:

```toml
app_grpc_address = "127.0.0.1:<APP_GRPC_PORT>"
signer_grpc_address = "127.0.0.1:<PRIVVAL_GRPC_PORT>"
server_listen_address = "0.0.0.0:7980"
```

Start the exact `fibre` binary packaged with the same reviewed celestia-app release, with explicit `--home`, `--app-grpc-address`, `--signer-grpc-address`, and `--server-listen-address` arguments. Manage it as a dedicated service that requires the validator service, restarts only on failure, and starts on boot. Do not place keys, passphrases, or account credentials in a unit file, environment file, or guide.

## Verification and registration

Before registration, require all of the following:

- validator service active, synced, advancing, bonded, and not jailed;
- Fibre service stable with no restart loop and a ready signer;
- app and PrivValidator gRPC listeners reachable only on `127.0.0.1`;
- public TCP `7980` reachable from an independent host;
- a fresh committed validator signature confirmed by independent Mocha-5 RPCs;
- no existing `x/valaddr` provider record for the validator consensus address.

Only then may an explicitly approved operator transaction set the public host:

```text
celestia-appd tx valaddr set-host <PUBLIC-IP-OR-DNS:7980> \
  --from <VALIDATOR-ACCOUNT> \
  --chain-id mocha-5 \
  --home <REVIEWED-MOCHA-5-HOME> \
  --node <TRUSTED-MOCHA-5-RPC>
```

Review the generated transaction's chain ID, message type, signer, exact host and port, account sequence, and fee before signing. Confirm its committed result (`code: 0`) and query the resulting provider record. A local listener alone does not register a Fibre provider or receive network traffic.

## Monitoring

Monitor Fibre process liveness/restarts, data-plane reachability, host disk, CPU, memory, app-node sync, validator signing, and the published provider record. Export Fibre OpenTelemetry metrics to an approved collector before claiming metrics coverage. Alert on a failing signer connection, unavailable app gRPC, restart loop, listener loss, disk pressure, or missing fresh validator signatures.

## Sources

- Official Celestia Fibre server guide
- Official Fibre metrics and monitoring guide
- celestia-app v10.2.0-mocha Fibre command documentation
- [Mocha-5 multiplexer and v10 guide](multiplexer.md)
- [Celestia key and signer boundaries](keys.md)
