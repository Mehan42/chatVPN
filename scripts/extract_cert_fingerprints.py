#!/usr/bin/env python3
"""
XVPN Certificate Fingerprint Extractor
Extracts certificate fingerprint from production server for TLS pinning
"""

import ssl
import socket
import hashlib
import json
import os
from pathlib import Path

def get_server_certificate_fingerprint(hostname, port=443):
    """
    Get SHA-256 fingerprint of server certificate
    """
    print(f"🔍 Getting certificate fingerprint from {hostname}:{port}...")
    
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
                
                # Calculate SHA-256 fingerprint
                fingerprint = hashlib.sha256(cert_der).hexdigest()
                
                # Get certificate details
                cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                
                print(f"✅ Certificate fingerprint extracted successfully")
                print(f"   Fingerprint (SHA-256): {fingerprint}")
                print(f"   Certificate expires: {ssock.getpeercert().get('notAfter', 'Unknown')}")
                
                return {
                    "fingerprint": fingerprint,
                    "hostname": hostname,
                    "port": port,
                    "expires": ssock.getpeercert().get("notAfter", "Unknown"),
                    "extracted_at": __import__("time").time()
                }
                
    except Exception as e:
        print(f"❌ Error extracting certificate: {e}")
        return None

def save_fingerprint_config(fingerprint_data, config_path=None):
    """
    Save fingerprint data to configuration file
    """
    if config_path is None:
        config_path = Path.home() / "chatvpn" / "client" / "config" / "cert_fingerprints.json"
    
    try:
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save fingerprint data
        with open(config_path, "w") as f:
            json.dump(fingerprint_data, f, indent=2)
        
        print(f"✅ Certificate fingerprint saved to {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving fingerprint config: {e}")
        return False

def main():
    """
    Main function to extract and save certificate fingerprints
    """
    print("🔐 XVPN Certificate Fingerprint Extractor")
    print("=" * 45)
    
    # Servers to extract fingerprints from
    servers = [
        {"hostname": "77.110.123.27", "port": 8443},  # Production API server
        {"hostname": "api.uss.hopto.org", "port": 443},  # Legacy API server
    ]
    
    # Extract fingerprints
    fingerprints = {}
    
    for server in servers:
        fingerprint_data = get_server_certificate_fingerprint(
            server["hostname"], 
            server["port"]
        )
        
        if fingerprint_data:
            key = f"{server['hostname']}:{server['port']}"
            fingerprints[key] = fingerprint_data
    
    # Save to config file
    if fingerprints:
        config_path = Path.home() / "chatvpn" / "client" / "config" / "cert_fingerprints.json"
        save_fingerprint_config({
            "fingerprints": fingerprints,
            "generated_at": __import__("time").time(),
            "note": "This file contains certificate fingerprints for TLS pinning"
        }, config_path)
        
        print("\n📋 Generated Fingerprints:")
        print("=" * 30)
        for key, data in fingerprints.items():
            print(f"Server: {key}")
            print(f"  Fingerprint: {data['fingerprint']}")
            print(f"  Expires: {data['expires']}")
            print()
        
        print("💡 Next steps:")
        print("1. Update client code to use these fingerprints for TLS pinning")
        print("2. Implement fingerprint validation in HTTPS requests")
        print("3. Set up automatic fingerprint renewal before expiration")
        return 0
    else:
        print("❌ Failed to extract any certificate fingerprints")
        return 1

if __name__ == "__main__":
    exit(main())