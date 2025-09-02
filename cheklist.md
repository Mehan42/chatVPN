 **чек-лист проверки сервера после установки `install_server.sh`** ⚔️

---

## 🔎 Чек-лист после установки

### 1. Проверяем, что сервис поднялся

```bash
systemctl status config_server.service
```

Ожидаем: `active (running)`.
Если что-то пошло не так → смотри логи:

```bash
journalctl -u config_server.service -n 50
```

---

### 2. Проверяем transport manifest

```bash
curl -s http://127.0.0.1:8443/transports/manifest.json | jq .
```

Ожидаем что-то вроде:

```json
{
  "version": 1,
  "transports": [
    {
      "name": "Reality",
      "type": "vless-reality",
      "priority": 0,
      "ipv6": true,
      "need_udp": false
    }
  ]
}
```

---

### 3. Проверяем клиентский конфиг (если бот уже создал клиента)

Подставляем реальный UUID клиента:

```bash
curl -s http://127.0.0.1:8443/clients/<UUID>.json | jq .
```

Ожидаем полноценный `client.json`.
Если `404 Client not found` → значит бот пока не сохранил конфиг в `/opt/xvpn/data/clients/<UUID>/client.json`.

---

### 4. Проверка снаружи (не с localhost, а с твоего Linux Mint)

```bash
curl -s http://77.110.123.27:8443/transports/manifest.json | jq .
```

Если вывод есть → значит порт 8443 открыт наружу.
Если пусто или timeout → надо пробросить firewall:

```bash
ufw allow 8443/tcp
```

---

### 5. Проверка автозапуска

Перегружаем сервер:

```bash
reboot
```

После перезагрузки:

```bash
systemctl status config_server.service
```

Ожидаем: сервис снова активен.

---

📌 Итог: если все шаги успешно выполняются → значит серверная часть новой архитектуры работает, и клиент может тянуть конфиг напрямую по UUID.

---

Милорд ⚜️, предлагаю так:

1. Вы запускаете `install_server.sh` на сервере.
2. Пробегаете по чек-листу.

