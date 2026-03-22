# DEPLOY FLOW — Как добавить новую сеть на nodes.posthuman.digital

## Обзор стека

- **Репо с данными:** https://github.com/Validator-POSTHUMAN/posthuman-source-data
- **Сайт (Next.js):** `valoper@65.21.7.184` → `/srv/data/apps/posthuman-source-2`
- **Process manager:** PM2, процесс называется `nodes`
- **Локальная рабочая копия:** `~/.openclaw/workspace/posthuman-source-data/`
- **Данные читаются с:** `https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/main`

---

## ⚠️ ВАЖНЫЕ ПРАВИЛА

1. **Сайт читает ТОЛЬКО `networks.json`** — без записи там сеть не появится
2. **НИКОГДА не использовать `json.dump` / `python3 json.load+dump`** для редактирования `networks.json` — это переформатирует файл и ломает сайт. Только `sed -i` или ручное редактирование
3. **Иконки — только SVG** (не PNG, не JPG). Сайт не рендерит другие форматы
4. **Не-Cosmos сети** (Espresso, Ethereum, Near, Monad и т.д.) — `"endpoints": {}`, без rpc/rest/grpc/peer
5. **Cosmos сети** — полный набор endpoints: rpc, rest, grpc, peer, snapshots

---

## Полный флоу: добавить сеть

### Шаг 1 — Создать директорию сети

```bash
mkdir posthuman-source-data/<name>/
```

### Шаг 2 — Добавить иконку (круглую SVG)

**Вариант A — обернуть существующую SVG в круг:**
```bash
BASE="https://raw.githubusercontent.com/..."  # URL оригинальной иконки

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

**Вариант B — получена PNG из чата, конвертировать:**
```bash
# Обрезать до квадрата, сделать круглой маской, сохранить PNG
convert input.jpg \
  -gravity Center -crop MINxMIN+0+0 +repage -resize 256x256 \
  ( +clone -alpha extract \
    -draw "fill black polygon 0,0 0,256 256,256 256,0 fill white circle 128,128 128,0" \
    ( +clone -flip ) -compose Multiply -composite \
    ( +clone -flop ) -compose Multiply -composite \
  ) \
  -alpha off -compose CopyOpacity -composite PNG32:output.png

# Обернуть PNG в SVG (embed base64)
B64=$(base64 -w 0 output.png)
echo '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256"><image href="data:image/png;base64,'$B64'" x="0" y="0" width="256" height="256"/></svg>' > <name>/<name>-logo.svg
```

Ссылка на иконку:
```
https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/refs/heads/main/<name>/<name>-logo.svg
```

### Шаг 3 — Добавить install-guide.md (если нужен)

Файл: `<name>/install-guide.md`

Изучить официальную документацию проекта и написать гайд по установке.

### Шаг 4 — Добавить запись в `networks.json`

**Только через ручное редактирование или sed!** Вставить перед последним `]`:

**Шаблон для Cosmos сети:**
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

**Шаблон для не-Cosmos сети (EVM, L2, другие):**
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

**Поля `generatedServices`** — генерируются автоматически из шаблонов:
- `installation-guide` — автогенерация гайда
- `state-sync` — автогенерация state-sync инструкций

**Поля `services`** — ссылаются на статичные файлы в директории сети:
- `installation-guide` → `<name>/install-guide.md`
- `snapshots`
- `bridge-node-setup`
- `full-node-setup`
- `light-node-setup`
- `one-liner`
- `monitoring`

### Шаг 5 — Закоммитить и запушить

```bash
cd ~/.openclaw/workspace/posthuman-source-data
git add .
git commit -m "feat: add <NetworkName> network"
git push
```

**Credentials:** настроены через `~/.git-credentials` (user: `web3validator`)

### Шаг 6 — Деплой сайта

```bash
ssh valoper@65.21.7.184 "cd /srv/data/apps/posthuman-source-2 && sudo rm -rf .next/ && sudo yarn build && pm2 restart nodes"
```

**Что делает каждая команда:**
- `rm -rf .next/` — удаляет кеш сборки
- `yarn build` — пересобирает Next.js (занимает ~45-50 сек)
- `pm2 restart nodes` — перезапускает процесс сайта

---

## Быстрая памятка

```
1. mkdir <name>/               ← директория
2. <name>/<name>-logo.svg      ← круглая SVG иконка
3. <name>/install-guide.md     ← гайд (если нужен)
4. networks.json               ← добавить запись (sed или вручную!)
5. git add . && git commit && git push
6. ssh rebuild (rm .next + yarn build + pm2 restart nodes)
```

---

## Сервер сайта

| Параметр | Значение |
|----------|----------|
| Host | `valoper@65.21.7.184` |
| App dir | `/srv/data/apps/posthuman-source-2` |
| PM2 process | `nodes` |
| Framework | Next.js 14.1 |
| Package manager | yarn |
| Backup build | `backup.next/` (используй если сайт упал) |

## Восстановление из бэкапа

Если сайт упал после rebuild:
```bash
ssh valoper@65.21.7.184 "cd /srv/data/apps/posthuman-source-2 && sudo rm -rf .next && sudo cp -r backup.next .next && pm2 restart nodes"
```
