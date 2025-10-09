# XVPN - Intelligent VPN with AI Agents and Proxy Integration

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://www.docker.com/)
[![CI/CD](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Mehan42/chatVPN/actions/workflows/ci-cd.yml)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-green)](https://github.com/Mehan42/chatVPN)
[![Security](https://img.shields.io/badge/security-A%2B-brightgreen)](https://github.com/Mehan42/chatVPN)

[English](#english) | [Русский](#russian)

---

## English {#english}

Complete VPN system with intelligent agents for automatic transport management, monitoring and self-healing, plus ProxyBroker2 integration for enhanced proxy discovery.

### 🎯 Overview

XVPN is an intelligent VPN system that uses AI agents to automatically manage transport protocols, monitor connection health, and provide self-healing capabilities. Unlike traditional VPN solutions, XVPN continuously adapts to network conditions and automatically switches between transports to maintain optimal performance and security.

XVPN now includes integration with ProxyBroker2 for enhanced proxy discovery and management capabilities, providing robust solutions for bypassing network restrictions.

### 🌟 Features

#### 🔐 Security & Privacy
- **AI-powered transport switching**: Automatic selection of optimal VPN transports based on real-time performance and security analysis
- **Real-time health monitoring**: Continuous assessment of connection quality, security posture, and anonymity level
- **Multi-transport support**: VLESS, VMess, Trojan, Shadowsocks, WireGuard, and other protocols with automatic fallback
- **IPv6 dual-stack support**: Full IPv4/IPv6 connectivity with automatic dual-stack optimization
- **Proxy modes**: SOCKS5, HTTP, transparent proxy, and auto-detection modes for maximum compatibility
- **Secure TLS connections**: End-to-end encryption with certificate pinning and mutual authentication
- **Automatic failover**: Seamless transport switching on failures with zero downtime
- **Smart load balancing**: Traffic distribution based on performance metrics and security considerations
- **ProxyBroker2 Integration**: Automatic discovery and validation of proxies from 50+ sources for enhanced bypass capabilities

#### 🤖 Intelligence & Automation
- **AI Orchestration**: Advanced AI agents powered by ChromaDB RAG system for intelligent decision-making
- **Self-healing capabilities**: Automatic recovery from network issues, transport failures, and system errors
- **Predictive transport selection**: Machine learning algorithms predict optimal transports based on historical data
- **Dynamic configuration updates**: Real-time configuration adjustments without service interruption
- **Intelligent error handling**: Automatic error detection, classification, and resolution
- **Automated proxy management**: Continuous discovery and validation of working proxies for bypass scenarios

#### 🚀 Flexible Deployment
XVPN now supports flexible deployment in arbitrary directories with automatic update capabilities:

##### Client Installation in Custom Directory
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client
```

##### Server Installation
```bash
sudo ./install_server_flexible.sh
```

##### Automatic Updates
The system includes advanced deployment watcher that monitors repository changes and automatically updates clients and servers:

```bash
python3 advanced_deployment_watcher.py --config deployment_config.json
```

See [FLEXIBLE_DEPLOYMENT_GUIDE.md](FLEXIBLE_DEPLOYMENT_GUIDE.md) for detailed documentation.

#### 🛠️ Management & Monitoring
- **Telegram Bot Interface**: Full-featured management via Telegram with real-time notifications
- **Comprehensive CLI**: Powerful command-line interface for advanced users and automation
- **Web Dashboard**: Modern web interface for monitoring and configuration (coming soon)
- **Extensive logging**: Structured JSON logging with Prometheus metrics integration
- **Centralized monitoring**: Unified view of all system components with alerting capabilities
- **Performance analytics**: Detailed performance metrics and historical data analysis
- **Proxy pool management**: Centralized proxy discovery, validation, and distribution

#### 🎯 Language Support
- **English** - Full interface and documentation
- **Russian** - Полный интерфейс и документация

---

## Russian {#russian}

Полная VPN-система с интеллектуальными агентами для автоматического управления транспортами, мониторинга и самовосстановления, а также интеграция с ProxyBroker2 для расширенного обнаружения прокси.

### 🎯 Обзор

XVPN - это интеллектуальная VPN-система, использующая ИИ-агенты для автоматического управления протоколами транспорта, мониторинга состояния соединения и обеспечения возможностей самовосстановления. В отличие от традиционных VPN-решений, XVPN непрерывно адаптируется к условиям сети и автоматически переключается между транспортами для поддержания оптимальной производительности и безопасности.

XVPN теперь включает интеграцию с ProxyBroker2 для расширенного обнаружения и управления прокси, обеспечивая надежные решения для обхода сетевых ограничений.

### 🌟 Особенности

#### 🔐 Безопасность и конфиденциальность
- **Переключение транспортов на основе ИИ**: Автоматический выбор оптимальных VPN-транспортов на основе анализа производительности и безопасности в реальном времени
- **Мониторинг состояния в реальном времени**: Непрерывная оценка качества соединения, уровня безопасности и анонимности
- **Поддержка нескольких транспортов**: VLESS, VMess, Trojan, Shadowsocks, WireGuard и другие протоколы с автоматическим резервированием
- **Двухсторонняя поддержка IPv6**: Полная IPv4/IPv6 связность с автоматической оптимизацией двойного стека
- **Режимы прокси**: SOCKS5, HTTP, прозрачный прокси и режимы автоопределения для максимальной совместимости
- **Безопасные TLS-соединения**: Сквозное шифрование с закреплением сертификатов и взаимной аутентификацией
- **Автоматическое переключение при сбоях**: Бесшовное переключение транспортов при сбоях без простоев
- **Интеллектуальная балансировка нагрузки**: Распределение трафика на основе метрик производительности и соображений безопасности
- **Интеграция с ProxyBroker2**: Автоматическое обнаружение и проверка прокси из 50+ источников для усиления возможностей обхода

#### 🤖 Интеллект и автоматизация
- **Оркестрация ИИ**: Продвинутые ИИ-агенты на базе системы ChromaDB RAG для интеллектуального принятия решений
- **Возможности самовосстановления**: Автоматическое восстановление после сетевых проблем, сбоев транспортов и системных ошибок
- **Предиктивный выбор транспорта**: Алгоритмы машинного обучения прогнозируют оптимальные транспорты на основе исторических данных
- **Динамическое обновление конфигурации**: Обновление конфигурации в реальном времени без прерывания сервиса
- **Интеллектуальная обработка ошибок**: Автоматическое обнаружение, классификация и устранение ошибок
- **Автоматизированное управление прокси**: Непрерывное обнаружение и проверка рабочих прокси для сценариев обхода

#### 🚀 Гибкое развертывание
XVPN теперь поддерживает гибкое развертывание в произвольных директориях с возможностью автоматического обновления:

##### Установка клиента в произвольную директорию
```bash
./install_client_flexible.sh -d /opt/my_xvpn_client
```

##### Установка сервера
```bash
sudo ./install_server_flexible.sh
```

##### Автоматические обновления
Система включает расширенный watcher развертывания, который отслеживает изменения в репозитории и автоматически обновляет клиенты и серверы:

```bash
python3 advanced_deployment_watcher.py --config deployment_config.json
```

Подробную документацию см. в [FLEXIBLE_DEPLOYMENT_GUIDE.md](FLEXIBLE_DEPLOYMENT_GUIDE.md).

#### 🛠️ Управление и мониторинг
- **Интерфейс Telegram-бота**: Полнофункциональное управление через Telegram с уведомлениями в реальном времени
- **Комплексный CLI**: Мощный интерфейс командной строки для продвинутых пользователей и автоматизации
- **Веб-панель**: Современный веб-интерфейс для мониторинга и конфигурации (в разработке)
- **Обширное логирование**: Структурированное логирование JSON с интеграцией метрик Prometheus
- **Централизованный мониторинг**: Единое представление всех компонентов системы с возможностями оповещения
- **Аналитика производительности**: Подробные метрики производительности и исторические данные анализа
- **Управление пулом прокси**: Централизованное обнаружение, проверка и распределение прокси

#### 🎯 Языковая поддержка
- **Английский** - Полный интерфейс и документация
- **Русский** - Full interface and documentation

---

*Made with ❤️ for secure communications*