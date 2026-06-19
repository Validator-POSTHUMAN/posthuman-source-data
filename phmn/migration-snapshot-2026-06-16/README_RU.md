# Финальный пакет PHMN для публичного ревью

Эта папка содержит текущий публичный review package для миграции PHMN на новый токен.

English version: [README.md](README.md)

Этот пакет заменяет предыдущий audit-only snapshot package. Здесь намеренно оставлены только финальные файлы, которые нужны для проверки перед созданием нового denom и финальным broadcast.

## Текущий статус

- Версия: `v2_olim_excluded`
- Исходный snapshot package: `phmn/migration-snapshot-2026-06-16`
- Базовый commit source-data, из которого собран candidate: `95941d5`
- Denom нового PHMN: `DENOM_TBD`
- Общий supply нового PHMN: `131,072.000000 PHMN`
- Recipient rows: `23,456`
- Decimals: `6`

`DENOM_TBD` оставлен специально на время публичного ревью. После создания нового TokenFactory denom колонка `denom` должна быть заменена на реальный denom, checksums должны быть пересчитаны, и только этот финальный CSV с реальным denom должен использоваться для broadcast.

## Файлы

- `phmn_final_distribution_broadcast_candidate.csv` - broadcast-shaped distribution candidate с колонками `recipient_address,amount_micro,amount_phmn,denom`.
- `phmn_final_distribution_broadcast_candidate_breakdown.csv` - человекочитаемая таблица для публичного ревью только с колонками `recipient_address,amount_phmn`. Суммы показаны в PHMN с 6 знаками после точки, без micro units и без denom placeholders.
- `phmn_old_addresses_not_receiving_new_phmn.csv` - old PHMN source addresses или accounting rows, которые не получают новый PHMN на старый адрес, с причиной и destination/handling.
- `PHMN_MIGRATION_FINAL_RULES.md` - финальные правила миграции, по которым собран candidate.
- `summary.json` - machine-readable summary по totals и applied rules.
- `SHA256SUMS` - checksums для проверки package.

## Что проверять сообществу

Просим проверить:

1. Корректность recipient addresses.
2. Корректность amounts.
3. Excluded incident и Olim-linked rows.
4. Reroute старых treasury/SubDAO/core-team балансов в новые SubDAO treasuries.
5. Handling unresolved Osmosis accounting gap.
6. Очевидные дубликаты или пропущенные адреса.

Переводы старого PHMN после финального snapshot не меняют этот candidate.

## Главные totals

- Total distribution candidate: `131,072.000000 PHMN`
- Olim override routed to Strategic SubDAO: `300.009116 PHMN`
- Strategic SubDAO recipient: `cosmos146s5j3t7gh2g37ywm47dp8avhesu2htvjjaxq7z55e7xj0rq0k8q5qnjjy`

## Проверка

Из этой папки:

```bash
sha256sum -c SHA256SUMS
```

Ожидаемый результат: каждый файл должен вернуть `OK`.

## Важно перед broadcast

Этот package ещё не является финальным broadcast package, потому что в CSV стоит `DENOM_TBD`.

После community review:

1. Создаётся новый PHMN TokenFactory denom.
2. `DENOM_TBD` заменяется на реальный denom.
3. `SHA256SUMS` пересчитывается.
4. Публикуется final broadcast package.
5. Для реального distribution используется только CSV с реальным denom.
