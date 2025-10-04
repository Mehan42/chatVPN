# XVPN Security Monitoring Configuration
# Конфигурация автоматического мониторинга безопасности

# === Trivy Security Scanner Configuration ===
# trivy.yaml

# Глобальные настройки
scan:
  # Типы сканирования
  security-checks:
    - vuln        # Уязвимости
    - config      # Конфигурационные ошибки
    - secret      # Секреты и пароли
    - license     # Лицензии
    - malware     # Вредоносное ПО
    
  # Уровни серьезности
  severity:
    - CRITICAL
    - HIGH
    - MEDIUM
    - LOW
    
  # Игнорировать устраненные уязвимости
  ignore-unfixed: true
  
  # Игнорировать тестовые зависимости
  skip-dirs:
    - node_modules
    - .git
    - vendor
    - build
    - dist
    - venv
    - .venv
    - env
    - .env
    
  # Игнорировать файлы
  skip-files:
    - package-lock.json
    - yarn.lock
    - Gemfile.lock
    - Pipfile.lock

# === Сканирование образов Docker ===
image:
  # Регистры Docker
  registry:
    # Docker Hub
    docker-hub:
      username: ${{ secrets.DOCKER_USERNAME }}
      password: ${{ secrets.DOCKER_PASSWORD }}
      
    # GitHub Container Registry
    ghcr:
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}

# === Сканирование файловой системы ===
filesystem:
  # Директории для сканирования
  dirs:
    - src/
    - server/
    - client/
    - config/
    - tests/
    
  # Файлы для сканирования
  files:
    - "**/*.py"
    - "**/*.yml"
    - "**/*.yaml"
    - "**/*.json"
    - "**/*.sh"
    - "**/*.js"
    - "**/*.ts"
    
  # Проверка конфигурации
  misconfiguration:
    # Проверка Dockerfile
    dockerfile:
      enabled: true
      
    # Проверка Kubernetes
    kubernetes:
      enabled: false
      
    # Проверка Terraform
    terraform:
      enabled: false
      
    # Проверка CloudFormation
    cloudformation:
      enabled: false

# === Сканирование репозитория ===
repository:
  # GitHub
  github:
    owner: Mehan42
    repo: chatVPN
    token: ${{ secrets.GITHUB_TOKEN }}
    
  # GitLab
  gitlab:
    url: https://gitlab.com
    token: ${{ secrets.GITLAB_TOKEN }}

# === Секреты и учетные данные ===
secret:
  # Включить сканирование секретов
  enabled: true
  
  # Типы секретов
  secret-types:
    - aws-access-key
    - aws-secret-key
    - github-token
    - slack-webhook
    - docker-password
    - ssh-private-key
    - pgp-private-key
    - rsa-private-key
    - dsa-private-key
    - ec-private-key
    - jwt-token
    - api-key
    
  # Пути для игнорирования
  exclude-paths:
    - tests/fixtures/
    - docs/examples/
    - .git/

# === Лицензии ===
license:
  # Включить проверку лицензий
  enabled: true
  
  # Разрешенные лицензии
  allow-list:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
    - ISC
    - MPL-2.0
    - Unlicense
    
  # Запрещенные лицензии
  deny-list:
    - GPL-1.0
    - GPL-2.0
    - GPL-3.0
    - AGPL-1.0
    - AGPL-3.0

# === Выходные форматы ===
output:
  # Формат вывода
  format: table  # table, json, sarif, template
  
  # Файл вывода
  file: security-report.json
  
  # Уровень детализации
  verbosity: detail  # quiet, normal, detail, trace

# === Интеграции ===
integration:
  # GitHub Security Center
  github-security:
    enabled: true
    
  # Slack уведомления
  slack:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    channel: "#security-alerts"
    
  # Telegram уведомления
  telegram:
    bot-token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
    
  # Email уведомления
  email:
    smtp-server: smtp.gmail.com
    smtp-port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    to: security@xvpn.local
    from: security-monitor@xvpn.local

# === Bandit Security Configuration ===
# bandit.yaml

