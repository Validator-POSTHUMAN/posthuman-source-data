# Solana Mainnet-Beta Endpoints and References

## Cluster parameters

| Parameter | Value |
|---|---|
| Cluster | `mainnet-beta` |
| Genesis hash | `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d` |
| Public RPC | `https://api.mainnet-beta.solana.com` |
| Public WebSocket | `wss://api.mainnet-beta.solana.com` |

The public RPC is rate-limited and is for operator checks and light use only.
Do not point an application or a monitoring scrape loop at it.

## Gossip entrypoints

````
entrypoint.mainnet-beta.solana.com:8001
entrypoint2.mainnet-beta.solana.com:8001
entrypoint3.mainnet-beta.solana.com:8001
entrypoint4.mainnet-beta.solana.com:8001
entrypoint5.mainnet-beta.solana.com:8001
````

## Known validators for snapshot bootstrap

Use with `--only-known-rpc` so the node will not take a snapshot from an
arbitrary gossip peer:

````
7Np41oeYqPefeNQEHSv1UDhYrehxin3NStELsSKCT4K2
GdnSyH3YtwcxFvQrVVJMm1JhTS4QVX7MFsX56uJLUfiZ
DE1bawNcRJB9rVm3buyMVfr8mBEoyyu73NBovf2oXJsJ
CakcnaRDHka2gXyfbEd2d3xsvkJkqsLw2akB3zsN1D2S
````

## Ports

| Port | Protocol | Purpose | Exposure |
|---|---|---|---|
| 8000–8020 (default) | TCP + UDP | gossip, turbine, repair, TPU | open to the internet |
| 8899 | TCP | JSON-RPC over HTTP | **closed** on a staked validator |
| 8900 | TCP | JSON-RPC over WebSocket (`rpc-port + 1`) | **closed** on a staked validator |
| 22 | TCP | SSH | restricted to a static management address |

Pin the P2P range with `--dynamic-port-range 8000-8050` so the firewall rule and
the process agree. Outbound traffic must not be filtered.

## Metrics

Reporting to the public cluster metrics server is required for the Solana
Foundation Delegation Program. Set `SOLANA_METRICS_CONFIG` in the validator
environment with the mainnet-beta value published in the Anza cluster
documentation.

## Official references

- Agave operations documentation — <https://docs.anza.xyz/operations/>
- Available clusters and example command lines — <https://docs.anza.xyz/clusters/available>
- Vote account management — <https://docs.anza.xyz/operations/guides/vote-accounts>
- Security best practices — <https://docs.anza.xyz/operations/best-practices/security>
- Monitoring best practices — <https://docs.anza.xyz/operations/best-practices/monitoring>
- Agave repository — <https://github.com/anza-xyz/agave>
- Feature-gate tracker — <https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule>
- Solana Improvement Documents — <https://github.com/solana-foundation/solana-improvement-documents>
- Hardware compatibility list — <https://www.solanahcl.org/>
- Solana Foundation Delegation Program criteria — <https://solana.org/delegation-criteria>

## Explorers

- <https://explorer.solana.com/>
- <https://solscan.io/>
- <https://solanabeach.io/>

## Validator dashboards

- <https://www.validators.app/> — scoring, data-centre and ASN concentration
- <https://live.trillium.so/> — per-epoch rewards, MEV, block production
- <https://dashboards.validblocks.com/validators>
- <https://stakeutils.com/>
- <https://gdindex.app/>

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
