"""
ProxyBroker2 Integration for XVPN
================================

This module integrates ProxyBroker2 functionality into the XVPN project,
providing proxy discovery and management capabilities.

Architecture:
- Server side: Uses ProxyBroker2 to find and validate proxies
- Client side: Receives proxies from server and manages them
- Both sides: Communicate through XVPN's existing infrastructure

Key Features:
- Automatic proxy discovery from multiple sources
- Proxy validation and anonymity checking
- Load balancing across multiple proxies
- Automatic failover when proxies become unavailable
- Integration with XVPN's existing transport system
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

from proxybroker import Broker, Proxy, ProxyPool
from proxybroker.errors import NoProxyError, ProxyError

logger = logging.getLogger(__name__)


class XVPNProxyManager:
    """XVPN Proxy Manager - Integrates ProxyBroker2 with XVPN infrastructure."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize XVPN Proxy Manager.
        
        Args:
            config: Configuration dictionary with proxy settings
        """
        self.config = config or {}
        self.broker = None
        self.proxy_pool = None
        self.proxies_queue = None
        self.is_running = False
        
    async def initialize_broker(self) -> None:
        """Initialize ProxyBroker with XVPN configuration."""
        # Create queue for found proxies
        self.proxies_queue = asyncio.Queue()
        
        # Initialize broker with XVPN-specific settings
        broker_config = {
            'timeout': self.config.get('proxy_timeout', 8),
            'max_conn': self.config.get('proxy_max_connections', 200),
            'max_tries': self.config.get('proxy_max_tries', 3),
            'verify_ssl': self.config.get('proxy_verify_ssl', False)
        }
        
        self.broker = Broker(self.proxies_queue, **broker_config)
        logger.info("ProxyBroker initialized with config: %s", broker_config)
        
    async def find_proxies(self, types: List[str] = None, limit: int = 100, 
                          countries: List[str] = None) -> List[Dict]:
        """
        Find and validate proxies with specified criteria.
        
        Args:
            types: List of proxy types (HTTP, HTTPS, SOCKS4, SOCKS5, etc.)
            limit: Maximum number of proxies to find
            countries: List of ISO country codes
            
        Returns:
            List of proxy dictionaries with validation info
        """
        if not self.broker:
            await self.initialize_broker()
            
        # Default proxy types for XVPN
        if not types:
            types = ['HTTP', 'HTTPS', 'SOCKS5']
            
        logger.info("Finding %d %s proxies from countries: %s", 
                   limit, types, countries or 'any')
        
        # Find proxies using ProxyBroker
        try:
            await self.broker.find(
                types=types,
                countries=countries,
                limit=limit
            )
        except Exception as e:
            logger.error("Error finding proxies: %s", e)
            return []
            
        # Collect found proxies
        proxies = []
        while not self.proxies_queue.empty():
            try:
                proxy = self.proxies_queue.get_nowait()
                if proxy and proxy.is_working:
                    proxy_info = {
                        'host': proxy.host,
                        'port': proxy.port,
                        'types': list(proxy.types.keys()),
                        'anonymity_levels': list(proxy.types.values()),
                        'avg_response_time': proxy.avg_resp_time,
                        'error_rate': proxy.error_rate,
                        'country': proxy.geo.code if proxy.geo else 'Unknown',
                        'full_info': proxy.as_json()
                    }
                    proxies.append(proxy_info)
            except asyncio.QueueEmpty:
                break
                
        logger.info("Found %d working proxies", len(proxies))
        return proxies
        
    async def grab_proxies(self, countries: List[str] = None, 
                          limit: int = 100) -> List[Dict]:
        """
        Quickly grab proxies without validation (for speed).
        
        Args:
            countries: List of ISO country codes
            limit: Maximum number of proxies to grab
            
        Returns:
            List of proxy dictionaries (not validated)
        """
        if not self.broker:
            await self.initialize_broker()
            
        logger.info("Grabbing %d proxies without validation", limit)
        
        try:
            await self.broker.grab(
                countries=countries,
                limit=limit
            )
        except Exception as e:
            logger.error("Error grabbing proxies: %s", e)
            return []
            
        # Collect grabbed proxies
        proxies = []
        while not self.proxies_queue.empty():
            try:
                proxy = self.proxies_queue.get_nowait()
                if proxy:
                    proxy_info = {
                        'host': proxy.host,
                        'port': proxy.port,
                        'types': list(proxy.types.keys()) if proxy.types else [],
                        'country': proxy.geo.code if proxy.geo else 'Unknown',
                        'raw_info': proxy.as_json()
                    }
                    proxies.append(proxy_info)
            except asyncio.QueueEmpty:
                break
                
        logger.info("Grabbed %d proxies", len(proxies))
        return proxies
        
    async def start_proxy_server(self, host: str = '127.0.0.1', 
                                port: int = 8888, limit: int = 100) -> None:
        """
        Start local proxy server that distributes requests to external proxies.
        
        Args:
            host: Host to bind the proxy server to
            port: Port to bind the proxy server to
            limit: Maximum number of proxies to use
        """
        if not self.broker:
            await self.initialize_broker()
            
        logger.info("Starting proxy server on %s:%d with %d proxies", 
                   host, port, limit)
        
        # Configure server settings
        server_config = {
            'host': host,
            'port': port,
            'limit': limit,
            'min_queue': self.config.get('proxy_min_queue', 5),
            'strategy': self.config.get('proxy_strategy', 'best'),
            'min_req_proxy': self.config.get('proxy_min_requests', 5),
            'max_error_rate': self.config.get('proxy_max_error_rate', 0.5),
            'max_resp_time': self.config.get('proxy_max_response_time', 8),
            'prefer_connect': self.config.get('proxy_prefer_connect', False),
            'http_allowed_codes': self.config.get('proxy_http_codes', [200]),
            'backlog': self.config.get('proxy_backlog', 100)
        }
        
        try:
            # This will start the server and begin finding proxies
            self.broker.serve(**server_config)
            self.is_running = True
            logger.info("Proxy server started successfully")
        except Exception as e:
            logger.error("Error starting proxy server: %s", e)
            raise
            
    def stop_proxy_server(self) -> None:
        """Stop the proxy server."""
        if self.broker and self.is_running:
            try:
                self.broker.stop()
                self.is_running = False
                logger.info("Proxy server stopped")
            except Exception as e:
                logger.error("Error stopping proxy server: %s", e)
                
    async def get_best_proxy(self, scheme: str = 'http') -> Optional[Dict]:
        """
        Get the best available proxy for the specified scheme.
        
        Args:
            scheme: Protocol scheme (http, https, socks5, etc.)
            
        Returns:
            Proxy dictionary or None if no proxies available
        """
        if not self.proxy_pool and not self.proxies_queue:
            logger.warning("No proxy pool initialized")
            return None
            
        # If we have a ProxyPool, use it to get the best proxy
        if self.proxy_pool:
            try:
                proxy = await self.proxy_pool.get(scheme=scheme.lower())
                if proxy:
                    return {
                        'host': proxy.host,
                        'port': proxy.port,
                        'types': list(proxy.types.keys()),
                        'anonymity_levels': list(proxy.types.values()),
                        'avg_response_time': proxy.avg_resp_time,
                        'error_rate': proxy.error_rate
                    }
            except NoProxyError:
                logger.warning("No proxies available in pool")
                return None
            except Exception as e:
                logger.error("Error getting proxy from pool: %s", e)
                return None
                
        # If we only have a queue, get proxy from queue
        if self.proxies_queue and not self.proxies_queue.empty():
            try:
                proxy = self.proxies_queue.get_nowait()
                if proxy and proxy.is_working:
                    return {
                        'host': proxy.host,
                        'port': proxy.port,
                        'types': list(proxy.types.keys()),
                        'anonymity_levels': list(proxy.types.values()),
                        'avg_response_time': proxy.avg_resp_time,
                        'error_rate': proxy.error_rate
                    }
            except asyncio.QueueEmpty:
                pass
                
        logger.warning("No working proxies available")
        return None
        
    async def validate_proxy(self, host: str, port: int, 
                            proxy_type: str = 'HTTP') -> bool:
        """
        Validate a specific proxy.
        
        Args:
            host: Proxy host
            port: Proxy port
            proxy_type: Type of proxy to validate
            
        Returns:
            True if proxy is working, False otherwise
        """
        try:
            # Create a proxy object
            proxy = Proxy(host, port)
            
            # Create checker with appropriate settings
            from proxybroker.checker import Checker
            
            checker = Checker(
                judges=[],  # Use default judges
                timeout=self.config.get('proxy_timeout', 8),
                max_tries=self.config.get('proxy_max_tries', 3),
                verify_ssl=self.config.get('proxy_verify_ssl', False)
            )
            
            # Check the proxy
            result = await checker.check(proxy)
            return result
            
        except Exception as e:
            logger.error("Error validating proxy %s:%d: %s", host, port, e)
            return False
            
    def get_statistics(self) -> Dict:
        """
        Get proxy statistics.
        
        Returns:
            Dictionary with proxy statistics
        """
        stats = {
            'total_proxies_found': 0,
            'working_proxies': 0,
            'average_response_time': 0,
            'error_rate': 0,
            'proxy_types_distribution': {},
            'countries_distribution': {}
        }
        
        if self.proxies_queue:
            # Collect statistics from queue
            proxies_count = 0
            total_resp_time = 0
            total_errors = 0
            
            # Note: We can't iterate through queue without consuming items
            # In a real implementation, we would maintain separate statistics
            
        return stats


# Convenience functions for XVPN integration
async def create_proxy_manager(config: Dict = None) -> XVPNProxyManager:
    """
    Create and initialize XVPN Proxy Manager.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized XVPNProxyManager instance
    """
    manager = XVPNProxyManager(config)
    await manager.initialize_broker()
    return manager


async def find_vpn_proxies(manager: XVPNProxyManager, 
                          limit: int = 50) -> List[Dict]:
    """
    Find proxies suitable for VPN bypass.
    
    Args:
        manager: XVPNProxyManager instance
        limit: Maximum number of proxies to find
        
    Returns:
        List of suitable proxies
    """
    # Focus on HTTP/HTTPS/SOCKS proxies that are good for bypassing restrictions
    proxy_types = [
        'HTTP', 
        'HTTPS', 
        'SOCKS5',
        'CONNECT:80',  # HTTP CONNECT method
        'CONNECT:25'   # SMTP CONNECT method
    ]
    
    return await manager.find_proxies(types=proxy_types, limit=limit)


async def start_xvpn_proxy_service(manager: XVPNProxyManager,
                                   host: str = '127.0.0.1',
                                   port: int = 8888) -> None:
    """
    Start XVPN proxy service for clients.
    
    Args:
        manager: XVPNProxyManager instance
        host: Host to bind the service to
        port: Port to bind the service to
    """
    await manager.start_proxy_server(host=host, port=port, limit=100)


# Example usage
async def example_usage():
    """Example of how to use XVPN Proxy Manager."""
    # Create manager with custom configuration
    config = {
        'proxy_timeout': 10,
        'proxy_max_tries': 3,
        'proxy_verify_ssl': False
    }
    
    manager = await create_proxy_manager(config)
    
    # Find some proxies
    print("Finding proxies...")
    proxies = await find_vpn_proxies(manager, limit=10)
    print(f"Found {len(proxies)} proxies")
    
    # Print first few proxies
    for proxy in proxies[:3]:
        print(f"Proxy: {proxy['host']}:{proxy['port']} - {proxy['types']}")
    
    # Get the best proxy
    best_proxy = await manager.get_best_proxy('http')
    if best_proxy:
        print(f"Best proxy: {best_proxy['host']}:{best_proxy['port']}")
    
    # Start proxy server
    print("Starting proxy server...")
    try:
        await start_xvpn_proxy_service(manager, '127.0.0.1', 8888)
        print("Proxy server started on 127.0.0.1:8888")
    except Exception as e:
        print(f"Failed to start proxy server: {e}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())