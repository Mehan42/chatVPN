#!/usr/bin/env python3
"""
XVPN API Security Audit Script
Audits API endpoints for proper authentication and authorization
"""

import os
import sys
import ast
import re
from pathlib import Path

def find_api_endpoints(file_path):
    """
    Find all API endpoints in a Flask application
    """
    endpoints = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the Python file
        tree = ast.parse(content)
        
        # Walk through the AST to find route decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for route decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == 'route':
                            # Extract route information
                            route_path = None
                            route_methods = ['GET']
                            
                            # Get route path
                            if decorator.args:
                                if isinstance(decorator.args[0], ast.Constant):
                                    route_path = decorator.args[0].value
                                elif isinstance(decorator.args[0], ast.Str):
                                    route_path = decorator.args[0].s
                            
                            # Get route methods
                            for keyword in decorator.keywords:
                                if keyword.arg == 'methods':
                                    if isinstance(keyword.value, ast.List):
                                        route_methods = [elem.value if isinstance(elem, ast.Constant) else elem.s 
                                                        for elem in keyword.value.elts]
                            
                            # Check if function has authentication decorator
                            has_auth = any(
                                isinstance(d, ast.Call) and 
                                (isinstance(d.func, ast.Name) and d.func.id == 'require_auth' or
                                 isinstance(d.func, ast.Attribute) and d.func.attr == 'require_auth')
                                for d in node.decorator_list
                            )
                            
                            endpoints.append({
                                'function': node.name,
                                'path': route_path,
                                'methods': route_methods,
                                'has_auth': has_auth,
                                'line': node.lineno
                            })
        
        return endpoints
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def audit_api_security(api_file_path):
    """
    Audit API security and generate report
    """
    print("🔐 XVPN API Security Audit")
    print("=" * 30)
    
    # Find all endpoints
    endpoints = find_api_endpoints(api_file_path)
    
    if not endpoints:
        print("❌ No endpoints found or error parsing file")
        return
    
    print(f"📊 Found {len(endpoints)} API endpoints")
    print()
    
    # Categorize endpoints
    unprotected_endpoints = []
    protected_endpoints = []
    admin_endpoints = []
    
    for endpoint in endpoints:
        if endpoint['has_auth']:
            protected_endpoints.append(endpoint)
            # Check if it's an admin endpoint
            if 'admin' in endpoint['path'] or 'admin' in endpoint['function']:
                admin_endpoints.append(endpoint)
        else:
            unprotected_endpoints.append(endpoint)
    
    # Display results
    print("✅ Protected Endpoints:")
    if protected_endpoints:
        for endpoint in protected_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"   {endpoint['path']} ({methods}) - Line {endpoint['line']}")
    else:
        print("   None")
    print()
    
    print("❌ Unprotected Endpoints:")
    if unprotected_endpoints:
        for endpoint in unprotected_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"   {endpoint['path']} ({methods}) - Line {endpoint['line']}")
    else:
        print("   None")
    print()
    
    print("👑 Admin Endpoints:")
    if admin_endpoints:
        for endpoint in admin_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"   {endpoint['path']} ({methods}) - Line {endpoint['line']}")
    else:
        print("   None")
    print()
    
    # Security recommendations
    print("💡 Security Recommendations:")
    if unprotected_endpoints:
        print("   🔒 Add authentication to unprotected endpoints:")
        for endpoint in unprotected_endpoints:
            print(f"      - {endpoint['path']} ({', '.join(endpoint['methods'])})")
        print()
    
    if admin_endpoints:
        print("   👑 Verify admin endpoints have proper permissions:")
        for endpoint in admin_endpoints:
            print(f"      - {endpoint['path']} ({', '.join(endpoint['methods'])})")
        print()
    
    # Summary
    total_endpoints = len(endpoints)
    protected_count = len(protected_endpoints)
    unprotected_count = len(unprotected_endpoints)
    
    print("📈 Security Summary:")
    print(f"   Total Endpoints: {total_endpoints}")
    print(f"   Protected: {protected_count} ({protected_count/total_endpoints*100:.1f}%)")
    print(f"   Unprotected: {unprotected_count} ({unprotected_count/total_endpoints*100:.1f}%)")
    
    if unprotected_count > 0:
        print("   🔴 Security Risk: Unprotected endpoints detected")
    else:
        print("   🟢 Security Status: All endpoints protected")
    
    return {
        'total_endpoints': total_endpoints,
        'protected_endpoints': protected_endpoints,
        'unprotected_endpoints': unprotected_endpoints,
        'admin_endpoints': admin_endpoints
    }

