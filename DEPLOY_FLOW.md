# DEPLOY FLOW — How to Add a New Network to nodes.posthuman.digital

## Stack Overview

- **Data Repository:** https://github.com/Validator-POSTHUMAN/posthuman-source-data
- **Website:** Next.js application
- **Process Manager:** PM2
- **Data Source:** `https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/main`

---

## ⚠️ IMPORTANT RULES

1. **The website reads ONLY `networks.json`** — networks won't appear without an entry there
2. **NEVER use `json.dump` / `python3 json.load+dump`** to edit `networks.json` — it reformats the file and breaks the site. Use `sed -i` or manual editing only
3. **Icons must be SVG** (not PNG, not JPG). The site doesn't render other formats
4. **Non-Cosmos networks** (Espresso, Ethereum, Near, Monad, etc.) — use `"endpoints": {}`, without rpc/rest/grpc/peer
5. **Cosmos networks** — full endpoint set: rpc, rest, grpc, peer, snapshots

---

## Complete Flow: Add a Network

### Step 1 — Create Network Directory

```bash
mkdir posthuman-source-data/<name>/
```

### Step 2 — Add Icon (Circular SVG)

**Option A — Wrap existing SVG in circle:**
```bash
BASE="https://raw.githubusercontent.com/..."  # Original icon URL

cat > <name>/<name>-logo.svg << EOF
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="256" height="256">
  <defs>
    <clipPath id="circle-clip">
      <circle cx="50" cy="50" r="50"/>
    </clipPath>
  </defs>
  <image href="$BASE" x="0" y="0" width="100" height="100" clip-path="url(#circle-clip)"/>
</svg>
EOF
```

**Option B — Convert PNG to circular SVG:**
```bash
# Crop to square, apply circular mask, save as PNG
convert input.jpg \
  -gravity Center -crop MINxMIN+0+0 +repage -resize 256x256 \
  ( +clone -alpha extract \
    -draw "fill black polygon 0,0 0,256 256,256 256,0 fill white circle 128,128 128,0" \
    ( +clone -flip ) -compose Multiply -composite \
    ( +clone -flop ) -compose Multiply -composite \
  ) \
  -alpha off -compose CopyOpacity -composite PNG32:output.png

# Embed PNG in SVG (base64)
B64=$(base64 -w 0 output.png)
echo '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256"><image href="data:image/png;base64,'$B64'" x="0" y="0" width="256" height="256"/></svg>' > <name>/<name>-logo.svg
```

Icon URL format:
```
https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/refs/heads/main/<name>/<name>-logo.svg
```

### Step 3 — Add install-guide.md (If Needed)

File: `<name>/install-guide.md`

Study the project's official documentation and write an installation guide.

### Step 4 — Add Entry to `networks.json`

**Manual editing or sed only!** Insert before the last `]`:

**Template for Cosmos Network:**
```json
  {
    "name": "chainname",
    "type": "mainnet",
    "title": "Chain Title",
    "website": "https://...",
    "twitter": "https://x.com/...",
    "discord": "https://discord.com/invite/...",
    "github": "https://github.com/...",
    "icon": "https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/refs/heads/main/chainname/chainname-logo.svg",
    "stake": "https://explorer.posthuman.digital/chainname/staking/valoperXXXX",
    "explorer": "https://explorer.posthuman.digital/chainname",
    "chain_id": "chain-1",
    "endpoints": {
      "rpc": "https://rpc.chainname.posthuman.digital:443",
      "rest": "https://rest.chainname.posthuman.digital:443",
      "grpc": "https://grpc.chainname.posthuman.digital:443",
      "peer": "NODEID@peer.chainname.posthuman.digital:PORT",
      "snapshots": "https://snapshots.chainname.posthuman.digital:443"
    },
    "contributions": "ChainName",
    "generatedServices": ["installation-guide", "state-sync"],
    "services": ["snapshots"]
  }
```

**Template for Non-Cosmos Network (EVM, L2, Other):**
```json
  {
    "name": "chainname",
    "type": "mainnet",
    "title": "Chain Title",
    "website": "https://...",
    "twitter": "https://x.com/...",
    "discord": "https://discord.com/invite/...",
    "github": "https://github.com/...",
    "icon": "https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/refs/heads/main/chainname/chainname-logo.svg",
    "stake": "",
    "explorer": "",
    "endpoints": {},
    "contributions": "ChainName",
    "generatedServices": ["installation-guide"],
    "services": []
  }
```

**Field `generatedServices`** — auto-generated from templates:
- `installation-guide` — auto-generate installation guide
- `state-sync` — auto-generate state-sync instructions

**Field `services`** — reference static files in network directory:
- `installation-guide` → `<name>/install-guide.md`
- `snapshots`
- `bridge-node-setup`
- `full-node-setup`
- `light-node-setup`
- `one-liner`
- `monitoring`

### Step 5 — Commit and Push

```bash
cd ~/.openclaw/workspace/posthuman-source-data
git add .
git commit -m "feat: add <NetworkName> network"
git push
```

### Step 6 — Deploy Website

Rebuild the Next.js application according to your internal deployment procedures.

The network will appear at: `https://nodes.posthuman.digital/chains/<chainname>`

---

## Quick Reference

```
1. mkdir <name>/               ← directory
2. <name>/<name>-logo.svg      ← circular SVG icon
3. <name>/install-guide.md     ← guide (if needed)
4. networks.json               ← add entry (sed or manual!)
5. git add . && git commit && git push
6. Deploy according to internal procedures
```

---

## Website Infrastructure

| Parameter | Details |
|-----------|---------|
| Framework | Next.js 14.1 |
| Package Manager | yarn |

## Restore from Backup

If the site crashes after rebuild, restore from backup according to your internal recovery procedures.

---

*This is internal documentation for POSTHUMAN validator operations.*