# Тесты для запуска
tests:
  - B101  # assert_used
  - B102  # exec_used
  - B103  # setattr_bad_example
  - B104  # hardcoded_bind_all_interfaces
  - B105  # hardcoded_password_string
  - B106  # hardcoded_password_funcarg
  - B107  # hardcoded_password_default
  - B108  # hardcoded_tmp_directory
  - B110  # try_except_pass
  - B112  # try_except_continue
  - B201  # flask_debug_true
  - B301  # pickle
  - B302  # marshal
  - B303  # md5
  - B304  # ciphers
  - B305  # cipher_modes
  - B306  # mktemp_q
  - B307  # eval
  - B308  # mark_safe
  - B309  # httpsconnection
  - B310  # urllib_urlopen
  - B311  # random
  - B312  # telnetlib
  - B313  # xml_bad_cElementTree
  - B314  # xml_bad_ElementTree
  - B315  # xml_bad_expatreader
  - B316  # xml_bad_expatbuilder
  - B317  # xml_bad_sax
  - B318  # xml_bad_minidom
  - B319  # xml_bad_pulldom
  - B320  # xml_bad_etree
  - B321  # ftplib
  - B322  # input
  - B323  # unverified_context
  - B324  # hashlib_new_insecure_functions
  - B325  # tempnam
  - B401  # import_telnetlib
  - B402  # import_ftplib
  - B403  # import_pickle
  - B404  # import_subprocess
  - B405  # import_xml_etree
  - B406  # import_xml_sax
  - B407  # import_xml_expat
  - B408  # import_xml_minidom
  - B409  # import_xml_pulldom
  - B410  # import_lxml
  - B411  # import_xmlrpclib
  - B412  # import_httpoxy
  - B413  # import_pycrypto
  - B501  # request_with_no_cert_validation
  - B502  # ssl_with_bad_version
  - B503  # ssl_with_bad_defaults
  - B504  # ssl_with_no_version
  - B505  # weak_cryptographic_key
  - B506  # yaml_load
  - B507  # ssh_no_host_key_verification
  - B601  # paramiko_calls
  - B602  # subprocess_popen_with_shell_equals_true
  - B603  # subprocess_without_shell_equals_true
  - B604  # any_other_function_with_shell_equals_true
  - B605  # start_process_with_a_shell
  - B606  # start_process_with_no_shell
  - B607  # start_process_with_partial_path
  - B608  # hardcoded_sql_expressions
  - B609  # linux_commands_wildcard_injection
  - B610  # django_rawsql_injection
  - B611  # django_extra_injection
  - B701  # jinja2_autoescape_false
  - B702  # use_of_mako_templates
  - B703  # django_mark_safe

# Уровни серьезности
severity:
  # Критические
  critical:
    - B301  # pickle
    - B302  # marshal
    - B303  # md5
    - B307  # eval
    - B322  # input
    - B401  # import_telnetlib
    - B402  # import_ftplib
    - B403  # import_pickle
    - B411  # import_xmlrpclib
    - B501  # request_with_no_cert_validation
    - B502  # ssl_with_bad_version
    - B601  # paramiko_calls
    - B602  # subprocess_popen_with_shell_equals_true
    - B605  # start_process_with_a_shell
    - B608  # hardcoded_sql_expressions
    
  # Высокие
  high:
    - B101  # assert_used
    - B102  # exec_used
    - B104  # hardcoded_bind_all_interfaces
    - B105  # hardcoded_password_string
    - B106  # hardcoded_password_funcarg
    - B107  # hardcoded_password_default
    - B304  # ciphers
    - B305  # cipher_modes
    - B310  # urllib_urlopen
    - B311  # random
    - B323  # unverified_context
    - B404  # import_subprocess
    - B410  # import_lxml
    - B503  # ssl_with_bad_defaults
    - B504  # ssl_with_no_version
    - B505  # weak_cryptographic_key
    - B603  # subprocess_without_shell_equals_true
    - B604  # any_other_function_with_shell_equals_true
    - B606  # start_process_with_no_shell
    - B607  # start_process_with_partial_path
    - B609  # linux_commands_wildcard_injection
    
  # Средние
  medium:
    - B103  # setattr_bad_example
    - B108  # hardcoded_tmp_directory
    - B110  # try_except_pass
    - B112  # try_except_continue
    - B201  # flask_debug_true
    - B306  # mktemp_q
    - B308  # mark_safe
    - B309  # httpsconnection
    - B312  # telnetlib
    - B313  # xml_bad_cElementTree
    - B314  # xml_bad_ElementTree
    - B315  # xml_bad_expatreader
    - B316  # xml_bad_expatbuilder
    - B317  # xml_bad_sax
    - B318  # xml_bad_minidom
    - B319  # xml_bad_pulldom
    - B320  # xml_bad_etree
    - B321  # ftplib
    - B324  # hashlib_new_insecure_functions
    - B325  # tempnam
    - B405  # import_xml_etree
    - B406  # import_xml_sax
    - B407  # import_xml_expat
    - B408  # import_xml_minidom
    - B409  # import_xml_pulldom
    - B506  # yaml_load
    - B507  # ssh_no_host_key_verification
    - B701  # jinja2_autoescape_false
    - B702  # use_of_mako_templates
    - B703  # django_mark_safe
    
  # Низкие
  low:
    - B105  # hardcoded_password_string
    - B106  # hardcoded_password_funcarg
    - B107  # hardcoded_password_default

