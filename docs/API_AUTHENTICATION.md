# 🔐 XVPN API Authentication Documentation

## Overview

This document describes the token-based authentication system for XVPN API endpoints, including how to generate, manage, and use API tokens.

## Authentication Architecture

XVPN API uses Bearer token authentication with the following components:

1. **Token Manager** - Generates and manages API tokens
2. **Authentication Middleware** - Validates tokens on protected endpoints
3. **Permission System** - Controls access based on token permissions
4. **Token Storage** - Securely stores tokens with expiration dates

## Token Types

### Admin Token
- **Permissions**: `admin`, `read`, `write`
- **Usage**: Administrative functions, client management
- **Expiration**: Never expires (unless manually revoked)

### Client Token
- **Permissions**: `read`
- **Usage**: Client configuration retrieval
- **Expiration**: Never expires (unless manually revoked)

### Bot Token
- **Permissions**: `read`, `write`
- **Usage**: Telegram bot operations
- **Expiration**: Never expires (unless manually revoked)

## Token Generation

### Automatic Generation
During initial setup, default tokens are automatically generated and stored in `/opt/xvpn/data/api_tokens.json`:

```json
{
  "admin": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "permissions": ["admin", "read", "write"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Default admin token"
  },
  "client": {
    "token": "cGxlYXNlIGRvbid0IHN0ZWFsIHRoaXMgdG9rZW4=",
    "permissions": ["read"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Default client token"
  },
  "bot": {
    "token": "dGhpcyBpcyBhIHRlc3QgdG9rZW4gZm9yIHRoZSBib3Q=",
    "permissions": ["read", "write"],
    "created_at": 1234567890.123,
    "expires_at": null,
    "description": "Telegram bot token"
  }
}
```

### Manual Generation
Use the `generate_api_tokens.py` script to create new tokens:

```bash
# Generate a new admin token
python3 /opt/xvpn/scripts/generate_api_tokens.py create \
    --name "new-admin" \
    --permissions "admin,read,write" \
    --description "New admin token for team member"

# Generate a temporary token with expiration
python3 /opt/xvpn/scripts/generate_api_tokens.py create \
    --name "temp-user" \
    --permissions "read" \
    --expires 7 \
    --description "Temporary token for 7 days"
```

## Token Management

### Listing Tokens
View all tokens (without revealing actual token values):

```bash
python3 /opt/xvpn/scripts/generate_api_tokens.py list
```

### Showing Token Details
View details for a specific token:

```bash
python3 /opt/xvpn/scripts/generate_api_tokens.py show --name "admin"
```

### Revoking Tokens
Revoke a token to invalidate it:

```bash
python3 /opt/xvpn/scripts/generate_api_tokens.py revoke --name "temp-user"
```

### Generating Default Tokens
Create default tokens for a fresh installation:

```bash
python3 /opt/xvpn/scripts/generate_api_tokens.py generate-defaults
```

## Using Tokens

### API Requests
Include tokens in the `Authorization` header of API requests:

```bash
# Using curl
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://77.110.123.27:8443/mcp/v1/vpn.health

# Using Python requests
import requests

headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}

response = requests.get(
    "https://77.110.123.27:8443/mcp/v1/vpn.health",
    headers=headers,
    verify=False  # For self-signed certificates
)
```

### Environment Variables
Store tokens in environment variables for convenience:

```bash
# Set environment variable
export XVPN_API_TOKEN="your_token_here"

# Use in scripts
curl -H "Authorization: Bearer $XVPN_API_TOKEN" \
     https://77.110.123.27:8443/mcp/v1/vpn.health
```

## Protected Endpoints

### Health Check Endpoint
```http
GET /mcp/v1/vpn.health
Authorization: Bearer <token>
```

Returns system health information. Requires `read` permission.

### Transport Manifest Endpoint
```http
GET /transports/manifest.json
Authorization: Bearer <token>
```

Returns available transport protocols. Requires `read` permission.

### Client Configuration Endpoint
```http
GET /clients/<uuid>.json
Authorization: Bearer <token>
```

Returns client configuration. Requires `read` permission.

