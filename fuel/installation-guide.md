Запустить узел
Получить двоичный файл и генезис из этого репозитория:

Двоичный файл из:
https://github.com/FuelLabs/fuel-sequencer-deployments/releases/tag/seq-mainnet-1.3.2
Значок ссылки

fuelsequencerd-seq-mainnet-1.3.2-darwin-amd64для Linux x64
Генезис из:
https://github.com/FuelLabs/fuel-sequencer-deployments/blob/main/seq-mainnet-1/genesis.json
Значок ссылки
Загрузите нужный двоичный файл, соответствующий вашей архитектуре, $GOPATH/bin/с именем fuelsequencerd:

echo $GOPATHЧтобы убедиться, что он существует. Если нет, goвозможно, он не установлен.
Убедитесь, что GOPATHнастройки в файле .bashrcили установлены правильно .zshrc. Запустите source ~/.bashrcили source ~/.zshrc, чтобы применить изменения.
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

Значок буфера обмена Текст
mkdir $GOPATH/bin/, если каталог не существует.
wget <url/to/binary> для загрузки бинарного файла или любого другого аналогичного подхода. Например:
wget https://github.com/FuelLabs/fuel-sequencer-deployments/releases/download/seq-mainnet-1.3.2/fuelsequencerd-seq-mainnet-1.3.2-darwin-arm64

Значок буфера обмена Текст
cp <binary> $GOPATH/bin/fuelsequencerdчтобы скопировать двоичный файл в GOPATH/bin/каталог.
chmod +x $GOPATH/bin/fuelsequencerdчтобы сделать двоичный файл исполняемым.
fuelsequencerd versionдля проверки работоспособности двоичного файла.
Попробуйте двоичный файл:

fuelsequencerd version  # expect seq-mainnet-1.3.2

Значок буфера обмена Текст
Инициализируйте каталог узла, дав вашему узлу осмысленное имя:

fuelsequencerd init <node-name> --chain-id seq-mainnet-1

Значок буфера обмена Текст
Скопируйте загруженный файл генезиса в ~/.fuelsequencer/config/genesis.json:

cp <path/to/genesis.json> ~/.fuelsequencer/config/genesis.json

Значок буфера обмена Текст
Настройте узел (часть 1 ~/.fuelsequencer/config/app.toml:):

Набор minimum-gas-prices = "10fuel".
Настроить [sidecar]:
Убедитесь, что enabled = false.
Настройте узел (часть 2 ~/.fuelsequencer/config/config.toml:):

Настроить [p2p]:
Набор persistent_peers = "fc5fd264190e4a78612ec589994646268b81f14e@80.64.208.207:26656".
Настроить [mempool]:
Установить max_tx_bytes = 1258291(1,2 МБ)
Установить max_txs_bytes = 23068672(22МиБ)
Настроить [rpc]:
Установить max_body_bytes = 1153434(необязательно - актуально для публичного RPC).
Значок InfoCircle
Примечание: Для снижения задержек транзакций важно обеспечить согласованность параметров пула памяти CometBFT на всех узлах сети. Это включает в себя mempool.size, mempool.max_txs_bytes, mempool.max_tx_bytesи
config.toml
Значок ссылки
и minimum-gas-pricesв
приложение.toml
Значок ссылки
, как указано выше.

Установить Космовизор
Чтобы установить Cosmovisor, запуститеgo install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest

Установите переменные среды:

echo "# Setup Cosmovisor" >> ~/.zshrc
echo "export DAEMON_NAME=fuelsequencerd" >> ~/.zshrc
echo "export DAEMON_HOME=$HOME/.fuelsequencer" >> ~/.zshrc
echo "export DAEMON_ALLOW_DOWNLOAD_BINARIES=true" >> ~/.zshrc
echo "export DAEMON_LOG_BUFFER_SIZE=512" >> ~/.zshrc
echo "export DAEMON_RESTART_AFTER_UPGRADE=true" >> ~/.zshrc
echo "export UNSAFE_SKIP_BACKUP=true" >> ~/.zshrc
echo "export DAEMON_SHUTDOWN_GRACE=15s" >> ~/.zshrc

# You can check https://docs.cosmos.network/main/tooling/cosmovisor for more configuration options.

Значок буфера обмена Текст
Применить к текущему сеансу:source ~/.zshrc

echo "# Setup Cosmovisor" >> ~/.bashrc
echo "export DAEMON_NAME=fuelsequencerd" >> ~/.bashrc
echo "export DAEMON_HOME=$HOME/.fuelsequencer" >> ~/.bashrc
echo "export DAEMON_ALLOW_DOWNLOAD_BINARIES=true" >> ~/.bashrc
echo "export DAEMON_LOG_BUFFER_SIZE=512" >> ~/.bashrc
echo "export DAEMON_RESTART_AFTER_UPGRADE=true" >> ~/.bashrc
echo "export UNSAFE_SKIP_BACKUP=true" >> ~/.bashrc
echo "export DAEMON_SHUTDOWN_GRACE=15s" >> ~/.bashrc

# You can check https://docs.cosmos.network/main/tooling/cosmovisor for more configuration options.

Значок буфера обмена Текст
Применить к текущему сеансу:source ~/.bashrc

Теперь вы можете проверить, что Космовизор установлен правильно:

cosmovisor version

Значок буфера обмена Текст
Инициализируйте каталоги Cosmovisor (подсказка: whereis fuelsequencerdдля пути):

cosmovisor init <path/to/fuelsequencerd>

Значок буфера обмена Текст
На этом этапе cosmovisor runбудет выполнено действие, эквивалентное запуску fuelsequencerd, однако на данный момент вам не следует запускать узел.

Настроить синхронизацию состояний
State Sync позволяет узлу быстро синхронизироваться.

Чтобы настроить синхронизацию состояний, вам необходимо установить следующие значения в ~/.fuelsequencer/config/config.tomlразделе [statesync]:

enable = trueдля включения синхронизации состояния
rpc_servers = ...
trust_height = ...
trust_hash = ...
Последние три значения можно получить из
исследователь
Значок ссылки
.

Вам потребуется указать как минимум два RPC-сервера, разделённых запятыми rpc_servers. Вы можете либо обратиться к списку альтернативных RPC-серверов выше, либо использовать один и тот же сервер дважды.

Запуск секвенсора
На этом этапе вы уже должны быть готовы cosmovisor run startзапустить секвенсор. Однако настоятельно рекомендуется запустить секвенсор в фоновом режиме .

Ниже приведены примеры для Linux и Mac. Вам потребуется реплицировать переменные окружения, заданные при настройке Cosmovisor.

Линукс
В Linux вы можете использовать его systemdдля запуска секвенсора в фоновом режиме. systemdПредполагается, что вы знаете, как им пользоваться.

Вот пример файла службы с некоторыми <...>значениями-заполнителями ( ), которые необходимо заполнить:

[Unit]
Description=Sequencer Node
After=network.target

[Service]
Type=simple
User=<USER>
ExecStart=/home/<USER>/go/bin/cosmovisor run start
Restart=on-failure
RestartSec=3
LimitNOFILE=4096

Environment="DAEMON_NAME=fuelsequencerd"
Environment="DAEMON_HOME=/home/<USER>/.fuelsequencer"
Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=true"
Environment="DAEMON_LOG_BUFFER_SIZE=512"
Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
Environment="UNSAFE_SKIP_BACKUP=true"
Environment="DAEMON_SHUTDOWN_GRACE=15s"

[Install]
WantedBy=multi-user.target