# === Safety Configuration ===
# safety.yaml

# Источники уязвимостей
sources:
  - pypi
  - github
  - nvd
  - ossindex

# Уровни серьезности
severity:
  - critical
  - high
  - medium
  - low

# Игнорируемые уязвимости
ignore-vulnerabilities:
  # Список CVE для игнорирования
  cve:
    - CVE-2018-20225  # Пример CVE для игнорирования
    - CVE-2020-26116  # Пример CVE для игнорирования
    
  # Игнорируемые зависимости
  packages:
    # Примеры зависимостей для игнорирования
    - name: example-package
      version: "<1.0.0"
      reason: "Not used in production"

# === OWASP ZAP Configuration ===
# zap.yaml

# Цели сканирования
targets:
  - url: https://api.xvpn.local
    name: XVPN API
    auth:
      type: bearer
      token: ${{ secrets.API_TOKEN }}
      
  - url: https://dashboard.xvpn.local
    name: XVPN Dashboard
    auth:
      type: form
      login-url: https://dashboard.xvpn.local/login
      username: ${{ secrets.TEST_USERNAME }}
      password: ${{ secrets.TEST_PASSWORD }}

# Типы сканирования
scans:
  - type: spider  # Паук для обхода сайта
    depth: 5
    max-duration: 300
    
  - type: active-scan  # Активное сканирование
    policy: Default Policy
    max-duration: 600
    
  - type: passive-scan  # Пассивное сканирование
    max-duration: 300
    
  - type: ajax-spider  # AJAX паук
    max-duration: 300

# === ClamAV Configuration ===
# clamav.conf

# Настройки сканера
Scanner:
  # Директории для сканирования
  scan-dirs:
    - /opt/xvpn/
    - /var/log/xvpn/
    - /etc/xvpn/
    
  # Типы файлов для сканирования
  file-types:
    - .exe
    - .dll
    - .sys
    - .bat
    - .cmd
    - .ps1
    - .sh
    - .pl
    - .pyc
    - .jar
    - .war
    - .apk
    - .ipa
    
  # Исключения
  exclude-dirs:
    - /proc/
    - /sys/
    - /dev/
    - /run/
    
  exclude-files:
    - .git/
    - __pycache__/
    - *.log
    - *.tmp
    - *.cache

# === GitHub Security Scanning ===
# .github/workflows/security-scan.yml

name: Security Scanning

