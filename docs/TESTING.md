# XVPN - Testing Guide

## Overview

This guide provides comprehensive testing procedures for XVPN, including unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_client.py
│   ├── test_agent.py
│   ├── test_api.py
│   └── test_state_machine.py
├── integration/             # Integration tests
│   ├── test_docker_integration.py
│   ├── test_systemd_services.py
│   └── test_https_security.py
├── performance/             # Performance tests
│   ├── test_vpn_speed.py
│   ├── test_memory_usage.py
│   └── test_concurrent_connections.py
└── e2e/                     # End-to-end tests
    ├── test_full_workflow.py
    └── test_failure_scenarios.py
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock requests docker

# Install development dependencies
pip install black flake8 mypy pre-commit
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xvpn

# Run specific test file
pytest tests/unit/test_client.py

# Run specific test
pytest tests/unit/test_client.py::test_client_initialization

# Run tests with verbose output
pytest -v

# Run tests with progress
pytest --tb=short

# Run tests in parallel
pytest -n auto
```

## Unit Tests

### Client Tests

```python
# tests/unit/test_client.py
import pytest
from unittest.mock import Mock, patch
from xvpn.client.vpn_client import VPNClient

def test_client_initialization():
    """Test client initialization"""
    client = VPNClient()
    assert client is not None
    assert client.config is not None

def test_client_state_machine():
    """Test state machine integration"""
    client = VPNClient()
    assert client.state_machine is not None
    assert client.get_current_state() == "disconnected"
```

### Agent Tests

```python
# tests/unit/test_agent.py
import pytest
from unittest.mock import Mock
from xvpn.agent.agent import Agent

def test_agent_initialization():
    """Test agent initialization"""
    agent = Agent()
    assert agent is not None
    assert agent.health_monitor is not None

def test_agent_rag_system():
    """Test RAG system functionality"""
    agent = Agent()
    response = agent.process_query("What is VPN?")
    assert response is not None
    assert isinstance(response, str)
```

### API Tests

```python
# tests/unit/test_api.py
import pytest
from fastapi.testclient import TestClient
from xvpn.api.app import app

