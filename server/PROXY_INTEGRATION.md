# ProxyBroker2 Integration Guide

## Overview

ProxyBroker2 integration provides enhanced proxy discovery and management capabilities for XVPN. This document explains how to configure and use ProxyBroker2 with XVPN.

## Installation

ProxyBroker2 can be installed in two ways:

### Method 1: Direct Installation
```bash
pip3 install git+https://github.com/bluet/proxybroker2.git
```

### Method 2: Using XVPN Installation Script
```bash
./server/install_proxybroker2.sh
```

## Configuration

ProxyBroker2 can be configured through environment variables:

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_TIMEOUT` | Timeout for proxy requests (seconds) | 8 |
| `PROXY_MAX_CONN` | Maximum concurrent proxy connections | 200 |
| `PROXY_MAX_TRIES` | Maximum attempts to check a proxy | 3 |
| `PROXY_VERIFY_SSL` | Verify SSL certificates | false |
| `PROXY_MIN_REQ_PROXY` | Minimum requests for proxy evaluation | 5 |
| `PROXY_MAX_ERROR_RATE` | Maximum error rate (0.0-1.0) | 0.5 |
| `PROXY_MAX_RESP_TIME` | Maximum response time (seconds) | 8 |

### Example Configuration
```bash
# Set in .env file or export before running XVPN
export PROXY_TIMEOUT=10
export PROXY_MAX_CONN=100
export PROXY_MAX_TRIES=2
export PROXY_VERIFY_SSL=false
export PROXY_MIN_REQ_PROXY=3
export PROXY_MAX_ERROR_RATE=0.3
export PROXY_MAX_RESP_TIME=5
```

## API Endpoints

Once installed, ProxyBroker2 integration is available through XVPN's API:

### Find Proxies
```bash
# Find HTTP/HTTPS proxies
curl -k https://localhost:8443/mcp/v1/admin.newclient

# Find SOCKS proxies
curl -k https://localhost:8443/mcp/v1/admin.newclient?type=socks
```

### Get Proxy Configuration
```bash
# Get configuration for specific proxy
curl -k https://localhost:8443/clients/{uuid}.json
```

### Proxy Status
```bash
# Check proxy health
curl -k https://localhost:8443/mcp/v1/vpn.health
```

## Usage Examples

### Basic Proxy Discovery
```python
import asyncio
from proxybroker import Broker

async def find_proxies():
    proxies = asyncio.Queue()
    broker = Broker(proxies)
    
    # Find 10 HTTP proxies
    await broker.find(types=['HTTP'], limit=10)
    
    # Process found proxies
    while True:
        proxy = await proxies.get()
        if proxy is None:
            break
        print(f"Found proxy: {proxy}")

asyncio.run(find_proxies())
```

### Advanced Proxy Configuration
```python
import asyncio
from proxybroker import Broker

async def find_advanced_proxies():
    proxies = asyncio.Queue()
    
    # Configure broker with advanced settings
    broker = Broker(
        queue=proxies,
        timeout=10,
        max_conn=100,
        max_tries=2,
        verify_ssl=False
    )
    
    # Find proxies with specific criteria
    await broker.find(
        types=['HTTP', 'HTTPS', 'SOCKS5'],
        countries=['US', 'GB', 'DE'],
        limit=20
    )
    
    # Process proxies
    working_proxies = []
    while True:
        proxy = await proxies.get()
        if proxy is None:
            break
        working_proxies.append(proxy)
        print(f"Working proxy: {proxy}")

asyncio.run(find_advanced_proxies())
```

### Proxy Validation
```python
import asyncio
from proxybroker import Proxy

async def validate_proxy():
    # Create proxy object
    proxy = await Proxy.create('127.0.0.1', 8080)
    
    # Validate proxy
    is_working = await proxy.is_working()
    print(f"Proxy working: {is_working}")
    
    # Get proxy details
    if is_working:
        print(f"Proxy types: {proxy.types}")
        print(f"Response time: {proxy.avg_resp_time}")
        print(f"Error rate: {proxy.error_rate}")

asyncio.run(validate_proxy())
```

## Integration with XVPN Components

### Server Integration
ProxyBroker2 integrates with XVPN server components through:

1. **API Endpoints**: `/mcp/v1/admin.newclient` for proxy discovery
2. **Configuration Management**: Automatic proxy configuration generation
3. **Health Monitoring**: Continuous proxy health checks
4. **Load Balancing**: Distribution of proxy requests

### Client Integration
XVPN clients can use ProxyBroker2 through:

1. **Proxy Configuration**: Automatic proxy configuration retrieval
2. **Failover Mechanisms**: Automatic switching to backup proxies
3. **Performance Monitoring**: Real-time proxy performance tracking
4. **Anonymity Checking**: Verification of proxy anonymity levels

## Security Considerations

### SSL/TLS Configuration
```bash
# Enable SSL verification for production
export PROXY_VERIFY_SSL=true

# Use custom CA certificates
export REQUESTS_CA_BUNDLE=/path/to/ca-certificates.crt
```

### Proxy Validation
ProxyBroker2 validates proxies through:
- Connection testing
- Anonymity level verification
- Response time measurement
- Error rate calculation

### Secure Proxy Usage
```python
# Use verified SSL connections
proxy = Proxy('127.0.0.1', 8080, verify_ssl=True)

