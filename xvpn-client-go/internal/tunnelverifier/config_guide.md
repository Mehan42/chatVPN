# Руководство по конфигурации проверок туннелирования

## Обзор

Это руководство описывает настройку модуля проверки туннелирования (`tunnelverifier`) для различных сценариев использования. Модуль обеспечивает проверку целостности VPN-туннеля, защиту от утечек трафика и мониторинг безопасности соединения.

## Базовая конфигурация

### Параметры конфигурации

```go
type Config struct {
    // Интервал между проверками туннелирования
    CheckInterval time.Duration
    
    // Таймаут для каждой проверки
    Timeout time.Duration
    
    // Список эндпоинтов для проверки неРУ трафика
    VerificationEndpoints []string
    
    // Тестовая нагрузка для проверки
    TestPayload string
    
    // Уровень логирования (debug, info, warn, error)
    LogLevel string
    
    // Сервис для проверки внешнего IP
    IPCheckService string
    
    // Включить проверку IP-утечек
    CheckIPLeak bool
    
    // Включить проверку DNS-утечек
    CheckDNSLeak bool
    
    // Включить проверку маршрутизации трафика
    VerifyRouting bool
    
    // Включить комплексное обнаружение утечек
    EnableComprehensiveLeakDetection bool
    
    // Включить расширенную проверку маршрутизации
    EnableAdvancedRoutingVerification bool
}
```

## Типовые конфигурации

### 1. Минимальная конфигурация (по умолчанию)

```go
config := tunnelverifier.Config{
    CheckInterval:         30 * time.Second,
    Timeout:              60 * time.Second,
    VerificationEndpoints: []string{"8.8.8.8", "1.1.1.1"},
    TestPayload:          "TUNNEL_TEST",
    LogLevel:             "info",
    IPCheckService:       "https://httpbin.org/ip",
    CheckIPLeak:          true,
    CheckDNSLeak:         true,
    VerifyRouting:        true,
}
```

### 2. Конфигурация для высокой безопасности

```go
config := tunnelverifier.Config{
    CheckInterval:         15 * time.Second,  // Более частые проверки
    Timeout:              30 * time.Second,   // Более короткий таймаут
    VerificationEndpoints: []string{
        "1.1.1.1",     // Cloudflare DNS
        "8.8.8.8",     // Google DNS
        "208.67.222.222", // OpenDNS
        "www.google.com",
        "www.youtube.com",
    },
    TestPayload:          "HIGH_SECURITY_T0K3N",
    LogLevel:             "debug",  // Подробное логирование
    IPCheckService:       "https://ipinfo.io/ip",
    CheckIPLeak:          true,
    CheckDNSLeak:         true,
    VerifyRouting:        true,
    EnableComprehensiveLeakDetection: true,
    EnableAdvancedRoutingVerification: true,
}
```

### 3. Конфигурация для экономии ресурсов (эко-режим)

```go
config := tunnelverifier.Config{
    CheckInterval:         60 * time.Second,  // Реже проверяем
    Timeout:              120 * time.Second,  // Более длительные таймауты
    VerificationEndpoints: []string{"1.1.1.1"},
    TestPayload:          "ECO_MODE",
    LogLevel:             "warn",  // Минимальное логирование
    IPCheckService:       "https://httpbin.org/ip",
    CheckIPLeak:          true,
    CheckDNSLeak:         false,  // Отключена проверка DNS-утечек
    VerifyRouting:        false,  // Отключена проверка маршрутизации
    EnableComprehensiveLeakDetection: false,
}
```

## Настройка уровней логирования

### Параметры логирования

- `debug`: Подробное логирование всех операций, включая служебные вызовы
- `info`: Основные события и результаты проверок
- `warn`: Предупреждения о потенциальных проблемах
- `error`: Ошибки в работе модуля

### Пример настройки логирования

```go
// Включить JSON-формат логов
logger := tunnelverifier.NewLogger(tunnelverifier.Debug, true)
tunnelVerifier.SetLogger(logger)

// Или использовать стандартное логирование
tunnelVerifier.SetLogger(log.Writer())
```

## Настройка эндпоинтов проверки

### Выбор эндпоинтов для проверки неРУ трафика

Для корректной проверки маршрутизации неРУ трафика рекомендуется использовать:

- Известные неРУ IP-адреса (например, Cloudflare, Google, AWS)
- НеРУ доменные имена (google.com, facebook.com и т.д.)
- Специализированные сервисы для проверки утечек

### Пример выбора эндпоинтов

```go
verificationEndpoints := []string{
    // Популярные DNS-серверы
    "1.1.1.1",        // Cloudflare
    "8.8.8.8",        // Google
    "8.8.4.4",        // Google
    "208.67.222.222", // OpenDNS
    
    // Популярные веб-сайты
    "www.google.com",
    "www.youtube.com",
    "www.facebook.com",
    "www.twitter.com",
    "www.wikipedia.org",
    
    // Известные IP-адреса
    "142.250.180.110", // IP Google
}
```

## Расширенные настройки

### Настройка чувствительности проверок

```go
// Для более чувствительной проверки (обнаружение проблем быстрее)
config.CheckInterval = 10 * time.Second
config.EnableComprehensiveLeakDetection = true

// Для менее чувствительной проверки (меньше ресурсов)
config.CheckInterval = 120 * time.Second
config.EnableComprehensiveLeakDetection = false
```

### Настройка уведомлений

Уведомления отправляются через интеграцию с модулем `internal/alerts` и могут быть настроены следующим образом:

- Уведомления о сбоях отправляются с высоким приоритетом
- Уведомления о восстановлении отправляются с низким приоритетом
- Критические проблемы (утечки) получают критический уровень важности

## Использование с машиной состояний

### Интеграция с состояниями VPN

Модуль автоматически интегрирован с машиной состояний и реагирует на переходы:

- `StateIdle` → `StateRunning`: запуск проверок
- `StateRunning` → `StateStopping`: остановка проверок
- `StateRunning` → `StateIdle`: остановка проверок

### Проверка состояния туннелирования

```go
// Проверка валидности туннелирования из любого места
isValid, err := tunnelVerifier.IsTunnelingValid()
if err != nil {
    log.Printf("Ошибка проверки туннелирования: %v", err)
} else if !isValid {
    log.Println("Обнаружена проблема с туннелированием!")
} else {
    log.Println("Туннелирование в порядке")
}
```

## Рекомендации по настройке

### Для обычного использования
- Интервал проверки: 30-60 секунд
- Включить все типы проверок
- Уровень логирования: info
- Использовать 2-3 проверочных эндпоинта

### Для высокой безопасности
- Интервал проверки: 10-30 секунд
- Включить все типы проверок
- Уровень логирования: debug
- Использовать 5-10 проверочных эндпоинта
- Включить комплексное обнаружение утечек

### Для экономии ресурсов
- Интервал проверки: 60-300 секунд
- Оставить только базовые проверки
- Уровень логирования: warn или error
- Использовать 1-2 проверочных эндпоинта

## Диагностика и устранение неполадок

### Распространенные проблемы

1. **Частые ложные срабатывания**:
   - Увеличьте таймауты проверок
   - Увеличьте интервал проверок
   - Проверьте сетевое соединение

2. **Пропуск утечек**:
   - Увеличьте чувствительность
   - Сократите интервал проверок
   - Увеличьте количество проверочных эндпоинтов

3. **Высокое потребление ресурсов**:
   - Увеличьте интервал проверок
   - Отключите комплексные проверки
   - Снижьте уровень логирования