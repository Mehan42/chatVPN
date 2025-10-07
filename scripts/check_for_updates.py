#!/usr/bin/env python3
"""
XVPN Update Checker
Checks for available updates and notifies users
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

class XVPNUpdateChecker:
    """
    Checks for XVPN updates and manages notifications
    """
    
    def __init__(self, repo_url="https://github.com/Mehan42/chatVPN"):
        self.repo_url = repo_url
        self.local_dir = Path.home() / "chatvpn"
        self.server_dir = Path("/opt/xvpn")
        self.last_check_file = self.local_dir / "logs" / "last_update_check.json"
        
        # Create logs directory
        self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_local_commit(self):
        """
        Get local repository commit hash
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.local_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def get_remote_commit(self):
        """
        Get remote repository commit hash
        """
        try:
            # Use GitHub API to get latest commit
            api_url = "https://api.github.com/repos/Mehan42/chatVPN/commits/main"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            commit_data = response.json()
            return commit_data["sha"]
        except Exception as e:
            print(f"❌ Error getting remote commit: {e}")
            return None
    
    def check_for_updates(self):
        """
        Check if updates are available
        """
        print("🔍 Checking for XVPN updates...")
        
        local_commit = self.get_local_commit()
        remote_commit = self.get_remote_commit()
        
        if not local_commit:
            print("❌ Error getting local commit")
            return False
            
        if not remote_commit:
            print("❌ Error getting remote commit")
            return False
        
        print(f"   Local commit:  {local_commit[:8]}")
        print(f"   Remote commit: {remote_commit[:8]}")
        
        if local_commit == remote_commit:
            print("✅ Client is up to date")
            self.save_last_check(local_commit, remote_commit, False)
            return False
        else:
            print("🆕 Update available!")
            self.save_last_check(local_commit, remote_commit, True)
            return True
    
    def save_last_check(self, local_commit, remote_commit, update_available):
        """
        Save last check results
        """
        check_data = {
            "timestamp": time.time(),
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "update_available": update_available,
            "checked_at": datetime.now().isoformat()
        }
        
        try:
            with open(self.last_check_file, "w") as f:
                json.dump(check_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving last check: {e}")
    
    def load_last_check(self):
        """
        Load last check results
        """
        try:
            if self.last_check_file.exists():
                with open(self.last_check_file, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"❌ Error loading last check: {e}")
            return None
    
    def get_update_details(self):
        """
        Get detailed information about available updates
        """
        try:
            # Get commit history
            api_url = "https://api.github.com/repos/Mehan42/chatVPN/commits"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            commits = response.json()
            
            # Get local commit
            local_commit = self.get_local_commit()
            
            # Find commits since local version
            new_commits = []
            for commit in commits:
                if commit["sha"] == local_commit:
                    break
                new_commits.append({
                    "sha": commit["sha"][:8],
                    "message": commit["commit"]["message"].split('\n')[0],
                    "author": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"]
                })
            
            return new_commits
            
        except Exception as e:
            print(f"❌ Error getting update details: {e}")
            return []
    
    def notify_updates(self, update_available):
        """
        Notify user about available updates
        """
        if not update_available:
            return
        
        print("\n📢 Update Notification")
        print("=" * 25)
        
        # Get update details
        updates = self.get_update_details()
        
        if updates:
            print(f"🆕 {len(updates)} new commits available:")
            for update in updates[:5]:  # Show only first 5
                print(f"   {update['sha']} - {update['message']}")
            
            if len(updates) > 5:
                print(f"   ... and {len(updates) - 5} more commits")
        else:
            print("🆕 New updates available")
        
        print("\n💡 To update:")
        print("   cd ~/chatvpn && ./scripts/update_client.sh")
    
    def check_server_updates(self):
        """
        Check if server updates are needed
        """
        print("\n🔍 Checking server updates...")
        
        if not self.server_dir.exists():
            print("⚠️  Server directory not found, skipping server update check")
            return
        
        try:
            # Check server commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.server_dir,
                capture_output=True,
                text=True,
                check=True
            )
            server_commit = result.stdout.strip()
            
            # Compare with remote
            remote_commit = self.get_remote_commit()
            
            if server_commit and remote_commit:
                print(f"   Server commit: {server_commit[:8]}")
                print(f"   Remote commit: {remote_commit[:8]}")
                
                if server_commit == remote_commit:
                    print("✅ Server is up to date")
                    return False
                else:
                    print("🆕 Server update available!")
                    return True
            else:
                print("⚠️  Could not determine server update status")
                return False
                
        except subprocess.CalledProcessError:
            print("⚠️  Could not check server commit")
            return False
        except Exception as e:
            print(f"❌ Error checking server updates: {e}")
            return False
    
    def run_update_check(self):
        """
        Run complete update check
        """
        print("🔄 XVPN Update Checker")
        print("=" * 25)
        
        # Check client updates
        update_available = self.check_for_updates()
        
        # Check server updates
        server_update_needed = self.check_server_updates()
        
        # Notify about updates
        self.notify_updates(update_available)
        
        # Summary
        print(f"\n📊 Update Status:")
        print(f"   Client update available: {'Yes' if update_available else 'No'}")
        print(f"   Server update available: {'Yes' if server_update_needed else 'No'}")
        
        if update_available or server_update_needed:
            print(f"\n💡 Recommendation: Run update scripts")
            if update_available:
                print(f"   Client: ~/chatvpn/scripts/update_client.sh")
            if server_update_needed:
                print(f"   Server: sudo /opt/xvpn/scripts/update_server.sh")
        
        return update_available or server_update_needed

def main():
    """
    Main function to check for updates
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN Update Checker")
    parser.add_argument("--notify", action="store_true",
                       help="Show notifications for available updates")
    parser.add_argument("--check-interval", type=int, default=86400,  # 24 hours
                       help="Minimum interval between checks (seconds)")
    
    args = parser.parse_args()
    
    # Create update checker
    checker = XVPNUpdateChecker()
    
    # Check last check time
    last_check = checker.load_last_check()
    if last_check:
        time_since_last_check = time.time() - last_check.get("timestamp", 0)
        if time_since_last_check < args.check_interval:
            if not args.notify:
                print(f"🕒 Checked recently ({time_since_last_check/3600:.1f} hours ago), skipping check")
                return 0
    
    # Run update check
    updates_available = checker.run_update_check()
    
    return 0 if not updates_available else 1

if __name__ == "__main__":
    sys.exit(main())