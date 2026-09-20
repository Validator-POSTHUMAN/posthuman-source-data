# Solana Testnet Endpoints and References

## Cluster parameters

| Parameter | Value |
|---|---|
| Cluster | `testnet` |
| Genesis hash | `4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY` |
| Public RPC | `https://api.testnet.solana.com` |
| Public WebSocket | `wss://api.testnet.solana.com` |
| Faucet | `solana airdrop 1` (1 SOL per request) |
| Explorer | <https://explorer.solana.com/?cluster=testnet> |

Testnet is subject to **ledger resets** and coordinated cluster restarts. Both
change the shred version; neither is an incident on your side.

## Gossip entrypoints

````
entrypoint.testnet.solana.com:8001
entrypoint2.testnet.solana.com:8001
entrypoint3.testnet.solana.com:8001
````

## Known validators for snapshot bootstrap

Use with `--only-known-rpc`:

````
5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on   # Anza
dDzy5SR3AXdYWVqbDEkVFdvSPCtS9ihF5kJkHCtXoFs   # MonkeDAO
Ft5fbkqNa76vnsjYNwjDZUXoTWpP7VYm3mtsaQckQADN   # Certus One
eoKpUABi59aT4rR9HGS3LcMecfut9x7zJyodWWP43YQ   # SerGo
9QxCLckBiJc783jnMvXZubK4wH86Eqqvashtrwvcsgkv   # Algo|Stake
````

## Example validator command line

````bash
exec agave-validator \
  --identity /home/sol/testnet-validator-keypair.json \
  --vote-account /home/sol/testnet-vote-account-keypair.json \
  --ledger /mnt/ledger \
  --accounts /mnt/accounts \
  --snapshots /mnt/ledger/snapshots \
  --log /home/sol/agave-validator.log \
  --rpc-port 8899 \
  --private-rpc \
  --dynamic-port-range 8000-8050 \
  --entrypoint entrypoint.testnet.solana.com:8001 \
  --entrypoint entrypoint2.testnet.solana.com:8001 \
  --entrypoint entrypoint3.testnet.solana.com:8001 \
  --known-validator 5D1fNXzvv5NjV1ysLjirC4WY92RNsVH18vjmcszZd8on \
  --known-validator dDzy5SR3AXdYWVqbDEkVFdvSPCtS9ihF5kJkHCtXoFs \
  --known-validator Ft5fbkqNa76vnsjYNwjDZUXoTWpP7VYm3mtsaQckQADN \
  --known-validator eoKpUABi59aT4rR9HGS3LcMecfut9x7zJyodWWP43YQ \
  --known-validator 9QxCLckBiJc783jnMvXZubK4wH86Eqqvashtrwvcsgkv \
  --only-known-rpc \
  --expected-genesis-hash 4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY \
  --wal-recovery-mode skip_any_corrupted_record \
  --limit-ledger-size
````

## Ports

| Port | Protocol | Purpose | Exposure |
|---|---|---|---|
| 8000–8050 | TCP + UDP | gossip, turbine, repair, TPU | open |
| 8899 / 8900 | TCP | JSON-RPC HTTP / WebSocket | closed |
| 22 | TCP | SSH | restricted to management address |

## Metrics

Reporting to the public cluster metrics server is required for the Solana
Foundation Delegation Program on **both** clusters. The testnet
`SOLANA_METRICS_CONFIG` value is published in the Anza cluster documentation
and differs from the mainnet-beta value — setting the mainnet one on a testnet
node does not satisfy the criterion.

## References

- Available clusters — <https://docs.anza.xyz/clusters/available>
- Setup an Agave validator (written for testnet) — <https://docs.anza.xyz/operations/setup-a-validator>
- Delegation programme criteria — <https://solana.org/delegation-criteria>
- Feature-gate tracker — <https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule>
- Testnet explorer — <https://explorer.solana.com/?cluster=testnet>
- validators.app testnet view — <https://www.validators.app/?network=testnet>

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
