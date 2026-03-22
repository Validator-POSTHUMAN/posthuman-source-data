# DEPLOY FLOW — Как добавить новую сеть на posthuman.digital

## Обзор стека

- **Репо с данными:** https://github.com/Validator-POSTHUMAN/posthuman-source-data
- **Сайт (Next.js):** `valoper@65.21.7.184` → `/srv/data/apps/posthuman-source-2`
- **Process manager:** PM2, процесс называется `nodes`
- **Рабочая копия данных:** `~/.openclaw/workspace/posthuman-source-data/`

---

## Полный флоу: добавить сеть

### ⚠️ ВАЖНО: Сайт читает ТОЛЬКО `networks.json`
Файл `<name>/<name>.json` — вспомогательный, на сайте не отображается.
Чтобы сеть появилась на nodes.posthuman.digital — **обязательно** добавить запись в `networks.json`.

### Шаг 1 — Добавить запись в `networks.json`

Файл: `networks.json` в корне репо.

**Минимальная структура:**
```json
{
  "name": "espresso",
  "type": "mainnet",
  "title": "Espresso",
  "website": "https://espresso.network/",
  "twitter": "https://x.com/EspressoNetwork",
  "discord": "https://discord.gg/espresso",
  "github": "https://github.com/EspressoSystems",
  "icon": "https://...",
  "stake": "",
  "explorer": "",
  "chain_id": "espresso-mainnet",
  "endpoints": {
    "rpc": "https://rpc.espresso.network",
    "rest": "https://rest.espresso.network",
    "grpc": "https://grpc.espresso.network",
    "peer": "",
    "snapshots": ""
  },
  "contributions": "Espresso",
  "generatedServices": ["installation-guide", "state-sync"],
  "services": ["snapshots"]
}
```

**Поля `generatedServices`** — генерируются автоматически из шаблонов:
- `installation-guide`
- `state-sync`

**Поля `services`** — статичные файлы из директории сети:
- `installation-guide` — `<name>/install-guide.md`
- `snapshots`
- `bridge-node-setup`
- `full-node-setup`
- `light-node-setup`
- `one-liner`

---

### Шаг 2 — Создать директорию сети

```bash
mkdir posthuman-source-data/<name>/
```

Добавить файлы по необходимости:
- `install-guide.md` — гайд по установке (если `services` содержит `installation-guide`)
- `<name>.json` — дополнительные данные по сети (опционально)
- иконка `.svg` или `.png` (если не используется внешний URL)

---

### Шаг 3 — Закоммитить и запушить

```bash
cd ~/.openclaw/workspace/posthuman-source-data
git add .
git commit -m "feat: add <NetworkName> network"
git push
```

**Credentials:** настроены через `~/.git-credentials` (user: `web3validator`)

---

### Шаг 4 — Обновить сайт

SSH на сервер и пересобрать Next.js:

```bash
ssh valoper@65.21.7.184 "cd /srv/data/apps/posthuman-source-2 && sudo rm -rf .next/ && sudo yarn build && pm2 restart nodes"
```

Или с задержкой (если репо только что запушено и нужно время на синхронизацию):

```bash
ssh valoper@65.21.7.184 "sleep 20 && cd /srv/data/apps/posthuman-source-2 && sudo rm -rf .next/ && sudo yarn build && pm2 restart nodes"
```

**Что делает каждая команда:**
- `rm -rf .next/` — удаляет кеш сборки
- `yarn build` — пересобирает Next.js с новыми данными
- `pm2 restart nodes` — перезапускает процесс сайта

---

## Быстрая памятка

```
1. networks.json  ← добавить запись
2. <name>/        ← создать директорию + файлы
3. git commit + push
4. ssh rebuild    ← rm .next + yarn build + pm2 restart nodes
```

---

## Сервер сайта

| Параметр | Значение |
|----------|----------|
| Host | `valoper@65.21.7.184` |
| App dir | `/srv/data/apps/posthuman-source-2` |
| PM2 process | `nodes` |
| Framework | Next.js |
| Package manager | yarn |
