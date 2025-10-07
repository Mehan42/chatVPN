#!/usr/bin/env python3
"""
XVPN API Token Generator
Generates and manages API tokens for authentication
"""

import os
import sys
import json
import time
import secrets
from pathlib import Path
from datetime import datetime

class APITokenGenerator:
    """
    Generates and manages API tokens for XVPN
    """
    
    def __init__(self, tokens_file=None):
        self.tokens_file = tokens_file or "/opt/xvpn/data/api_tokens.json"
        self.tokens_dir = Path(self.tokens_file).parent
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing tokens
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """
        Load existing tokens from file
        """
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"❌ Error loading tokens: {e}")
            return {}
    
    def _save_tokens(self):
        """
        Save tokens to file
        """
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving tokens: {e}")
            return False
    
    def _generate_secure_token(self, length=32):
        """
        Generate a cryptographically secure random token
        """
        return secrets.token_urlsafe(length)
    
    def create_token(self, name, permissions, expires_in_days=None, description=""):
        """
        Create a new API token
        """
        # Validate permissions
        valid_permissions = ["read", "write", "admin"]
        if isinstance(permissions, str):
            permissions = [permissions]
        
        for perm in permissions:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}. Valid permissions: {valid_permissions}")
        
        # Generate token
        token = self._generate_secure_token()
        
        # Create token info
        token_info = {
            "token": token,
            "permissions": permissions,
            "created_at": time.time(),
            "description": description
        }
        
        # Set expiration if specified
        if expires_in_days:
            token_info["expires_at"] = time.time() + (expires_in_days * 24 * 3600)
        else:
            token_info["expires_at"] = None  # Never expires
        
        # Add to tokens
        self.tokens[name] = token_info
        
        # Save tokens
        if self._save_tokens():
            print(f"✅ Token '{name}' created successfully!")
            print(f"   Token: {token}")
            print(f"   Permissions: {', '.join(permissions)}")
            if expires_in_days:
                expiry_date = datetime.fromtimestamp(token_info["expires_at"])
                print(f"   Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   Expires: Never")
            print(f"   Description: {description}")
            return token
        else:
            print(f"❌ Failed to save token '{name}'")
            return None
    
    def revoke_token(self, name):
        """
        Revoke an API token
        """
        if name in self.tokens:
            del self.tokens[name]
            if self._save_tokens():
                print(f"✅ Token '{name}' revoked successfully!")
                return True
            else:
                print(f"❌ Failed to save tokens after revoking '{name}'")
                return False
        else:
            print(f"❌ Token '{name}' not found!")
            return False
    
    def list_tokens(self):
        """
        List all tokens (without revealing actual token values)
        """
        if not self.tokens:
            print("📭 No tokens found")
            return
        
        print("📋 API Tokens:")
        print("=" * 50)
        
        for name, info in self.tokens.items():
            # Mask token value
            token_preview = info.get("token", "")[:10] + "..." if info.get("token") else "None"
            
            # Format permissions
            permissions = ", ".join(info.get("permissions", []))
            
            # Format expiration
            expires_at = info.get("expires_at")
            if expires_at:
                if time.time() > expires_at:
                    expiry_status = "EXPIRED"
                else:
                    expiry_date = datetime.fromtimestamp(expires_at)
                    expiry_status = expiry_date.strftime('%Y-%m-%d')
            else:
                expiry_status = "Never"
            
            # Format creation
            created_at = info.get("created_at")
            if created_at:
                creation_date = datetime.fromtimestamp(created_at)
                created_str = creation_date.strftime('%Y-%m-%d')
            else:
                created_str = "Unknown"
            
            print(f"🔖 Name: {name}")
            print(f"   Preview: {token_preview}")
            print(f"   Permissions: {permissions}")
            print(f"   Created: {created_str}")
            print(f"   Expires: {expiry_status}")
            print(f"   Description: {info.get('description', 'No description')}")
            print()
    
    def show_token(self, name):
        """
        Show detailed information about a specific token
        """
        if name not in self.tokens:
            print(f"❌ Token '{name}' not found!")
            return
        
        info = self.tokens[name]
        
        print(f"🔑 Token Details: {name}")
        print("=" * 30)
        print(f"Token: {info.get('token', 'None')}")
        print(f"Permissions: {', '.join(info.get('permissions', []))}")
        print(f"Created: {datetime.fromtimestamp(info.get('created_at')).strftime('%Y-%m-%d %H:%M:%S')}")
        
        expires_at = info.get("expires_at")
        if expires_at:
            if time.time() > expires_at:
                print(f"Expires: EXPIRED ({datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print(f"Expires: {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Expires: Never")
        
        print(f"Description: {info.get('description', 'No description')}")
    
    def generate_default_tokens(self):
        """
        Generate default tokens for fresh installation
        """
        print("🔐 Generating default API tokens...")
        
        # Admin token
        admin_token = self.create_token(
            name="admin",
            permissions=["admin", "read", "write"],
            description="Default admin token with full permissions"
        )
        
        # Client token
        client_token = self.create_token(
            name="client",
            permissions=["read"],
            description="Default client token with read-only access"
        )
        
        # Bot token
        bot_token = self.create_token(
            name="bot",
            permissions=["read", "write"],
            description="Telegram bot token for administrative functions"
        )
        
        return {
            "admin": admin_token,
            "client": client_token,
            "bot": bot_token
        }

def main():
    """
    Main function to manage API tokens
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN API Token Generator")
    parser.add_argument("action", choices=["create", "revoke", "list", "show", "generate-defaults"],
                       help="Action to perform")
    parser.add_argument("--name", help="Token name")
    parser.add_argument("--permissions", help="Comma-separated permissions (read,write,admin)")
    parser.add_argument("--expires", type=int, help="Expiration in days")
    parser.add_argument("--description", help="Token description")
    parser.add_argument("--tokens-file", default="/opt/xvpn/data/api_tokens.json",
                       help="Tokens file path")
    
    args = parser.parse_args()
    
    # Create token generator
    generator = APITokenGenerator(tokens_file=args.tokens_file)
    
    if args.action == "create":
        if not args.name:
            print("❌ --name is required for create action")
            return 1
        
        permissions = args.permissions.split(",") if args.permissions else ["read"]
        
        token = generator.create_token(
            name=args.name,
            permissions=permissions,
            expires_in_days=args.expires,
            description=args.description or f"Token created on {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        if token:
            return 0
        else:
            return 1
    
    elif args.action == "revoke":
        if not args.name:
            print("❌ --name is required for revoke action")
            return 1
        
        if generator.revoke_token(args.name):
            return 0
        else:
            return 1
    
    elif args.action == "list":
        generator.list_tokens()
        return 0
    
    elif args.action == "show":
        if not args.name:
            print("❌ --name is required for show action")
            return 1
        
        generator.show_token(args.name)
        return 0
    
    elif args.action == "generate-defaults":
        tokens = generator.generate_default_tokens()
        if tokens:
            print(f"\n🔐 Default tokens generated successfully!")
            print(f"   Admin token: {tokens['admin'][:10]}...")
            print(f"   Client token: {tokens['client'][:10]}...")
            print(f"   Bot token: {tokens['bot'][:10]}...")
            return 0
        else:
            print("❌ Failed to generate default tokens")
            return 1

if __name__ == "__main__":
    sys.exit(main())