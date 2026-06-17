# Чеклист восстановления PHMN

Обновлено: 2026-06-18

Этот чеклист показывает, что уже сделано для миграции старого PHMN в новый
PHMN, и что ещё нужно выполнить перед созданием нового TokenFactory-токена на
Cosmos Hub и его распределением.

Основным источником данных остаются CSV/JSON-файлы в этой директории. Этот
чеклист является трекером прогресса, а не заменой snapshot-файлов или
миграционной политики.

## Текущая цель

Восстановить PHMN следующим порядком:

1. Создать новый PHMN TokenFactory-токен на Cosmos Hub.
2. Распределить новый PHMN согласно финальному снапшоту старого PHMN и
   опубликованным правилам миграции.
3. Создать новый POSTHUMAN DAS под управлением нового PHMN.
4. Открыть недельное окно для лока токенов держателями.
5. Добавить ликвидность поэтапно только после окончания lock window.
6. Использовать часть средств Liquidity SubDAO для выкупа PHMN из новых пулов
   после восстановления ликвидности.

## Уже сделано

- [x] Подтверждён компромисс minter-адреса старого Juno CW20 PHMN и
      неавторизованный mint.
- [x] Собраны и опубликованы evidence по incident-related адресам для
      подтверждённого кластера attacker/minter.
- [x] Создан финальный ownership snapshot по Juno, Osmosis, Neutron и BeeZee.
- [x] Исправлено двойное IBC escrow accounting: bridged PHMN считается на
      финальной holder-chain, а не одновременно на Juno и destination chain.
- [x] Опубликован `phmn_address_lookup.csv` / `.json`, чтобы держатели могли
      искать старые source addresses и видеть snapshot amount и distribution
      status.
- [x] Опубликован `phmn_final_snapshot_expanded_rows.csv` / `.json` для
      source-level accounting.
- [x] Опубликован `phmn_final_snapshot_user_attribution.csv` / `.json` для
      grouped holder attribution по normalized Cosmos address.
- [x] Старый POSTHUMAN DAS staking contract row разложен на per-user active
      stake и pending-claim rows.
- [x] Определены и опубликованы SubDAO treasury reroute rules для нового
      Strategic SubDAO и Liquidity SubDAO.
- [x] Применена Osmosis gap correction от 2026-06-17 для
      `osmo1z0e05ptv5hpfh4lp54373t86zxquv3y5vkfm5p`.
- [x] Добавлен Osmosis pool liquidity audit, показывающий PHMN на Osmosis
      pool accounts.
- [x] Опубликованы distribution status totals в
      `distribution_status_summary.csv` / `.json`.
- [x] Опубликованы SHA-256 checksums для файлов пакета.

## Текущее состояние публичного снапшота

- Corrected old PHMN snapshot total: `121,822.000000 PHMN`.
- New PHMN maximum supply target: `131,072.000000 PHMN`.
- Разница до cap/reserve, которая должна контролироваться новым Strategic
  SubDAO: `9,250.000000 PHMN`, до применения дополнительных quarantine или
  excluded-balance routing policies.
- `phmn_address_lookup.csv`: source-level lookup rows для публичного поиска
  адресов.
- `phmn_final_snapshot_user_attribution.csv`: grouped holder attribution rows
  по normalized Cosmos address.
- Current package row counts: `phmn_address_lookup.csv` содержит `26,030`
  source-level data rows, а `phmn_final_snapshot_user_attribution.csv`
  содержит `23,476` grouped holder rows.
- Остаточный unresolved Osmosis accounting gap после correction:
  `57.230100 PHMN`.
- DAS unattributed residual: `0.010001 PHMN`.
- Osmosis pool-account PHMN audit total: `65.821395 PHMN`.

## Уже принятые решения

- [x] Переводы старого PHMN после публикации финального снапшота не влияют на
      распределение нового PHMN.
- [x] Старые SubDAO treasury balances reroute-ятся в новые SubDAO treasuries,
      а не отправляются обратно на старые treasury addresses.
- [x] PHMN, принадлежащий LP providers, которых пока нельзя точно раскрыть до
      individual LP share holders, временно отправляется в Strategic SubDAO
      bucket до разрешения LP holders.
- [x] Остаточный Osmosis unresolved accounting gap отправляется в quarantine /
      Strategic SubDAO bucket.
