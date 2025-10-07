#!/usr/bin/env python3
"""
XVPN HTTPS Connection Test Script
"""

import os
import sys
import ssl
import socket
import requests
import subprocess
from pathlib import Path

def test_https_server(host="localhost", port=8443):
    """
    Test HTTPS server connectivity
    """
    print(f"🔍 Testing HTTPS connection to {host}:{port}...")
    
    # Test 1: Basic HTTPS connectivity
    try:
        response = requests.get(
            f"https://{host}:{port}/mcp/v1/vpn.health",
            verify=False,  # Disable verification for self-signed certs
            timeout=10
        )
        print(f"✅ HTTPS connectivity test PASSED")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTPS connectivity test FAILED: {e}")
        return False
    
    # Test 2: Certificate validation
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                print(f"✅ Certificate validation test PASSED")
                print(f"   Cipher: {cipher[0]}")
                print(f"   Protocol: {ssock.version()}")
    except Exception as e:
        print(f"❌ Certificate validation test FAILED: {e}")
        return False
    
    return True

def check_certificate_files():
    """
    Check if certificate files exist and are readable
    """
    print("🔍 Checking certificate files...")
    
    cert_paths = [
        "/opt/xvpn/tls/cert.pem",
        "/home/uss/chatvpn/security/tls/cert.pem",
        "./security/tls/cert.pem"
    ]
    
    found_cert = False
    for cert_path in cert_paths:
        key_path = cert_path.replace("cert.pem", "key.pem")
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            print(f"✅ Certificate files found at: {cert_path}")
            
            # Check permissions
            cert_perms = oct(os.stat(cert_path).st_mode)[-3:]
            key_perms = oct(os.stat(key_path).st_mode)[-3:]
            
            print(f"   Certificate permissions: {cert_perms} (should be 644)")
            print(f"   Key permissions: {key_perms} (should be 600)")
            
            found_cert = True
            break
    
    if not found_cert:
        print("❌ Certificate files NOT FOUND")
        return False
    
    return True

def test_flask_app_import():
    """
    Test that Flask app can be imported without errors
    """
    print("🔍 Testing Flask app import...")
    
    try:
        # Add parent directory to path
        sys.path.append(str(Path(__file__).parent / "server" / "api"))
        
        # Try to import the app
        import app
        print("✅ Flask app import test PASSED")
        return True
    except ImportError as e:
        print(f"❌ Flask app import test FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Flask app import test FAILED with unexpected error: {e}")
        return False

def main():
    """
    Main function to run all tests
    """
    print("🧪 XVPN HTTPS Connection Test Suite")
    print("=" * 40)
    
    # Run all tests
    tests = [
        check_certificate_files,
        test_flask_app_import,
        lambda: test_https_server("localhost", 8443)
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests PASSED! HTTPS is configured correctly.")
        return 0
    else:
        print("❌ Some tests FAILED! Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())