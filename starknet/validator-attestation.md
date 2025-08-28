# Starknet Validator Attestation

This is a tool for attesting validators on Starknet. Implements the attestation specification in [SNIP 28](https://community.starknet.io/t/snip-28-staking-v2-proposal/115250).


## Requirements

- A Starknet node with support for the JSON-RPC 0.8.1 API specification. This tool has been tested with [Pathfinder](https://github.com/eqlabs/pathfinder) v0.16.3.
- Staking contracts set up and registered with Staking v2.
- Sufficient funds in the operational account to pay for attestation transactions.


## Installation

You can either use the Docker image we publish on [GitHub](https://github.com/eqlabs/starknet-validator-attestation/pkgs/container/starknet-validator-attestation), the binaries on our [release page](https://github.com/eqlabs/starknet-validator-attestation/releases/latest) or compile the source code from this repository. Compilation requires Rust 1.85+.


## Running

```shell
docker run -it --rm --network host \
  -e VALIDATOR_ATTESTATION_OPERATIONAL_PRIVATE_KEY="0xdeadbeef" \
  ghcr.io/eqlabs/starknet-validator-attestation \
  --staker-operational-address 0x02e216b191ac966ba1d35cb6cfddfaf9c12aec4dfe869d9fa6233611bb334ee9 \
  --node-url http://localhost:9545/rpc/v0_8 \
  --local-signer
```

Each CLI option can also be set via environment variables. Please check the output of `starknet-validator-attestation --help` for more information.

Log level defaults to `info`. Verbose logging can be enabled by setting the `RUST_LOG` environment variable to `debug`.


### Signatures

There are two options for signing attestation transactions sent by the tool.

- You can use `--local-signer`. In this case you _must_ set the private key of the operational account in the `VALIDATOR_ATTESTATION_OPERATIONAL_PRIVATE_KEY` environment variable.
- You can use an external signer implementing a simple HTTP API. Use `--remote-signer-url URL` or set the `VALIDATOR_ATTESTATION_REMOTE_SIGNER_URL` to the URL of the external signer API.
