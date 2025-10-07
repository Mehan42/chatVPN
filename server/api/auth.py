#!/usr/bin/env python3
"""
XVPN Authentication Middleware
Provides token-based authentication for API endpoints
"""

import os
import json
import hashlib
import hmac
import time
import secrets
from functools import wraps
from flask import request, jsonify, g
from pathlib import Path

class AuthManager:
    """
    Manages API authentication tokens and access control
    """
    
    def __init__(self, tokens_file=None):
        self.tokens_file = tokens_file or "/opt/xvpn/data/api_tokens.json"
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """
        Load API tokens from file
        """
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default tokens file
                return self._create_default_tokens()
        except Exception as e:
            print(f"❌ Error loading API tokens: {e}")
            return {}
    
    def _create_default_tokens(self):
        """
        Create default API tokens file
        """
        try:
            # Create directory if it doesn't exist
            tokens_dir = os.path.dirname(self.tokens_file)
            os.makedirs(tokens_dir, exist_ok=True)
            
            # Generate default admin token
            default_tokens = {
                "admin": {
                    "token": self._generate_secure_token(),
                    "permissions": ["admin", "read", "write"],
                    "created_at": time.time(),
                    "expires_at": None,  # Never expires
                    "description": "Default admin token"
                },
                "client": {
                    "token": self._generate_secure_token(),
                    "permissions": ["read"],
                    "created_at": time.time(),
                    "expires_at": None,  # Never expires
                    "description": "Default client token"
                }
            }
            
            # Save tokens
            self._save_tokens(default_tokens)
            print(f"✅ Created default API tokens file: {self.tokens_file}")
            
            return default_tokens
        except Exception as e:
            print(f"❌ Error creating default API tokens: {e}")
            return {}
    
    def _save_tokens(self, tokens):
        """
        Save API tokens to file
        """
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving API tokens: {e}")
            return False
    
    def _generate_secure_token(self, length=32):
        """
        Generate a cryptographically secure random token
        """
        return secrets.token_urlsafe(length)
    
    def authenticate_token(self, token):
        """
        Authenticate a token and return token info if valid
        """
        if not token:
            return None
        
        # Check each token
        for token_name, token_info in self.tokens.items():
            if token_info.get("token") == token:
                # Check expiration
                expires_at = token_info.get("expires_at")
                if expires_at and time.time() > expires_at:
                    continue  # Token expired
                
                # Token is valid
                return {
                    "name": token_name,
                    "permissions": token_info.get("permissions", []),
                    "description": token_info.get("description", ""),
                    "created_at": token_info.get("created_at")
                }
        
        return None
    
    def has_permission(self, token_info, required_permission):
        """
        Check if token has required permission
        """
        if not token_info:
            return False
        
        permissions = token_info.get("permissions", [])
        return "admin" in permissions or required_permission in permissions
    
    def create_token(self, name, permissions, expires_in_days=None, description=""):
        """
        Create a new API token
        """
        token = self._generate_secure_token()
        
        token_info = {
            "token": token,
            "permissions": permissions,
            "created_at": time.time(),
            "description": description
        }
        
        if expires_in_days:
            token_info["expires_at"] = time.time() + (expires_in_days * 24 * 3600)
        else:
            token_info["expires_at"] = None  # Never expires
        
        # Add to tokens
        self.tokens[name] = token_info
        
        # Save tokens
        self._save_tokens(self.tokens)
        
        return token
    
    def revoke_token(self, name):
        """
        Revoke an API token
        """
        if name in self.tokens:
            del self.tokens[name]
            self._save_tokens(self.tokens)
            return True
        return False
    
    def list_tokens(self):
        """
        List all tokens (without revealing actual token values)
        """
        token_list = []
        for name, info in self.tokens.items():
            token_list.append({
                "name": name,
                "permissions": info.get("permissions", []),
                "description": info.get("description", ""),
                "created_at": info.get("created_at"),
                "expires_at": info.get("expires_at")
            })
        return token_list

# Global auth manager instance
auth_manager = AuthManager()

def require_auth(required_permissions=None):
    """
    Decorator to require authentication for API endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    "error": "Missing Authorization header",
                    "message": "Token required for this endpoint"
                }), 401
            
            # Parse Bearer token
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    "error": "Invalid Authorization header",
                    "message": "Use 'Bearer <token>' format"
                }), 401
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Authenticate token
            token_info = auth_manager.authenticate_token(token)
            
            if not token_info:
                return jsonify({
                    "error": "Invalid or expired token",
                    "message": "Provided token is not valid"
                }), 401
            
            # Check permissions if required
            if required_permissions:
                if isinstance(required_permissions, str):
                    required_permissions = [required_permissions]
                
                for perm in required_permissions:
                    if not auth_manager.has_permission(token_info, perm):
                        return jsonify({
                            "error": "Insufficient permissions",
                            "message": f"Token lacks required permission: {perm}",
                            "available_permissions": token_info.get("permissions", [])
                        }), 403
            
            # Store token info in request context
            g.current_token = token_info
            
            # Call the original function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def generate_admin_token():
    """
    Generate and display admin token for initial setup
    """
    print("🔐 XVPN Admin Token Generator")
    print("=" * 35)
    
    # Check if tokens file exists
    if os.path.exists("/opt/xvpn/data/api_tokens.json"):
        print("⚠️  API tokens file already exists!")
        print("   Loading existing tokens...")
        
        # Load existing tokens
        tokens = auth_manager._load_tokens()
        
        # Find admin token
        admin_token = None
        for name, info in tokens.items():
            if "admin" in info.get("permissions", []):
                admin_token = info.get("token")
                print(f"✅ Found existing admin token: {name}")
                break
        
        if admin_token:
            print(f"\n🔑 Admin Token:")
            print(f"   {admin_token}")
            print(f"\n💡 Usage:")
            print(f"   curl -H \"Authorization: Bearer {admin_token[:10]}...\" https://your-server/mcp/v1/admin.endpoint")
            return admin_token
        else:
            print("❌ No admin token found in existing tokens!")
    else:
        print("📋 Creating new API tokens file...")
        
        # Create default tokens
        tokens = auth_manager._create_default_tokens()
        
        # Find admin token
        admin_token = tokens.get("admin", {}).get("token")
        
        if admin_token:
            print(f"\n✅ API tokens file created successfully!")
            print(f"\n🔑 Admin Token:")
            print(f"   {admin_token}")
            print(f"\n💡 Usage:")
            print(f"   curl -H \"Authorization: Bearer {admin_token[:10]}...\" https://your-server/mcp/v1/admin.endpoint")
            return admin_token
        else:
            print("❌ Failed to create admin token!")
            return None

if __name__ == "__main__":
    # Generate and display admin token when run as script
    generate_admin_token()