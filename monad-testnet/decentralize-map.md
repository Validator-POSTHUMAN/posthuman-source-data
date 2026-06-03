# Monad Testnet Decentralize Map

POSTHUMAN publishes testnet RPC and WebSocket endpoints for users, wallets and test tooling. The map separates public access services from validator-sensitive infrastructure.

## Quick Search

| Search term | Result |
|-------------|--------|
| `monad testnet rpc` | `https://rpc-monad-testnet.posthuman.digital` |
| `monad testnet wss` | `wss://rpc-monad-testnet.posthuman.digital` |
| `chain id 10143` | Monad Testnet |
| `posthuman testnet validator region` | POSTHUMAN validator region: Warsaw, Poland |
| `public gateway` | POSTHUMAN RPC Gateway, Helsinki region |

---

## Public Endpoints

| Type | Endpoint | Chain ID | Status |
|------|----------|----------|--------|
| HTTPS JSON-RPC | `https://rpc-monad-testnet.posthuman.digital` | `10143` / `0x279f` | Live |
| WebSocket JSON-RPC | `wss://rpc-monad-testnet.posthuman.digital` | `10143` / `0x279f` | Live |

The public RPC and WSS domains are served through Cloudflare and the POSTHUMAN endpoint fleet. Validator-local RPC is not exposed publicly.

---

## Map Markers

| Marker | Layer | Approx. Location | Provider / Network | What users can do |
|--------|-------|------------------|--------------------|-------------------|
| POSTHUMAN Testnet RPC Gateway | Public RPC/WSS | Helsinki, Finland | POSTHUMAN endpoint fleet / Cloudflare front door | Query blocks, submit JSON-RPC transactions, connect WSS clients |
| POSTHUMAN Testnet Validator Region | Validator | Warsaw, Poland | Privacy protected | Understand regional validator distribution without exposing the host |
| Cloudflare Edge | Anycast edge | Global | Cloudflare | Reach the RPC/WSS gateway through nearby edge POPs |

---

## GeoJSON-Style Data

This feed can be converted into an interactive map layer. Coordinates are approximate and intentionally avoid validator IP exposure.

```json
{
  "network": "monad-testnet",
  "chain_id": "10143",
  "markers": [
    {
      "id": "posthuman-monad-testnet-rpc-gateway",
      "label": "POSTHUMAN Monad Testnet RPC Gateway",
      "layer": "public_rpc_wss",
      "status": "live",
      "endpoints": {
        "rpc": "https://rpc-monad-testnet.posthuman.digital",
        "wss": "wss://rpc-monad-testnet.posthuman.digital"
      },
      "lat": 60.1695,
      "lon": 24.9354,
      "city": "Helsinki",
      "country": "FI",
      "privacy": "public service endpoint"
    },
    {
      "id": "posthuman-monad-testnet-validator-region",
      "label": "POSTHUMAN Testnet Validator Region",
      "layer": "validator_region",
      "status": "active",
      "lat": 52.2298,
      "lon": 21.0118,
      "city": "Warsaw",
      "country": "PL",
      "privacy": "region only; validator IP and topology are not published"
    },
    {
      "id": "cloudflare-anycast-front-door",
      "label": "Cloudflare Edge Front Door",
      "layer": "edge_network",
      "status": "live",
      "scope": "global_anycast",
      "privacy": "Cloudflare edge; origin is hidden"
    }
  ]
}
```

---

## Wallet Configuration

| Field | Value |
|-------|-------|
| Network name | `Monad Testnet POSTHUMAN` |
| Chain ID | `10143` |
| Currency symbol | `MON` |
| RPC URL | `https://rpc-monad-testnet.posthuman.digital` |
| WSS URL | `wss://rpc-monad-testnet.posthuman.digital` |

---

## Decentralization View

| Layer | Purpose | Privacy rule |
|-------|---------|--------------|
| RPC/WSS gateway | Public access for users, wallets and test clients | Public endpoints only |
| Validator region | Show geographic diversity | Region/city only, no validator IP |
| Edge network | Improve reachability | Cloudflare anycast is shown as a global front door |
| Monitoring | Validate chain ID, block progress and WSS health | Internal alert channels are not published |

## Privacy Rules

- Validator IP addresses, private topology and sentry details are not published.
- Public RPC/WSS endpoints are safe to display and copy.
- Geo markers are approximate and service-oriented.
- Testnet WSS is verified through POSTHUMAN domain before publication.

---

## Snapshot Layer

POSTHUMAN Monad testnet snapshots are served through the shared snapshot gateway:

| Field | Value |
|-------|-------|
| Snapshot index | `https://snapshots.posthuman.digital/monad/` |
| Testnet metadata | `https://snapshots.posthuman.digital/monad/testnet/latest.json` |
| Latest height | `https://snapshots.posthuman.digital/monad/testnet/latest-height.txt` |
| Format | `tar.lz4` |
| Checksum | `sha256` per release |
| Retention | Latest 3 local releases, mirrored to R2 with deletion sync |

Map data feed:

```json
{
  "network_id": "monad-testnet",
  "node_type": "snapshot_mirror",
  "operator": "Posthuman",
  "status": "healthy",
  "metadata_url": "https://snapshots.posthuman.digital/monad/testnet/latest.json",
  "privacy": "public snapshot endpoint"
}
```
