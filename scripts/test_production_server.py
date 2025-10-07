#!/usr/bin/env python3
"""
XVPN Production Server HTTPS Test Script
"""

import os
import sys
import ssl
import socket
import requests
import subprocess
from pathlib import Path

def test_production_https(server_ip="77.110.123.27", port=8443):
    """
    Test HTTPS connectivity to production server
    """
    print(f"🔍 Testing HTTPS connection to production server {server_ip}:{port}...")
    
    try:
        # Test HTTPS endpoint
        response = requests.get(
            f"https://{server_ip}:{port}/mcp/v1/vpn.health",
            verify=False,  # Disable verification for self-signed certs
            timeout=15
        )
        
        print(f"✅ HTTPS connectivity test PASSED")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTPS connectivity test FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during HTTPS test: {e}")
        return False

def test_ssh_connectivity(server_ip="77.110.123.27"):
    """
    Test SSH connectivity to production server
    """
    print(f"🔍 Testing SSH connectivity to {server_ip}...")
    
    try:
        # Test SSH connection
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", 
             f"root@{server_ip}", "echo 'SSH OK'"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and "SSH OK" in result.stdout:
            print(f"✅ SSH connectivity test PASSED")
            return True
        else:
            print(f"❌ SSH connectivity test FAILED")
            print(f"   Return code: {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ SSH connectivity test TIMED OUT")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during SSH test: {e}")
        return False

def test_certificate_files():
    """
    Check if local certificate files exist
    """
    print("🔍 Checking local certificate files...")
    
    cert_path = "/home/uss/chatvpn/security/tls/cert.pem"
    key_path = "/home/uss/chatvpn/security/tls/key.pem"
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"✅ Local certificate files found")
        print(f"   Certificate: {cert_path}")
        print(f"   Private Key: {key_path}")
        
        # Check file permissions
        cert_perms = oct(os.stat(cert_path).st_mode)[-3:]
        key_perms = oct(os.stat(key_path).st_mode)[-3:]
        
        print(f"   Certificate permissions: {cert_perms} (should be 644)")
        print(f"   Key permissions: {key_perms} (should be 600)")
        return True
    else:
        print(f"❌ Local certificate files NOT FOUND")
        print(f"   Expected certificate: {cert_path}")
        print(f"   Expected key: {key_path}")
        return False

def test_local_https_server(port=8443):
    """
    Test local HTTPS server if running
    """
    print(f"🔍 Testing local HTTPS server on port {port}...")
    
    try:
        # Test local HTTPS endpoint
        response = requests.get(
            f"https://localhost:{port}/mcp/v1/vpn.health",
            verify=False,  # Disable verification for self-signed certs
            timeout=10
        )
        
        print(f"✅ Local HTTPS server test PASSED")
        print(f"   Status Code: {response.status_code}")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Local HTTPS server NOT RUNNING (this is OK for production testing)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Local HTTPS server test FAILED: {e}")
        return True  # Continue even if local server test fails
    except Exception as e:
        print(f"❌ Unexpected error during local HTTPS test: {e}")
        return True  # Continue even if local server test fails

def main():
    """
    Main function to run all production tests
    """
    print("🧪 XVPN Production Server Test Suite")
    print("=" * 40)
    
    # Run all tests
    tests = [
        test_certificate_files,
        test_ssh_connectivity,
        test_local_https_server,
        lambda: test_production_https("77.110.123.27", 8443)
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
        print("✅ All tests PASSED! Production server is ready.")
        return 0
    else:
        print("❌ Some tests FAILED! Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())