- [x] DAS unattributed residual отправляется в новый Strategic SubDAO.
- [x] Confirmed attacker/minter/excluded rows не распределяются на старые
      source addresses. Они обрабатываются через DAO-controlled policy buckets.
- [x] Порядок восстановления: создать новый PHMN, распределить по финальному
      снапшоту, создать новый DAS, открыть недельный lock window, затем
      восстановить ликвидность поэтапно.

## Что осталось до создания токена и распределения

- [ ] Сгенерировать final distribution CSV из публичного snapshot package.
      Это должен быть broadcast-ready файл, а не audit-only файл.
- [ ] Применить все destination overrides в final CSV: SubDAO reroutes, LP
      temporary bucket, Osmosis unresolved gap bucket, DAS residual bucket,
      attacker/minter exclusions и другие quarantine rows.
- [ ] Проверить, что final distribution CSV сходится ровно в
      `131,072.000000 PHMN` с micro-PHMN precision.
- [ ] Опубликовать понятную status summary: сколько нового PHMN уходит normal
      eligible holders, Liquidity SubDAO, Strategic SubDAO reserve, temporary
      LP bucket, unresolved/quarantine buckets и excluded incident buckets.
- [ ] Построить transaction/address evidence graph для incident-related
      addresses и опубликовать graph source data.
- [ ] Проверить graph на false-positive links до использования его для
      exclusion decisions.
- [ ] Проверить live параметры Cosmos Hub TokenFactory перед broadcast:
      denom creation fee, denom format and length, metadata support, gas
      requirements, creator/admin controls и mint authority controls.
- [ ] Принять и задокументировать точную модель mint/admin authority:
      DAO/multisig control или другую enforceable no-extra-mint policy.
- [ ] Сгенерировать distribution transactions из final CSV в dry-run или
      generate-only mode.
- [ ] Проверить batch size, gas, fees и total outputs до подписи.
- [ ] Broadcast distribution transactions.
- [ ] Сохранить transaction hashes и опубликовать post-distribution
      reconciliation.

## Правила проверки evidence graph

Evidence graph должен отделять сильные evidence от обычной on-chain
активности. Сам факт связи не является достаточным доказательством.

Не считать автоматическими attacker links:

- shared DEX или swap contracts, которыми пользуются многие пользователи;
- liquidity pool contracts или pool module addresses;
- IBC escrow addresses;
- router contracts;
- SubDAO treasury payments;
- обычные PHMN transfers между известными community, team или operator
  addresses;
- interactions, которые доказывают только использование общего контракта.

Каждый graph edge должен быть классифицирован по типу:

- direct PHMN transfer;
- direct gas funding transfer;
- swap / DEX interaction;
- IBC transfer;
- bridge / CCTP transfer;
- contract call through a shared contract;
- SubDAO treasury transfer;
- known benign operator or community interaction;
- unresolved weak link.

Operator-provided benign-context addresses должны использоваться как controls
при проверке graph. Один известный high-activity PHMN sender address:

- `juno1e8238v24qccht9mqc2w0r4luq462yxttdl93mj`

То, что этот адрес взаимодействовал с Olim или другими PHMN users, само по
себе не должно считаться attacker evidence.

## После распределения

- [ ] Создать новый POSTHUMAN DAS под управлением нового PHMN.
- [ ] Объявить новый DAS и недельный PHMN lock window.
- [ ] Команда лочит свой новый PHMN в новом POSTHUMAN DAS во время lock
      window.
- [ ] Подождать одну неделю, чтобы другие держатели тоже могли залочить PHMN.
- [ ] После окончания lock window добавить новую PHMN liquidity поэтапно.
- [ ] Использовать часть средств Liquidity SubDAO для buybacks из новых PHMN
      liquidity pools.
- [ ] Опубликовать финальные liquidity и buyback transaction references.

## Публичные файлы для проверки

- `README.md`
- `PHMN_MIGRATION_FINAL_SNAPSHOT_POLICY.md`
- `phmn_address_lookup.csv`
- `phmn_final_snapshot_user_attribution.csv`
- `phmn_final_snapshot_expanded_rows.csv`
- `subdao_reroute_adjustments.csv`
- `distribution_status_summary.csv`
- `osmosis_phmn_pool_liquidity_audit.csv`
- `SHA256SUMS`
