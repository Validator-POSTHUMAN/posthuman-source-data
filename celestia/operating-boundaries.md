# Celestia Mainnet — Operating Boundaries

Use this page to choose the correct Node Ops guide and to keep public evidence
separate from operating authority. It does not enable a service or publish a
network endpoint.

## Choose the correct role

`celestia-appd` is the consensus full-node and validator plane. `celestia-node`
is the data-availability plane. The supported DA roles are **Bridge** and
**Light**; the old “DA Full” role is retired and is not a runnable target.

- Consensus node or validator: [Installation](installation-guide.md).
- DA role selection and legacy-store retirement: [Node roles](full-node-setup.md).
- Bridge or Light service: [DA bridge](bridge-node-setup.md) or
  [DA light](light-node-setup.md).

## Evidence does not establish trust

Use the pinned official bootstrap source and the chain-specific public registry
for discovery. A public peer address or successful TCP/2121 connection proves
only reachability; it does not authenticate ownership, retention, DAS quality,
or host health. Do not turn a partial public registry into sentry inventory.

The [Bridge Nodes Explorer](/explorer/celestia/bridge-nodes) is a public
discovery surface, not an operator inventory.

## Recovery and signer boundaries

Consensus snapshots and state sync follow their dedicated Node Ops sections.
DA recovery follows the selected Bridge or Light guide. Preserve keys,
configuration, and rollback evidence; do not mix a partial public registry with
private topology.

The consensus signer and its state remain one live pair. Follow
[Keys](keys.md) before any recovery, migration, or key-bearing action. No
remote-signer, KMS, or Horcrux procedure is published here without first-party
evidence for the exact celestia-app and CometBFT combination; generic Cosmos
templates are not runnable for Celestia.

## Local DA self-check

The [downloadable self-check](/install/celestia-node-self-check.mjs) is
hard-bound to `127.0.0.1:26658`. It reads an existing restrictive local token
file and reports readiness, network identity, local and network heads, sync
state, and DAS sampling to stdout. It does not expose the endpoint or send
credentials.

## Capacity and status context

Re-check the [official role-specific hardware requirements](https://github.com/celestiaorg/docs/tree/8fbaa868a323c13d3edae2875d9b27765eb29c45/operate/getting-started)
before provisioning. Correlate local evidence with the [official mainnet status
history](https://status.celestia.dev/status/mainnet); neither a green status page
nor host reachability proves that a local node is correct.

For alerting and recovery evidence, use [Monitoring](monitoring.md).
