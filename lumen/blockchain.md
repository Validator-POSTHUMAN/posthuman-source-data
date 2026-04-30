# Lumen

Lumen is a Cosmos SDK chain focused on DNS auctions, release distribution, and gateway settlement flows.  
The codebase is organised as a standard Go module (`module lumen`) and relies on the Cosmos SDK v0.53 stack.


## Modules at a Glance

| Module | Purpose |
|--------|---------|
| `x/dns` | On-chain domain registry with auction mechanics. |
| `x/gateways` | Gateway contracts, settlement, and rate limits. |
| `x/release` | Artifact publishing, mirroring, and verification. |
| `x/tokenomics` | Chain-wide economic parameters (supply, taxation). |
| `x/pqc` | Dilithium key registry + dual-sign ante (always REQUIRED). |
| `x/gov` (SDK) | Cosmos governance module backing DAO votes & param authority. |


## Security

- **PQC is mandatory.** There is no configuration knob or CLI flag that disables Dilithium signatures.
- Release builds panic if a non-approved PQC backend (test-only/noop) is linked. CI guards enforce this.
- Admission control relies on signature checks, per-account rate limits, and a global mempool cap.

## Project docs

- 🔐 Security: see [SECURITY.md](./SECURITY.md) and the detailed [docs/Security.md](./docs/Security.md)
- 🧪 Simulator (Docker): see [docs/simulation.md](./docs/simulation.md)
- 🧩 Changelog: see [CHANGELOG.md](./CHANGELOG.md)
- 🤝 Contributing: see [CONTRIBUTING.md](./CONTRIBUTING.md)

## Requirements

- Go 1.25.3+ (recommended; older Go 1.23/1.24 still work with toolchain forwarding)
- `jq`, `curl`, `sed`, `awk`, `find`, `tar`
- `buf` (for protobuf generation)
- Docker ≥ 24.0 (only if you use the builder image)

## Building

> ℹ️ **Workflow note:** Documentation now references `make <target>` wrappers (e.g. `make build-native`). The underlying
> `.sh` helpers remain in `devtools/scripts` and `devtools/tests` for direct use when needed.

```bash
# Local developer build (produces build/lumend)
make build-native

# Optional: copy binaries to a custom directory
NETWORK_DIR=artifacts/bin make build-native
```

The canonical binary entry point lives in `cmd/lumend`.

> **Toolchain note:** The module defines `go 1.25.3` and may include a `toolchain go1.25.3` directive.
> Users running Go ≥ 1.21 automatically forward to the proper toolchain without setting `GOTOOLCHAIN` manually.

## Testing

```bash
# Unit tests only
./devtools/scripts/go_test.sh

# Full suite: unit tests + end-to-end flows + REST smoke checks
HOME=$(mktemp -d) make e2e

# PQC flow only (Dilithium3 dual-signing)
make e2e-pqc

# Static analysis
make lint

# Vulnerability scan
make vulncheck
```

Individual flows are exposed via dedicated make targets (wrapping the scripts under `devtools/tests/`), e.g.
`make e2e-dns-auction`, `make e2e-send-tax`, `make e2e-gateways`, `make e2e-release`, or `make e2e-gov`. Most targets rebuild the
binary unless `SKIP_BUILD=1` is exported.

The PQC client injector is enabled by default; pass `--pqc-enable=false` on any `lumend tx` command to intentionally
omit Dilithium signatures (useful for negative tests such as the `e2e_pqc` flow).

You can run all end-to-end tests with:

```bash
make e2e-pqc
HOME=$(mktemp -d) make e2e
make e2e-gov ARGS="--skip-build"
```

All E2E scripts now enforce PQC dual-signing by default.

For a focused gate before opening PRs, run `make preflight`. To spin up a short-lived Docker network that exercises PQC,
DNS, gateways, releases, and rate limits end-to-end, use:

```bash
make simulate-network ARGS="--fast --clean"
```

## Fees & Mempool

Gas prices must remain zero: the node refuses to start if `--minimum-gas-prices` is set to any non-zero value.
Instead of fee bidding, admission control
relies on strict **per-account** and **global** rate limits plus consensus-level block caps. Operators should monitor
the `LUMEN_RL_*` environment knobs only to tighten limits; lowering them below the built-in clamps has no effect.
To avoid dust spam, tokenomics enforces `min_send_ulmn` (default `1000ulmn`) on every `MsgSend`/`MsgMultiSend` output (module accounts are exempt).

## Local Validation (Go 1.23/1.24/1.25)

Tested with Go 1.23, 1.24, and 1.25.
The blocking jobs remain golangci-lint run ./..., staticcheck ./..., and ./devtools/scripts/go_test.sh.

