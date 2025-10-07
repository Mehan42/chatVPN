#!/usr/bin/env python3
"""
XVPN Automated Security Testing Script
Runs comprehensive security tests on the XVPN API
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

class XVPNSecurityTester:
    """
    Automated security testing for XVPN API
    """
    
    def __init__(self, base_url="https://localhost:8443"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        self.results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0
            }
        }
    
    def add_result(self, test_name, status, message="", details=None):
        """
        Add test result to results
        """
        self.results["tests"][test_name] = {
            "status": status,  # pass, fail, skip
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        
        self.results["summary"]["total"] += 1
        if status == "pass":
            self.results["summary"]["passed"] += 1
        elif status == "fail":
            self.results["summary"]["failed"] += 1
        elif status == "skip":
            self.results["summary"]["skipped"] += 1
    
    def load_api_tokens(self):
        """
        Load API tokens for authentication testing
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
    
    def test_https_connectivity(self):
        """
        Test HTTPS connectivity to API server
        """
        print("🔍 Testing HTTPS connectivity...")
        
        try:
            response = self.session.get(f"{self.base_url}/mcp/v1/vpn.health", timeout=10)
            
            if response.status_code == 200:
                self.add_result(
                    "HTTPS Connectivity", 
                    "pass", 
                    "HTTPS connection successful",
                    {"status_code": response.status_code, "response_time": response.elapsed.total_seconds()}
                )
                return True
            else:
                self.add_result(
                    "HTTPS Connectivity", 
                    "fail", 
                    f"Unexpected status code: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:100]}
                )
                return False
                
        except requests.exceptions.SSLError as e:
            self.add_result(
                "HTTPS Connectivity", 
                "fail", 
                f"SSL error: {e}",
                {"error": str(e)}
            )
            return False
        except requests.exceptions.ConnectionError as e:
            self.add_result(
                "HTTPS Connectivity", 
                "fail", 
                f"Connection error: {e}",
                {"error": str(e)}
            )
            return False
        except Exception as e:
            self.add_result(
                "HTTPS Connectivity", 
                "fail", 
                f"Unexpected error: {e}",
                {"error": str(e)}
            )
            return False
    
    def test_authentication_required(self):
        """
        Test that authentication is required for protected endpoints
        """
        print("🔍 Testing authentication requirement...")
        
        # Test endpoints that should require authentication
        protected_endpoints = [
            "/mcp/v1/vpn.health",
            "/transports/manifest.json",
            "/clients/test-uuid.json",
            "/mcp/v1/admin.newclient"
        ]
        
        auth_required_count = 0
        total_endpoints = len(protected_endpoints)
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                # Check if authentication is required (401 or 403)
                if response.status_code in [401, 403]:
                    auth_required_count += 1
                    self.add_result(
                        f"Auth Required - {endpoint}", 
                        "pass", 
                        f"Authentication correctly required (status: {response.status_code})",
                        {"status_code": response.status_code}
                    )
                else:
                    self.add_result(
                        f"Auth Required - {endpoint}", 
                        "fail", 
                        f"Authentication NOT required (status: {response.status_code})",
                        {"status_code": response.status_code, "response": response.text[:100]}
                    )
                    
            except Exception as e:
                self.add_result(
                    f"Auth Required - {endpoint}", 
                    "fail", 
                    f"Error testing endpoint: {e}",
                    {"error": str(e)}
                )
        
        # Overall result
        if auth_required_count == total_endpoints:
            self.add_result(
                "Authentication Requirement", 
                "pass", 
                f"All {total_endpoints} endpoints require authentication"
            )
            return True
        else:
            self.add_result(
                "Authentication Requirement", 
                "fail", 
                f"Only {auth_required_count}/{total_endpoints} endpoints require authentication"
            )
            return False
    
    def test_valid_token_access(self):
        """
        Test access with valid tokens
        """
        print("🔍 Testing valid token access...")
        
        # Load tokens
        tokens = self.load_api_tokens()
        if not tokens:
            self.add_result(
                "Valid Token Access", 
                "skip", 
                "No API tokens found, skipping token tests"
            )
            return False
        
        # Find admin token
        admin_token = None
        client_token = None
        
        for token_name, token_info in tokens.items():
            if "admin" in token_info.get("permissions", []):
                admin_token = token_info.get("token")
            elif "read" in token_info.get("permissions", []):
                client_token = token_info.get("token")
        
        success_count = 0
        total_tests = 0
        
        # Test with client token
        if client_token:
            client_headers = {"Authorization": f"Bearer {client_token}"}
            
            # Test read endpoints
            read_endpoints = [
                "/mcp/v1/vpn.health",
                "/transports/manifest.json"
            ]
            
            for endpoint in read_endpoints:
                total_tests += 1
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}", 
                        headers=client_headers, 
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        self.add_result(
                            f"Client Token - {endpoint}", 
                            "pass", 
                            f"Access granted with client token (status: {response.status_code})",
                            {"status_code": response.status_code}
                        )
                    else:
                        self.add_result(
                            f"Client Token - {endpoint}", 
                            "fail", 
                            f"Access denied with client token (status: {response.status_code})",
                            {"status_code": response.status_code, "response": response.text[:100]}
                        )
                except Exception as e:
                    self.add_result(
                        f"Client Token - {endpoint}", 
                        "fail", 
                        f"Error testing endpoint: {e}",
                        {"error": str(e)}
                    )
        
        # Test with admin token
        if admin_token:
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Test admin endpoints
            admin_endpoints = [
                "/mcp/v1/admin.newclient"
            ]
            
            for endpoint in admin_endpoints:
                total_tests += 1
                try:
                    # For POST endpoints, send empty JSON
                    if endpoint.endswith("newclient"):
                        response = self.session.post(
                            f"{self.base_url}{endpoint}", 
                            headers=admin_headers, 
                            json={}, 
                            timeout=10
                        )
                    else:
                        response = self.session.get(
                            f"{self.base_url}{endpoint}", 
                            headers=admin_headers, 
                            timeout=10
                        )
                    
                    # Admin endpoints might return 400 for empty requests, but not 401/403
                    if response.status_code not in [401, 403]:
                        success_count += 1
                        self.add_result(
                            f"Admin Token - {endpoint}", 
                            "pass", 
                            f"Access granted with admin token (status: {response.status_code})",
                            {"status_code": response.status_code}
                        )
                    else:
                        self.add_result(
                            f"Admin Token - {endpoint}", 
                            "fail", 
                            f"Access denied with admin token (status: {response.status_code})",
                            {"status_code": response.status_code, "response": response.text[:100]}
                        )
                except Exception as e:
                    self.add_result(
                        f"Admin Token - {endpoint}", 
                        "fail", 
                        f"Error testing endpoint: {e}",
                        {"error": str(e)}
                    )
        
        # Overall result
        if total_tests > 0 and success_count == total_tests:
            self.add_result(
                "Valid Token Access", 
                "pass", 
                f"All {success_count}/{total_tests} token access tests passed"
            )
            return True
        elif total_tests > 0:
            self.add_result(
                "Valid Token Access", 
                "fail", 
                f"Only {success_count}/{total_tests} token access tests passed"
            )
            return False
        else:
            self.add_result(
                "Valid Token Access", 
                "skip", 
                "No valid tokens found for testing"
            )
            return False
    
    def test_invalid_token_access(self):
        """
        Test access with invalid tokens
        """
        print("🔍 Testing invalid token access...")
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_1234567890"}
        
        # Test endpoints
        test_endpoints = [
            "/mcp/v1/vpn.health",
            "/transports/manifest.json"
        ]
        
        denied_count = 0
        total_endpoints = len(test_endpoints)
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}", 
                    headers=invalid_headers, 
                    timeout=10
                )
                
                # Check if access is denied (401 or 403)
                if response.status_code in [401, 403]:
                    denied_count += 1
                    self.add_result(
                        f"Invalid Token - {endpoint}", 
                        "pass", 
                        f"Access correctly denied (status: {response.status_code})",
                        {"status_code": response.status_code}
                    )
                else:
                    self.add_result(
                        f"Invalid Token - {endpoint}", 
                        "fail", 
                        f"Access NOT denied (status: {response.status_code})",
                        {"status_code": response.status_code, "response": response.text[:100]}
                    )
                    
            except Exception as e:
                self.add_result(
                    f"Invalid Token - {endpoint}", 
                    "fail", 
                    f"Error testing endpoint: {e}",
                    {"error": str(e)}
                )
        
        # Overall result
        if denied_count == total_endpoints:
            self.add_result(
                "Invalid Token Access", 
                "pass", 
                f"All {total_endpoints} endpoints denied invalid token access"
            )
            return True
        else:
            self.add_result(
                "Invalid Token Access", 
                "fail", 
                f"Only {denied_count}/{total_endpoints} endpoints denied invalid token access"
            )
            return False
    
    def test_no_token_access(self):
        """
        Test access without any token
        """
        print("🔍 Testing no token access...")
        
        # Test endpoints without token
        test_endpoints = [
            "/mcp/v1/vpn.health",
            "/transports/manifest.json"
        ]
        
        denied_count = 0
        total_endpoints = len(test_endpoints)
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}", 
                    timeout=10
                )
                
                # Check if access is denied (401 or 403)
                if response.status_code in [401, 403]:
                    denied_count += 1
                    self.add_result(
                        f"No Token - {endpoint}", 
                        "pass", 
                        f"Access correctly denied (status: {response.status_code})",
                        {"status_code": response.status_code}
                    )
                else:
                    self.add_result(
                        f"No Token - {endpoint}", 
                        "fail", 
                        f"Access NOT denied (status: {response.status_code})",
                        {"status_code": response.status_code, "response": response.text[:100]}
                    )
                    
            except Exception as e:
                self.add_result(
                    f"No Token - {endpoint}", 
                    "fail", 
                    f"Error testing endpoint: {e}",
                    {"error": str(e)}
                )
        
        # Overall result
        if denied_count == total_endpoints:
            self.add_result(
                "No Token Access", 
                "pass", 
                f"All {total_endpoints} endpoints denied access without token"
            )
            return True
        else:
            self.add_result(
                "No Token Access", 
                "fail", 
                f"Only {denied_count}/{total_endpoints} endpoints denied access without token"
            )
            return False
    
    def run_all_tests(self):
        """
        Run all security tests
        """
        print("🛡️  XVPN API Security Testing Suite")
        print("=" * 40)
        print(f"Testing server: {self.base_url}")
        print()
        
        # Run all tests
        tests = [
            self.test_https_connectivity,
            self.test_authentication_required,
            self.test_valid_token_access,
            self.test_invalid_token_access,
            self.test_no_token_access
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Error running test {test.__name__}: {e}")
            print()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        return self.results["summary"]["failed"] == 0
    
    def print_summary(self):
        """
        Print test summary
        """
        print("=" * 40)
        print("📊 Security Test Summary")
        print("=" * 40)
        
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        skipped = self.results["summary"]["skipped"]
        total = self.results["summary"]["total"]
        
        print(f"✅ Passed:     {passed}/{total} tests")
        print(f"❌ Failed:     {failed}/{total} tests")
        print(f"⚠️  Skipped:   {skipped}/{total} tests")
        print()
        
        # Overall status
        if failed == 0 and skipped == 0:
            print("🎉 All security tests PASSED! API is secure.")
            overall_status = "PASS"
        elif failed == 0:
            print("✅ Security tests mostly PASSED with some skipped tests.")
            overall_status = "WARN"
        else:
            print("❌ Some security tests FAILED! Immediate attention required.")
            overall_status = "FAIL"
        
        print()
        print(f"Overall Status: {overall_status}")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for test_name, result in self.results["tests"].items():
            status_symbol = {
                "pass": "✅",
                "fail": "❌",
                "skip": "⚠️ "
            }.get(result["status"], "❓")
            
            print(f"   {status_symbol} {test_name}: {result['message']}")
    
    def save_results(self):
        """
        Save test results to file
        """
        results_file = Path.home() / "chatvpn" / "security" / "api_security_test_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📝 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run security tests
    """
    # Parse arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN API Security Testing")
    parser.add_argument("--url", default="https://localhost:8443", 
                       help="Base URL for API testing (default: https://localhost:8443)")
    parser.add_argument("--output", default=None,
                       help="Output file for results (default: ~/chatvpn/security/api_security_test_results.json)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = XVPNSecurityTester(base_url=args.url)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())