def main():
    """
    Main function
    """
    api_file_path = "/home/uss/chatvpn/server/api/app.py"
    
    if not os.path.exists(api_file_path):
        print(f"❌ API file not found: {api_file_path}")
        return 1
    
    result = audit_api_security(api_file_path)
    
    # Generate detailed report
    report_path = "/home/uss/chatvpn/security/api_security_audit_report.md"
    generate_detailed_report(result, report_path)
    
    return 0

def generate_detailed_report(audit_result, report_path):
    """
    Generate detailed security audit report
    """
    with open(report_path, 'w') as f:
        f.write("# XVPN API Security Audit Report\n\n")
        f.write("## Overview\n\n")
        f.write(f"- **Total Endpoints**: {audit_result['total_endpoints']}\n")
        f.write(f"- **Protected Endpoints**: {len(audit_result['protected_endpoints'])}\n")
        f.write(f"- **Unprotected Endpoints**: {len(audit_result['unprotected_endpoints'])}\n")
        f.write(f"- **Admin Endpoints**: {len(audit_result['admin_endpoints'])}\n\n")
        
        f.write("## Protected Endpoints\n\n")
        if audit_result['protected_endpoints']:
            for endpoint in audit_result['protected_endpoints']:
                methods = ', '.join(endpoint['methods'])
                f.write(f"- `{endpoint['path']}` ({methods}) - Line {endpoint['line']}\n")
        else:
            f.write("None\n")
        f.write("\n")
        
        f.write("## Unprotected Endpoints\n\n")
        if audit_result['unprotected_endpoints']:
            for endpoint in audit_result['unprotected_endpoints']:
                methods = ', '.join(endpoint['methods'])
                f.write(f"- `{endpoint['path']}` ({methods}) - Line {endpoint['line']}\n")
        else:
            f.write("None\n")
        f.write("\n")
        
        f.write("## Admin Endpoints\n\n")
        if audit_result['admin_endpoints']:
            for endpoint in audit_result['admin_endpoints']:
                methods = ', '.join(endpoint['methods'])
                f.write(f"- `{endpoint['path']}` ({methods}) - Line {endpoint['line']}\n")
        else:
            f.write("None\n")
        f.write("\n")
        
        f.write("## Security Recommendations\n\n")
        if audit_result['unprotected_endpoints']:
            f.write("### Add Authentication to Unprotected Endpoints\n\n")
            for endpoint in audit_result['unprotected_endpoints']:
                methods = ', '.join(endpoint['methods'])
                f.write(f"- `{endpoint['path']}` ({methods})\n")
            f.write("\n")
        
        if audit_result['admin_endpoints']:
            f.write("### Verify Admin Endpoint Permissions\n\n")
            for endpoint in audit_result['admin_endpoints']:
                methods = ', '.join(endpoint['methods'])
                f.write(f"- `{endpoint['path']}` ({methods})\n")
            f.write("\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Add `@require_auth()` decorator to unprotected endpoints\n")
        f.write("2. Verify admin endpoints have appropriate permissions\n")
        f.write("3. Test authentication with generated tokens\n")
        f.write("4. Update documentation with authentication requirements\n")
    
    print(f"📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    sys.exit(main())