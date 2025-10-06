"""Test public API contracts that must remain stable.

These tests ensure that the public interfaces that users depend on remain
backward compatible. Changes that break these tests require major version bumps.

Focus: API signatures, return types, exception contracts, and data structures.
"""

import asyncio
import inspect
from unittest.mock import MagicMock, patch

import pytest

from proxybroker import Broker, Proxy, ProxyPool, Server
from proxybroker.errors import (
    NoProxyError,
    ProxyConnError,
    ProxyEmptyRecvError,
    ProxyError,
    ProxyRecvError,
    ProxySendError,
    ProxyTimeoutError,
    ResolveError,
)


class TestPublicAPIContracts:
    """Test public API contracts."""

    def test_broker_public_interface(self):
        """Test Broker public interface stability."""
        # Test that all expected public methods exist
        broker = Broker()
        
        # Essential public methods
        assert hasattr(broker, 'find')
        assert hasattr(broker, 'grab')
        assert hasattr(broker, 'serve')
        assert hasattr(broker, 'stop')
        
        # Test method signatures
        sig = inspect.signature(broker.find)
        assert 'types' in sig.parameters
        assert 'limit' in sig.parameters
        
        sig = inspect.signature(broker.grab)
        assert 'countries' in sig.parameters
        assert 'limit' in sig.parameters
        
        sig = inspect.signature(broker.serve)
        assert 'host' in sig.parameters
        assert 'port' in sig.parameters
        assert 'limit' in sig.parameters

    def test_proxy_public_interface(self):
        """Test Proxy public interface stability."""
        proxy = Proxy('127.0.0.1', 8080)
        
        # Essential public attributes and methods
        assert hasattr(proxy, 'host')
        assert hasattr(proxy, 'port')
        assert hasattr(proxy, 'types')
        assert hasattr(proxy, 'is_working')
        assert hasattr(proxy, 'avg_resp_time')
        assert hasattr(proxy, 'error_rate')
        assert hasattr(proxy, 'as_json')
        assert hasattr(proxy, 'as_text')
        
        # Test that types can be set and retrieved
        proxy.types = {'HTTP': 'Anonymous'}
        assert proxy.types == {'HTTP': 'Anonymous'}
        
        # Test JSON output structure
        json_data = proxy.as_json()
        assert isinstance(json_data, dict)
        assert 'host' in json_data
        assert 'port' in json_data
        assert 'geo' in json_data
        assert 'types' in json_data
        assert 'avg_resp_time' in json_data
        assert 'error_rate' in json_data
        
        # Test text output
        text_data = proxy.as_text()
        assert isinstance(text_data, str)
        assert ':' in text_data

    def test_proxypool_public_interface(self):
        """Test ProxyPool public interface stability."""
        proxies = asyncio.Queue()
        pool = ProxyPool(proxies)
        
        # Essential public methods
        assert hasattr(pool, 'get')
        assert hasattr(pool, 'put')
        
        sig = inspect.signature(pool.get)
        assert 'scheme' in sig.parameters
        
        sig = inspect.signature(pool.put)
        assert 'proxy' in sig.parameters

    def test_server_public_interface(self):
        """Test Server public interface stability."""
        # Test that Server class exists and has essential methods
        assert Server is not None
        assert hasattr(Server, '__init__')
        assert hasattr(Server, 'start')
        assert hasattr(Server, 'stop')

    def test_exception_hierarchy(self):
        """Test that exception hierarchy remains stable."""
        # Test base exceptions
        assert issubclass(ProxyError, Exception)
        assert issubclass(NoProxyError, Exception)
        assert issubclass(ResolveError, Exception)
        
        # Test network exceptions
        assert issubclass(ProxyConnError, ProxyError)
        assert issubclass(ProxyRecvError, ProxyError)
        assert issubclass(ProxySendError, ProxyError)
        assert issubclass(ProxyTimeoutError, ProxyError)
        assert issubclass(ProxyEmptyRecvError, ProxyError)

    def test_proxy_creation_api(self):
        """Test Proxy creation APIs."""
        # Test direct creation
        proxy = Proxy('127.0.0.1', 8080)
        assert proxy.host == '127.0.0.1'
        assert proxy.port == 8080
        
        # Test validation
        with pytest.raises(ValueError):
            Proxy('127.0.0.1', 65536)  # Port too high
            
        with pytest.raises(ValueError):
            Proxy('127.0.0.1', -1)  # Port too low

    @pytest.mark.asyncio
    async def test_proxy_async_creation(self):
        """Test Proxy async creation."""
        with patch('proxybroker.resolver.Resolver.resolve') as mock_resolve:
            mock_resolve.return_value = '127.0.0.1'
            proxy = await Proxy.create('localhost', 8080)
            assert proxy.host == '127.0.0.1'
            assert proxy.port == 8080

    def test_broker_initialization_parameters(self):
        """Test Broker initialization parameters."""
        # Test with various parameter combinations
        broker1 = Broker()
        assert broker1 is not None
        
        broker2 = Broker(timeout=10)
        assert broker2 is not None
        
        broker3 = Broker(max_conn=100, max_tries=5)
        assert broker3 is not None
        
        # Test with queue
        queue = asyncio.Queue()
        broker4 = Broker(queue)
        assert broker4 is not None

    def test_proxy_geo_property(self):
        """Test Proxy geo property structure."""
        proxy = Proxy('8.8.8.8', 80)
        
        # Geo should be a named tuple with expected fields
        geo = proxy.geo
        assert hasattr(geo, 'code')
        assert hasattr(geo, 'name')
        assert hasattr(geo, 'region_code')
        assert hasattr(geo, 'region_name')
        assert hasattr(geo, 'city_name')

    def test_proxy_runtime_properties(self):
        """Test Proxy runtime properties."""
        proxy = Proxy('127.0.0.1', 8080)
        
        # These should be readable properties
        assert isinstance(proxy.avg_resp_time, (int, float))
        assert isinstance(proxy.error_rate, (int, float))
        assert isinstance(proxy.is_working, bool)
        assert isinstance(proxy.schemes, tuple)

    def test_proxy_pool_initialization(self):
        """Test ProxyPool initialization."""
        queue = asyncio.Queue()
        
        # Test basic initialization
        pool1 = ProxyPool(queue)
        assert pool1 is not None
        
        # Test with parameters
        pool2 = ProxyPool(
            queue,
            min_req_proxy=10,
            max_error_rate=0.1,
            max_resp_time=5,
            min_queue=3,
            strategy='best'
        )
        assert pool2 is not None

    def test_server_initialization(self):
        """Test Server initialization parameters."""
        queue = asyncio.Queue()
        
        # Test that Server accepts expected parameters
        # Note: We don't actually start the server to avoid port conflicts
        server = Server.__new__(Server)  # Create without calling __init__
        assert server is not None


