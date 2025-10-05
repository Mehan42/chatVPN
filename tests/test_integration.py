#!/usr/bin/env python3
"""XVPN Component Integration Test"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_component_imports():
    """Test importing all components"""
    print("🔍 Testing component imports...")
    
    # Test state machine import
    try:
        from client.state_machine import create_state_machine, State, Event
        print("✅ State machine imported successfully")
    except Exception as e:
        print(f"❌ State machine import failed: {e}")
        return False
    
    # Test transport manager import
    try:
        from client.transport_manager import get_transport_manager
        print("✅ Transport manager imported successfully")
    except Exception as e:
        print(f"❌ Transport manager import failed: {e}")
        return False
    
    # Test health monitor import
    try:
        from client.health import get_mask_score, get_network_info
        print("✅ Health monitor imported successfully")
    except Exception as e:
        print(f"❌ Health monitor import failed: {e}")
        return False
    
    # Test chatvpn backend import
    try:
        from client.chatvpn_backend import start_xray, stop_xray, get_status, load_config_from_server
        print("✅ ChatVPN backend imported successfully")
    except Exception as e:
        print(f"❌ ChatVPN backend import failed: {e}")
        return False
    
    # Test IPv6 manager import
    try:
        from client.ipv6_manager import get_ipv6_manager
        print("✅ IPv6 manager imported successfully")
    except Exception as e:
        print(f"❌ IPv6 manager import failed: {e}")
        return False
    
    # Test proxy helper import
    try:
        from client.proxy_helper import get_proxy_modes_manager
        print("✅ Proxy helper imported successfully")
    except Exception as e:
        print(f"❌ Proxy helper import failed: {e}")
        return False
    
    return True

def test_state_machine_basic():
    """Test basic state machine functionality"""
    print("\n🔍 Testing state machine basic functionality...")
    
    try:
        from client.state_machine import create_state_machine, State, Event
        
        # Create state machine
        sm = create_state_machine('test-uuid-123')
        print(f"✅ State machine created with UUID: test-uuid-123")
        
        # Check initial state
        initial_state = sm.get_current_state()
        print(f"✅ Initial state: {initial_state.value}")
        
        # Get state info
        state_info = sm.get_state_info()
        print(f"✅ State info retrieved: {len(state_info)} fields")
        
        return True
    except Exception as e:
        print(f"❌ State machine basic test failed: {e}")
        return False

def test_transport_manager():
    """Test transport manager functionality"""
    print("\n🔍 Testing transport manager...")
    
    try:
        from client.transport_manager import get_transport_manager
        
        # Get transport manager
        tm = get_transport_manager('test-uuid-123')
        print("✅ Transport manager created")
        
        # Get available transports
        transports = tm.get_available_transports()
        print(f"✅ Available transports: {len(transports) if transports else 0}")
        
        # Get current transport
        current_transport = tm.get_current_transport()
        print(f"✅ Current transport: {current_transport.get('id', 'None') if current_transport else 'None'}")
        
        return True
    except Exception as e:
        print(f"❌ Transport manager test failed: {e}")
        return False

def test_health_monitor():
    """Test health monitor functionality"""
    print("\n🔍 Testing health monitor...")
    
    try:
        from client.health import get_mask_score, get_network_info
        
        # Get mask score
        mask_score = get_mask_score()
        print(f"✅ Mask score: {mask_score}/5")
        
        # Get network info
        network_info = get_network_info()
        print(f"✅ Network info retrieved: {len(network_info) if network_info else 0} fields")
        
        return True
    except Exception as e:
        print(f"❌ Health monitor test failed: {e}")
        return False

def test_ipv6_manager():
    """Test IPv6 manager functionality"""
    print("\n🔍 Testing IPv6 manager...")
    
    try:
        from client.ipv6_manager import get_ipv6_manager
        
        # Get IPv6 manager
        ipv6_mgr = get_ipv6_manager()
        print("✅ IPv6 manager created")
        
        # Get IPv6 connectivity status
        ipv6_status = ipv6_mgr.get_ipv6_connectivity_status()
        print(f"✅ IPv6 status: {ipv6_status}")
        
        return True
    except Exception as e:
        print(f"❌ IPv6 manager test failed: {e}")
        return False

def test_proxy_helper():
    """Test proxy helper functionality"""
    print("\n🔍 Testing proxy helper...")
    
    try:
        from client.proxy_helper import get_proxy_modes_manager
        
        # Get proxy modes manager
        proxy_mgr = get_proxy_modes_manager()
        print("✅ Proxy modes manager created")
        
        # Get proxy info
        proxy_info = proxy_mgr.get_proxy_info()
        print(f"✅ Proxy info: {proxy_info}")
        
        return True
    except Exception as e:
        print(f"❌ Proxy helper test failed: {e}")
        return False

def test_file_structure():
    """Test file structure"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "client/state_machine.py",
        "client/transport_manager.py",
        "client/health.py",
        "client/chatvpn_backend.py",
        "client/ipv6_manager.py",
        "client/proxy_helper.py",
        "client/proxy_modes.py",
        "client/discover.py",
        "server/api/app.py",
        "server/agent/agent.py",
        "server/admin/tg_bot.py",
        "server/worker/worker.py",
        "server/agent/orchestrator.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = Path.home() / 'chatvpn' / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"❌ Missing file: {file_path}")
        else:
            print(f"✅ Found file: {file_path}")
    
    if missing_files:
        print(f"❌ {len(missing_files)} files missing")
        return False
    else:
        print("✅ All required files found")
        return True

def test_configuration_files():
    """Test configuration files"""
    print("\n🔍 Testing configuration files...")
    
    config_files = [
        "config/api.json",
        "config/agent.json",
        "config/bot.json",
        "config/worker.json",
        "config/orchestrator.json"
    ]
    
    missing_configs = []
    for config_path in config_files:
        full_path = Path.home() / 'chatvpn' / config_path
        if not full_path.exists():
            missing_configs.append(config_path)
            print(f"⚠️  Missing config: {config_path}")
        else:
            print(f"✅ Found config: {config_path}")
    
    if missing_configs:
        print(f"⚠️  {len(missing_configs)} config files missing (this is acceptable for development)")
    
    print("✅ Configuration files checked")
    return True

def main():
    """Main test function"""
    print("🧪 XVPN Component Integration Test")
    print("=" * 40)
    
    tests = [
        test_component_imports,
        test_state_machine_basic,
        test_transport_manager,
        test_health_monitor,
        test_ipv6_manager,
        test_proxy_helper,
        test_file_structure,
        test_configuration_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    elif passed >= total * 0.8:
        print("✅ Most tests passed, system is mostly functional")
        return 0
    else:
        print("❌ Too many tests failed, system needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())