### Admin Client Creation Endpoint
```http
POST /mcp/v1/admin.newclient
Authorization: Bearer <token>
Content-Type: application/json
```

Creates new client configuration. Requires `admin` permission.

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Missing Authorization header",
  "message": "Token required for this endpoint"
}
```

### 401 Invalid Token
```json
{
  "error": "Invalid or expired token",
  "message": "Provided token is not valid"
}
```

### 403 Insufficient Permissions
```json
{
  "error": "Insufficient permissions",
  "message": "Token lacks required permission: admin",
  "available_permissions": ["read"]
}
```

## Security Best Practices

### Token Storage
1. **Environment Variables**: Store tokens in environment variables
2. **Encrypted Files**: Store tokens in encrypted configuration files
3. **Secret Management**: Use secret management systems (HashiCorp Vault, etc.)
4. **Never in Code**: Never commit tokens to version control

### Token Usage
1. **Least Privilege**: Use tokens with minimal required permissions
2. **Token Expiration**: Set expiration dates for temporary tokens
3. **Token Rotation**: Regularly rotate tokens
4. **Token Revocation**: Revoke unused tokens

### Token Monitoring
1. **Access Logging**: Log all token usage
2. **Anomaly Detection**: Monitor for unusual token activity
3. **Expiration Alerts**: Alert on expiring tokens
4. **Audit Trails**: Maintain audit trails of token usage

## Testing Authentication

### Automated Testing
Use the `test_api_auth.py` script to test authentication:

```bash
# Test API authentication
python3 /opt/xvpn/scripts/test_api_auth.py --url https://77.110.123.27:8443
```

### Manual Testing
Test endpoints manually with curl:

```bash
# Test without token (should fail)
curl -I https://77.110.123.27:8443/mcp/v1/vpn.health

# Test with invalid token (should fail)
curl -H "Authorization: Bearer invalid_token" \
     -I https://77.110.123.27:8443/mcp/v1/vpn.health

# Test with valid token (should succeed)
curl -H "Authorization: Bearer YOUR_VALID_TOKEN" \
     -I https://77.110.123.27:8443/mcp/v1/vpn.health
```

## Troubleshooting

### Common Issues

#### Token Not Working
1. **Verify Token Exists**: Check `/opt/xvpn/data/api_tokens.json`
2. **Check Token Format**: Ensure using `Bearer <token>` format
3. **Verify Permissions**: Check token has required permissions
4. **Check Expiration**: Ensure token hasn't expired

#### Authentication Errors
1. **401 Unauthorized**: Missing or invalid token
2. **403 Forbidden**: Insufficient permissions
3. **SSL Errors**: Certificate verification issues

#### SSL/TLS Issues
1. **Self-signed Certificates**: Use `verify=False` for development
2. **Certificate Pinning**: Ensure using correct certificates
3. **HTTPS Required**: All endpoints require HTTPS

### Debugging Commands

```bash
# Check tokens file
cat /opt/xvpn/data/api_tokens.json

# Test API endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -k https://77.110.123.27:8443/mcp/v1/vpn.health

# Check API logs
journalctl -u xvpn-api -f

# Test authentication
python3 /opt/xvpn/scripts/test_api_auth.py
```

## Future Enhancements

### Planned Improvements
1. **JWT Tokens**: Implement JSON Web Tokens for better security
2. **OAuth Integration**: Add OAuth 2.0 support for external authentication
3. **Rate Limiting**: Add per-token rate limiting
4. **Token Scopes**: Implement granular token scopes
5. **Audit Logging**: Enhanced audit logging for all token operations

### Security Enhancements
1. **Token Encryption**: Encrypt tokens at rest
2. **Multi-factor Authentication**: Add MFA for admin tokens
3. **Token Binding**: Bind tokens to specific IP addresses or devices
4. **Session Management**: Implement session-based tokens
5. **Token Federation**: Support federated token management

## Conclusion

The XVPN API authentication system provides robust token-based security for all API endpoints. By following the guidelines in this document, you can securely manage and use API tokens for XVPN administration and client operations.

For any authentication-related issues, please refer to the troubleshooting section or contact the XVPN development team.