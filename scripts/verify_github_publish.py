#!/usr/bin/env python3
"""
XVPN GitHub Publish Verification Script
Verifies that all changes have been successfully published to GitHub
"""

import os
import sys
import subprocess
import requests
import json
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
        response = requests.get(repo_url, timeout=10)
        
        if response.status_code == 200:
            commits = response.json()
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
        else:
            print(f"❌ Error accessing GitHub API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking GitHub commit: {e}")
        return False

def check_published_files():
    """
    Check if key security files are published to GitHub
    """
    print("🔍 Checking published security files...")
    
    # Key security files that should be published
    security_files = [
        "docs/API_AUTHENTICATION_GUIDE.md",
        "docs/CERTIFICATE_MANAGEMENT_GUIDE.md",
        "docs/FINAL_PROJECT_STATUS_REPORT.md",
        "docs/FINAL_SECURITY_IMPLEMENTATION_REPORT.md",
        "docs/PROJECT_COMPLETION_REPORT.md",
        "docs/SECURITY_BEST_PRACTICES.md",
        "docs/SECURITY_IMPLEMENTATION_SUMMARY.md",
        "docs/THREAT_MODELING_AND_MITIGATION.md",
        "docs/TLS_DEPLOYMENT_GUIDE.md",
        "scripts/deploy_certificates.sh",
        "scripts/extract_cert_fingerprints.py",
        "scripts/generate_tls_certs.sh",
        "scripts/install_tls_certs.sh",
        "scripts/manage_api_tokens.py",
        "scripts/monitor_certificates.py",
        "scripts/renew_certificates.py",
        "scripts/security_health_check.py",
        "scripts/test_https_connection.py",
        "scripts/test_production_server.py",
        "scripts/update_cert_fingerprints.py",
        "server/api/auth.py"
    ]
    
    missing_files = []
    found_files = []
    
    for file_path in security_files:
        full_path = f"https://github.com/Mehan42/chatVPN/blob/main/{file_path}"
        try:
            response = requests.head(full_path, timeout=5)
            if response.status_code == 200:
                found_files.append(file_path)
            else:
                missing_files.append(file_path)
        except Exception as e:
            missing_files.append(file_path)
    
    print(f"✅ Found {len(found_files)} security files on GitHub")
    print(f"❌ Missing {len(missing_files)} security files on GitHub")
    
    if missing_files:
        print("Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    return True

def check_repository_integrity():
    """
    Check overall repository integrity
    """
    print("🔍 Checking repository integrity...")
    
    try:
        # Check repository URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd="/home/uss/chatvpn"
        )
        
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            print(f"✅ Remote URL: {remote_url}")
            
            if "Mehan42/chatVPN" in remote_url:
                print("✅ Repository URL is correct")
                return True
            else:
                print("❌ Repository URL is incorrect")
                return False
        else:
            print("❌ Error getting remote URL")
            return False
            
    except Exception as e:
        print(f"❌ Error checking repository integrity: {e}")
        return False

def main():
    """
    Main function to verify GitHub publish
    """
    print("🚀 XVPN GitHub Publish Verification")
    print("=" * 40)
    
    # Run all checks
    checks = [
        ("Git Status", check_git_status),
        ("GitHub Commit", check_github_commit),
        ("Published Files", check_published_files),
        ("Repository Integrity", check_repository_integrity)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 20)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Publish Verification Summary")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} checks")
    print(f"❌ Failed: {total - passed}/{total} checks")
    
    if passed == total:
        print("\n🎉 All checks PASSED! Changes successfully published to GitHub.")
        print("✅ Repository is up to date with all security enhancements.")
        return 0
    else:
        print("\n❌ Some checks FAILED! Please review the errors above.")
        print("⚠️  Repository may not be fully synchronized with GitHub.")
        return 1

if __name__ == "__main__":
    sys.exit(main())