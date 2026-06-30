# Celestia Testnet Decentralization Map Runbook

This document describes how to update and deploy the Celestia Mocha testnet decentralization map used on:

- https://nodes.posthuman.digital/chains/celestia-testnet?tab=decentralize-map

## Files

- `networks.json` — enables the `decentralize-map` tab for `celestia-testnet`.
- `celestia-testnet/decentralize-map.json` — rendered map data consumed by the UI.
- `celestia-testnet/decentralize-map.md` — markdown fallback/description for the tab.
- `scripts/update-celestia-testnet-decentralize-map.py` — local generator for `celestia-testnet/decentralize-map.json`.
- `scripts/update-celestia-testnet-decentralize-map-and-deploy.sh` — cron-friendly update, commit, push and deploy wrapper.

## Data sources

The generator intentionally uses only public Celestia Mocha testnet infrastructure:

1. Cosmos chain-registry Celestia Mocha testnet `chain.json`:
   - public RPC endpoints;
   - public seeds;
   - public persistent peers.
2. POSTHUMAN public Celestia testnet RPC endpoints.
3. Public RPC `/net_info` from known Mocha testnet RPC providers.
4. GeoIP lookup through `http://ip-api.com/batch`.

Private validator IPs, private sentry topology, non-global addresses and local non-Mocha addrbooks must not be published.

Important: local `~/.celestia-app` must only be used if it is explicitly verified to be Celestia Mocha testnet (`chain_id == mocha-4`). Do not mix mainnet, Arabica, Blockspace Race, or any other local addrbook data into this map.

## Manual update

Run from the source-data repository:

```bash
cd /home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data
python3 scripts/update-celestia-testnet-decentralize-map.py
```

Validate the result:

```bash
python3 -m py_compile scripts/update-celestia-testnet-decentralize-map.py
python3 -m json.tool networks.json >/dev/null
python3 -m json.tool celestia-testnet/decentralize-map.json >/dev/null
python3 scripts/update-celestia-testnet-decentralize-map.py --check
```

Optional stricter integrity check:

```bash
python3 -c "import json, ipaddress; data=json.load(open('celestia-testnet/decentralize-map.json')); points=data['points']; ids=[p['id'] for p in points]; assert data['schema']=='posthuman-decentralization-map/v1'; assert data['network_id']=='celestia-testnet-mocha-4'; assert data['chain_id']=='mocha-4'; assert len(ids)==len(set(ids)); assert all(ipaddress.ip_address(p['ip']).is_global for p in points if p.get('ip')); assert all(isinstance(p.get('lat'), (int, float)) and isinstance(p.get('lon'), (int, float)) for p in points); assert any(p.get('type')=='rpc' and 'posthuman.digital' in str(p.get('endpoint')).lower() for p in points); assert any(p.get('type')=='observed_peer' for p in points); assert any(p.get('type')=='bootstrap' for p in points); assert data['summary']['points']==len(points); print(data['summary'])"
```

Commit and push only the intended Celestia testnet map files:

```bash
git add celestia-testnet/decentralize-map.json scripts/update-celestia-testnet-decentralize-map.py celestia-testnet/decentralize-map.md celestia-testnet/decentralize-map-runbook.md scripts/update-celestia-testnet-decentralize-map-and-deploy.sh networks.json
git commit -m "Update Celestia testnet decentralization map"
git push
```

## Manual production rebuild

The UI reads source-data through `CONFIG_REPO`. After pushing source-data, rebuild and restart the production UI if an immediate refresh is required:

```bash
ssh -o BatchMode=yes valoper@65.21.7.184 "cd /srv/data/apps/posthuman-nodes-ui && git pull --ff-only && sudo yarn install --frozen-lockfile && sudo rm -rf .next && sudo yarn build && sudo pm2 restart nodes"
```

Check the live page:

```bash
python3 -c "import urllib.request; url='https://nodes.posthuman.digital/chains/celestia-testnet?tab=decentralize-map'; req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}); html=urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore'); print('has_tab', 'decentralize map' in html.lower()); print('has_points', 'Map points' in html); print('generic_text', 'public endpoint health checks, registry data and observed public peers' in html.lower())"
```

## Automated update

Use:

```bash
/home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data/scripts/update-celestia-testnet-decentralize-map-and-deploy.sh
```

The script:

1. takes a lock to prevent overlapping runs;
2. pulls latest `main`;
3. regenerates `celestia-testnet/decentralize-map.json`;
4. validates Python syntax and JSON;
5. commits only `celestia-testnet/decentralize-map.json` when it changed;
6. pushes to GitHub;
7. installs UI dependencies with the locked Yarn file;
8. rebuilds and restarts production `posthuman-nodes-ui` through SSH.

Cron log path used by the current setup:

```text
/home/ubuntu/celestia-testnet-decentralize-map-update.log
```

Current cron schedule:

```cron
45 6 */3 * * /home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data/scripts/update-celestia-testnet-decentralize-map-and-deploy.sh >> /home/ubuntu/celestia-testnet-decentralize-map-update.log 2>&1
```

This runs at 06:45 UTC every third day of the month.

## Troubleshooting

- If POSTHUMAN RPC returns `403` from Python, keep the custom `User-Agent` in `scripts/update-celestia-testnet-decentralize-map.py`.
- If GeoIP is partially missing, rerun later; `ip-api.com` may rate-limit or temporarily fail.
- If the UI build fails on Tailwind plugins, keep the CJS/ESM plugin resolver in `posthuman-nodes-ui/tailwind.config.ts`.
- If cron pushes fail, check SSH/GitHub auth for the `ubuntu` user.
- If deploy fails, check SSH access to `valoper@65.21.7.184` and `pm2 status nodes` on the production host.
