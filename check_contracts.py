#!/usr/bin/env python3
"""Check public API contracts without pytest."""

import asyncio
import inspect
import sys
from unittest.mock import MagicMock, patch

def check_broker_public_interface():
    """Check Broker public interface stability."""
    print("Checking Broker public interface...")
    
    try:
        from proxybroker import Broker
        
        # Test that all expected public methods exist
        broker = Broker()
        
        # Essential public methods
        assert hasattr(broker, 'find'), "Broker missing find method"
        assert hasattr(broker, 'grab'), "Broker missing grab method"
        assert hasattr(broker, 'serve'), "Broker missing serve method"
        assert hasattr(broker, 'stop'), "Broker missing stop method"
        
        # Test method signatures
        sig = inspect.signature(broker.find)
        assert 'types' in sig.parameters, "find method missing types parameter"
        assert 'limit' in sig.parameters, "find method missing limit parameter"
        
        sig = inspect.signature(broker.grab)
        assert 'countries' in sig.parameters, "grab method missing countries parameter"
        assert 'limit' in sig.parameters, "grab method missing limit parameter"
        
        sig = inspect.signature(broker.serve)
        assert 'host' in sig.parameters, "serve method missing host parameter"
        assert 'port' in sig.parameters, "serve method missing port parameter"
        assert 'limit' in sig.parameters, "serve method missing limit parameter"
        
        print("✓ Broker public interface is stable")
        return True
    except Exception as e:
        print(f"✗ Broker public interface check failed: {e}")
        return False

def check_proxy_public_interface():
    """Check Proxy public interface stability."""
    print("Checking Proxy public interface...")
    
    try:
        from proxybroker import Proxy
        
        # Test direct creation
        proxy = Proxy('127.0.0.1', 8080)
        
        # Essential public attributes and methods
        assert hasattr(proxy, 'host'), "Proxy missing host attribute"
        assert hasattr(proxy, 'port'), "Proxy missing port attribute"
        assert hasattr(proxy, 'types'), "Proxy missing types attribute"
        assert hasattr(proxy, 'is_working'), "Proxy missing is_working attribute"
        assert hasattr(proxy, 'avg_resp_time'), "Proxy missing avg_resp_time attribute"
        assert hasattr(proxy, 'error_rate'), "Proxy missing error_rate attribute"
        assert hasattr(proxy, 'as_json'), "Proxy missing as_json method"
        assert hasattr(proxy, 'as_text'), "Proxy missing as_text method"
        
        # Test that types can be set and retrieved
        proxy.types = {'HTTP': 'Anonymous'}
        assert proxy.types == {'HTTP': 'Anonymous'}, "Proxy types property not working"
        
        # Test JSON output structure
        json_data = proxy.as_json()
        assert isinstance(json_data, dict), "as_json() should return dict"
        assert 'host' in json_data, "JSON missing host field"
        assert 'port' in json_data, "JSON missing port field"
        assert 'geo' in json_data, "JSON missing geo field"
        assert 'types' in json_data, "JSON missing types field"
        assert 'avg_resp_time' in json_data, "JSON missing avg_resp_time field"
        assert 'error_rate' in json_data, "JSON missing error_rate field"
        
        # Test text output
        text_data = proxy.as_text()
        assert isinstance(text_data, str), "as_text() should return string"
        assert ':' in text_data, "Text output should contain host:port format"
        
        print("✓ Proxy public interface is stable")
        return True
    except Exception as e:
        print(f"✗ Proxy public interface check failed: {e}")
        return False

def check_proxypool_public_interface():
    """Check ProxyPool public interface stability."""
    print("Checking ProxyPool public interface...")
    
    try:
        from proxybroker import ProxyPool
        import asyncio
        
        # Test basic initialization
        proxies = asyncio.Queue()
        pool = ProxyPool(proxies)
        
        # Essential public methods
        assert hasattr(pool, 'get'), "ProxyPool missing get method"
        assert hasattr(pool, 'put'), "ProxyPool missing put method"
        
        sig = inspect.signature(pool.get)
        assert 'scheme' in sig.parameters, "get method missing scheme parameter"
        
        sig = inspect.signature(pool.put)
        assert 'proxy' in sig.parameters, "put method missing proxy parameter"
        
        print("✓ ProxyPool public interface is stable")
        return True
    except Exception as e:
        print(f"✗ ProxyPool public interface check failed: {e}")
        return False

