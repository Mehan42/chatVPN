Общие правила работы

Все изменения фиксировать в репозитории и в ~/chatvpn/CHANGELOG.md.

Абсолютные пути в любом скрипте/инструкции: всегда ~/chatvpn/... (клиент) и /opt/xvpn/... (сервер).

Логи клиентов пишем в ~/chatvpn/client/logs/.

Перед изменением серверного кода делать бэкап: sudo cp -a /opt/xvpn /opt/xvpn.bak-$(date +%s).

Тесты сначала на dev-сервере (если есть), потом на прод.

Фаза 1 — Базовый рабочий контур (прямой HTTPS конфиг)
Task 1.1 — Подготовить TLS и простой HTTPS сервис на сервере

Путь / файлы: /opt/xvpn/tls/selfsigned.crt, /opt/xvpn/tls/selfsigned.key, /home/<user>/chatvpn/server/config_server.py, systemd unit /etc/systemd/system/xvpn-config.service
Шаги:

Создать каталог TLS: sudo mkdir -p /opt/xvpn/tls.

Сгенерировать self-signed сертификат (тестовый):

sudo openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /opt/xvpn/tls/selfsigned.key \
  -out /opt/xvpn/tls/selfsigned.crt \
  -subj "/CN=77.110.123.27"
sudo chmod 600 /opt/xvpn/tls/selfsigned.key


Развернуть скрипт config_server.py по пути /home/<user>/chatvpn/server/config_server.py (см. README).

Создать systemd unit /etc/systemd/system/xvpn-config.service с запуском от нужного пользователя.

Запустить и включить: sudo systemctl daemon-reload && sudo systemctl enable --now xvpn-config.service.
Acceptance:

curl -sk https://127.0.0.1:8443/clients/<UUID>.json возвращает JSON при наличии файла /opt/xvpn/data/clients/<UUID>/client.json.

sudo systemctl status xvpn-config.service — service active (running).
Проверка:

curl -sk "https://127.0.0.1:8443/clients/<TEST_UUID>.json" | jq .

Task 1.2 — Положить клиентские конфиги на сервер в ожидаемой структуре

Путь / файлы: /opt/xvpn/data/clients/<UUID>/client.json
Шаги:

Убедиться, что каталоги существуют: sudo mkdir -p /opt/xvpn/data/clients/<UUID>.

Положить валидный client.json в эту папку и выставить права:

sudo cp ~/chatvpn/server/samples/client.json /opt/xvpn/data/clients/<UUID>/client.json
sudo chown -R root:root /opt/xvpn/data/clients/<UUID>
sudo chmod 640 /opt/xvpn/data/clients/<UUID>/client.json


Acceptance:

На сервере файл присутствует и корректен.

curl -sk "https://127.0.0.1:8443/clients/<UUID>.json" возвращает корректный JSON.
Проверка:

sudo ls -la /opt/xvpn/data/clients/<UUID>/client.json
curl -sk "https://127.0.0.1:8443/clients/<UUID>.json" | jq .

Task 1.3 — Клиент: реализовать и протестировать загрузку client.json напрямую

Путь / файлы: ~/chatvpn/client/chatvpn_backend.py (функция fetch_config_from_server)
Шаги:

Вставить/обновить реализацию fetch_config_from_server() (см. README/ROADMAP).

Убедиться, что SERVER_IP и SERVER_PORT верны в файле.

На клиенте выполнить:

python3 ~/chatvpn/client/chatvpn_gui.py


или тест с консоли:

python3 -c "import chatvpn_backend as b; print(b.fetch_config_from_server())"


Acceptance:

fetch_config_from_server() возвращает (True, "Конфиг получен напрямую (HTTPS)") и создаёт ~/chatvpn/client/client.json.

GUI после автозагрузки показывает источник — «HTTPS».
Проверка:

python3 -c "import chatvpn_backend as b; print(b.fetch_config_from_server()) ; ls -la ~/chatvpn/client/client.json"

Фаза 2 — Светофор невидимости и метрики
Task 2.1 — Определить набор метрик и реализовать сбор (health)

Путь / файлы: ~/chatvpn/client/health.py, логи ~/chatvpn/client/logs/health.log
Шаги:

