# Cosmos Hub Decentralization Map Runbook

The map uses `posthuman-decentralization-map/v1` and is generated only from
public Cosmos Hub infrastructure: chain-registry RPC/seeds/persistent peers,
POSTHUMAN public RPC, selected public RPC `/net_info` responses and GeoIP.
Private validator IPs, signer locations, sentry topology and local addrbooks
are excluded.

Generate and validate:

```bash
cd /home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data
python3 scripts/update-cosmoshub-decentralize-map.py
python3 -m py_compile scripts/update-celestia-decentralize-map.py \
  scripts/update-cosmoshub-decentralize-map.py
python3 -m json.tool cosmoshub/decentralize-map.json >/dev/null
python3 scripts/update-cosmoshub-decentralize-map.py --check
```

Integrity requirements:

- schema is `posthuman-decentralization-map/v1`;
- `network_id` is `cosmoshub-mainnet` and `chain_id` is `cosmoshub-4`;
- point IDs are unique and every coordinate is valid;
- every included IP is globally routable;
- at least one public RPC, bootstrap entry and observed peer is present;
- summary point count exactly matches the points array.

The generated JSON is public source data. Review its diff before commit. The
Network Hub projection intentionally strips raw IPs and private metadata.
