#!/usr/bin/env python3
"""
XVPN Certificate Fingerprint Updater
Automatically updates certificate fingerprints for TLS pinning
"""

import ssl
import socket
import hashlib
import json
import time
import os
from pathlib import Path

def get_server_certificate_info(hostname, port=443):
    """
    Get certificate information including fingerprint and expiration
    """
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Don't verify for extraction
        
        # Connect to server and get certificate
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate in DER format
                cert_der = ssock.getpeercert(binary_form=True)
                
                # Get certificate details
                cert_info = ssock.getpeercert()
                
                # Calculate SHA-256 fingerprint
                fingerprint = hashlib.sha256(cert_der).hexdigest()
                
                return {
                    "fingerprint": fingerprint,
                    "hostname": hostname,
                    "port": port,
                    "not_before": cert_info.get("notBefore"),
                    "not_after": cert_info.get("notAfter"),
                    "serial_number": cert_info.get("serialNumber"),
                    "issuer": dict(cert_info.get("issuer", {})),
                    "subject": dict(cert_info.get("subject", {})),
                    "extracted_at": time.time()
                }
                
    except Exception as e:
        print(f"❌ Error getting certificate info for {hostname}:{port} - {e}")
        return None

def load_existing_fingerprints():
    """
    Load existing certificate fingerprints
    """
    config_path = Path.home() / "chatvpn" / "client" / "config" / "cert_fingerprints.json"
    
    try:
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            return {"fingerprints": {}, "generated_at": time.time()}
    except Exception as e:
        print(f"❌ Error loading existing fingerprints: {e}")
        return {"fingerprints": {}, "generated_at": time.time()}

def save_updated_fingerprints(fingerprint_data):
    """
    Save updated certificate fingerprints
    """
    config_path = Path.home() / "chatvpn" / "client" / "config" / "cert_fingerprints.json"
    
    try:
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save fingerprint data
        with open(config_path, "w") as f:
            json.dump(fingerprint_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated certificate fingerprints saved to {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving updated fingerprints: {e}")
        return False

def check_certificate_expiration(fingerprint_data):
    """
    Check if any certificates are expiring soon
    """
    expiring_soon = []
    expired = []
    
    current_time = time.time()
    
    for server_key, cert_info in fingerprint_data.get("fingerprints", {}).items():
        try:
            # Parse expiration date
            not_after_str = cert_info.get("not_after")
            if not_after_str:
                # Parse date string like "Oct  7 13:11:22 2025 GMT"
                import datetime
                not_after_parsed = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                not_after_timestamp = not_after_parsed.timestamp()
                
                # Check if expired
                if not_after_timestamp < current_time:
                    expired.append({
                        "server": server_key,
                        "expired_days": (current_time - not_after_timestamp) / (24 * 3600)
                    })
                
                # Check if expiring within 30 days
                elif (not_after_timestamp - current_time) < (30 * 24 * 3600):
                    expiring_soon.append({
                        "server": server_key,
                        "days_until_expiry": (not_after_timestamp - current_time) / (24 * 3600)
                    })
                    
        except Exception as e:
            print(f"⚠️  Error parsing expiration date for {server_key}: {e}")
    
    return expiring_soon, expired

def main():
    """
    Main function to update certificate fingerprints
    """
    print("🔐 XVPN Certificate Fingerprint Updater")
    print("=" * 45)
    
    # Servers to monitor
    servers = [
        {"hostname": "77.110.123.27", "port": 8443},  # Production API server
        {"hostname": "api.uss.hopto.org", "port": 443},  # Legacy API server
    ]
    
    # Load existing fingerprints
    existing_data = load_existing_fingerprints()
    updated_fingerprints = existing_data.get("fingerprints", {}).copy()
    
    print(f"📊 Found {len(updated_fingerprints)} existing certificate fingerprints")
    
    # Update fingerprints for all servers
    updated_count = 0
    failed_count = 0
    
    for server in servers:
        hostname = server["hostname"]
        port = server["port"]
        server_key = f"{hostname}:{port}"
        
        print(f"\n🔄 Updating certificate for {server_key}...")
        
        cert_info = get_server_certificate_info(hostname, port)
        
        if cert_info:
            updated_fingerprints[server_key] = cert_info
            print(f"✅ Updated certificate fingerprint for {server_key}")
            print(f"   Fingerprint: {cert_info['fingerprint'][:32]}...")
            print(f"   Expires: {cert_info['not_after']}")
            updated_count += 1
        else:
            print(f"❌ Failed to update certificate for {server_key}")
            failed_count += 1
    
    # Check for expiring/expired certificates
    print(f"\n🔍 Checking certificate expiration...")
    expiring_soon, expired = check_certificate_expiration({
        "fingerprints": updated_fingerprints
    })
    
    if expired:
        print(f"🚨 {len(expired)} certificates have expired:")
        for cert in expired:
            print(f"   - {cert['server']} (expired {cert['expired_days']:.1f} days ago)")
    
    if expiring_soon:
        print(f"⚠️  {len(expiring_soon)} certificates expiring soon:")
        for cert in expiring_soon:
            print(f"   - {cert['server']} (expires in {cert['days_until_expiry']:.1f} days)")
    
    # Save updated fingerprints
    if updated_count > 0:
        updated_data = {
            "fingerprints": updated_fingerprints,
            "generated_at": time.time(),
            "updated_at": time.time(),
            "note": "This file contains certificate fingerprints for TLS pinning",
            "servers_monitored": len(servers),
            "successfully_updated": updated_count,
            "failed_updates": failed_count
        }
        
        if save_updated_fingerprints(updated_data):
            print(f"\n🎉 Successfully updated {updated_count} certificate fingerprints")
            if failed_count > 0:
                print(f"⚠️  Failed to update {failed_count} certificates")
            return 0
        else:
            print(f"\n❌ Failed to save updated certificate fingerprints")
            return 1
    else:
        print(f"\n⚠️  No certificates were updated")
        return 1

if __name__ == "__main__":
    exit(main())