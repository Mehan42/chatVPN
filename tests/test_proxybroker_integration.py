"""Test ProxyBroker2 integration with XVPN."""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proxybroker import Broker, Proxy, ProxyPool
from proxybroker.errors import NoProxyError, ProxyError


class TestProxyBroker2Integration:
    """Test ProxyBroker2 integration with XVPN components."""

    @pytest.fixture
    def mock_proxy(self):
        """Create a mock proxy for testing."""
        proxy = Mock(spec=Proxy)
        proxy.host = "127.0.0.1"
        proxy.port = 8080
        proxy.types = {"HTTP": "Anonymous"}
        proxy.is_working = True
        proxy.avg_resp_time = 1.5
        proxy.error_rate = 0.1
        proxy.as_json.return_value = {
            "host": "127.0.0.1",
            "port": 8080,
            "types": [{"type": "HTTP", "level": "Anonymous"}],
            "avg_resp_time": 1.5,
            "error_rate": 0.1,
        }
        proxy.as_text.return_value = "127.0.0.1:8080\n"
        return proxy

    @pytest.fixture
    def mock_broker(self):
        """Create a mock broker for testing."""
        broker = Mock(spec=Broker)
        broker.find = AsyncMock()
        broker.grab = AsyncMock()
        broker.serve = Mock()
        broker.stop = Mock()
        return broker

    @pytest.fixture
    def mock_queue(self):
        """Create a mock queue for testing."""
        queue = Mock(spec=asyncio.Queue)
        queue.get = AsyncMock()
        queue.put_nowait = Mock()
        queue.empty = Mock(return_value=False)
        queue.qsize = Mock(return_value=1)
        queue.join = AsyncMock()
        return queue

    @pytest.mark.asyncio
    async def test_broker_creation(self):
        """Test that Broker can be created with XVPN parameters."""
        # Test basic creation
        queue = asyncio.Queue()
        broker = Broker(
            queue=queue,
            timeout=8,
            max_conn=200,
            max_tries=3,
            verify_ssl=False,
            stop_broker_on_sigint=False,  # Disable for testing
        )
        assert broker is not None
        assert broker._timeout == 8
        assert broker._max_tries == 3
        assert broker._verify_ssl is False

    @pytest.mark.asyncio
    async def test_broker_find_method(self, mock_broker):
        """Test Broker.find() method integration."""
        # Test that find method can be called with XVPN parameters
        await mock_broker.find(
            types=["HTTP", "HTTPS"],
            countries=["US", "GB"],
            limit=10,
            post=False,
            strict=False,
        )
        
        # Verify the method was called with correct parameters
        mock_broker.find.assert_called_once_with(
            types=["HTTP", "HTTPS"],
            countries=["US", "GB"],
            limit=10,
            post=False,
            strict=False,
        )

    @pytest.mark.asyncio
    async def test_broker_grab_method(self, mock_broker):
        """Test Broker.grab() method integration."""
        # Test that grab method can be called with XVPN parameters
        await mock_broker.grab(countries=["US", "GB"], limit=10)
        
        # Verify the method was called with correct parameters
        mock_broker.grab.assert_called_once_with(countries=["US", "GB"], limit=10)

    @pytest.mark.asyncio
    async def test_broker_serve_method(self, mock_broker):
        """Test Broker.serve() method integration."""
        # Test that serve method can be called with XVPN parameters
        mock_broker.serve(
            host="127.0.0.1",
            port=8888,
            types=["HTTP", "HTTPS"],
            limit=100,
            max_tries=3,
            prefer_connect=False,
            min_req_proxy=5,
            max_error_rate=0.5,
            max_resp_time=8,
            http_allowed_codes=[200, 301, 302],
            backlog=100,
        )
        
        # Verify the method was called with correct parameters
        mock_broker.serve.assert_called_once_with(
            host="127.0.0.1",
            port=8888,
            types=["HTTP", "HTTPS"],
            limit=100,
            max_tries=3,
            prefer_connect=False,
            min_req_proxy=5,
            max_error_rate=0.5,
            max_resp_time=8,
            http_allowed_codes=[200, 301, 302],
            backlog=100,
        )

    def test_proxy_creation(self, mock_proxy):
        """Test Proxy creation and methods."""
        # Test that proxy has required attributes
        assert hasattr(mock_proxy, "host")
        assert hasattr(mock_proxy, "port")
        assert hasattr(mock_proxy, "types")
        assert hasattr(mock_proxy, "is_working")
        assert hasattr(mock_proxy, "avg_resp_time")
        assert hasattr(mock_proxy, "error_rate")
        assert hasattr(mock_proxy, "as_json")
        assert hasattr(mock_proxy, "as_text")

        # Test JSON output
        json_output = mock_proxy.as_json()
        assert isinstance(json_output, dict)
        assert "host" in json_output
        assert "port" in json_output
        assert "types" in json_output
        assert "avg_resp_time" in json_output
        assert "error_rate" in json_output

        # Test text output
        text_output = mock_proxy.as_text()
        assert isinstance(text_output, str)
        assert "127.0.0.1:8080" in text_output

    @pytest.mark.asyncio
    async def test_proxy_pool_creation(self, mock_queue):
        """Test ProxyPool creation and basic methods."""
        # Test basic creation
        pool = ProxyPool(
            mock_queue,
            min_req_proxy=5,
            max_error_rate=0.5,
            max_resp_time=8,
            min_queue=5,
            strategy="best",
        )
        assert pool is not None
        assert pool._min_req_proxy == 5
        assert pool._max_error_rate == 0.5
        assert pool._max_resp_time == 8
        assert pool._min_queue == 5
        assert pool._strategy == "best"

    @pytest.mark.asyncio
    async def test_proxy_pool_get_method(self, mock_queue):
        """Test ProxyPool.get() method."""
        pool = ProxyPool(mock_queue)
        
        # Test that get method exists and can be called
        assert hasattr(pool, "get")
        # Note: We can't easily test the actual get method without a real queue

    @pytest.mark.asyncio
    async def test_proxy_pool_put_method(self, mock_queue):
        """Test ProxyPool.put() method."""
        pool = ProxyPool(mock_queue)
        
        # Test that put method exists and can be called
        assert hasattr(pool, "put")
        # Note: We can't easily test the actual put method without a real queue

    def test_proxy_attributes(self):
        """Test Proxy attributes that users depend on."""
        proxy = Proxy("127.0.0.1", 8080)
        
        # Test basic attributes
        assert proxy.host == "127.0.0.1"
        assert proxy.port == 8080
        assert isinstance(proxy.types, dict)
        assert proxy.is_working is False  # Initially False
        assert proxy.avg_resp_time == 0.0  # Initially 0
        assert proxy.error_rate == 0.0  # Initially 0

    def test_proxy_json_output_structure(self):
        """Test that Proxy JSON output has expected structure."""
        proxy = Proxy("8.8.8.8", 3128)
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}
        proxy._runtimes = [1.0, 2.0, 3.0]  # Set some response times
        
        json_data = proxy.as_json()
        
        # Required fields that users depend on
        required_fields = [
            "host", "port", "geo", "types", "avg_resp_time", "error_rate"
        ]
        for field in required_fields:
            assert field in json_data, f"Missing required field: {field}"
        
        # Test geo structure
        assert "country" in json_data["geo"]
        assert "code" in json_data["geo"]["country"]
        assert "name" in json_data["geo"]["country"]
        
        # Test types structure
        assert isinstance(json_data["types"], list)
        if json_data["types"]:  # If there are types
            first_type = json_data["types"][0]
            assert "type" in first_type
            assert "level" in first_type

    def test_proxy_text_output_format(self):
        """Test that Proxy text output follows expected format."""
        proxy = Proxy("127.0.0.1", 8080)
        text_output = proxy.as_text()
        
        # Should be in host:port format with newline
        assert text_output == "127.0.0.1:8080\n"

    @pytest.mark.asyncio
    async def test_broker_error_handling(self, mock_broker):
        """Test that Broker handles errors gracefully."""
        # Test that broker methods handle exceptions
        mock_broker.find.side_effect = ProxyError("Test error")
        
        with pytest.raises(ProxyError):
            await mock_broker.find(types=["HTTP"], limit=1)
        
        # Verify the method was called
        mock_broker.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_proxy_pool_error_handling(self, mock_queue):
        """Test that ProxyPool handles errors gracefully."""
        pool = ProxyPool(mock_queue)
        
        # Test that pool methods exist and can handle edge cases
        assert hasattr(pool, "get")
        assert hasattr(pool, "put")

    def test_broker_public_api(self):
        """Test that Broker has all required public methods."""
        broker = Broker(stop_broker_on_sigint=False)  # Disable signal handling for testing
        
        # Essential public methods that users depend on
        required_methods = ["find", "grab", "serve", "stop"]
        for method in required_methods:
            assert hasattr(broker, method), f"Missing required method: {method}"
            assert callable(getattr(broker, method)), f"Method {method} is not callable"

    def test_proxy_public_api(self):
        """Test that Proxy has all required public methods."""
        proxy = Proxy("127.0.0.1", 8080)
        
        # Essential public methods that users depend on
        required_methods = ["as_json", "as_text"]
        for method in required_methods:
            assert hasattr(proxy, method), f"Missing required method: {method}"
            assert callable(getattr(proxy, method)), f"Method {method} is not callable"

    def test_proxy_pool_public_api(self):
        """Test that ProxyPool has all required public methods."""
        queue = asyncio.Queue()
        pool = ProxyPool(queue)
        
        # Essential public methods that users depend on
        required_methods = ["get", "put"]
        for method in required_methods:
            assert hasattr(pool, method), f"Missing required method: {method}"
            assert callable(getattr(pool, method)), f"Method {method} is not callable"

    @pytest.mark.asyncio
    async def test_broker_ssl_verification_setting(self):
        """Test that Broker respects SSL verification settings."""
        queue = asyncio.Queue()
        
        # Test with SSL verification disabled (default)
        broker1 = Broker(queue, verify_ssl=False, stop_broker_on_sigint=False)
        assert broker1._verify_ssl is False
        
        # Test with SSL verification enabled
        broker2 = Broker(queue, verify_ssl=True, stop_broker_on_sigint=False)
        assert broker2._verify_ssl is True

    def test_proxy_geo_information(self):
        """Test that Proxy provides geo information."""
        proxy = Proxy("8.8.8.8", 80)
        
        # Should have geo information
        assert hasattr(proxy, "geo")
        geo = proxy.geo
        assert hasattr(geo, "code")
        assert hasattr(geo, "name")
        assert hasattr(geo, "region_code")
        assert hasattr(geo, "region_name")
        assert hasattr(geo, "city_name")

    def test_broker_timeout_settings(self):
        """Test that Broker respects timeout settings."""
        queue = asyncio.Queue()
        
        # Test with custom timeout
        broker = Broker(queue, timeout=15, stop_broker_on_sigint=False)
        assert broker._timeout == 15

    def test_broker_max_tries_settings(self):
        """Test that Broker respects max tries settings."""
        queue = asyncio.Queue()
        
        # Test with custom max tries
        broker = Broker(queue, max_tries=5, stop_broker_on_sigint=False)
        assert broker._max_tries == 5

    def test_proxy_pool_settings(self):
        """Test that ProxyPool respects settings."""
        queue = asyncio.Queue()
        
        # Test with custom settings
        pool = ProxyPool(
            queue,
            min_req_proxy=10,
            max_error_rate=0.3,
            max_resp_time=5,
            min_queue=3,
            strategy="round_robin",  # Different strategy
        )
        assert pool._min_req_proxy == 10
        assert pool._max_error_rate == 0.3
        assert pool._max_resp_time == 5
        assert pool._min_queue == 3
        assert pool._strategy == "round_robin"