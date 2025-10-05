# Установка XVPN сервера на удаленном сервере

## Подготовка сервера

1. Убедитесь, что у вас есть доменное имя, указывающее на IP-адрес сервера
2. Установите необходимые системные зависимости:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl wget git docker.io docker-compose jq
```

3. Установите XRay:

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

## Клонирование и установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Mehan42/chatVPN.git
cd chatVPN
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_server.txt
```

3. Настройте порты для работы с открытыми портами провайдера:

* API будет работать на порту 443 (HTTPS)
* Для этого потребуется получить SSL-сертификат

## Получение SSL-сертификата

1. Установите Certbot:

```bash
sudo apt install -y certbot
```

2. Получите сертификат (замените yourdomain.com на ваш домен):

```bash
sudo certbot certonly --standalone -d yourdomain.com
```

## Настройка конфигурации

1. Отредактируйте конфигурацию сервера:

```bash
sudo mkdir -p /opt/xvpn/tls
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/xvpn/tls/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/xvpn/tls/key.pem
```

2. Установите права на файлы сертификатов:

```bash
sudo chown -R xvpn:xvpn /opt/xvpn/tls
sudo chmod 600 /opt/xvpn/tls/key.pem
```

## Запуск сервера

1. Запустите компоненты:

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите API сервер (он будет использовать порт 443)
nohup python3 server/api/app.py > /var/log/xvpn/api.log 2>&1 &

# Запустите агента
nohup python3 server/agent/agent.py > /var/log/xvpn/agent.log 2>&1 &

# Запустите остальные компоненты по необходимости
```

## Проверка

1. Убедитесь, что API доступен:

```bash
curl -k https://yourdomain.com:443/mcp/v1/vpn.health
```

## Альтернативная установка через PEX (рекомендуется)

```bash
# Установите PEX
pip install pex

# Соберите серверные PEX-файлы
./build_pex.sh server

# Запустите API с использованием PEX
chmod +x dist/pex/xvpn-api.pex
sudo -u xvpn ./dist/pex/xvpn-api.pex
```