Создать модуль health.py с функциями:

check_ip_leak() — сравнивает внешний IP (https://api.ipify.org) и локальный ISP-IP (опционально)

check_tls_profile() — простая эвристика: попытка TLS ClientHello (базовая) или проверка transport flag из манифеста

check_dns_protection() — тест DoH разрешения (например, запрос к https://cloudflare-dns.com/dns-query)

Записывать результаты в ~/chatvpn/client/logs/health.log в формате TS JSON.

Выдать API: get_mask_score() → int 0..5 по правилам README.
Acceptance:

При вызове python3 -c "import health; print(health.get_mask_score())" возвращает число 0–5.

Логи в ~/chatvpn/client/logs/health.log появляются и содержат JSON событий.
Проверка:

python3 -c "import health; print(health.get_mask_score())"
tail -n 20 ~/chatvpn/client/logs/health.log

Task 2.2 — GUI: отобразить «светофор» и транспорт

Путь / файлы: ~/chatvpn/client/chatvpn_gui.py
Шаги:

Подключить health.get_mask_score() и отрисовать индикатор цвета (0–5).

Добавить текстовый статус текущего транспорта: Transport: T0 (VLESS+Reality) — берётся из ~/chatvpn/client/transports/manifest.json либо из client.json.

Добавить всплывающую подсказку при наведении с деталями метрик (TLS, DNS, IP leak).
Acceptance:

GUI показывает светофор (цвет + число) и транспорт строкой.

Tooltip показывает расшифровку проверки.
Проверка:

Запустить GUI и визуально проверить; посмотреть логи ~/chatvpn/client/logs/health.log.

Фаза 3 — Манифест транспортов и DISCOVER
Task 3.1 — Создать шаблон manifest.json на сервере

Путь / файлы: /opt/xvpn/data/transports/manifest.json
Шаги:

Создать статичный файл с полем: список транспортов с приоритетом, flags (ipv4, ipv6, need_udp), connect_timeout, min_hold_time. Пример структуры в README.

Поставить права: sudo chmod 640 /opt/xvpn/data/transports/manifest.json.
Acceptance:

curl -sk https://127.0.0.1:8443/transports/manifest.json возвращает JSON.
Проверка:

sudo cat /opt/xvpn/data/transports/manifest.json | jq .
curl -sk https://127.0.0.1:8443/transports/manifest.json | jq .

Task 3.2 — Клиент: загрузить и кешировать manifest

Путь / файлы: ~/chatvpn/client/chatvpn_backend.py (функция fetch_manifest_from_server), ~/chatvpn/client/transports/manifest.json (кеш)
Шаги:

Реализовать fetch_manifest_from_server() и кеширование.

В chatvpn_gui.py при старте загружать/кэшировать манифест.
Acceptance:

Файл ~/chatvpn/client/transports/manifest.json появляется с содержимым.

GUI отображает первый транспорт как «candidate».
Проверка:

python3 -c "import chatvpn_backend as b; print(b.fetch_manifest_from_server())"
ls -la ~/chatvpn/client/transports/manifest.json

Task 3.3 — DISCOVER: префлайт-тест транспорта (микроскрипт)

Путь / файлы: ~/chatvpn/client/discover.py
Шаги:

Для каждого транспорта из manifest выполнить быстрые проверки:

TCP connect к серверу (v4 и v6) по порту;

TLS ClientHello — минимальная проверка (timeout короткий);

при need_udp — короткий UDP ping (если поддерживается).

Собрать баллы и выдавать очередь приоритетов.
Acceptance:

python3 ~/chatvpn/client/discover.py возвращает список кандидатов с метриками (v4/v6 success, rtt).
Проверка:

python3 ~/chatvpn/client/discover.py

Фаза 4 — AUTO-FALLBACK state machine (пилотный)
Task 4.1 — Реализовать простую state-machine (DISCOVER→CONNECT→ACTIVE→FALLBACK)

Путь / файлы: ~/chatvpn/client/state_machine.py
Шаги:

Написать модуль, который:

читает manifest и discover-данные;

пытается поднять транспорт (в MVP — запуск Xray с соответствующим client.json/transport);

отслеживает health (через health.py);

при деградации — переключается на следующий candidate;

логирует переходы в ~/chatvpn/client/logs/state.log.

Интегрировать вызовы в chatvpn_gui.py: кнопка «Включить VPN» запускает state-machine (начиная с best candidate).
Acceptance:

При искусственном сбросе T0 (например, firewall drop), через min_hold_time происходит переключение на T1.

Логи содержат переходы состояний.
Проверка:

Вручную пометить сервер unreachable/iptables DROP и смотреть state.log.

tail -f ~/chatvpn/client/logs/state.log

Фаза 5 — IPv6 / Proxy-modes / UX
Task 5.1 — Включить поддержку параллельного dial v4/v6

Путь / файлы: ~/chatvpn/client/discover.py, state_machine.py
Шаги:

Реализовать параллельную проверку v4 и v6 в discover; сравнение RTT и выбор лучшего.

Отобразить в GUI выбор (v4/v6) и текущую версию IP.
Acceptance:

Клиент выбирает v6, если v6 доступен и RTT не хуже порогов.
Проверка:

python3 ~/chatvpn/client/discover.py

Task 5.2 — Локальные прокси: SOCKS5/HTTP и режим «Proxy only»

Путь / файлы: ~/chatvpn/client/proxy_helper.py
Шаги:

Поднять инструкцию/скрипт для запуска локального SOCKS5 (через xray или shadowsocks) на случай proxy-only.

GUI добавить переключатель режимов: TUN / Proxy / Auto.
Acceptance:

При выборе Proxy mode локальный SOCKS-сервер поднимается и доступен на 127.0.0.1:random_port.
Проверка:

ss -ltnp | grep xray
curl --socks5 127.0.0.1:<port> https://api.ipify.org

Фаза 6 — Телеграм и админ-эндпоинты (non-blocking)
Task 6.1 — REST-эндпоинты для бота (админ)

Путь / файлы: /opt/xvpn/http_admin/ (скрипты), systemd unit (опционально)
Шаги:

Реализовать простой auth-ограниченный REST (token) для операций: получить список клиентов, перегенерировать config для UUID, скачать client.json.

Бот будет вызывать эти эндпоинты (async), а не полагаться на sendDocument→getUpdates.
Acceptance:

REST доступен на https://77.110.123.27:8444/admin/... с токеном.
Проверка:

curl -sk "https://77.110.123.27:8444/admin/clients" -H "Authorization: Bearer <token>"

Чек-лист релиза каждой фазы

Фаза 1: direct HTTPS загрузка работает и GUI получает client.json автоматически.

Фаза 2: светофор отображается и логирует health.

Фаза 3: manifest раздаётся сервером и кешируется клиентом.

Фаза 4: state-machine переключается при деградации.

Фаза 5: IPv6 и proxy-modes работают тестово.

Фаза 6: REST-эндпоинты для бота готовы (не обязательны для MVP).

Распределение приоритетов (M — must, S — should, C — could)

M: Task 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2

S: Task 3.3, 4.1, 5.1

C: Task 5.2, 6.1

Временные оценки (ориентировочно)

(для одного инженера, full-time)

Фаза 1 (Tasks 1.1–1.3): 2–3 дня

Фаза 2 (Tasks 2.1–2.2): 1–2 дня

Фаза 3 (Tasks 3.1–3.3): 2 дня

Фаза 4 (Task 4.1): 2–3 дня

Фаза 5 (Tasks 5.1–5.2): 2–3 дня

Фаза 6 (Task 6.1): 1–2 дня

Контроль качества и тесты

Unit-tests: health functions (исключить реальные сетевые вызовы, мокать).

Integration-tests:

curl к серверу HTTPS;

поднятие xray локально и проверка IP;

симуляция блокировки (iptables) и проверка переключения.

Логи: все операции писать в ~/chatvpn/client/logs/ и на сервере в /var/log/xvpn/.

Замечания и риск-лог

Самоподписанный TLS — временно для тестов. Для продакшена обязательно CA-сертификат.

Webhook-бот даёт удобство, но getUpdates в такой конфигурации не работает — поэтому REST/HTTPS обязательны.

Реализация авто-переключения требует аккуратного тестирования (чтобы избежать «дёргания»).
