#!/usr/bin/env python3
"""
XVPN Project Status Checker
Checks the overall status of the XVPN project and generates a comprehensive report
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_git_status():
    """
    Check Git repository status
    """
    print("🔍 Checking Git repository status...")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode != 0:
            print("❌ Not in a Git repository")
            return False
        
        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            print(f"✅ Current branch: {current_branch}")
        else:
            print("❌ Error getting current branch")
            return False
        
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("❌ Uncommitted changes found:")
                print(result.stdout)
                return False
            else:
                print("✅ No uncommitted changes")
        else:
            print("❌ Error checking Git status")
            return False
        
        # Check if local branch is ahead of remote
        result = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..main"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode == 0:
            ahead_count = int(result.stdout.strip())
            if ahead_count > 0:
                print(f"❌ Local branch is {ahead_count} commits ahead of remote")
                return False
            else:
                print("✅ Local branch is up to date with remote")
        else:
            print("❌ Error checking branch status")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Git status: {e}")
        return False

def check_github_commit():
    """
    Check if the latest commit exists on GitHub
    """
    print("🔍 Checking GitHub for latest commit...")
    
    try:
        # Get latest local commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode != 0:
            print("❌ Error getting local commit hash")
            return False
        
        local_commit_hash = result.stdout.strip()[:7]  # Short hash
        print(f"✅ Latest local commit: {local_commit_hash}")
        
        # Check GitHub API for this commit
        repo_url = "https://api.github.com/repos/Mehan42/chatVPN/commits"
        response = subprocess.run(
            ["curl", "-s", repo_url],
            capture_output=True,
            text=True
        )
        
        if response.returncode == 0:
            try:
                commits = json.loads(response.stdout)
                if commits and len(commits) > 0:
                    latest_github_commit = commits[0]["sha"][:7]  # Short hash
                    print(f"✅ Latest GitHub commit: {latest_github_commit}")
                    
                    if local_commit_hash == latest_github_commit:
                        print("✅ Local and GitHub commits match")
                        return True
                    else:
                        print("❌ Local and GitHub commits do not match")
                        return False
                else:
                    print("❌ No commits found on GitHub")
                    return False
            except json.JSONDecodeError:
                print("❌ Error parsing GitHub API response")
                return False
        else:
            print(f"❌ Error accessing GitHub API: {response.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking GitHub commit: {e}")
        return False

def check_project_structure():
    """
    Check project directory structure
    """
    print("🔍 Checking project directory structure...")
    
    required_dirs = [
        "client",
        "server",
        "scripts",
        "docs",
        "security"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = Path("/home/uss/chatvpn") / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ All required directories present")
        return True

def check_key_files():
    """
    Check for key project files
    """
    print("🔍 Checking key project files...")
    
    # Key files that should exist
    key_files = [
        "server/api/app.py",
        "client/chatvpn_backend.py",
        "scripts/install_server.sh",
        "scripts/install_client.sh",
        "docs/USER_GUIDE.md",
        "docs/INSTALLATION_GUIDE.md",
        "docs/API_AUTHENTICATION.md",
        "docs/TLS_DEPLOYMENT_GUIDE.md",
        "docs/SECURITY_BEST_PRACTICES.md",
        "security/tls/cert.pem",
        "security/tls/key.pem"
    ]
    
    missing_files = []
    for file_path in key_files:
        full_path = Path("/home/uss/chatvpn") / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing key files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All key files present")
        return True

def check_dependencies():
    """
    Check for required dependencies
    """
    print("🔍 Checking dependencies...")
    
    # Required Python packages
    required_packages = [
        "flask",
        "requests",
        "psutil",
        "cryptography",
        "pyopenssl"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ All required Python packages installed")
        return True

def check_security_implementation():
    """
    Check security implementation status
    """
    print("🔍 Checking security implementation...")
    
    # Security implementation checks
    security_checks = [
        ("HTTPS/TLS Implementation", "server/api/app.py", "ssl_context"),
        ("Certificate Management", "scripts/generate_tls_certs.sh", "openssl"),
        ("Certificate Pinning", "client/chatvpn_backend.py", "verify_certificate_fingerprint"),
        ("API Authentication", "server/api/auth.py", "require_auth"),
        ("Security Testing", "scripts/test_api_auth.py", "test_api_auth")
    ]
    
    failed_checks = []
    for check_name, file_path, keyword in security_checks:
        full_path = Path("/home/uss/chatvpn") / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    if keyword in content:
                        print(f"   ✅ {check_name}: Implemented")
                    else:
                        print(f"   ❌ {check_name}: Not implemented")
                        failed_checks.append(check_name)
            except Exception as e:
                print(f"   ❌ {check_name}: Error reading file - {e}")
                failed_checks.append(check_name)
        else:
            print(f"   ❌ {check_name}: File not found")
            failed_checks.append(check_name)
    
    if failed_checks:
        print(f"❌ Security implementation incomplete: {', '.join(failed_checks)}")
        return False
    else:
        print("✅ All security features implemented")
        return True

def generate_final_report(git_status, github_status, structure_status, files_status, deps_status, security_status):
    """
    Generate final project status report
    """
    print("\n" + "=" * 50)
    print("📊 XVPN Project Status Report")
    print("=" * 50)
    
    # Overall status
    all_checks = [git_status, github_status, structure_status, files_status, deps_status, security_status]
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    print(f"\n📈 Overall Status: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("✅ PROJECT READY FOR PRODUCTION DEPLOYMENT!")
        print("🎉 All checks PASSED!")
        overall_status = "SUCCESS"
    elif passed_checks >= total_checks * 0.8:
        print("🟡 PROJECT ALMOST READY FOR PRODUCTION")
        print("⚠️  Most checks PASSED with minor issues")
        overall_status = "WARN"
    else:
        print("🔴 PROJECT NOT READY FOR PRODUCTION")
        print("❌ Many checks FAILED!")
        overall_status = "FAIL"
    
    # Detailed results
    print(f"\n🔍 Detailed Results:")
    checks = [
        ("Git Repository Status", git_status),
        ("GitHub Commit Status", github_status),
        ("Project Structure", structure_status),
        ("Key Files Presence", files_status),
        ("Dependencies", deps_status),
        ("Security Implementation", security_status)
    ]
    
    for check_name, status in checks:
        symbol = "✅" if status else "❌"
        print(f"   {symbol} {check_name}: {'PASSED' if status else 'FAILED'}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if not git_status:
        print("   🔧 Fix Git repository issues")
    if not github_status:
        print("   🔄 Push local changes to GitHub")
    if not structure_status:
        print("   📁 Fix project directory structure")
    if not files_status:
        print("   📄 Create missing key files")
    if not deps_status:
        print("   📦 Install missing dependencies")
    if not security_status:
        print("   🔐 Complete security implementation")
    
    # Next steps
    print(f"\n🚀 Next Steps:")
    if overall_status == "SUCCESS":
        print("   🎉 Deploy to production server (77.110.123.27)")
        print("   🧪 Test HTTPS/TLS connectivity")
        print("   🔍 Verify certificate pinning")
        print("   🛡️ Test API authentication")
    elif overall_status == "WARN":
        print("   🛠️  Fix minor issues")
        print("   🧪 Test functionality")
        print("   🔄 Update repository")
        print("   📦 Install dependencies")
    else:
        print("   🛠️  Fix critical issues")
        print("   📁 Organize project structure")
        print("   📄 Create missing files")
        print("   🔐 Implement security features")
    
    return overall_status

def main():
    """
    Main function to run project status check
    """
    print("🧪 XVPN Project Status Checker")
    print("=" * 30)
    
    # Run all checks
    git_status = check_git_status()
    print()
    
    github_status = check_github_commit()
    print()
    
    structure_status = check_project_structure()
    print()
    
    files_status = check_key_files()
    print()
    
    deps_status = check_dependencies()
    print()
    
    security_status = check_security_implementation()
    print()
    
    # Generate report
    overall_status = generate_final_report(
        git_status, 
        github_status, 
        structure_status, 
        files_status, 
        deps_status, 
        security_status
    )
    
    # Exit code
    if overall_status == "SUCCESS":
        print(f"\n🎊 Project is ready for production deployment!")
        return 0
    elif overall_status == "WARN":
        print(f"\n⚠️  Project almost ready, fix minor issues")
        return 1
    else:
        print(f"\n🚨 Project not ready, fix critical issues")
        return 2

if __name__ == "__main__":
    sys.exit(main())