#!/usr/bin/env python3
"""
XVPN Security Health Check Script
Comprehensive security validation for the XVPN system
"""

import os
import sys
import json
import ssl
import socket
import subprocess
import requests
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class XVPNSecurityHealthChecker:
    """
    Performs comprehensive security health checks for XVPN system
    """
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "total": 0
            }
        }
    
    def add_result(self, category, name, status, message="", details=None):
        """
        Add check result to results
        """
        result = {
            "category": category,
            "name": name,
            "status": status,  # pass, fail, warn
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.results["checks"].append(result)
        self.results["summary"]["total"] += 1
        
        if status == "pass":
            self.results["summary"]["passed"] += 1
        elif status == "fail":
            self.results["summary"]["failed"] += 1
        elif status == "warn":
            self.results["summary"]["warnings"] += 1
        
        # Print result
        status_symbol = {
            "pass": "✅",
            "fail": "❌",
            "warn": "⚠️ "
        }.get(status, "❓")
        
        print(f"   {status_symbol} [{category}] {name}: {message}")
        return result
    
    def check_https_tls(self):
        """
        Check HTTPS/TLS configuration
        """
        print("🔍 Checking HTTPS/TLS Security...")
        
        # Check if certificates exist
        cert_path = "/opt/xvpn/tls/cert.pem"
        key_path = "/opt/xvpn/tls/key.pem"
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            self.add_result("HTTPS/TLS", "Certificate Files", "pass", 
                          "Certificate and key files exist",
                          {"cert_path": cert_path, "key_path": key_path})
        else:
            self.add_result("HTTPS/TLS", "Certificate Files", "fail",
                          "Certificate or key files missing",
                          {"cert_path": cert_path, "key_path": key_path})
            return False
        
        # Check certificate permissions
        try:
            cert_stat = os.stat(cert_path)
            key_stat = os.stat(key_path)
            
            # Certificate should be readable (644)
            if cert_stat.st_mode & 0o777 == 0o644:
                self.add_result("HTTPS/TLS", "Certificate Permissions", "pass",
                              "Certificate file has correct permissions (644)")
            else:
                self.add_result("HTTPS/TLS", "Certificate Permissions", "warn",
                              f"Certificate file has incorrect permissions ({oct(cert_stat.st_mode & 0o777)})",
                              {"expected": "644", "actual": oct(cert_stat.st_mode & 0o777)})
            
            # Key should be private (600)
            if key_stat.st_mode & 0o777 == 0o600:
                self.add_result("HTTPS/TLS", "Key Permissions", "pass",
                              "Private key file has correct permissions (600)")
            else:
                self.add_result("HTTPS/TLS", "Key Permissions", "fail",
                              f"Private key file has incorrect permissions ({oct(key_stat.st_mode & 0o777)})",
                              {"expected": "600", "actual": oct(key_stat.st_mode & 0o777)})
        except OSError as e:
            self.add_result("HTTPS/TLS", "Permissions Check", "fail",
                          f"Error checking file permissions: {e}")
        
        # Check TLS connectivity (if service is running)
        try:
            response = requests.get("https://localhost:8443/mcp/v1/vpn.health", 
                                 verify=False, timeout=10)
            if response.status_code == 200:
                self.add_result("HTTPS/TLS", "HTTPS Service", "pass",
                              "HTTPS service is responding correctly",
                              {"status_code": response.status_code})
            else:
                self.add_result("HTTPS/TLS", "HTTPS Service", "warn",
                              f"HTTPS service returned unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.add_result("HTTPS/TLS", "HTTPS Service", "warn",
                          "Could not connect to HTTPS service (may not be running)")
        except Exception as e:
            self.add_result("HTTPS/TLS", "HTTPS Service", "fail",
                          f"Error connecting to HTTPS service: {e}")
        
        return True
    
    def check_certificate_pinning(self):
        """
        Check certificate pinning implementation
        """
        print("🔍 Checking Certificate Pinning...")
        
        # Check if fingerprint file exists
        fingerprint_path = Path.home() / "chatvpn" / "client" / "config" / "cert_fingerprints.json"
        
        if fingerprint_path.exists():
            try:
                with open(fingerprint_path, 'r') as f:
                    fingerprints = json.load(f)
                
                if "fingerprints" in fingerprints and len(fingerprints["fingerprints"]) > 0:
                    self.add_result("Pinning", "Fingerprint Storage", "pass",
                                  f"Certificate fingerprints stored ({len(fingerprints['fingerprints'])} servers)",
                                  {"fingerprint_file": str(fingerprint_path)})
                else:
                    self.add_result("Pinning", "Fingerprint Storage", "warn",
                                  "Fingerprint file exists but is empty",
                                  {"fingerprint_file": str(fingerprint_path)})
            except Exception as e:
                self.add_result("Pinning", "Fingerprint Storage", "fail",
                              f"Error reading fingerprint file: {e}",
                              {"fingerprint_file": str(fingerprint_path)})
        else:
            self.add_result("Pinning", "Fingerprint Storage", "warn",
                          "Certificate fingerprint file not found",
                          {"expected_location": str(fingerprint_path)})
        
        return True
    
    def check_api_authentication(self):
        """
        Check API authentication implementation
        """
        print("🔍 Checking API Authentication...")
        
        # Check if auth module exists
        auth_path = Path(__file__).parent.parent / "server" / "api" / "auth.py"
        
        if auth_path.exists():
            self.add_result("Auth", "Auth Module", "pass",
                          "API authentication module exists",
                          {"auth_module": str(auth_path)})
        else:
            self.add_result("Auth", "Auth Module", "warn",
                          "API authentication module not found",
                          {"expected_location": str(auth_path)})
        
        # Check if tokens file exists
        tokens_path = "/opt/xvpn/data/api_tokens.json"
        
        if os.path.exists(tokens_path):
            try:
                with open(tokens_path, 'r') as f:
                    tokens = json.load(f)
                
                if isinstance(tokens, dict) and len(tokens) > 0:
                    self.add_result("Auth", "API Tokens", "pass",
                                  f"API tokens file exists with {len(tokens)} tokens",
                                  {"tokens_file": tokens_path})
                else:
                    self.add_result("Auth", "API Tokens", "warn",
                                  "API tokens file exists but is empty",
                                  {"tokens_file": tokens_path})
            except Exception as e:
                self.add_result("Auth", "API Tokens", "fail",
                              f"Error reading tokens file: {e}",
                              {"tokens_file": tokens_path})
        else:
            self.add_result("Auth", "API Tokens", "warn",
                          "API tokens file not found",
                          {"expected_location": tokens_path})
        
        return True
    
    def check_certificate_management(self):
        """
        Check certificate management implementation
        """
        print("🔍 Checking Certificate Management...")
        
        # Check monitoring scripts
        monitor_scripts = [
            "monitor_certificates.py",
            "renew_certificates.py"
        ]
        
        scripts_dir = Path(__file__).parent.parent / "scripts"
        
        for script_name in monitor_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                self.add_result("CertMgmt", f"Script {script_name}", "pass",
                              "Certificate management script exists",
                              {"script_path": str(script_path)})
            else:
                self.add_result("CertMgmt", f"Script {script_name}", "warn",
                              "Certificate management script missing",
                              {"expected_location": str(script_path)})
        
        return True
    
    def check_file_permissions(self):
        """
        Check critical file permissions
        """
        print("🔍 Checking Critical File Permissions...")
        
        critical_files = [
            ("/opt/xvpn/tls/key.pem", 0o600),
            ("/opt/xvpn/tls/cert.pem", 0o644),
            ("/opt/xvpn/data/api_tokens.json", 0o600),
        ]
        
        for file_path, expected_perms in critical_files:
            if os.path.exists(file_path):
                try:
                    stat = os.stat(file_path)
                    actual_perms = stat.st_mode & 0o777
                    
                    if actual_perms == expected_perms:
                        self.add_result("Perms", f"File {os.path.basename(file_path)}", "pass",
                                      f"Correct permissions ({oct(actual_perms)})",
                                      {"file": file_path})
                    else:
                        self.add_result("Perms", f"File {os.path.basename(file_path)}", "fail",
                                      f"Incorrect permissions: expected {oct(expected_perms)}, got {oct(actual_perms)}",
                                      {"file": file_path, "expected": oct(expected_perms), "actual": oct(actual_perms)})
                except OSError as e:
                    self.add_result("Perms", f"File {os.path.basename(file_path)}", "fail",
                                  f"Error checking permissions: {e}",
                                  {"file": file_path})
            else:
                self.add_result("Perms", f"File {os.path.basename(file_path)}", "warn",
                              "File not found",
                              {"file": file_path})
        
        return True
    
    def check_firewall_rules(self):
        """
        Check firewall configuration
        """
        print("🔍 Checking Firewall Rules...")
        
        try:
            # Check if iptables is available
            result = subprocess.run(["iptables", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_result("Firewall", "iptables Available", "pass",
                              "iptables is available for firewall rules")
            else:
                self.add_result("Firewall", "iptables Available", "warn",
                              "iptables not available or not working properly")
        except FileNotFoundError:
            self.add_result("Firewall", "iptables Available", "warn",
                          "iptables not installed")
        except Exception as e:
            self.add_result("Firewall", "iptables Available", "fail",
                          f"Error checking iptables: {e}")
        
        return True
    
    def run_all_checks(self):
        """
        Run all security health checks
        """
        print("🛡️  XVPN Security Health Check")
        print("=" * 40)
        print(f"Started: {self.results['timestamp']}")
        print()
        
        # Run all checks
        checks = [
            self.check_https_tls,
            self.check_certificate_pinning,
            self.check_api_authentication,
            self.check_certificate_management,
            self.check_file_permissions,
            self.check_firewall_rules,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"❌ Error in {check.__name__}: {e}")
        
        # Print summary
        print()
        print("=" * 40)
        print("📊 Security Health Check Summary")
        print("=" * 40)
        
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        warnings = self.results["summary"]["warnings"]
        total = self.results["summary"]["total"]
        
        print(f"✅ Passed:     {passed}/{total} checks")
        print(f"❌ Failed:     {failed}/{total} checks")
        print(f"⚠️  Warnings:   {warnings}/{total} checks")
        print()
        
        # Overall status
        if failed == 0 and warnings == 0:
            print("🎉 All security checks PASSED! System is secure.")
            overall_status = "PASS"
        elif failed == 0:
            print("✅ Security checks mostly PASSED with some warnings.")
            overall_status = "WARN"
        else:
            print("❌ Some security checks FAILED! Immediate attention required.")
            overall_status = "FAIL"
        
        print()
        print(f"Overall Status: {overall_status}")
        
        # Save results
        results_file = Path.home() / "chatvpn" / "logs" / f"security_check_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📝 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
        
        return overall_status == "PASS"

def main():
    """
    Main function to run security health check
    """
    checker = XVPNSecurityHealthChecker()
    success = checker.run_all_checks()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())