# Validate anonymity level
if proxy.anonymity_level == 'High':
    # Use for sensitive traffic
    pass
```

## Performance Optimization

### Connection Pooling
```python
# Configure connection pooling
broker = Broker(
    max_conn=200,  # Maximum concurrent connections
    timeout=8,     # Connection timeout
    max_tries=3    # Retry attempts
)
```

### Proxy Caching
ProxyBroker2 caches proxy information to reduce discovery overhead:
- Proxy configurations are cached for reuse
- Health checks are performed periodically
- Failed proxies are automatically removed from cache

### Resource Management
```python
# Limit resource usage
broker = Broker(
    max_conn=100,      # Limit concurrent connections
    timeout=5,         # Shorter timeout for faster discovery
    max_tries=2        # Fewer retry attempts
)
```

## Troubleshooting

### Common Issues

1. **Proxy Discovery Fails**
   ```bash
   # Check network connectivity
   curl -k https://httpbin.org/get
   
   # Increase timeout
   export PROXY_TIMEOUT=15
   ```

2. **SSL Certificate Errors**
   ```bash
   # Disable SSL verification (for testing only)
   export PROXY_VERIFY_SSL=false
   
   # Use custom certificates
   export REQUESTS_CA_BUNDLE=/path/to/certificates.crt
   ```

3. **Performance Issues**
   ```bash
   # Reduce concurrent connections
   export PROXY_MAX_CONN=50
   
   # Limit retry attempts
   export PROXY_MAX_TRIES=1
   ```

### Logging and Debugging

Enable debug logging:
```bash
# Set log level
export LOG_LEVEL=DEBUG

# View logs
journalctl -u xvpn-api -f
```

### Error Handling

ProxyBroker2 provides comprehensive error handling:
- Connection timeouts
- SSL certificate errors
- Proxy authentication failures
- Network unreachable errors

```python
try:
    proxy = await Proxy.create('127.0.0.1', 8080)
    is_working = await proxy.is_working()
except ProxyTimeoutError:
    print("Proxy connection timed out")
except ProxyConnError:
    print("Proxy connection failed")
except ProxySSLError:
    print("SSL error with proxy")
```

## Advanced Features

### Multi-Protocol Support
ProxyBroker2 supports multiple protocols:
- HTTP/HTTPS
- SOCKS4/SOCKS5
- CONNECT:80/CONNECT:25
- Custom protocols

### Geographic Filtering
```python
# Find proxies in specific countries
await broker.find(
    types=['HTTP'],
    countries=['US', 'GB', 'DE'],
    limit=10
)
```

### Anonymity Levels
ProxyBroker2 detects and categorizes proxies by anonymity level:
- Transparent
- Anonymous
- High Anonymous

### Proxy Rotation
```python
# Implement proxy rotation
proxies = await broker.find(types=['HTTP'], limit=10)
current_proxy = proxies[0]

# Rotate to next proxy on failure
next_proxy = proxies[1]
```

## Best Practices

### 1. Proxy Selection
- Prefer high-anonymity proxies for sensitive traffic
- Use geographic filtering for regional access
- Validate proxies before use

### 2. Resource Management
- Limit concurrent connections to avoid overwhelming servers
- Set appropriate timeouts for your network conditions
- Use caching to reduce discovery overhead

### 3. Security
- Enable SSL verification in production
- Regularly rotate proxies to avoid detection
- Monitor proxy performance and remove poor performers

### 4. Error Handling
- Implement graceful fallbacks for proxy failures
- Log errors for troubleshooting
- Retry failed operations with different proxies

## Monitoring and Metrics

ProxyBroker2 provides metrics for monitoring:
- Proxy response times
- Error rates
- Success/failure counts
- Geographic distribution

```python
# Get proxy statistics
stats = broker.get_statistics()
print(f"Working proxies: {stats['working']}")
print(f"Average response time: {stats['avg_resp_time']}")
print(f"Error rate: {stats['error_rate']}")
```

## Integration Testing

Test ProxyBroker2 integration with XVPN:

### Unit Tests
```python
import pytest
from proxybroker import Proxy

def test_proxy_creation():
    proxy = Proxy('127.0.0.1', 8080)
    assert proxy.host == '127.0.0.1'
    assert proxy.port == 8080

@pytest.mark.asyncio
async def test_proxy_validation():
    proxy = await Proxy.create('127.0.0.1', 8080)
    # Mock validation for testing
    assert proxy is not None
```

### Integration Tests
```python
import pytest
import asyncio
from proxybroker import Broker

@pytest.mark.asyncio
async def test_proxy_discovery():
    proxies = asyncio.Queue()
    broker = Broker(proxies)
    
    # Test finding proxies
    await broker.find(types=['HTTP'], limit=1)
    
    # Verify proxy was found
    proxy = await proxies.get()
    assert proxy is not None
```

## Conclusion

ProxyBroker2 integration enhances XVPN with powerful proxy discovery and management capabilities. By following this guide, you can effectively integrate ProxyBroker2 into your XVPN deployment for improved proxy handling and bypass capabilities.