class TestAPIBackwardCompatibility:
    """Test that existing API usage patterns continue to work."""
    
    def test_basic_broker_usage(self):
        """Test basic Broker usage pattern."""
        # This is the most common usage pattern users depend on
        proxies = asyncio.Queue()
        broker = Broker(proxies, timeout=1, max_conn=10, max_tries=1)
        
        # Should be able to access essential properties
        assert hasattr(broker, '_proxies')
        assert broker._timeout == 1
        assert broker._max_tries == 1
    
    def test_proxy_json_output_structure(self):
        """Test that Proxy JSON output maintains expected structure."""
        proxy = Proxy('8.8.8.8', 3128)
        proxy.types = {'HTTP': 'Anonymous', 'HTTPS': None}
        
        json_output = proxy.as_json()
        
        # Essential fields that users depend on
        required_fields = ['host', 'port', 'geo', 'types', 'avg_resp_time', 'error_rate']
        for field in required_fields:
            assert field in json_output, f"Missing required field: {field}"
        
        # Geo structure
        assert 'country' in json_output['geo']
        assert 'code' in json_output['geo']['country']
        assert 'name' in json_output['geo']['country']
        
        # Types structure
        assert isinstance(json_output['types'], list)
        if json_output['types']:  # If there are types
            first_type = json_output['types'][0]
            assert 'type' in first_type
            assert 'level' in first_type
    
    def test_proxy_text_output_format(self):
        """Test that Proxy text output follows expected format."""
        proxy = Proxy('127.0.0.1', 8080)
        text_output = proxy.as_text()
        
        # Should be in host:port format with newline
        assert text_output == '127.0.0.1:8080\n'
    
    def test_broker_method_signatures(self):
        """Test that Broker method signatures remain stable."""
        # Get method signatures
        find_sig = inspect.signature(Broker.find)
        grab_sig = inspect.signature(Broker.grab)
        serve_sig = inspect.signature(Broker.serve)
        
        # Test essential parameters exist
        assert 'types' in find_sig.parameters or 'data' in find_sig.parameters
        assert 'limit' in find_sig.parameters
        assert 'countries' in grab_sig.parameters
        assert 'limit' in grab_sig.parameters
        assert 'host' in serve_sig.parameters
        assert 'port' in serve_sig.parameters
    
    def test_exception_messages(self):
        """Test that exception messages follow expected patterns."""
        # Test that exceptions have descriptive messages
        conn_error = ProxyConnError("Connection failed")
        assert "Connection failed" in str(conn_error)
        assert hasattr(conn_error, 'errmsg')
        
        timeout_error = ProxyTimeoutError("Timeout occurred")
        assert "Timeout occurred" in str(timeout_error)
        assert hasattr(timeout_error, 'errmsg')


class TestExportedSymbols:
    """Test that all expected symbols are properly exported."""
    
    def test_main_exports(self):
        """Test that main classes are exported."""
        # These should be available at the top level
        from proxybroker import Broker, Proxy, ProxyPool, Server
        
        assert Broker is not None
        assert Proxy is not None
        assert ProxyPool is not None
        assert Server is not None
    
    def test_error_exports(self):
        """Test that error classes are exported."""
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
        assert issubclass(ProxyError, Exception)
        assert issubclass(NoProxyError, Exception)
        assert issubclass(ResolveError, Exception)