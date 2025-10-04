# XVPN Performance Testing Configuration
# Конфигурация автоматического тестирования производительности

# === Locust Performance Testing Configuration ===
# locustfile.py

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import string
import time
import json

class XVPNAPIClient(HttpUser):
    wait_time = between(1, 5)  # Время ожидания между запросами
    
    def on_start(self):
        """Выполняется при запуске клиента"""
        self.client.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'XVPN-Performance-Tester/1.0'
        }
        
    @task(10)  # Высокий вес - часто выполняется
    def health_check(self):
        """Проверка состояния здоровья API"""
        with self.client.get("/mcp/v1/vpn.health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"Health check failed: {data}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(5)  # Средний вес
    def get_transport_manifest(self):
        """Получение манифеста транспортов"""
        with self.client.get("/transports/manifest.json", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "transports" in data:
                        response.success()
                    else:
                        response.failure("Missing transports in manifest")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)  # Низкий вес
    def get_client_config(self):
        """Получение конфигурации клиента"""
        # Генерируем случайный UUID для тестирования
        test_uuid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        
        with self.client.get(f"/clients/{test_uuid}.json", catch_response=True) as response:
            # 404 допустим для несуществующих клиентов
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)  # Очень низкий вес - редко выполняется
    def stress_test(self):
        """Стресс-тестирование"""
        # Выполняем несколько последовательных запросов
        for _ in range(10):
            self.health_check()
            time.sleep(0.1)
            self.get_transport_manifest()
            time.sleep(0.1)

# === Настройки Locust ===
locust_config = {
    # Хост для тестирования
    "host": "https://api.xvpn.local",
    
    # Количество пользователей
    "users": 100,
    
    # Скорость появления пользователей (пользователей в секунду)
    "spawn_rate": 10,
    
    # Продолжительность теста (в секундах)
    "run_time": "10m",
    
    # Логирование
    "loglevel": "INFO",
    
    # Формат вывода
    "headless": True,
    
    # Вывод в CSV файлы
    "csv": "performance-results",
    
    # HTML отчет
    "html": "performance-report.html",
    
    # Только мастер (для распределенного тестирования)
    "master": False,
    
    # Только воркер (для распределенного тестирования)
    "worker": False,
    
    # Порт для веб-интерфейса
    "web_port": 8089,
    
    # Порт для мастер-сервера
    "master_bind_host": "*",
    "master_bind_port": 5557,
    
    # Таймауты
    "http_timeout": 30,
    "connection_timeout": 30,
    
    # Повторные попытки
    "max_retries": 3,
    
    # Проверка SSL сертификатов
    "verify_ssl": True,
    
    # Метки для теста
    "tags": ["performance", "api", "stress"],
    
    # Исключенные метки
    "exclude_tags": ["slow", "manual"],
    
    # Кастомные метрики
    "custom_metrics": {
        "health_check_latency": "ms",
        "manifest_download_latency": "ms",
        "client_config_latency": "ms"
    }
}

# === Pytest Performance Testing Configuration ===
# conftest.py

import pytest
import time
import asyncio
from functools import wraps

