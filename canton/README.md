# Canton Network Validator Guide

![Canton Logo](https://raw.githubusercontent.com/Validator-POSTHUMAN/posthuman-source-data/refs/heads/main/canton/canton-logo.svg)

## О Canton Network

Canton Network — первая публичная permissionless блокчейн-платформа, созданная специально для институциональных финансов, сочетающая privacy, interoperability и масштабируемость.

**Основные особенности:**
- Privacy-preserving архитектура
- Atomic cross-domain transactions
- BFT consensus
- Institutional-grade security

**Участники:**
Goldman Sachs, Deutsche Börse, BNP Paribas, Microsoft, Moody's, S&P Global, Digital Asset и другие институциональные игроки.

## Инвестиции

Проект получил косвенные инвестиции ~$400M от Tier-1 фондов.

## Сети

| Сеть | Назначение | Version | Migration ID |
|------|------------|---------|--------------|
| **DevNet** | Тестирование, свободный доступ | 0.5.3 | 1 |
| **TestNet** | Pre-production тестирование | 0.4.22 | 0 |
| **MainNet** | Production сеть | 0.4.25 | 0 |

## Требования

### Hardware

| Компонент | Минимум | Рекомендовано |
|-----------|---------|---------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 250 GB NVMe |
| Network | 100 Mbps | 1 Gbps |

### Software

- Docker 20.10+
- Docker Compose 2.0+
- jq
- grpcurl (опционально)

## Подготовка

### 1. Заполнить форму валидатора

**DevNet** - IP автоматически добавляется в whitelist после онбординга
**TestNet/MainNet** - требуется approval от Tokenomics Committee (~2 недели)

Форма: https://sync.global/validator-request/

⚠️ **Важно:** Используйте корпоративную email (не бесплатную типа Gmail)

### 2. IP Whitelist

Каждая сеть требует отдельный уникальный IP:
- DevNet IP → один сервер
- TestNet IP → другой сервер  
- MainNet IP → третий сервер

Подать IP для whitelist:
1. Написать SV sponsor в Slack
2. Подождать 2-7 дней (2/3 Super Validators должны добавить)

### 3. Проверить IP whitelist

**DevNet:**
```bash
bash -c 'CURL="curl -fsS -m 5 --connect-timeout 5"
for url in $($CURL https://scan.sv-1.dev.global.canton.network.sync.global/api/scan/v0/scans | jq -r ".scans[].scans[].publicUrl"); do
  echo -n "$url: "
  $CURL "$url"/api/scan/version | jq -r ".version" 2>&1 || echo "TIMEOUT"
done'
```

**MainNet:**
```bash
bash -c 'CURL="curl -fsS -m 5 --connect-timeout 5"
for url in $($CURL https://scan.sv-1.global.canton.network.sync.global/api/scan/v0/scans | jq -r ".scans[].scans[].publicUrl"); do
  echo -n "$url: "
  $CURL "$url"/api/scan/version | jq -r ".version" 2>&1 || echo "TIMEOUT"
done'
```

Если все SV отвечают версией (не TIMEOUT) - IP whitelisted ✅

## Установка (DevNet)

### One-liner установка

```bash
# Установка зависимостей
sudo apt update && sudo apt install -y curl jq docker.io docker-compose

# Проверить текущую версию сети
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.'

# Создать директорию
VERSION="0.5.3"
MIGRATION_ID="1"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

# Скачать релиз
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator

# Получить onboarding secret (живет 1 час)
SECRET=$(curl -X POST https://sv.sv-1.dev.global.canton.network.sync.global/api/sv/v0/devnet/onboard/validator/prepare)

# Запустить validator
export IMAGE_TAG=${VERSION}
./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "${SECRET}" \
  -p "YOUR_VALIDATOR_NAME" \
  -m "${MIGRATION_ID}" \
  -w
```

### Пошаговая установка

#### 1. Подготовка системы

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка зависимостей
apt install -y curl iptables build-essential git wget jq make gcc \
  nano tmux htop pkg-config libssl-dev tar clang ncdu unzip

# Установка Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt update && apt install -y docker-ce
docker --version

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Установка grpcurl (опционально)
snap install grpcurl
```

#### 2. Проверка сети

```bash
# Узнать текущую версию и migration ID
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.'

# Результат:
# {
#   "network": "devnet",
#   "sv": {
#     "migration_id": 1,
#     "version": "0.5.3"
#   },
#   "synchronizer": {
#     "active": {
#       "migration_id": 1,
#       "version": "0.5.3"
#     }
#   }
# }
```

#### 3. Скачивание Canton Node

```bash
# Создать директорию (используйте актуальную версию)
VERSION="0.5.3"
mkdir -p ~/.canton/${VERSION}
cd ~/.canton/${VERSION}

# Скачать релиз
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${VERSION}/${VERSION}_splice-node.tar.gz

# Распаковать
tar xzf ${VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator
```

#### 4. Получение Onboarding Secret

**DevNet** (автоматически через API, действует 1 час):
```bash
curl -X POST https://sv.sv-1.dev.global.canton.network.sync.global/api/sv/v0/devnet/onboard/validator/prepare
```

**MainNet** (запросить у SV sponsor в Slack, действует 48 часов)

#### 5. Запуск Validator

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator

export IMAGE_TAG=0.5.3

./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "YOUR_ONBOARDING_SECRET" \
  -p "POSTHUMAN" \
  -m "1" \
  -w
```

Где:
- `-s` - Sponsor SV URL
- `-o` - Onboarding secret (после первого запуска ставим `""`)
- `-p` - Party hint (название валидатора)
- `-m` - Migration ID (смотреть на https://sync.global/sv-network/)
- `-w` - Enable wallet

#### 6. Проверка статуса

```bash
# Статус контейнеров
docker ps --filter "name=splice-validator"

# Логи
docker logs splice-validator-validator-1 -f --tail 100

# Проверка healthy status
docker ps --filter "name=splice-validator-validator" --format "{{.Names}}: {{.Status}}"

# Должно быть: Up X minutes (healthy)
```

## Управление

### Остановка

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator
./stop.sh
```

### Перезапуск

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator
export IMAGE_TAG=0.5.3

# После первого запуска onboarding secret не нужен
./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "" \
  -p "POSTHUMAN" \
  -m "1" \
  -w
```

### Просмотр логов

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator

# Все контейнеры
docker compose logs -f

# Только validator
docker compose logs -f validator

# Последние 100 строк
docker logs splice-validator-validator-1 --tail 100
```

## Обновление

⚠️ **Важно:** Всегда делать backup перед обновлением!

### Процесс обновления

```bash
# 1. Узнать новую версию
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.sv.version'

# 2. Остановить текущую ноду
cd ~/.canton/0.5.3/splice-node/docker-compose/validator
./stop.sh

# 3. Сделать backup (опционально но рекомендуется)
docker run --rm -v splice-validator_postgres-splice:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data

# 4. Создать директорию для новой версии
NEW_VERSION="0.5.4"  # пример
mkdir -p ~/.canton/${NEW_VERSION}
cd ~/.canton/${NEW_VERSION}

# 5. Скачать новый релиз
wget https://github.com/digital-asset/decentralized-canton-sync/releases/download/v${NEW_VERSION}/${NEW_VERSION}_splice-node.tar.gz
tar xzf ${NEW_VERSION}_splice-node.tar.gz
cd splice-node/docker-compose/validator

# 6. Запустить с новой версией
export IMAGE_TAG=${NEW_VERSION}
./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "" \
  -p "POSTHUMAN" \
  -m "1" \
  -w

# 7. Проверить логи
docker compose logs -f validator
```

### Major Upgrade (с изменением Migration ID)

При major upgrade требуется флаг `-M` и новый migration_id:

```bash
# 1. Проверить новый migration_id
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.synchronizer.active.migration_id'

# 2. Обновление
cd ~/.canton/NEW_VERSION/splice-node/docker-compose/validator
export IMAGE_TAG=NEW_VERSION

# ПЕРВЫЙ запуск после major upgrade - с флагом -M
./start.sh \
  -s "https://sv.sv-1.dev.global.canton.network.sync.global" \
  -o "" \
  -p "POSTHUMAN" \
  -m "2" \
  -M \
  -w

# 3. При последующих перезапусках флаг -M убрать
./start.sh -s "https://sv.sv-1.dev.global.canton.network.sync.global" -o "" -p "POSTHUMAN" -m "2" -w
```

## Backup & Recovery

### Backup Identity

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator

# Получить токен
TOKEN=$(python3 get-token.py administrator)

# Создать backup
curl --fail -sS "http://localhost:5003/api/validator/v0/admin/participant/identities" \
  -H "authorization: Bearer ${TOKEN}" \
  -o ~/canton_identity_backup_$(date +%Y%m%d).json
```

### Backup Database

```bash
# Создать dump PostgreSQL
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator \
  > ~/canton_db_backup_$(date +%Y%m%d).sql

# Или весь volume
docker run --rm -v splice-validator_postgres-splice:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

### Автоматический backup (cron)

```bash
cat > /root/canton_backup.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="/root/canton_backups"
mkdir -p ${BACKUP_DIR}
DATE=$(date +%Y%m%d_%H%M%S)

# DB backup
docker exec splice-validator-postgres-splice-1 pg_dump -U cnadmin validator \
  > ${BACKUP_DIR}/canton_db_${DATE}.sql

# Удалить старые (>7 дней)
find ${BACKUP_DIR} -name "canton_db_*.sql" -mtime +7 -delete
SCRIPT

chmod +x /root/canton_backup.sh

# Добавить в cron (каждые 4 часа)
(crontab -l; echo "0 */4 * * * /root/canton_backup.sh") | crontab -
```

## Мониторинг

### Prometheus метрики

Canton экспортирует метрики на порту **10013** (Prometheus format)

```bash
# Проверить доступность метрик
docker exec splice-validator-validator-1 curl -s http://localhost:10013/metrics | head -20
```

### Telegram алерты

Простой мониторинг с уведомлениями в Telegram:

```bash
cat > /root/check_canton.sh << 'SCRIPT'
#!/bin/bash
BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"

if ! docker ps --format '{{.Names}} {{.Status}}' | grep -q 'splice-validator-validator.*healthy'; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d text="🔴 Canton Validator DOWN - $(hostname)"
fi
SCRIPT

chmod +x /root/check_canton.sh

# Добавить в cron (каждые 10 минут)
(crontab -l; echo "*/10 * * * * /root/check_canton.sh") | crontab -
```

## Безопасность

### Закрыть публичные порты

По умолчанию wallet UI доступен публично. Для безопасности:

**Вариант 1:** Изменить порт на localhost-only

```bash
cd ~/.canton/0.5.3/splice-node/docker-compose/validator
nano compose.yaml

# Найти и изменить
ports:
  - "127.0.0.1:8080:80"  # вместо "80:80"
```

**Вариант 2:** Доступ через SSH tunnel

```bash
# С локальной машины
ssh -L 8080:127.0.0.1:8080 user@validator_ip -N

# Затем открыть в браузере
http://localhost:8080
```

## Полезные ссылки

- **Официальная документация:** https://docs.dev.sync.global/
- **Validator форма:** https://sync.global/validator-request/
- **SV Network Status:** https://sync.global/sv-network/
- **Canton Foundation:** https://canton.foundation/
- **GitHub:** https://github.com/digital-asset/decentralized-canton-sync
- **WhitePaper:** https://www.canton.network/whitepaper
- **DevNet Explorer:** https://lighthouse.devnet.cantonloop.com/
- **MainNet Explorer:** https://lighthouse.cantonloop.com/

## Troubleshooting

### Container постоянно перезапускается

```bash
# Проверить логи
docker logs splice-validator-validator-1 --tail 100

# Частые проблемы:
# 1. Неправильный migration_id
# 2. Onboarding secret expired (для первого запуска)
# 3. IP не в whitelist
```

### "Unknown secret" error

```bash
# Получить новый secret для DevNet
curl -X POST https://sv.sv-1.dev.global.canton.network.sync.global/api/sv/v0/devnet/onboard/validator/prepare

# Для MainNet - запросить у SV sponsor
```

### Проблемы с портом 80

```bash
# Проверить что занимает порт
sudo lsof -i :80

# Изменить на другой порт (например 8080) в compose.yaml
```

### Очистка и переустановка

```bash
# Остановить
cd ~/.canton/0.5.3/splice-node/docker-compose/validator
./stop.sh

# Удалить volumes (⚠️ удалит все данные!)
docker volume rm splice-validator_postgres-splice splice-validator_domain-upgrade-dump

# Запустить заново с новым onboarding secret
```

## Статус сети

Проверить текущее состояние сетей:

```bash
# DevNet
curl -s https://docs.dev.global.canton.network.sync.global/info | jq '.'

# TestNet  
curl -s https://docs.test.global.canton.network.sync.global/info | jq '.'

# MainNet
curl -s https://docs.global.canton.network.sync.global/info | jq '.'
```

## Награды

Валидаторы получают Canton Coin (CC) за:
- Liveness (активность ноды)
- Traffic generation
- Featured app participation

Проверить баланс можно в wallet UI: http://localhost:8080

---

**Создано POSTHUMAN validators**

Наш сайт: https://posthuman.digital
