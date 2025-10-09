#!/usr/bin/env python3
"""
XVPN Full System Status Checker
Comprehensive status check for all XVPN components
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

def check_component_status(component_name, check_function):
    """
    Check status of a component and return standardized result
    """
    print(f"🔍 Checking {component_name}...")
    
    try:
        result = check_function()
        if result.get("status") == "ok":
            print(f"   ✅ {component_name}: {result.get('message', 'OK')}")
        else:
            print(f"   ❌ {component_name}: {result.get('message', 'Error')}")
        return result
    except Exception as e:
        print(f"   ❌ {component_name}: Exception - {e}")
        return {"status": "error", "message": str(e)}

def check_api_server():
    """
    Check API server status
    """
    try:
        # Check if API server is running
        result = subprocess.run(
            ["systemctl", "is-active", "xvpn-api"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip() == "active":
            # Check API health endpoint
            response = requests.get(
                "https://localhost:8443/mcp/v1/vpn.health",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "ok",
                    "message": f"Running (Health: {health_data.get('status', 'unknown')})"
                }
            else:
                return {
                    "status": "warning",
                    "message": f"Service active but health check failed (Status: {response.status_code})"
                }
        else:
            return {
                "status": "error",
                "message": "Service not active"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking service status"
        }
    except requests.exceptions.RequestException:
        return {
            "status": "error",
            "message": "Cannot reach API endpoint"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_agent_service():
    """
    Check agent service status
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "xvpn-agent"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip() == "active":
            return {
                "status": "ok",
                "message": "Running"
            }
        else:
            return {
                "status": "error",
                "message": "Service not active"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking service status"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_bot_service():
    """
    Check bot service status
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "xvpn-bot"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip() == "active":
            return {
                "status": "ok",
                "message": "Running"
            }
        else:
            return {
                "status": "error",
                "message": "Service not active"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking service status"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_tls_certificates():
    """
    Check TLS certificate status
    """
    try:
        cert_path = "/opt/xvpn/tls/cert.pem"
        key_path = "/opt/xvpn/tls/key.pem"
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            # Check certificate expiration
            result = subprocess.run(
                ["openssl", "x509", "-in", cert_path, "-noout", "-dates"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                not_after_line = [line for line in output_lines if line.startswith('notAfter=')]
                if not_after_line:
                    not_after = not_after_line[0].replace('notAfter=', '')
                    return {
                        "status": "ok",
                        "message": f"Valid (Expires: {not_after})"
                    }
            
            return {
                "status": "warning",
                "message": "Certificates exist but cannot parse expiration"
            }
        else:
            return {
                "status": "error",
                "message": "Certificates not found"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking certificates"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_api_tokens():
    """
    Check API token status
    """
    try:
        tokens_file = "/opt/xvpn/data/api_tokens.json"
        
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
            
            token_count = len(tokens)
            return {
                "status": "ok",
                "message": f"{token_count} tokens configured"
            }
        else:
            return {
                "status": "error",
                "message": "Tokens file not found"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_firewall_rules():
    """
    Check firewall rules status
    """
    try:
        # Check if ufw is active
        result = subprocess.run(
            ["ufw", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            if "Status: active" in result.stdout:
                return {
                    "status": "ok",
                    "message": "Active"
                }
            else:
                return {
                    "status": "warning",
                    "message": "Inactive"
                }
        else:
            # Try iptables
            result = subprocess.run(
                ["iptables", "-L", "-n"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "status": "ok",
                    "message": "Configured (iptables)"
                }
            else:
                return {
                    "status": "warning",
                    "message": "Not configured"
                }
                
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking firewall"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_docker_containers():
    """
    Check Docker container status
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}: {{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            if containers and containers[0]:
                return {
                    "status": "ok",
                    "message": f"{len(containers)} containers running"
                }
            else:
                return {
                    "status": "warning",
                    "message": "No containers running"
                }
        else:
            return {
                "status": "error",
                "message": "Docker not available"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout checking Docker"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def check_system_resources():
    """
    Check system resource usage
    """
    try:
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "ok",
            "message": f"CPU: {cpu_percent}%, RAM: {memory.percent}%, Disk: {disk.percent}%"
        }
        
    except ImportError:
        return {
            "status": "error",
            "message": "psutil not installed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def generate_comprehensive_report(results):
    """
    Generate comprehensive system status report
    """
    print("\n" + "=" * 60)
    print("📊 XVPN Full System Status Report")
    print("=" * 60)
    
    # Summary
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r.get("status") == "ok")
    warning_checks = sum(1 for r in results if r.get("status") == "warning")
    failed_checks = total_checks - passed_checks - warning_checks
    
    print(f"\n📋 Summary:")
    print(f"   Total Components Checked: {total_checks}")
    print(f"   ✅ Healthy: {passed_checks}")
    print(f"   ⚠️  Warnings: {warning_checks}")
    print(f"   ❌ Errors: {failed_checks}")
    
    if failed_checks == 0 and warning_checks == 0:
        print("   🟢 System Status: HEALTHY")
        overall_status = "HEALTHY"
    elif failed_checks == 0:
        print("   🟡 System Status: DEGRADED")
        overall_status = "DEGRADED"
    else:
        print("   🔴 System Status: CRITICAL")
        overall_status = "CRITICAL"
    
    # Detailed results
    print(f"\n🔍 Detailed Results:")
    for component, result in results.items():
        status_symbols = {
            "ok": "✅",
            "warning": "⚠️ ",
            "error": "❌"
        }
        symbol = status_symbols.get(result.get("status"), "❓")
        print(f"   {symbol} {component}: {result.get('message', 'Unknown')}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if failed_checks > 0:
        print("   🔧 Fix critical issues immediately:")
        for component, result in results.items():
            if result.get("status") == "error":
                print(f"      - {component}: {result.get('message', 'Unknown error')}")
    
    if warning_checks > 0:
        print("   ⚠️  Address warnings:")
        for component, result in results.items():
            if result.get("status") == "warning":
                print(f"      - {component}: {result.get('message', 'Warning')}")
    
    if failed_checks == 0 and warning_checks == 0:
        print("   🎉 All systems operational!")
        print("   🚀 XVPN is ready for production use!")
    
    # Next steps
    print(f"\n🚀 Next Steps:")
    if overall_status == "HEALTHY":
        print("   ✅ System is production-ready")
        print("   📊 Continue monitoring system health")
        print("   🛠️  Perform regular maintenance")
        print("   📈 Monitor performance metrics")
    elif overall_status == "DEGRADED":
        print("   ⚠️  System is operational but with issues")
        print("   🔧 Address warnings to improve stability")
        print("   📊 Monitor system closely")
        print("   🛠️  Plan maintenance to fix issues")
    else:
        print("   🚨 System requires immediate attention")
        print("   🔧 Fix critical issues before production use")
        print("   📊 Monitor system status after fixes")
        print("   🛠️  Test all components after repairs")
    
    return overall_status

def main():
    """
    Main function to check all XVPN components
    """
    print("🧪 XVPN Full System Status Checker")
    print("=" * 35)
    
    # Components to check
    components = {
        "API Server": check_api_server,
        "Agent Service": check_agent_service,
        "Bot Service": check_bot_service,
        "TLS Certificates": check_tls_certificates,
        "API Tokens": check_api_tokens,
        "Firewall Rules": check_firewall_rules,
        "Docker Containers": check_docker_containers,
        "System Resources": check_system_resources
    }
    
    # Run checks
    results = {}
    for component_name, check_function in components.items():
        results[component_name] = check_component_status(component_name, check_function)
        print()
    
    # Generate report
    overall_status = generate_comprehensive_report(results)
    
    # Exit code
    if overall_status == "HEALTHY":
        return 0
    elif overall_status == "DEGRADED":
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())