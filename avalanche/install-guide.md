# Avalanche Node and Validator Guide

> Reviewed on 2026-09-14. This is a public, copy-only runbook. It does not
> connect to a host, handle a wallet, sign a staking transaction, or change a
> running validator.

## 1. Choose an installation path

Avalanche publishes three current installation paths: the guided installer,
a pre-built release archive, and a source build. The installer creates the
node configuration and a system service; a manual installation leaves runtime
supervision to the operator. Sources: [official installer guide](https://build.avax.network/docs/nodes/run-a-node/using-install-script/installing-avalanche-go), [pre-built binary guide](https://build.avax.network/docs/nodes/run-a-node/using-binary), [source-build guide](https://build.avax.network/docs/nodes/run-a-node/from-source).

For a reproducible source build, pin the reviewed tag and verify that it
resolves to the expected commit before building:

```bash
set -Eeuo pipefail
VERSION=v1.15.0
EXPECTED_COMMIT=70bd6d063b7343fd2cd8217200aaf77b57f19f68

git clone https://github.com/ava-labs/avalanchego.git
cd avalanchego
git checkout --detach "$VERSION"
test "$(git rev-parse HEAD)" = "$EXPECTED_COMMIT"
./scripts/build.sh
./build/avalanchego --version
```

The build prerequisites and `scripts/build.sh` workflow are documented by
Avalanche; the v1.15.0 tag and commit are pinned here so a moving branch is not
treated as a release. Sources: [source-build guide](https://build.avax.network/docs/nodes/run-a-node/from-source), [AvalancheGo v1.15.0](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

For a pre-built Linux AMD64 installation, use the release asset named
`avalanchego-linux-amd64-v1.15.0.tar.gz`. Verify its detached signature and
this reviewed SHA-256 before extracting it:

```text
ca5330e6cf8f31106f89929db84c65af7bf2a6a74789bad36a7bbde4cbea7019
```

Source: [AvalancheGo v1.15.0 release assets](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

## 2. Network and API baseline

AvalancheGo's HTTP API listens on `127.0.0.1:9650` by default, while the
Primary Network staking port is TCP `9651`. A validator must send and receive
traffic on its staking port and have a reachable public address. Sources:
[AvalancheGo configuration flags](https://build.avax.network/docs/nodes/configure/configs-flags), [validator requirements](https://build.avax.network/docs/primary-network/validate/node-validator).

Keep a validator's API on loopback:

```json
{
  "http-host": "127.0.0.1",
  "http-port": 9650
}
```

A dedicated RPC node may bind the HTTP API to an explicitly reviewed private
interface and publish it through an authenticated or allowlisted reverse
proxy. Do not expose a signing validator's API directly to the internet; the
official installer warns that a public RPC listener must be protected by a
firewall that admits only known clients. Sources: [configuration flags](https://build.avax.network/docs/nodes/configure/configs-flags), [installer RPC warning](https://build.avax.network/docs/nodes/run-a-node/using-install-script/installing-avalanche-go).

After bootstrap, the local Primary Network endpoints are:

```text
P-Chain: http://127.0.0.1:9650/ext/bc/P
X-Chain: http://127.0.0.1:9650/ext/bc/X
C-Chain: http://127.0.0.1:9650/ext/bc/C/rpc
```

Source: [official node guide](https://build.avax.network/docs/nodes/run-a-node/from-source#rpc).

## 3. Verify the node before staking

All three Primary Network chains must be bootstrapped before validator
registration. `health.health` reports the node's aggregate health, while
`info.getNodeID` returns the NodeID, BLS public key, and proof of possession
required for Primary Network validation. Sources: [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc), [Health RPC](https://build.avax.network/docs/rpcs/other/health-rpc), [validator guide](https://build.avax.network/docs/primary-network/validate/node-validator).

```bash
API=http://127.0.0.1:9650

curl -fsS "$API/ext/health" | jq '{healthy, checks}'

for chain in P X C; do
  curl -fsS -H 'content-type:application/json' \
    --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"info.isBootstrapped\",\"params\":{\"chain\":\"$chain\"}}" \
    "$API/ext/info" | jq -r --arg chain "$chain" '"\($chain): \(.result.isBootstrapped)"'
done

curl -fsS -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"info.getNodeID"}' \
  "$API/ext/info" | jq '.result'
```

Verify TCP `9651` from a different network before staking; a successful local
health check is not proof that peers can dial the node. Source: [validator
requirements](https://build.avax.network/docs/primary-network/validate/node-validator#requirements).

## 4. Create the validator

Avalanche's reviewed paths are Core web, `platform-cli`, the Avalanche SDK, or
the Builder Console. Validator registration is a P-Chain transaction. Source:
[Turn Node Into Validator](https://build.avax.network/docs/primary-network/validate/node-validator).

Safe operator sequence:

1. Complete the P/X/C bootstrap, health, and external TCP `9651` checks above.
   Source: [validator requirements](https://build.avax.network/docs/primary-network/validate/node-validator#requirements).
2. Retrieve the NodeID, BLS public key, and proof of possession with
   `info.getNodeID`. Source: [Info RPC](https://build.avax.network/docs/rpcs/other/info-rpc#infogetnodeid).
3. Open the official [Core staking interface](https://core.app) or
   [Builder Console staking tool](https://build.avax.network/console/primary-network/stake), select Primary Network validation, and enter the reviewed node and reward parameters. Source: [official validator guide](https://build.avax.network/docs/primary-network/validate/node-validator#add-a-validator-with-core-extension).
4. Review the NodeID, stake, duration, delegation fee, reward address, start
   condition, and wallet network before approving the P-Chain transaction.
   These parameters cannot be changed and stake cannot be removed early after
   submission. Source: [official validator warning](https://build.avax.network/docs/primary-network/validate/node-validator#introduction).
5. Before the start condition, confirm the NodeID through
   `platform.getPendingValidators`; after validation begins, use
   `platform.getCurrentValidators`. Source: [official verification steps](https://build.avax.network/docs/primary-network/validate/node-validator#verify-validator-status).

Refresh the current stake, duration, fee, and uptime requirements from the
official validator and Helicon sources immediately before signing. The
Helicon changes described in the Upgrade section apply at their documented
activation boundary, not retroactively. Sources: [validator guide](https://build.avax.network/docs/primary-network/validate/node-validator), [v1.15.0 release](https://github.com/ava-labs/avalanchego/releases/tag/v1.15.0).

## 5. Protect identity

The staking certificate, staking private key, and BLS signer key define the
node's validator identity. Keep their contents out of terminals, tickets, and
public repositories, and never run two nodes with the same staking identity.
Avalanche's backup guide identifies these files as the unique material needed
to reconstruct a NodeID. Source: [Backup and Restore](https://build.avax.network/docs/nodes/maintain/backup-restore).