def test_api_health():
    """Test API health endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## Integration Tests

### Docker Integration Tests

```python
# tests/integration/test_docker_integration.py
import pytest
import docker
import time

def test_docker_services():
    """Test Docker services startup"""
    client = docker.from_env()
    
    # Start services
    !docker-compose up -d
    
    # Wait for services to start
    time.sleep(30)
    
    # Check if containers are running
    containers = client.containers.list()
    assert len(containers) > 0
    
    # Check specific services
    api_container = client.containers.get("xvpn-api")
    assert api_container is not None
    assert api_container.status == "running"
```

### Systemd Service Tests

```python
# tests/integration/test_systemd_services.py
import pytest
import subprocess
import time

def test_systemd_services():
    """Test systemd services"""
    # Start services
    subprocess.run(["systemctl", "start", "xvpn-docker"], check=True)
    subprocess.run(["systemctl", "start", "xvpn-api"], check=True)
    subprocess.run(["systemctl", "start", "xvpn-client"], check=True)
    
    # Wait for services to start
    time.sleep(10)
    
    # Check service status
    result = subprocess.run(["systemctl", "is-active", "xvpn-api"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    
    # Check service logs
    result = subprocess.run(["journalctl", "-u", "xvpn-api", "--lines=10"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "Starting" in result.stdout
```

### HTTPS Security Tests

```python
# tests/integration/test_https_security.py
import pytest
import requests
from urllib.parse import urlparse

def test_https_endpoint():
    """Test HTTPS endpoint with TLS verification"""
    url = "https://api.xvpn.local/health"
    
    # Test with certificate verification
    response = requests.get(url, verify=True)
    assert response.status_code == 200
    
    # Test without certificate verification (should fail)
    with pytest.raises(requests.exceptions.SSLError):
        response = requests.get(url, verify=False)

def test_tls_pinning():
    """Test TLS certificate pinning"""
    from xvpn.client.tls_checker import TLSVerifier
    
    verifier = TLSVerifier()
    cert_hash = verifier.get_certificate_hash("api.xvpn.local")
    assert cert_hash is not None
    
    # Verify pinned certificate
    assert verifier.verify_certificate("api.xvpn.local", cert_hash)
```

## Performance Tests

### VPN Speed Tests

```python
# tests/performance/test_vpn_speed.py
import pytest
import time
import requests

def test_vpn_speed():
    """Test VPN connection speed"""
    # Connect to VPN
    connect_to_vpn()
    
    # Test download speed
    start_time = time.time()
    response = requests.get("https://speed.cloudflare.com/__static/10mb.bin")
    download_time = time.time() - start_time
    
    download_speed = len(response.content) / download_time / 1024 / 1024  # MB/s
    
    assert download_speed > 1  # At least 1 MB/s
    
    # Test upload speed
    # (Implementation for upload speed test)
```

### Memory Usage Tests

```python
# tests/performance/test_memory_usage.py
import pytest
import psutil
import time

def test_memory_usage():
    """Test memory usage under load"""
    process = psutil.Process()
    
    # Get initial memory usage
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Simulate load
    simulate_load()
    
    # Get peak memory usage
    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Assert memory usage is within limits
    assert peak_memory < 512  # Less than 512MB
    
    # Calculate memory growth
    memory_growth = peak_memory - initial_memory
    assert memory_growth < 100  # Less than 100MB growth
```

### Concurrent Connections Tests

```python
# tests/performance/test_concurrent_connections.py
import pytest
import threading
import time

def test_concurrent_connections():
    """Test concurrent connections"""
    def worker():
        """Worker function for concurrent testing"""
        response = requests.get("https://api.xvpn.local/health")
        assert response.status_code == 200
    
    # Create multiple threads
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Assert all requests succeeded
    assert all(thread.is_alive() == False for thread in threads)
```

## End-to-End Tests

### Full Workflow Test

```python
# tests/e2e/test_full_workflow.py
import pytest
import subprocess
import time

def test_full_workflow():
    """Test complete XVPN workflow"""
    # Step 1: Install XVPN
    subprocess.run(["./scripts/install_xvpn.sh"], check=True)
    
    # Step 2: Start services
    subprocess.run(["systemctl", "start", "xvpn-*"], check=True)
    time.sleep(30)
    
    # Step 3: Test API health
    response = requests.get("https://api.xvpn.local/health")
    assert response.status_code == 200
    
    # Step 4: Test client connection
    result = subprocess.run(["/opt/xvpn/client/chatvpn_backend.py", "status"], 
                          capture_output=True, text=True)
    assert "running" in result.stdout
    
    # Step 5: Test configuration loading
    result = subprocess.run(["/opt/xvpn/client/chatvpn_backend.py", "config"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    
    # Step 6: Test VPN connection
    # (Implementation for VPN connection test)
```

### Failure Scenario Tests

```python
# tests/e2e/test_failure_scenarios.py
import pytest
import subprocess
import time

def test_docker_failure():
    """Test system behavior when Docker fails"""
    # Stop Docker
    subprocess.run(["systemctl", "stop", "docker"], check=True)
    
    # Try to start XVPN services
    result = subprocess.run(["systemctl", "start", "xvpn-docker"], 
                          capture_output=True, text=True)
    
    # Assert that service fails gracefully
    assert result.returncode != 0
    
    # Restore Docker
    subprocess.run(["systemctl", "start", "docker"], check=True)

def test_memory_exhaustion():
    """Test system behavior under memory pressure"""
    # Simulate memory exhaustion
    # (Implementation for memory exhaustion test)
    
    # Assert system handles gracefully
    assert True
```

## Test Coverage

### Coverage Requirements

- Unit tests: 90%+ coverage
- Integration tests: 80%+ coverage
- Performance tests: 100% of critical paths
- End-to-end tests: 100% of user workflows

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=xvpn --cov-report=html --cov-report=term

# Generate XML coverage report
pytest --cov=xvpn --cov-report=xml

# Upload coverage to Codecov
codecov --token=your-token
```

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov docker
    
    - name: Run tests
      run: |
        pytest --cov=xvpn --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

## Test Data

### Test Certificates

Create test certificates for HTTPS testing:

```bash
# Generate test certificate
openssl req -x509 -newkey rsa:4096 -keyout test.key -out test.crt -days 365 -nodes

# Configure test server with test certificate
```

### Test Configuration

Create test configuration files:

```python
# tests/test_config.py
TEST_CONFIG = {
    "api": {
        "host": "localhost",
        "port": 8443,
        "ssl": True
    },
    "vpn": {
        "server": "test.vpn.com",
        "port": 1194,
        "protocol": "udp"
    }
}
```

## Performance Metrics

### Key Metrics to Monitor

1. **Response Time**
   - API endpoint response time < 100ms
   - VPN connection time < 5s

2. **Throughput**
   - Concurrent connections: 100+
   - Data transfer rate: 10+ Mbps

3. **Resource Usage**
   - Memory usage: < 512MB
   - CPU usage: < 50%
   - Disk usage: < 1GB

### Monitoring

```bash
# Monitor system resources
htop
free -h
df -h

# Monitor network
netstat -tulpn
iftop

# Monitor application logs
journalctl -u xvpn-* -f
```

## Troubleshooting Tests

### Common Test Failures

1. **Docker Not Available**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   sudo netstat -tulpn | grep :443
   ```

3. **Permission Issues**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER /opt/xvpn
   ```

### Debug Mode

Run tests with debug mode:

```bash
# Run with debug output
pytest --log-cli-level=DEBUG

# Run with pdb
pytest --pdb
```

## Contributing

### Adding New Tests

1. Create test file in appropriate directory
2. Follow naming conventions: `test_*.py`
3. Include docstrings for test functions
4. Add tests for both success and failure scenarios

### Test Documentation

- Document test prerequisites
- Include setup and teardown procedures
- Document expected outcomes
- Provide troubleshooting steps

## Conclusion

This testing guide provides comprehensive procedures for ensuring XVPN reliability and performance. Follow these guidelines to maintain high code quality and system stability.

For additional help, refer to:
- [XVPN Documentation](https://docs.xvpn.local)
- [GitHub Issues](https://github.com/xvpn/xvpn/issues)
- [Community Forum](https://forum.xvpn.local)