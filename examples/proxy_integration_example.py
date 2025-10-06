#!/usr/bin/env python3
"""
XVPN Proxy Integration Examples
===============================

This script demonstrates various ways to use ProxyBroker2 integration
with the XVPN project.

Examples:
1. Basic proxy discovery
2. Proxy server mode
3. Quick proxy grabbing
4. XVPN-specific proxy finding
5. Proxy validation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from server.proxy_integration import XVPNProxyManager, create_proxy_manager
    HAS_PROXYBROKER = True
except ImportError:
    print("ProxyBroker2 not available. Install with: pip install git+https://github.com/bluet/proxybroker2.git")
    HAS_PROXYBROKER = False


async def example_basic_discovery():
    """Example: Basic proxy discovery."""
    if not HAS_PROXYBROKER:
        print("Skipping - ProxyBroker2 not available")
        return
        
    print("=== Basic Proxy Discovery ===")
    
    # Create proxy manager
    config = {
        'proxy_timeout': 8,
        'proxy_max_tries': 3,
        'proxy_verify_ssl': False
    }
    
    manager = await create_proxy_manager(config)
    
    # Find HTTP/HTTPS proxies
    print("Finding 10 HTTP/HTTPS proxies...")
    proxies = await manager.find_proxies(
        types=['HTTP', 'HTTPS'],
        limit=10
    )
    
    print(f"Found {len(proxies)} working proxies")
    
    # Display proxy information
    for i, proxy in enumerate(proxies[:3]):  # Show first 3
        print(f"\nProxy #{i+1}:")
        print(f"  Host: {proxy['host']}")
        print(f"  Port: {proxy['port']}")
        print(f"  Types: {', '.join(proxy['types'])}")
        print(f"  Country: {proxy.get('country', 'Unknown')}")
        print(f"  Avg Response Time: {proxy.get('avg_response_time', 0):.2f}s")
        print(f"  Error Rate: {proxy.get('error_rate', 0):.2%}")
    
    print()


async def example_quick_grab():
    """Example: Quick proxy grabbing."""
    if not HAS_PROXYBROKER:
        print("Skipping - ProxyBroker2 not available")
        return
        
    print("=== Quick Proxy Grabbing ===")
    
    # Create proxy manager
    manager = await create_proxy_manager({})
    
    # Quickly grab proxies without validation
    print("Grabbing 20 proxies without validation...")
    proxies = await manager.grab_proxies(limit=20)
    
    print(f"Grabbed {len(proxies)} proxies (not validated)")
    
    # Display first few grabbed proxies
    for i, proxy in enumerate(proxies[:5]):  # Show first 5
        print(f"  {i+1}. {proxy['host']}:{proxy['port']} ({', '.join(proxy.get('types', ['Unknown']))})")
    
    print()


async def example_xvpn_specific():
    """Example: XVPN-specific proxy finding."""
    if not HAS_PROXYBROKER:
        print("Skipping - ProxyBroker2 not available")
        return
        
    print("=== XVPN-Specific Proxy Finding ===")
    
    # Create proxy manager with XVPN preferences
    config = {
        'proxy_timeout': 10,
        'proxy_max_tries': 3,
        'proxy_verify_ssl': False,
        'proxy_max_response_time': 8,
        'proxy_max_error_rate': 0.5
    }
    
    manager = await create_proxy_manager(config)
    
    # Find proxies suitable for VPN bypass
    print("Finding 15 proxies suitable for VPN bypass...")
    proxy_types = [
        'HTTP',
        'HTTPS', 
        'SOCKS5',
        'CONNECT:80',   # HTTP CONNECT
        'CONNECT:25'    # SMTP CONNECT
    ]
    
    proxies = await manager.find_proxies(
        types=proxy_types,
        limit=15,
        countries=['US', 'GB', 'DE', 'JP', 'CA', 'AU']  # Prefer stable countries
    )
    
    print(f"Found {len(proxies)} VPN-bypass proxies")
    
    # Categorize by type
    by_type = {}
    for proxy in proxies:
        for proxy_type in proxy['types']:
            if proxy_type not in by_type:
                by_type[proxy_type] = []
            by_type[proxy_type].append(proxy)
    
    # Display categorized results
    for proxy_type, proxy_list in by_type.items():
        print(f"\n{proxy_type} proxies ({len(proxy_list)}):")
        for proxy in proxy_list[:3]:  # Show first 3 of each type
            print(f"  {proxy['host']}:{proxy['port']} - {proxy.get('country', 'Unknown')}")
    
    print()


async def example_proxy_validation():
    """Example: Individual proxy validation."""
    if not HAS_PROXYBROKER:
        print("Skipping - ProxyBroker2 not available")
        return
        
    print("=== Individual Proxy Validation ===")
    
    # Create proxy manager
    manager = await create_proxy_manager({})
    
    # Test some well-known public proxies (these may not work)
    test_proxies = [
        {'host': '127.0.0.1', 'port': 8080, 'type': 'HTTP'},
        {'host': 'localhost', 'port': 3128, 'type': 'HTTP'},
    ]
    
    print("Validating test proxies...")
    for test_proxy in test_proxies:
        is_valid = await manager.validate_proxy(
            test_proxy['host'],
            test_proxy['port'],
            test_proxy['type']
        )
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {test_proxy['host']}:{test_proxy['port']} - {status}")
    
    print()


async def example_statistics():
    """Example: Getting proxy statistics."""
    if not HAS_PROXYBROKER:
        print("Skipping - ProxyBroker2 not available")
        return
        
    print("=== Proxy Statistics ===")
    
    # Create proxy manager
    manager = await create_proxy_manager({})
    
    # Get statistics
    stats = manager.get_statistics()
    
    print("Current proxy statistics:")
    print(f"  Total proxies found: {stats.get('total_proxies_found', 0)}")
    print(f"  Working proxies: {stats.get('working_proxies', 0)}")
    print(f"  Average response time: {stats.get('average_response_time', 0):.2f}s")
    print(f"  Error rate: {stats.get('error_rate', 0):.2%}")
    
    # Show proxy type distribution
    type_dist = stats.get('proxy_types_distribution', {})
    if type_dist:
        print("\nProxy type distribution:")
        for proxy_type, count in type_dist.items():
            print(f"  {proxy_type}: {count}")
    
    print()


async def main():
    """Run all examples."""
    print("XVPN Proxy Integration Examples")
    print("=" * 40)
    print()
    
    # Run examples
    await example_basic_discovery()
    await example_quick_grab()
    await example_xvpn_specific()
    await example_proxy_validation()
    await example_statistics()
    
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())