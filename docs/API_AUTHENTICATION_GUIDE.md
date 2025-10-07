# XVPN API Authentication Guide

## Overview

This guide explains how to use token-based authentication for XVPN API endpoints.

## Authentication Mechanism

XVPN API uses Bearer token authentication for protected endpoints. Tokens are stored in `/opt/xvpn/data/api_tokens.json` and can be managed using the `manage_api_tokens.py` script.

## Getting Started

### 1. Generate Admin Token

First, generate an admin token to access protected endpoints:

```bash
# Navigate to project directory
cd /home/uss/chatvpn

# Generate admin token
./scripts/manage_api_tokens.py generate
```

This will output an admin token that looks like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### 2. Using Tokens in API Requests

Include the token in the `Authorization` header of your requests:

```bash
# Using curl
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://77.110.123.27:8443/mcp/v1/admin.newclient

# Using Python requests
import requests

headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}

response = requests.post(
    "https://77.110.123.27:8443/mcp/v1/admin.newclient",
    headers=headers,
    json={"some": "data"}
)
```

## Protected Endpoints

The following endpoints require authentication:

- `POST /mcp/v1/admin.newclient` - Create new client (requires admin permission)
- Future endpoints for managing clients, transports, etc.

## Token Management

### List All Tokens

```bash
./scripts/manage_api_tokens.py list
```

### Create New Token

```bash
# Create a read-only token
./scripts/manage_api_tokens.py create \
    --name "readonly_client" \
    --permissions "read" \
    --description "Read-only access for monitoring"

# Create a token with limited lifespan
./scripts/manage_api_tokens.py create \
    --name "temporary_admin" \
    --permissions "admin,read,write" \
    --expires 7 \
    --description "Temporary admin access for 7 days"
```

### Revoke Token

```bash
./scripts/manage_api_tokens.py revoke --name "temporary_admin"
```

### Show Token Details

```bash
./scripts/manage_api_tokens.py show --name "readonly_client"
```

## Token Permissions

Tokens can have the following permissions:

- `read` - Read-only access to public endpoints
- `write` - Write access to modify resources
- `admin` - Full administrative access (includes read and write)

Tokens with `admin` permission automatically have access to all endpoints.

## Security Best Practices

### 1. Token Storage

- Store tokens securely (environment variables, encrypted files)
- Never commit tokens to version control
- Rotate tokens regularly

### 2. Token Usage

```bash
# Good: Store token in environment variable
export XVPN_API_TOKEN="your_token_here"
curl -H "Authorization: Bearer $XVPN_API_TOKEN" \
     https://77.110.123.27:8443/mcp/v1/admin.newclient

# Bad: Hardcoded tokens in scripts
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1Ni..." \
     https://77.110.123.27:8443/mcp/v1/admin.newclient
```

### 3. Token Revocation

Revoke tokens immediately if they are compromised or no longer needed:

```bash
./scripts/manage_api_tokens.py revoke --name "compromised_token"
```

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

## Example Usage

### Create New Client

```bash
# Get admin token
ADMIN_TOKEN=$(./scripts/manage_api_tokens.py generate | grep "Token:" | cut -d' ' -f2)

# Create new client
curl -X POST \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"client_name": "Test Client"}' \
     https://77.110.123.27:8443/mcp/v1/admin.newclient
```

### Python Example

```python
import requests
import os

# Get token from environment
token = os.getenv("XVPN_API_TOKEN")
if not token:
    raise ValueError("XVPN_API_TOKEN environment variable not set")

# Make authenticated request
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://77.110.123.27:8443/mcp/v1/admin.newclient",
    headers=headers,
    json={"client_name": "Test Client"}
)

if response.status_code == 200:
    print("Client created successfully!")
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Troubleshooting

### Token Not Working

1. Verify the token is correct and not expired
2. Check that the token has required permissions
3. Ensure the `Authorization` header is formatted correctly

### Permission Denied

1. Check token permissions with:
   ```bash
   ./scripts/manage_api_tokens.py show --name "token_name"
   ```
2. Create a new token with appropriate permissions if needed

### Token File Issues

If you encounter issues with the token file:

1. Check file permissions:
   ```bash
   ls -la /opt/xvpn/data/api_tokens.json
   ```

2. Ensure the file is readable by the API service

3. Regenerate tokens if the file is corrupted:
   ```bash
   # Remove corrupted file
   sudo rm /opt/xvpn/data/api_tokens.json
   
   # Generate new tokens
   ./scripts/manage_api_tokens.py generate
   ```

## Production Considerations

### Token Storage

In production environments:

1. Store tokens in secure vaults (HashiCorp Vault, AWS Secrets Manager)
2. Use short-lived tokens with automatic rotation
3. Implement token audit logging

### Network Security

1. Restrict API access to trusted networks
2. Use firewalls to limit exposure
3. Implement rate limiting to prevent abuse

### Monitoring

1. Log all authentication attempts
2. Monitor for suspicious activity
3. Set up alerts for token misuse

## Next Steps

1. Integrate authentication with client applications
2. Set up automatic token rotation
3. Implement audit logging for token usage
4. Configure monitoring and alerting for authentication events