on:
  # Запуск при пуше в основные ветки
  push:
    branches:
      - main
      - develop
      - security/**
    paths:
      - "**.py"
      - "**.yml"
      - "**.yaml"
      - "**.json"
      - "**.sh"
      - "**/Dockerfile*"
      - "docker-compose.yml"
      - "requirements.txt"
      - "pyproject.toml"
      
  # Запуск при создании pull request
  pull_request:
    branches:
      - main
      - develop
    paths:
      - "**.py"
      - "**.yml"
      - "**.yaml"
      - "**.json"
      - "**.sh"
      - "**/Dockerfile*"
      - "docker-compose.yml"
      - "requirements.txt"
      - "pyproject.toml"
      
  # Запуск по расписанию (ежедневно в 4:00)
  schedule:
    - cron: "0 4 * * *"
    
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Trivy Security Scan ===
  trivy-scan:
    name: Trivy Security Scan
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Trivy
      - name: Install Trivy
        run: |
          sudo apt-get update
          sudo apt-get install -y wget apt-transport-https gnupg lsb-release
          wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
          echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
          sudo apt-get update
          sudo apt-get install -y trivy
          
      # Сканирование файловой системы
      - name: Filesystem Security Scan
        run: |
          trivy fs \
            --severity CRITICAL,HIGH,MEDIUM \
            --format json \
            --output trivy-fs-report.json \
            .
            
      # Сканирование Dockerfile
      - name: Dockerfile Security Scan
        run: |
          trivy config \
            --severity CRITICAL,HIGH,MEDIUM \
            --format json \
            --output trivy-config-report.json \
            .
            
      # Загрузка результатов
      - name: Upload Trivy Reports
        uses: actions/upload-artifact@v3
        with:
          name: trivy-security-reports
          path: |
            trivy-fs-report.json
            trivy-config-report.json
            
      # Проверка результатов
      - name: Check for Critical Issues
        run: |
          # Проверяем наличие критических уязвимостей
          if [ -f trivy-fs-report.json ]; then
            critical_count=$(jq -r '[.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL")] | length' trivy-fs-report.json)
            if [ "$critical_count" -gt 0 ]; then
              echo "Critical vulnerabilities found: $critical_count"
              exit 1
            fi
          fi

  # === Bandit Security Scan ===
  bandit-scan:
    name: Bandit Security Scan
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python зависимостей
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка Bandit
      - name: Install Bandit
        run: |
          pip install bandit
          
      # Сканирование Python кода
      - name: Run Bandit Security Scan
        run: |
          bandit -r src/ server/ client/ \
                 -f json \
                 -o bandit-report.json \
                 --exit-zero
                 
      # Загрузка результатов
      - name: Upload Bandit Report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-security-report
          path: bandit-report.json
          
      # Анализ результатов
      - name: Analyze Bandit Results
        run: |
          if [ -f bandit-report.json ]; then
            critical_issues=$(jq -r '.results | map(select(.issue_severity == "HIGH")) | length' bandit-report.json)
            if [ "$critical_issues" -gt 0 ]; then
              echo "High severity security issues found: $critical_issues"
              jq -r '.results[] | select(.issue_severity == "HIGH") | .filename + ":" + (.line_number|tostring) + " - " + .issue_text' bandit-report.json
            fi
          fi

  # === Safety Dependency Check ===
  safety-scan:
    name: Safety Dependency Check
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python зависимостей
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка Safety
      - name: Install Safety
        run: |
          pip install safety
          
      # Проверка зависимостей
      - name: Run Safety Check
        run: |
          safety check \
            --full-report \
            --json \
            --output-file safety-report.json \
            || true  # Продолжаем выполнение даже при уязвимостях
            
      # Загрузка результатов
      - name: Upload Safety Report
        uses: actions/upload-artifact@v3
        with:
          name: safety-security-report
          path: safety-report.json
          
      # Анализ результатов
      - name: Analyze Safety Results
        run: |
          if [ -f safety-report.json ]; then
            vulnerable_deps=$(jq -r '.vulnerabilities | length' safety-report.json)
            if [ "$vulnerable_deps" -gt 0 ]; then
              echo "Vulnerable dependencies found: $vulnerable_deps"
              jq -r '.vulnerabilities[] | .package_name + " " + .installed_version + " -> " + .affected_versions + " (" + .vulnerability_id + ")"' safety-report.json
            fi
          fi

  # === Secret Scanning ===
  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Полная история для поиска секретов
        
      # Установка Gitleaks
      - name: Install Gitleaks
        run: |
          curl -L https://github.com/zricethezav/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz -o gitleaks.tar.gz
          tar -xzf gitleaks.tar.gz
          sudo install gitleaks /usr/local/bin/gitleaks
          
      # Сканирование на наличие секретов
      - name: Run Gitleaks Secret Scan
        run: |
          gitleaks detect --report-format json --report-path gitleaks-report.json || true
          
      # Загрузка результатов
      - name: Upload Gitleaks Report
        uses: actions/upload-artifact@v3
        with:
          name: gitleaks-secret-report
          path: gitleaks-report.json
          
      # Анализ результатов
      - name: Analyze Secret Detection Results
        run: |
          if [ -f gitleaks-report.json ]; then
            leaks_count=$(jq -r 'length' gitleaks-report.json)
            if [ "$leaks_count" -gt 0 ]; then
              echo "Potential secrets detected: $leaks_count"
              jq -r '.[] | .Description + " in " + .File + " line " + (.StartLine|tostring)' gitleaks-report.json
              exit 1
            fi
          fi

  # === Security Report Generation ===
  security-report:
    name: Generate Security Report
    runs-on: ubuntu-latest
    needs: [trivy-scan, bandit-scan, safety-scan, secret-scan]
    steps:
      # Загрузка всех отчетов
      - name: Download All Security Reports
        uses: actions/download-artifact@v3
        with:
          path: security-reports/
          
      # Генерация сводного отчета
      - name: Generate Summary Report
        run: |
          echo "# XVPN Security Report" > security-summary.md
          echo "Generated on $(date -Iseconds)" >> security-summary.md
          echo "" >> security-summary.md
          
          echo "## Summary" >> security-summary.md
          echo "" >> security-summary.md
          
          # Подсчет уязвимостей из разных источников
          echo "### Trivy Findings" >> security-summary.md
          if [ -f security-reports/trivy-security-reports/trivy-fs-report.json ]; then
            critical=$(jq -r '[.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL")] | length' security-reports/trivy-security-reports/trivy-fs-report.json)
            high=$(jq -r '[.Results[].Vulnerabilities[] | select(.Severity=="HIGH")] | length' security-reports/trivy-security-reports/trivy-fs-report.json)
            medium=$(jq -r '[.Results[].Vulnerabilities[] | select(.Severity=="MEDIUM")] | length' security-reports/trivy-security-reports/trivy-fs-report.json)
            echo "- Critical: $critical" >> security-summary.md
            echo "- High: $high" >> security-summary.md
            echo "- Medium: $medium" >> security-summary.md
          fi
          echo "" >> security-summary.md
          
          echo "### Bandit Findings" >> security-summary.md
          if [ -f security-reports/bandit-security-report/bandit-report.json ]; then
            high_issues=$(jq -r '.results | map(select(.issue_severity == "HIGH")) | length' security-reports/bandit-security-report/bandit-report.json)
            echo "- High severity issues: $high_issues" >> security-summary.md
          fi
          echo "" >> security-summary.md
          
          echo "### Safety Findings" >> security-summary.md
          if [ -f security-reports/safety-security-report/safety-report.json ]; then
            vulnerable_deps=$(jq -r '.vulnerabilities | length' security-reports/safety-security-report/safety-report.json)
            echo "- Vulnerable dependencies: $vulnerable_deps" >> security-summary.md
          fi
          echo "" >> security-summary.md
          
          echo "### Secret Detection" >> security-summary.md
          if [ -f security-reports/gitleaks-secret-report/gitleaks-report.json ]; then
            leaks=$(jq -r 'length' security-reports/gitleaks-secret-report/gitleaks-report.json)
            echo "- Potential secrets: $leaks" >> security-summary.md
          fi
          
          echo "Security scan completed. Please review the detailed reports for specific findings."
          
      # Загрузка сводного отчета
      - name: Upload Security Summary
        uses: actions/upload-artifact@v3
        with:
          name: security-summary-report
          path: security-summary.md
          
      # Уведомление о результатах
      - name: Security Scan Results Notification
        if: always()
        run: |
          echo "Security scanning workflow completed"
          # TODO: Add notification logic

