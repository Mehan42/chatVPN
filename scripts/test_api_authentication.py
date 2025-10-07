#!/usr/bin/env python3
"""
XVPN API Authentication Test Script
Tests authentication for all API endpoints
"""

import os
import sys
import requests
import json
from pathlib import Path

def load_api_tokens():
    """
    Load API tokens from configuration file
    """
    tokens_file = "/opt/xvpn/data/api_tokens.json"
    
    if os.path.exists(tokens_file):
        try:
            with open(tokens_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading API tokens: {e}")
            return {}
    else:
        print(f"⚠️  API tokens file not found: {tokens_file}")
        return {}

def test_unauthenticated_access(base_url):
    """
    Test API endpoints without authentication
    """
    print("🔍 Testing unauthenticated access...")
    
    endpoints = [
        "/mcp/v1/vpn.health",
        "/transports/manifest.json",
        "/clients/test-uuid.json"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, verify=False, timeout=10)
            
            results[endpoint] = {
                "status_code": response.status_code,
                "authenticated": response.status_code != 401,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
            }
            
            if response.status_code == 401:
                print(f"   ✅ {endpoint}: Authentication required (401)")
            else:
                print(f"   ❌ {endpoint}: No authentication required (status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                "error": str(e),
                "authenticated": False
            }
            print(f"   ❌ {endpoint}: Request error - {e}")
        except Exception as e:
            results[endpoint] = {
                "error": str(e),
                "authenticated": False
            }
            print(f"   ❌ {endpoint}: Unexpected error - {e}")
    
    return results

def test_authenticated_access(base_url, tokens):
    """
    Test API endpoints with authentication
    """
    print("\n🔍 Testing authenticated access...")
    
    # Get admin token
    admin_token = None
    client_token = None
    
    for token_name, token_info in tokens.items():
        if "admin" in token_info.get("permissions", []):
            admin_token = token_info.get("token")
        elif "read" in token_info.get("permissions", []):
            client_token = token_info.get("token")
    
    if not admin_token and not client_token:
        print("⚠️  No valid tokens found, skipping authenticated tests")
        return {}
    
    endpoints = [
        ("/mcp/v1/vpn.health", "GET"),
        ("/transports/manifest.json", "GET"),
        ("/clients/test-uuid.json", "GET"),
        ("/mcp/v1/admin.newclient", "POST")
    ]
    
    results = {}
    
    # Test with client token
    if client_token:
        print("\n   🧪 Testing with client token...")
        headers = {"Authorization": f"Bearer {client_token}"}
        
        for endpoint, method in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, headers=headers, verify=False, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json={}, verify=False, timeout=10)
                
                results[f"{endpoint}_client"] = {
                    "status_code": response.status_code,
                    "method": method,
                    "authenticated": response.status_code != 401,
                    "authorized": response.status_code not in [401, 403],
                    "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
                }
                
                if response.status_code == 401:
                    print(f"      ❌ {endpoint}: Authentication failed (401)")
                elif response.status_code == 403:
                    print(f"      ⚠️  {endpoint}: Access denied (403) - insufficient permissions")
                elif response.status_code == 200:
                    print(f"      ✅ {endpoint}: Access granted (200)")
                else:
                    print(f"      ⚠️  {endpoint}: Unexpected status ({response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                results[f"{endpoint}_client"] = {
                    "error": str(e),
                    "method": method,
                    "authenticated": False,
                    "authorized": False
                }
                print(f"      ❌ {endpoint}: Request error - {e}")
            except Exception as e:
                results[f"{endpoint}_client"] = {
                    "error": str(e),
                    "method": method,
                    "authenticated": False,
                    "authorized": False
                }
                print(f"      ❌ {endpoint}: Unexpected error - {e}")
    
    # Test with admin token
    if admin_token:
        print("\n   🧪 Testing with admin token...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        for endpoint, method in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, headers=headers, verify=False, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json={}, verify=False, timeout=10)
                
                results[f"{endpoint}_admin"] = {
                    "status_code": response.status_code,
                    "method": method,
                    "authenticated": response.status_code != 401,
                    "authorized": response.status_code not in [401, 403],
                    "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
                }
                
                if response.status_code == 401:
                    print(f"      ❌ {endpoint}: Authentication failed (401)")
                elif response.status_code == 403:
                    print(f"      ❌ {endpoint}: Access denied (403) - insufficient permissions")
                elif response.status_code == 200:
                    print(f"      ✅ {endpoint}: Access granted (200)")
                else:
                    print(f"      ⚠️  {endpoint}: Unexpected status ({response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                results[f"{endpoint}_admin"] = {
                    "error": str(e),
                    "method": method,
                    "authenticated": False,
                    "authorized": False
                }
                print(f"      ❌ {endpoint}: Request error - {e}")
            except Exception as e:
                results[f"{endpoint}_admin"] = {
                    "error": str(e),
                    "method": method,
                    "authenticated": False,
                    "authorized": False
                }
                print(f"      ❌ {endpoint}: Unexpected error - {e}")
    
    return results

def generate_test_report(unauth_results, auth_results, tokens):
    """
    Generate comprehensive test report
    """
    print("\n" + "=" * 50)
    print("📊 API Authentication Test Report")
    print("=" * 50)
    
    # Summary
    total_endpoints = len(unauth_results)
    protected_endpoints = sum(1 for result in unauth_results.values() if result.get("status_code") == 401)
    unprotected_endpoints = total_endpoints - protected_endpoints
    
    print(f"\n📋 Summary:")
    print(f"   Total Endpoints Tested: {total_endpoints}")
    print(f"   Protected Endpoints: {protected_endpoints}")
    print(f"   Unprotected Endpoints: {unprotected_endpoints}")
    
    if unprotected_endpoints == 0:
        print("   🟢 All endpoints properly protected!")
    else:
        print("   🔴 Some endpoints lack protection!")
    
    # Detailed results
    print(f"\n🔍 Detailed Results:")
    
    for endpoint, result in unauth_results.items():
        status = "Protected" if result.get("status_code") == 401 else "Unprotected"
        symbol = "✅" if status == "Protected" else "❌"
        print(f"   {symbol} {endpoint}: {status} (Status: {result.get('status_code', 'N/A')})")
    
    # Token information
    print(f"\n🔑 Token Information:")
    for token_name, token_info in tokens.items():
        permissions = ", ".join(token_info.get("permissions", []))
        print(f"   {token_name}: {permissions}")
    
    # Authenticated access results
    print(f"\n🔐 Authenticated Access Results:")
    client_tests = {k: v for k, v in auth_results.items() if "_client" in k}
    admin_tests = {k: v for k, v in auth_results.items() if "_admin" in k}
    
    if client_tests:
        print(f"   Client Token Tests:")
        for endpoint_key, result in client_tests.items():
            endpoint = endpoint_key.replace("_client", "")
            status = "Authorized" if result.get("authorized") else "Denied"
            symbol = "✅" if result.get("authorized") else "❌"
            print(f"      {symbol} {endpoint}: {status} (Status: {result.get('status_code', 'N/A')})")
    
    if admin_tests:
        print(f"   Admin Token Tests:")
        for endpoint_key, result in admin_tests.items():
            endpoint = endpoint_key.replace("_admin", "")
            status = "Authorized" if result.get("authorized") else "Denied"
            symbol = "✅" if result.get("authorized") else "❌"
            print(f"      {symbol} {endpoint}: {status} (Status: {result.get('status_code', 'N/A')})")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if unprotected_endpoints > 0:
        print("   🔒 Add authentication to unprotected endpoints")
    
    # Return overall status
    return unprotected_endpoints == 0

def main():
    """
    Main function to run API authentication tests
    """
    print("🧪 XVPN API Authentication Test Suite")
    print("=" * 40)
    
    # Configuration
    base_url = "https://localhost:8443"  # Default development URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"📍 Testing API at: {base_url}")
    
    # Load tokens
    tokens = load_api_tokens()
    if not tokens:
        print("⚠️  No API tokens found, some tests will be skipped")
    
    # Test unauthenticated access
    unauth_results = test_unauthenticated_access(base_url)
    
    # Test authenticated access
    auth_results = test_authenticated_access(base_url, tokens)
    
    # Generate report
    all_secure = generate_test_report(unauth_results, auth_results, tokens)
    
    # Exit code
    if all_secure:
        print("\n🎉 All API endpoints are properly secured!")
        return 0
    else:
        print("\n🚨 Some API endpoints lack proper authentication!")
        return 1

if __name__ == "__main__":
    sys.exit(main())