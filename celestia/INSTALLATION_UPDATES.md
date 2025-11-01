# Celestia Installation Guide Updates

## Что изменилось

### ✅ Убрана автогенерация network.json
- Файл `installation-guide.md` теперь в `services` (не в `generatedServices`)
- Guide создается и поддерживается вручную для точности

### ✅ Прямые ссылки на Posthuman infrastructure
Вместо placeholder'ов `<genesis_url>` и `<addrbook_url>` теперь используются конкретные URL:

**Mainnet:**
- Genesis: https://snapshots.posthuman.digital/celestia-mainnet/genesis.json
- Addrbook: https://snapshots.posthuman.digital/celestia-mainnet/addrbook.json
- Snapshot: https://snapshots.posthuman.digital/celestia-mainnet/snapshot-latest.tar.zst

**Testnet (Mocha-4):**
- Genesis: https://snapshots.posthuman.digital/celestia-testnet/genesis.json
- Addrbook: https://snapshots.posthuman.digital/celestia-testnet/addrbook.json
- Snapshot: https://snapshots.posthuman.digital/celestia-testnet/snapshot-latest.tar.zst

### ✅ Улучшенная структура

#### Mainnet (`celestia/installation-guide.md`)
- **Версия**: v5.0.11
- **Chain ID**: celestia
- Детальные секции с нумерацией
- Включены: pruning, indexer, prometheus настройки
- Добавлен блок Troubleshooting с workaround для REST API
- Секция Security и best practices
- Полезные команды для мониторинга
- Правильное использование `mv` вместо tar.gz backup

#### Testnet (`celestia-testnet/installation-guide.md`)
- **Версия**: v6.2.0-mocha
- **Chain ID**: mocha-4
- Отдельный systemd service (`celestia-appd-testnet`)
- Инструкции для получения testnet токенов (faucet)
- Адаптировано под testnet требования

### ✅ Технологично и эффективно

1. **Snapshot integration** — инструкции для быстрой синхронизации
2. **Service management** — systemd с автозапуском
3. **Конфигурация** — оптимальные настройки (pruning, gas price, peers)
4. **Fallback решения** — gRPC вместо REST при проблемах
5. **Мониторинг** — prometheus metrics enabled
6. **Безопасность** — firewall, SSH, backup рекомендации

## Сравнение с ITRocket

| Параметр | ITRocket | Posthuman (Updated) |
|----------|----------|---------------------|
| Genesis/Addrbook | ITRocket servers | **Posthuman snapshots** |
| Snapshot source | ITRocket | **Posthuman snapshots** |
| Структура | Компактная | **Детальная с секциями** |
| Troubleshooting | Нет | **Есть (REST/gRPC)** |
| Testnet guide | Нет отдельного | **Отдельный файл** |
| Security section | Firewall only | **Расширенная** |
| Auto-install | Да (скрипт) | Ручной (контроль) |

## Проверка

```bash
# Mainnet
cat ~/posthuman-source-data/celestia/installation-guide.md | grep "snapshots.posthuman.digital"

# Testnet
cat ~/posthuman-source-data/celestia-testnet/installation-guide.md | grep "snapshots.posthuman.digital"

# networks.json
jq '.[] | select(.name | startswith("celestia")) | {name, services, generatedServices}' \
  ~/posthuman-source-data/networks.json
```

## Использование

### Для пользователей
Просто следуйте шагам в соответствующем guide:
- Mainnet: `celestia/installation-guide.md`
- Testnet: `celestia-testnet/installation-guide.md`

### Для разработчиков
При обновлении версий:
1. Обновите `VERSION=` в шаге 3
2. Обновите footer "Last Updated"
3. Проверьте актуальность ссылок на snapshots
4. Commit изменения в git

## Git commit

```bash
cd ~/posthuman-source-data
git add celestia/installation-guide.md
git add celestia-testnet/installation-guide.md
git add networks.json
git commit -m "feat(celestia): update installation guides with Posthuman snapshots

- Replace auto-generated guides with manual detailed versions
- Add direct links to snapshots.posthuman.digital for genesis/addrbook
- Create separate testnet installation guide
- Add troubleshooting section with REST API fallback to gRPC
- Improve structure with numbered sections and best practices
- Update networks.json to move installation-guide from generatedServices to services"
```

---

**Готово!** 🚀

Гайды теперь:
- ✅ Используют Posthuman infrastructure
- ✅ Детальные и понятные
- ✅ Технологичные (snapshots, systemd, monitoring)
- ✅ С troubleshooting и security
- ✅ Без лишнего (focused на установку)
