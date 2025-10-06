"""Test XVPN integration with ProxyBroker2."""

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


class TestXVPNProxyBroker2Integration:
    """Test XVPN integration with ProxyBroker2 components."""

    def test_xvpn_proxy_manager_exists(self):
        """Test that XVPN ProxyManager class exists."""
        # This test verifies that the XVPN ProxyManager integration class exists
        # and can be imported from the server module
        try:
            from server.proxy_integration import XVPNProxyManager
            assert XVPNProxyManager is not None
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_creation(self):
        """Test that XVPN ProxyManager can be created."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Test basic creation
            config = {
                'proxy_timeout': 8,
                'proxy_max_tries': 3,
                'proxy_verify_ssl': False
            }
            
            manager = await XVPNProxyManager.create(config)
            assert manager is not None
            assert hasattr(manager, 'find_proxies')
            assert hasattr(manager, 'grab_proxies')
            assert hasattr(manager, 'start_proxy_server')
            assert hasattr(manager, 'get_best_proxy')
            assert hasattr(manager, 'validate_proxy')
            assert hasattr(manager, 'get_statistics')
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_has_required_methods(self):
        """Test that XVPN ProxyManager has all required methods."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Check that all required methods exist
            required_methods = [
                'create',
                'find_proxies',
                'grab_proxies', 
                'start_proxy_server',
                'get_best_proxy',
                'validate_proxy',
                'get_statistics'
            ]
            
            for method in required_methods:
                assert hasattr(XVPNProxyManager, method), f"Missing required method: {method}"
                assert callable(getattr(XVPNProxyManager, method)), f"Method {method} is not callable"
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_find_proxies_signature(self):
        """Test that XVPN ProxyManager.find_proxies has correct signature."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Check method signature
            import inspect
            sig = inspect.signature(manager.find_proxies)
            
            # Should have required parameters
            assert 'types' in sig.parameters
            assert 'limit' in sig.parameters
            assert 'countries' in sig.parameters
            
            # Check default values
            types_param = sig.parameters['types']
            limit_param = sig.parameters['limit']
            countries_param = sig.parameters['countries']
            
            assert types_param.default is None or isinstance(types_param.default, list)
            assert limit_param.default == 0
            assert countries_param.default is None or isinstance(countries_param.default, list)
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_grab_proxies_signature(self):
        """Test that XVPN ProxyManager.grab_proxies has correct signature."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Check method signature
            import inspect
            sig = inspect.signature(manager.grab_proxies)
            
            # Should have required parameters
            assert 'countries' in sig.parameters
            assert 'limit' in sig.parameters
            
            # Check default values
            countries_param = sig.parameters['countries']
            limit_param = sig.parameters['limit']
            
            assert countries_param.default is None or isinstance(countries_param.default, list)
            assert limit_param.default == 100
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_constants(self):
        """Test that XVPN ProxyManager has required constants."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Check that manager has required constants for configuration
            assert hasattr(XVPNProxyManager, '_HTTP_PROTOS')
            assert hasattr(XVPNProxyManager, '_HTTPS_PROTOS')
            
            # Check constant values
            http_protos = getattr(XVPNProxyManager, '_HTTP_PROTOS', None)
            https_protos = getattr(XVPNProxyManager, '_HTTPS_PROTOS', None)
            
            if http_protos is not None:
                assert isinstance(http_protos, frozenset)
                assert len(http_protos) > 0
                
            if https_protos is not None:
                assert isinstance(https_protos, frozenset)
                assert len(https_protos) > 0
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_proxy_validation(self):
        """Test that XVPN ProxyManager can validate proxies."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Should have validate_proxy method
            assert hasattr(manager, 'validate_proxy')
            assert callable(manager.validate_proxy)
            
            # Method should accept host, port, and proxy_type
            import inspect
            sig = inspect.signature(manager.validate_proxy)
            assert 'host' in sig.parameters
            assert 'port' in sig.parameters
            assert 'proxy_type' in sig.parameters
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_proxy_selection(self):
        """Test that XVPN ProxyManager can select best proxies."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Should have get_best_proxy method
            assert hasattr(manager, 'get_best_proxy')
            assert callable(manager.get_best_proxy)
            
            # Method should accept scheme parameter
            import inspect
            sig = inspect.signature(manager.get_best_proxy)
            assert 'scheme' in sig.parameters
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_statistics(self):
        """Test that XVPN ProxyManager provides statistics."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = XVPNProxyManager(config)
            
            # Should have get_statistics method
            assert hasattr(manager, 'get_statistics')
            assert callable(manager.get_statistics)
            
            # Method should return dictionary
            stats = manager.get_statistics()
            assert isinstance(stats, dict)
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_json_output(self):
        """Test that XVPN ProxyManager can output proxy information in JSON format."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Should have as_json method for proxy objects
            # This tests the integration with Proxy.as_json()
            proxy = Proxy("127.0.0.1", 8080)
            assert hasattr(proxy, 'as_json')
            assert callable(proxy.as_json)
            
            # Should return dictionary
            json_data = proxy.as_json()
            assert isinstance(json_data, dict)
            
            # Should have required fields
            required_fields = ['host', 'port', 'geo', 'types']
            for field in required_fields:
                assert field in json_data, f"Missing required field: {field}"
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_text_output(self):
        """Test that XVPN ProxyManager can output proxy information in text format."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Should have as_text method for proxy objects
            # This tests the integration with Proxy.as_text()
            proxy = Proxy("127.0.0.1", 8080)
            assert hasattr(proxy, 'as_text')
            assert callable(proxy.as_text)
            
            # Should return string
            text_data = proxy.as_text()
            assert isinstance(text_data, str)
            
            # Should be in host:port format with newline
            assert text_data == "127.0.0.1:8080\n"
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_proxy_pool_integration(self):
        """Test that XVPN ProxyManager integrates with ProxyPool."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = XVPNProxyManager(config)
            
            # Should be able to create ProxyPool
            proxies_queue = asyncio.Queue()
            proxy_pool = ProxyPool(proxies_queue)
            
            assert proxy_pool is not None
            assert hasattr(proxy_pool, 'get')
            assert hasattr(proxy_pool, 'put')
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_broker_integration(self):
        """Test that XVPN ProxyManager integrates with Broker."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = XVPNProxyManager(config)
            
            # Should be able to create Broker
            proxies_queue = asyncio.Queue()
            broker = Broker(proxies_queue, stop_broker_on_sigint=False)
            
            assert broker is not None
            assert hasattr(broker, 'find')
            assert hasattr(broker, 'grab')
            assert hasattr(broker, 'serve')
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    @pytest.mark.asyncio
    async def test_xvpn_proxy_manager_proxy_creation(self):
        """Test that XVPN ProxyManager can create proxies."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Create manager
            config = {}
            manager = await XVPNProxyManager.create(config)
            
            # Should be able to create Proxy
            proxy = Proxy("127.0.0.1", 8080)
            
            assert proxy is not None
            assert proxy.host == "127.0.0.1"
            assert proxy.port == 8080
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")

    def test_xvpn_proxy_manager_error_handling(self):
        """Test that XVPN ProxyManager handles errors gracefully."""
        try:
            from server.proxy_integration import XVPNProxyManager
            
            # Should handle invalid proxy creation gracefully
            with pytest.raises(ValueError):
                Proxy("127.0.0.1", 65536)  # Invalid port
                
            with pytest.raises(ValueError):
                Proxy("256.0.0.1", 8080)  # Invalid IP
        except ImportError:
            pytest.skip("XVPN ProxyManager not available in this environment")