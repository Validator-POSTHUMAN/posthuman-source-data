# Monad Mainnet Decentralize Map

POSTHUMAN publishes a public Monad mainnet RPC entrypoint and a privacy-safe infrastructure map. The map is designed for users and operators who want to find POSTHUMAN services without exposing validator-sensitive topology.

## Quick Search

| Search term | Result |
|-------------|--------|
| `monad mainnet rpc` | `https://rpc-monad.posthuman.digital` |
| `monad posthuman rpc` | POSTHUMAN Monad RPC Gateway, Helsinki region |
| `chain id 143` | Monad Mainnet |
| `mainnet validator region` | POSTHUMAN validator region: Tokyo, Japan |
| `public gateway` | POSTHUMAN RPC Gateway on the endpoint fleet |

---

## Public Endpoints

| Type | Endpoint | Chain ID | Status |
|------|----------|----------|--------|
| HTTPS JSON-RPC | `https://rpc-monad.posthuman.digital` | `143` / `0x8f` | Live |
| WebSocket | Not published yet | - | Waiting for healthy mainnet WSS upstream |

The public RPC domain is served through Cloudflare and the POSTHUMAN endpoint fleet. Validator-local RPC is not exposed publicly.

---

## Map Markers

| Marker | Layer | Approx. Location | Provider / Network | What users can do |
|--------|-------|------------------|--------------------|-------------------|
| POSTHUMAN RPC Gateway | Public RPC | Helsinki, Finland | POSTHUMAN endpoint fleet / Cloudflare front door | Query blocks, submit JSON-RPC transactions, configure wallets |
| POSTHUMAN Validator Region | Validator | Tokyo, Japan | Privacy protected | Understand regional validator distribution without exposing the host |
| Cloudflare Edge | Anycast edge | Global | Cloudflare | Reach the RPC gateway through nearby edge POPs |

---

## GeoJSON-Style Data

This feed can be converted into an interactive map layer. Coordinates are approximate and intentionally avoid validator IP exposure.

```json
{
  "network": "monad-mainnet",
  "chain_id": "143",
  "markers": [
    {
      "id": "posthuman-monad-mainnet-rpc-gateway",
      "label": "POSTHUMAN Monad RPC Gateway",
      "layer": "public_rpc",
      "status": "live",
      "endpoint": "https://rpc-monad.posthuman.digital",
      "lat": 60.1695,
      "lon": 24.9354,
      "city": "Helsinki",
      "country": "FI",
      "privacy": "public service endpoint"
    },
    {
      "id": "posthuman-monad-mainnet-validator-region",
      "label": "POSTHUMAN Validator Region",
      "layer": "validator_region",
      "status": "active",
      "lat": 35.6895,
      "lon": 139.6917,
      "city": "Tokyo",
      "country": "JP",
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
| Network name | `Monad POSTHUMAN` |
| Chain ID | `143` |
| Currency symbol | `MON` |
| RPC URL | `https://rpc-monad.posthuman.digital` |

---

## Decentralization View

| Layer | Purpose | Privacy rule |
|-------|---------|--------------|
| RPC gateway | Public access for users and wallets | Public endpoint only |
| Validator region | Show geographic diversity | Region/city only, no validator IP |
| Edge network | Improve reachability | Cloudflare anycast is shown as a global front door |
| Monitoring | Validate chain ID and block progress | Internal alert channels are not published |

## Privacy Rules

- Validator IP addresses, private topology and sentry details are not published.
- Public RPC endpoints are safe to display and copy.
- Geo markers are approximate and service-oriented.
- Mainnet WSS is not shown until a healthy upstream is selected and verified.