def measure_time(func):
    """Декоратор для измерения времени выполнения"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

@pytest.fixture(scope="session")
def performance_tracker():
    """Фикстура для отслеживания производительности"""
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
            
        def record_metric(self, name, value, unit="ms"):
            """Запись метрики"""
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append({"value": value, "unit": unit, "timestamp": time.time()})
            
        def get_average(self, name):
            """Получение среднего значения метрики"""
            if name in self.metrics and self.metrics[name]:
                values = [m["value"] for m in self.metrics[name]]
                return sum(values) / len(values)
            return 0
            
        def get_percentile(self, name, percentile=95):
            """Получение процентиля метрики"""
            if name in self.metrics and self.metrics[name]:
                values = sorted([m["value"] for m in self.metrics[name]])
                index = int(len(values) * percentile / 100)
                return values[min(index, len(values) - 1)]
            return 0
            
        def print_summary(self):
            """Вывод сводки по метрикам"""
            print("\n=== Performance Summary ===")
            for name, metrics in self.metrics.items():
                if metrics:
                    avg = self.get_average(name)
                    p95 = self.get_percentile(name, 95)
                    p99 = self.get_percentile(name, 99)
                    unit = metrics[0]["unit"]
                    print(f"{name}: avg={avg:.2f}{unit}, p95={p95:.2f}{unit}, p99={p99:.2f}{unit}")
    
    return PerformanceTracker()

# === Конфигурация pytest-benchmark ===
# pytest.ini

[tool:pytest]
# Добавляем pytest-benchmark
addopts = --benchmark-only --benchmark-columns=min,max,mean,stddev,median,iqr,outliers,rounds,iterations
markers = 
    benchmark: mark a test as a benchmark test
    performance: mark a test as a performance test
    stress: mark a test as a stress test

# === Конфигурация Apache Benchmark ===
# ab-test.sh

#!/bin/bash

# Apache Benchmark тестирование производительности XVPN API

# Переменные
API_URL="https://api.xvpn.local"
CONCURRENT_USERS=100
REQUESTS=10000
TIMEOUT=30

echo "🚀 Starting Apache Benchmark Performance Testing..."
echo "Target: $API_URL"
echo "Concurrent Users: $CONCURRENT_USERS"
echo "Requests: $REQUESTS"
echo "Timeout: ${TIMEOUT}s"
echo "==============================="

# Тест 1: Проверка состояния здоровья
echo "🧪 Test 1: Health Check Endpoint"
ab -n $REQUESTS -c $CONCURRENT_USERS -s $TIMEOUT -H "User-Agent: XVPN-AB-Tester/1.0" \
   $API_URL/mcp/v1/vpn.health

echo ""
echo "==============================="

# Тест 2: Получение манифеста транспортов
echo "🧪 Test 2: Transport Manifest Endpoint"
ab -n $REQUESTS -c $CONCURRENT_USERS -s $TIMEOUT -H "User-Agent: XVPN-AB-Tester/1.0" \
   $API_URL/transports/manifest.json

echo ""
echo "==============================="

# Тест 3: Получение конфигурации клиента (несуществующий UUID)
echo "🧪 Test 3: Client Config Endpoint (Non-existent)"
ab -n $REQUESTS -c $CONCURRENT_USERS -s $TIMEOUT -H "User-Agent: XVPN-AB-Tester/1.0" \
   $API_URL/clients/test-nonexistent-uuid.json

echo ""
echo "✅ Apache Benchmark Testing Completed!"

# === Конфигурация JMeter ===
# xvpn-performance-test.jmx

<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <!-- JMX файл для тестирования производительности XVPN -->
  <hashTree>
    <!-- Тестовый план -->
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="XVPN Performance Test" enabled="true">
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.comments">Performance testing for XVPN API</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="api_url" elementType="Argument">
            <stringProp name="Argument.name">api_url</stringProp>
            <stringProp name="Argument.value">https://api.xvpn.local</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="concurrent_users" elementType="Argument">
            <stringProp name="Argument.name">concurrent_users</stringProp>
            <stringProp name="Argument.value">100</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    
    <hashTree>
      <!-- Потоковая группа для тестирования здоровья API -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="API Health Check" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">100</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">100</stringProp>
        <stringProp name="ThreadGroup.ramp_time">10</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      
      <hashTree>
        <!-- HTTP запрос для проверки состояния здоровья -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Health Check Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${api_url}</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/mcp/v1/vpn.health</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout">30000</stringProp>
          <stringProp name="HTTPSampler.response_timeout">30000</stringProp>
        </HTTPSamplerProxy>
        
        <hashTree>
          <!-- Проверка ответа -->
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Response Assertion" enabled="true">
            <collectionProp name="Asserion.test_strings">
              <stringProp name="0">"status":"healthy"</stringProp>
            </collectionProp>
            <stringProp name="Assertion.custom_message"></stringProp>
            <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">2</intProp>
          </ResponseAssertion>
        </hashTree>
      </hashTree>
      
      <!-- Слушатели результатов -->
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <connectTime>true</connectTime>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <fileName>false</fileName>
            <hostname>true</hostname>
            <threadCounts>true</threadCounts>
            <sampleCount>true</sampleCount>
            <idleTime>true</idleTime>
            <timestamps>true</timestamps>
          </value>
        </objProp>
        <stringProp name="filename">health-check-results.jtl</stringProp>
      </ResultCollector>
    </hashTree>
  </hashTree>
</jmeterTestPlan>

# === Конфигурация автоматического запуска тестов ===
# .github/workflows/performance-test.yml

name: Performance Testing

on:
  # Запуск при пуше в основные ветки
  push:
    branches:
      - main
      - develop
      - perf/**
    paths:
      - "server/**"
      - "client/**"
      - "src/**"
      - "Dockerfile*"
      - "docker-compose.yml"
      - "requirements.txt"
      - "pyproject.toml"
      
  # Запуск по расписанию (еженедельно в воскресенье)
  schedule:
    - cron: "0 0 * * 0"
    
  # Запуск вручную
  workflow_dispatch:
    inputs:
      test_type:
        description: "Type of performance test"
        required: true
        default: "all"
        type: choice
        options:
          - all
          - api
          - client
          - stress
          - benchmark

jobs:
  # === API Performance Testing ===
  api-performance-test:
    name: API Performance Test
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка зависимостей
      - name: Install Dependencies
        run: |
          pip install locust pytest pytest-benchmark requests
          
      # Запуск Locust тестов
      - name: Run Locust Performance Tests
        run: |
          locust -f tests/performance/locustfile.py \
                --host https://api.xvpn.local \
                --users 100 \
                --spawn-rate 10 \
                --run-time 5m \
                --headless \
                --csv performance-results \
                --html performance-report.html
                
      # Сохранение результатов
      - name: Archive Performance Results
        uses: actions/upload-artifact@v3
        with:
          name: api-performance-results
          path: |
            performance-results_*.csv
            performance-report.html
            locust.log
            
      # Анализ результатов
      - name: Analyze Performance Results
        run: |
          echo "Performance test completed. Analyzing results..."
          # TODO: Add performance analysis logic
          
  # === Client Performance Testing ===
  client-performance-test:
    name: Client Performance Test
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка зависимостей
      - name: Install Dependencies
        run: |
          pip install pytest pytest-benchmark
          
      # Запуск тестов производительности клиента
      - name: Run Client Performance Tests
        run: |
          pytest tests/performance/client_benchmarks.py -v --benchmark-only
          
      # Сохранение результатов
      - name: Archive Client Performance Results
        uses: actions/upload-artifact@v3
        with:
          name: client-performance-results
          path: benchmark_*.json
          
  # === Stress Testing ===
  stress-test:
    name: Stress Test
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Apache Benchmark
      - name: Install Apache Benchmark
        run: |
          sudo apt-get update
          sudo apt-get install -y apache2-utils
          
      # Запуск стресс-тестов
      - name: Run Stress Tests
        run: |
          bash tests/performance/ab-test.sh
          
      # Сохранение результатов
      - name: Archive Stress Test Results
        uses: actions/upload-artifact@v3
        with:
          name: stress-test-results
          path: ab-results.txt
          
  # === Benchmark Testing ===
  benchmark-test:
    name: Benchmark Test
    runs-on: ubuntu-latest
    steps:
      # Проверка кода
      - name: Checkout Code
        uses: actions/checkout@v4
        
      # Установка Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      # Установка зависимостей
      - name: Install Dependencies
        run: |
          pip install pytest pytest-benchmark
          
      # Запуск бенчмарков
      - name: Run Benchmarks
        run: |
          pytest tests/benchmark/ -v --benchmark-only --benchmark-autosave
          
      # Сохранение результатов
      - name: Archive Benchmark Results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: .benchmarks/
          
  # === Performance Report Generation ===
  performance-report:
    name: Generate Performance Report
    runs-on: ubuntu-latest
    needs: [api-performance-test, client-performance-test, stress-test, benchmark-test]
    steps:
      # Загрузка артефактов
      - name: Download Artifacts
        uses: actions/download-artifact@v3
        with:
          path: performance-results/
          
      # Генерация отчета
      - name: Generate Performance Report
        run: |
          echo "Generating performance report..."
          # TODO: Add report generation logic
          
      # Загрузка отчета
      - name: Upload Performance Report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance-report.pdf
          
      # Уведомление о результатах
      - name: Performance Test Results Notification
        if: always()
        run: |
          echo "Performance testing completed!"
          # TODO: Add notification logic

# === Конфигурация мониторинга во время тестов ===
# tests/performance/monitoring.yml

version: '3.8'

services:
  # === Prometheus для сбора метрик ===
  prometheus:
    image: prom/prometheus:latest
    container_name: xvpn-perf-prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - perf-network
      
  # === Grafana для визуализации ===
  grafana:
    image: grafana/grafana:latest
    container_name: xvpn-perf-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"
    networks:
      - perf-network
    depends_on:
      - prometheus
      
  # === Node Exporter для системных метрик ===
  node-exporter:
    image: prom/node-exporter:latest
    container_name: xvpn-perf-node-exporter
    ports:
      - "9100:9100"
    networks:
      - perf-network
      
  # === Cadvisor для метрик контейнеров ===
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: xvpn-perf-cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    networks:
      - perf-network

volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local

networks:
  perf-network:
    driver: bridge