def check_server_public_interface():
    """Check Server public interface stability."""
    print("Checking Server public interface...")
    
    try:
        from proxybroker import Server
        
        # Test that Server class exists and has essential methods
        assert Server is not None, "Server class not found"
        assert hasattr(Server, '__init__'), "Server missing __init__ method"
        assert hasattr(Server, 'start'), "Server missing start method"
        assert hasattr(Server, 'stop'), "Server missing stop method"
        
        print("✓ Server public interface is stable")
        return True
    except Exception as e:
        print(f"✗ Server public interface check failed: {e}")
        return False

def check_exception_hierarchy():
    """Check that exception hierarchy remains stable."""
    print("Checking exception hierarchy...")
    
    try:
        from proxybroker.errors import (
            ProxyError,
            NoProxyError,
            ResolveError,
            ProxyConnError,
            ProxyRecvError,
            ProxySendError,
            ProxyTimeoutError,
            ProxyEmptyRecvError,
        )
        
        # Test base exceptions
        assert issubclass(ProxyError, Exception), "ProxyError should inherit from Exception"
        assert issubclass(NoProxyError, Exception), "NoProxyError should inherit from Exception"
        assert issubclass(ResolveError, Exception), "ResolveError should inherit from Exception"
        
        # Test network exceptions
        assert issubclass(ProxyConnError, ProxyError), "ProxyConnError should inherit from ProxyError"
        assert issubclass(ProxyRecvError, ProxyError), "ProxyRecvError should inherit from ProxyError"
        assert issubclass(ProxySendError, ProxyError), "ProxySendError should inherit from ProxyError"
        assert issubclass(ProxyTimeoutError, ProxyError), "ProxyTimeoutError should inherit from ProxyError"
        assert issubclass(ProxyEmptyRecvError, ProxyError), "ProxyEmptyRecvError should inherit from ProxyError"
        
        print("✓ Exception hierarchy is stable")
        return True
    except Exception as e:
        print(f"✗ Exception hierarchy check failed: {e}")
        return False

def check_proxy_creation_api():
    """Check Proxy creation APIs."""
    print("Checking Proxy creation APIs...")
    
    try:
        from proxybroker import Proxy
        
        # Test direct creation
        proxy = Proxy('127.0.0.1', 8080)
        assert proxy.host == '127.0.0.1', "Proxy host not set correctly"
        assert proxy.port == 8080, "Proxy port not set correctly"
        
        # Test validation
        try:
            Proxy('127.0.0.1', 65536)  # Port too high
            assert False, "Should have raised ValueError for port > 65535"
        except ValueError:
            pass  # Expected
        
        try:
            Proxy('127.0.0.1', -1)  # Port too low
            assert False, "Should have raised ValueError for port < 1"
        except ValueError:
            pass  # Expected
            
        print("✓ Proxy creation APIs are stable")
        return True
    except Exception as e:
        print(f"✗ Proxy creation API check failed: {e}")
        return False

def check_exported_symbols():
    """Check that all expected symbols are properly exported."""
    print("Checking exported symbols...")
    
    try:
        # Test that main classes are exported
        from proxybroker import Broker, Proxy, ProxyPool, Server
        assert Broker is not None, "Broker not exported"
        assert Proxy is not None, "Proxy not exported"
        assert ProxyPool is not None, "ProxyPool not exported"
        assert Server is not None, "Server not exported"
        
        # Test that error classes are exported
        from proxybroker.errors import (
            ProxyError,
            NoProxyError,
            ResolveError,
            ProxyConnError,
            ProxyRecvError,
            ProxySendError,
            ProxyTimeoutError,
            ProxyEmptyRecvError,
        )
        
        # All should be importable and be proper exception classes
        assert issubclass(ProxyError, Exception), "ProxyError not properly exported"
        assert issubclass(NoProxyError, Exception), "NoProxyError not properly exported"
        assert issubclass(ResolveError, Exception), "ResolveError not properly exported"
        
        print("✓ Exported symbols are stable")
        return True
    except Exception as e:
        print(f"✗ Exported symbols check failed: {e}")
        return False

def main():
    """Run all public contract checks."""
    print("Checking public API contracts...\n")
    
    checks = [
        check_broker_public_interface,
        check_proxy_public_interface,
        check_proxypool_public_interface,
        check_server_public_interface,
        check_exception_hierarchy,
        check_proxy_creation_api,
        check_exported_symbols,
    ]
    
    passed = 0
    failed = 0
    
    for check in checks:
        try:
            if check():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {check.__name__} failed with exception: {e}")
            failed += 1
        print()  # Add spacing between checks
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All public API contracts are stable!")
        return 0
    else:
        print("❌ Some public API contracts are broken!")
        return 1

if __name__ == "__main__":
    sys.exit(main())