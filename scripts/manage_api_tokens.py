#!/usr/bin/env python3
"""
XVPN API Token Manager
Script to generate, list, and manage API tokens
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from server.api.auth import AuthManager
except ImportError:
    try:
        # Try relative import
        from .auth import AuthManager
    except ImportError:
        # Try absolute import
        sys.path.append(str(Path(__file__).parent))
        from auth import AuthManager

def main():
    """
    Main function to manage API tokens
    """
    parser = argparse.ArgumentParser(description="XVPN API Token Manager")
    parser.add_argument("action", choices=["generate", "list", "create", "revoke", "show"], 
                       help="Action to perform")
    parser.add_argument("--name", help="Token name")
    parser.add_argument("--permissions", help="Comma-separated permissions (e.g., admin,read,write)")
    parser.add_argument("--expires", type=int, help="Expiration in days")
    parser.add_argument("--description", help="Token description")
    
    args = parser.parse_args()
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    if args.action == "generate":
        # Generate and show admin token
        print("🔐 XVPN API Token Generator")
        print("=" * 35)
        
        # Check if tokens file exists
        tokens_file = "/opt/xvpn/data/api_tokens.json"
        if os.path.exists(tokens_file):
            print("📋 Loading existing tokens...")
            tokens = auth_manager._load_tokens()
        else:
            print("📋 Creating new tokens file...")
            tokens = auth_manager._create_default_tokens()
        
        # Find or create admin token
        admin_token = None
        admin_token_name = None
        
        # Look for existing admin token
        for name, info in tokens.items():
            if "admin" in info.get("permissions", []):
                admin_token = info.get("token")
                admin_token_name = name
                break
        
        # If no admin token found, create one
        if not admin_token:
            print("⚠️  No admin token found, creating new one...")
            admin_token = auth_manager._generate_secure_token()
            admin_token_name = "admin_auto_generated"
            
            # Add to tokens
            tokens[admin_token_name] = {
                "token": admin_token,
                "permissions": ["admin", "read", "write"],
                "created_at": __import__('time').time(),
                "expires_at": None,
                "description": "Auto-generated admin token"
            }
            
            # Save tokens
            auth_manager._save_tokens(tokens)
        
        if admin_token:
            print(f"\n✅ Admin Token Generated Successfully!")
            print(f"   Name: {admin_token_name}")
            print(f"   Token: {admin_token}")
            print(f"   Permissions: admin, read, write")
            print(f"\n💡 Usage Examples:")
            print(f"   curl -H \"Authorization: Bearer {admin_token}\" https://your-server/mcp/v1/admin.newclient")
            print(f"   export XVPN_API_TOKEN={admin_token}")
        else:
            print("❌ Failed to generate admin token!")
            return 1
            
    elif args.action == "list":
        # List all tokens
        print("📋 XVPN API Tokens")
        print("=" * 20)
        
        tokens = auth_manager.list_tokens()
        
        if tokens:
            for token_info in tokens:
                print(f"\n🏷️  Name: {token_info['name']}")
                print(f"   Permissions: {', '.join(token_info['permissions'])}")
                print(f"   Description: {token_info['description']}")
                print(f"   Created: {token_info['created_at']}")
                if token_info['expires_at']:
                    print(f"   Expires: {token_info['expires_at']}")
                else:
                    print(f"   Expires: Never")
        else:
            print("❌ No tokens found!")
            
    elif args.action == "create":
        # Create new token
        if not args.name:
            print("❌ --name is required for create action!")
            return 1
            
        if not args.permissions:
            print("❌ --permissions is required for create action!")
            return 1
            
        permissions = args.permissions.split(",")
        expires_in_days = args.expires
        description = args.description or f"Token created on {__import__('time').strftime('%Y-%m-%d')}"
        
        # Create token
        token = auth_manager._generate_secure_token()
        
        # Add to tokens
        tokens = auth_manager._load_tokens()
        tokens[args.name] = {
            "token": token,
            "permissions": permissions,
            "created_at": __import__('time').time(),
            "expires_at": __import__('time').time() + (expires_in_days * 24 * 3600) if expires_in_days else None,
            "description": description
        }
        
        # Save tokens
        if auth_manager._save_tokens(tokens):
            print(f"✅ Token '{args.name}' created successfully!")
            print(f"   Token: {token}")
            print(f"   Permissions: {', '.join(permissions)}")
            if expires_in_days:
                print(f"   Expires in: {expires_in_days} days")
            else:
                print(f"   Expires: Never")
        else:
            print("❌ Failed to create token!")
            return 1
            
    elif args.action == "revoke":
        # Revoke token
        if not args.name:
            print("❌ --name is required for revoke action!")
            return 1
            
        tokens = auth_manager._load_tokens()
        if args.name in tokens:
            del tokens[args.name]
            if auth_manager._save_tokens(tokens):
                print(f"✅ Token '{args.name}' revoked successfully!")
            else:
                print("❌ Failed to save tokens after revocation!")
                return 1
        else:
            print(f"❌ Token '{args.name}' not found!")
            return 1
            
    elif args.action == "show":
        # Show specific token details
        if not args.name:
            print("❌ --name is required for show action!")
            return 1
            
        tokens = auth_manager._load_tokens()
        if args.name in tokens:
            token_info = tokens[args.name]
            print(f"🏷️  Token Details: {args.name}")
            print(f"   Permissions: {', '.join(token_info['permissions'])}")
            print(f"   Description: {token_info['description']}")
            print(f"   Created: {token_info['created_at']}")
            if token_info['expires_at']:
                print(f"   Expires: {token_info['expires_at']}")
            else:
                print(f"   Expires: Never")
        else:
            print(f"❌ Token '{args.name}' not found!")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())