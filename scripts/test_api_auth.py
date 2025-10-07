#!/usr/bin/env python3
"""
XVPN API Authentication Test Script
Tests authentication for all API endpoints
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

class XVPNAuthTester:
    """
    Tests XVPN API authentication
    """
    
    def __init__(self, base_url="https://localhost:8443"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        
        # Load tokens
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """
        Load API tokens from file
        """
        tokens_file = "/opt/xvpn/data/api_tokens.json"
        
        try:
            if os.path.exists(tokens_file):
                with open(tokens_file, 'r') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Tokens file not found: {tokens_file}")
                return {}
        except Exception as e:
            print(f"❌ Error loading tokens: {e}")
            return {}
    
    def get_token(self, token_name):
        """
        Get token value by name
        """
        if token_name in self.tokens:
            return self.tokens[token_name].get("token")
        return None
    
    def test_unauthenticated_access(self):
        """
        Test API endpoints without authentication
        """
        print("🔍 Testing unauthenticated access...")
        
        endpoints = [
            "/mcp/v1/vpn.health",
            "/transports/manifest.json",
            "/clients/test-uuid.json",
            "/mcp/v1/admin.newclient"
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "authenticated": response.status_code != 401,
                    "response": response.text[:100] if response.text else ""
                }
                
                if response.status_code == 401:
                    print(f"   ✅ {endpoint}: Authentication required (401)")
                elif response.status_code == 403:
                    print(f"   ✅ {endpoint}: Access forbidden (403)")
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
    
    def test_authenticated_access(self):
        """
        Test API endpoints with authentication
        """
        print("\n🔍 Testing authenticated access...")
        
        # Get tokens
        admin_token = self.get_token("admin")
        client_token = self.get_token("client")
        
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
                    url = f"{self.base_url}{endpoint}"
                    if method == "GET":
                        response = self.session.get(url, headers=headers, timeout=10)
                    elif method == "POST":
                        response = self.session.post(url, headers=headers, json={}, timeout=10)
                    
                    results[f"{endpoint}_client"] = {
                        "status_code": response.status_code,
                        "method": method,
                        "authenticated": response.status_code != 401,
                        "authorized": response.status_code not in [401, 403],
                        "response": response.text[:100] if response.text else ""
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
                    url = f"{self.base_url}{endpoint}"
                    if method == "GET":
                        response = self.session.get(url, headers=headers, timeout=10)
                    elif method == "POST":
                        response = self.session.post(url, headers=headers, json={}, timeout=10)
                    
                    results[f"{endpoint}_admin"] = {
                        "status_code": response.status_code,
                        "method": method,
                        "authenticated": response.status_code != 401,
                        "authorized": response.status_code not in [401, 403],
                        "response": response.text[:100] if response.text else ""
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
    
    def generate_test_report(self, unauth_results, auth_results):
        """
        Generate comprehensive test report
        """
        print("\n" + "=" * 50)
        print("📊 API Authentication Test Report")
        print("=" * 50)
        
        # Summary
        total_endpoints = len(unauth_results)
        protected_endpoints = sum(1 for result in unauth_results.values() if result.get("status_code") in [401, 403])
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
            if "status_code" in result:
                status_codes = {401: "Protected", 403: "Forbidden", 200: "Unprotected"}
                status = status_codes.get(result["status_code"], f"Other ({result['status_code']})")
                symbol = "✅" if result["status_code"] in [401, 403] else "❌"
                print(f"   {symbol} {endpoint}: {status} (Status: {result['status_code']})")
            else:
                print(f"   ❌ {endpoint}: Error - {result.get('error', 'Unknown')}")
        
        # Authenticated access results
        print(f"\n🔐 Authenticated Access Results:")
        client_tests = {k: v for k, v in auth_results.items() if "_client" in k}
        admin_tests = {k: v for k, v in auth_results.items() if "_admin" in k}
        
        if client_tests:
            print(f"   Client Token Tests:")
            for endpoint_key, result in client_tests.items():
                endpoint = endpoint_key.replace("_client", "")
                if result.get("authorized"):
                    print(f"      ✅ {endpoint}: Authorized (Status: {result.get('status_code')})")
                else:
                    print(f"      ❌ {endpoint}: Denied (Status: {result.get('status_code')})")
        
        if admin_tests:
            print(f"   Admin Token Tests:")
            for endpoint_key, result in admin_tests.items():
                endpoint = endpoint_key.replace("_admin", "")
                if result.get("authorized"):
                    print(f"      ✅ {endpoint}: Authorized (Status: {result.get('status_code')})")
                else:
                    print(f"      ❌ {endpoint}: Denied (Status: {result.get('status_code')})")
        
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
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN API Authentication Testing")
    parser.add_argument("--url", default="https://localhost:8443",
                       help="Base URL for API testing (default: https://localhost:8443)")
    parser.add_argument("--tokens-file", default="/opt/xvpn/data/api_tokens.json",
                       help="API tokens file path (default: /opt/xvpn/data/api_tokens.json)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = XVPNAuthTester(base_url=args.url)
    
    # Run tests
    print("🧪 XVPN API Authentication Test Suite")
    print("=" * 40)
    print(f"Testing server: {args.url}")
    print()
    
    # Test unauthenticated access
    unauth_results = tester.test_unauthenticated_access()
    
    # Test authenticated access
    auth_results = tester.test_authenticated_access()
    
    # Generate report
    all_secure = tester.generate_test_report(unauth_results, auth_results)
    
    # Exit code
    if all_secure:
        print("\n🎉 All API endpoints are properly secured!")
        return 0
    else:
        print("\n🚨 Some API endpoints lack proper authentication!")
        return 1

if __name__ == "__main__":
    sys.exit(main())