# === Конфигурация автоматического мониторинга ===
# .github/workflows/security-monitoring.yml

name: Security Monitoring

on:
  # Запуск по расписанию (ежечасно)
  schedule:
    - cron: "0 * * * *"
    
  # Запуск при изменении критических файлов
  push:
    paths:
      - "security/**"
      - "certificates/**"
      - "keys/**"
      - "**/Dockerfile*"
      - "docker-compose.yml"
      
  # Запуск вручную
  workflow_dispatch:

jobs:
  # === Continuous Security Monitoring ===
  continuous-monitoring:
    name: Continuous Security Monitoring
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Мониторинг сертификатов
      - name: Certificate Expiration Monitoring
        run: |
          echo "Checking certificate expiration..."
          # TODO: Add certificate expiration checks
          
      # Мониторинг зависимостей
      - name: Dependency Security Monitoring
        run: |
          echo "Monitoring dependency security..."
          # TODO: Add dependency security monitoring
          
      # Мониторинг конфигурации
      - name: Configuration Security Monitoring
        run: |
          echo "Monitoring configuration security..."
          # TODO: Add configuration security monitoring
          
      # Уведомление о результатах
      - name: Security Monitoring Notification
        if: always()
        run: |
          echo "Continuous security monitoring completed"
          # TODO: Add notification logic

# === Конфигурация безопасности Docker ===
# security/docker-security.conf

# === Docker Bench Security Configuration ===
# docker-bench-security configuration

# === Конфигурация сканирования образов ===
# image-scan.yaml

# === Конфигурация мониторинга в реальном времени ===
# realtime-monitor.yaml

# === Конфигурация оповещений ===
# alerts.yaml

# === Конфигурация интеграции SIEM ===
# siem-integration.conf