The make vulncheck target first runs a source scan; if it encounters the known upstream internal error
(x/sys/unix ↔ go-isatty), it rebuilds build/lumend and retries using govulncheck -mode=binary.
Only that specific internal error is tolerated — any other failure remains blocking.

```bash
go mod tidy
make lint
make staticcheck
./devtools/scripts/go_test.sh
make vuln-tools && make vulncheck
```
The optional make vulncheck-json target writes a non-blocking JSON report under
artifacts/security/ (source first, then binary fallback).

✅ All CI checks (lint, staticcheck, vulncheck, e2e tests) pass cleanly under Go 1.25.3.

## Protobuf Codegen

```bash
buf generate --template proto/buf.gen.gogo.yaml
```

Generation is configured via `buf.gen.yaml`/`buf.yaml` and writes Go code into the module tree under `x/<module>/types`. The `make proto` target wraps the command and runs `go mod tidy` afterwards.

## Docker Builder

A multi-stage builder lives in `devtools/docker/builder/`. Usage for both the builder target (extracting binaries) and the developer shell target is documented under [devtools/README.md](devtools/README.md#tools--scripts).

## Simulation (Docker)

End-to-end network simulation (seed, validators, full nodes, and a control runner) lives behind `make simulate-network`
(wrapping [`devtools/scripts/simulate_network.sh`](devtools/scripts/simulate_network.sh)). It exercises PQC linking + the negative
path, bank tax enforcement, DNS register→auction→settle, gateway contract create/claim/finalize, release publish, and
per-account/global rate-limit clamps. Logs and snapshots land under `artifacts/sim/`.

**Requirements:** Docker, Go, `jq`.

**Quick smoke:**
```bash
make simulate-network              # defaults: 2 validators, 1 full node
```

The seed node’s RPC/API bindings default to `localhost:27657` / `localhost:2327` (with `27656` for P2P). Override them with
`SIM_HOST_RPC_PORT`, `SIM_HOST_API_PORT`, or `SIM_HOST_P2P_PORT` if those ports are already in use (for example, when you
keep the Docker devnet online while running the simulator).

**Heavier run (cleanup + stronger global clamp signal):**
```bash
LUMEN_RL_GLOBAL_MAX=50 make simulate-network ARGS="--clean --timeout 600"
```

Flags forwarded to the script: `--validators N`, `--fullnodes N`, `--fast`, `--clean`, `--keep`, `--timeout SEC`,
`--image <tag>`.

On WSL, ensure Docker Desktop integration is enabled for the distribution. On Linux hosts add your user to the
`docker` group so the Makefile can reach the daemon.

See also:
- [devtools/README.md](devtools/README.md#tools--scripts) for CLI helpers and environment knobs.
- [docs/Security.md](docs/Security.md) for operational hardening notes.
- [docs/modules/pqc.md](docs/modules/pqc.md) for PQC policy details (required dual-signing; rotate disabled).

## Releases

Cross-platform release artifacts (Linux amd64/arm64, macOS arm64) can be produced locally with:

```bash
make build-release
```

The script emits binaries plus `SHA256SUMS`; verify the checksums before distributing artifacts.

Outputs land in `dist/<git-describe>/` alongside `SHA256SUMS`. Tagging and publishing remain a manual git/GitHub step.

On-chain release metadata (`x/release`) accepts `https://`, `ipfs://`, and `lumen://{ipfs,ipns,fqdn}` URLs, so published bundles can point to decentralized mirrors as well as traditional HTTPS endpoints (see [`docs/releases.md`](docs/releases.md) for details).

## Repository Map

```
app/                    # Cosmos SDK application wiring
cmd/lumend/             # CLI entry point
devtools/               # Build, test, docker, systemd tooling
docs/                   # Additional operator and module docs
proto/                  # Protobuf definitions
x/*                     # Cosmos SDK modules
```

## PQC

`x/pqc` exposes the account-level Dilithium registry and the dual-sign ante decorator. Runtime policy is **always
REQUIRED**: even if genesis params carry another enum, the keeper forces REQUIRED in-memory and `SetParams` panics if a
different value is supplied. Release binaries panic during `init()` if a non-approved PQC backend is linked (only the
Circl and PQClean Dilithium3 implementations are accepted).

The CLI auto-signs the PQC payload for each transaction (`--pqc-enable=true` by default) and exposes `lumend keys pqc-*`
helpers (dev/test build tags only) for importing/testing Dilithium key material. Passing `--pqc-enable=false` merely produces the negative path
used in tests—such transactions are rejected on-chain when the policy is REQUIRED.

See [docs/modules/pqc.md](docs/modules/pqc.md) for signing instructions, parameter descriptions, and CLI usage.

## License

MIT – see [LICENSE](LICENSE).

> ⚠️ Disclaimer: Lumen is open-source software provided *as is*. The maintainers are not responsible for third-party usage, forks, or deployments of the codebase.
