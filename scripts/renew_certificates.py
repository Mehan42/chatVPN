#!/usr/bin/env python3
"""
XVPN Certificate Renewal Script
Automatically renews certificates when they're close to expiration
"""

import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class CertificateRenewer:
    """
    Handles automatic certificate renewal
    """
    
    def __init__(self, config_file=None):
        self.config_file = config_file or "/opt/xvpn/data/cert_renewal_config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Load renewal configuration
        """
        default_config = {
            "certificates": {
                "production": {
                    "domains": ["77.110.123.27"],
                    "cert_path": "/opt/xvpn/tls/cert.pem",
                    "key_path": "/opt/xvpn/tls/key.pem",
                    "provider": "self-signed",  # or "letsencrypt"
                    "renew_days_before": 30
                }
            },
            "providers": {
                "self-signed": {
                    "script": "/home/uss/chatvpn/scripts/generate_tls_certs.sh",
                    "days_valid": 365
                },
                "letsencrypt": {
                    "script": "/usr/bin/certbot",
                    "days_valid": 90
                }
            },
            "deployment": {
                "script": "/home/uss/chatvpn/scripts/deploy_certificates.sh",
                "reload_services": True,
                "services": ["xvpn-api"]
            },
            "notifications": {
                "enabled": True,
                "telegram": {
                    "bot_token": "",
                    "chat_ids": []
                }
            }
        }
        
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config
            else:
                # Create default config
                self._save_config(default_config)
                return default_config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return default_config
    
    def _save_config(self, config):
        """
        Save renewal configuration
        """
        try:
            config_dir = Path(self.config_file).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def renew_certificate(self, cert_name):
        """
        Renew a specific certificate
        """
        print(f"🔄 Renewing certificate: {cert_name}")
        
        if cert_name not in self.config["certificates"]:
            print(f"❌ Certificate '{cert_name}' not found in configuration")
            return False
        
        cert_config = self.config["certificates"][cert_name]
        provider = cert_config["provider"]
        
        print(f"   Provider: {provider}")
        print(f"   Domains: {', '.join(cert_config['domains'])}")
        
        # Handle different providers
        if provider == "self-signed":
            return self._renew_self_signed(cert_config)
        elif provider == "letsencrypt":
            return self._renew_letsencrypt(cert_config)
        else:
            print(f"❌ Unsupported certificate provider: {provider}")
            return False
    
    def _renew_self_signed(self, cert_config):
        """
        Renew self-signed certificate
        """
        print("   Generating new self-signed certificate...")
        
        try:
            # Create backup of current certificate
            cert_path = Path(cert_config["cert_path"])
            key_path = Path(cert_config["key_path"])
            
            if cert_path.exists() and key_path.exists():
                backup_dir = cert_path.parent / "backup"
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cert_backup = backup_dir / f"cert_{timestamp}.pem"
                key_backup = backup_dir / f"key_{timestamp}.pem"
                
                shutil.copy2(cert_path, cert_backup)
                shutil.copy2(key_path, key_backup)
                
                print(f"   Backed up current certificate to {cert_backup}")
                print(f"   Backed up current key to {key_backup}")
            
            # Generate new certificate using existing script
            script_path = self.config["providers"]["self-signed"]["script"]
            
            if not Path(script_path).exists():
                print(f"❌ Certificate generation script not found: {script_path}")
                return False
            
            # Run certificate generation script
            env = os.environ.copy()
            env["CERT_OUTPUT_DIR"] = str(cert_path.parent)
            
            result = subprocess.run(
                [script_path],
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("   ✅ Self-signed certificate generated successfully")
                print(f"      Certificate: {cert_path}")
                print(f"      Key: {key_path}")
                return True
            else:
                print("   ❌ Failed to generate self-signed certificate")
                print(f"      Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ❌ Certificate generation timed out")
            return False
        except Exception as e:
            print(f"   ❌ Error generating self-signed certificate: {e}")
            return False
    
    def _renew_letsencrypt(self, cert_config):
        """
        Renew Let's Encrypt certificate
        """
        print("   Renewing Let's Encrypt certificate...")
        
        try:
            domains = cert_config["domains"]
            certbot_script = self.config["providers"]["letsencrypt"]["script"]
            
            if not Path(certbot_script).exists():
                print(f"❌ Certbot script not found: {certbot_script}")
                return False
            
            # Prepare certbot command
            cmd = [
                certbot_script,
                "certonly",
                "--standalone",
                "--non-interactive",
                "--agree-tos",
                "--email", "admin@xvpn.local"
            ]
            
            # Add domains
            for domain in domains:
                cmd.extend(["-d", domain])
            
            # Run certbot
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                print("   ✅ Let's Encrypt certificate renewed successfully")
                return True
            else:
                print("   ❌ Failed to renew Let's Encrypt certificate")
                print(f"      Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ❌ Let's Encrypt renewal timed out")
            return False
        except Exception as e:
            print(f"   ❌ Error renewing Let's Encrypt certificate: {e}")
            return False
    
    def deploy_certificate(self, cert_config):
        """
        Deploy renewed certificate to production
        """
        print("   Deploying certificate to production...")
        
        try:
            deployment_script = self.config["deployment"]["script"]
            
            if not Path(deployment_script).exists():
                print(f"❌ Deployment script not found: {deployment_script}")
                return False
            
            # Run deployment script
            result = subprocess.run(
                [deployment_script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("   ✅ Certificate deployed successfully")
                print(f"      Output: {result.stdout}")
                return True
            else:
                print("   ❌ Failed to deploy certificate")
                print(f"      Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ❌ Certificate deployment timed out")
            return False
        except Exception as e:
            print(f"   ❌ Error deploying certificate: {e}")
            return False
    
    def reload_services(self):
        """
        Reload services after certificate deployment
        """
        if not self.config["deployment"]["reload_services"]:
            print("   Service reload disabled")
            return True
        
        print("   Reloading services...")
        
        try:
            services = self.config["deployment"]["services"]
            success_count = 0
            
            for service in services:
                print(f"      Reloading {service}...")
                
                result = subprocess.run(
                    ["systemctl", "reload", service],
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minute timeout
                )
                
                if result.returncode == 0:
                    print(f"      ✅ {service} reloaded successfully")
                    success_count += 1
                else:
                    print(f"      ❌ Failed to reload {service}")
                    print(f"         Error: {result.stderr}")
            
            return success_count == len(services)
            
        except Exception as e:
            print(f"   ❌ Error reloading services: {e}")
            return False
    
    def send_notification(self, message):
        """
        Send notification about renewal
        """
        if not self.config["notifications"]["enabled"]:
            return True
        
        print("   Sending notification...")
        
        try:
            # Send Telegram notification
            telegram_config = self.config["notifications"]["telegram"]
            
            if telegram_config["bot_token"] and telegram_config["chat_ids"]:
                import requests
                
                for chat_id in telegram_config["chat_ids"]:
                    url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
                    data = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                    
                    response = requests.post(url, data=data)
                    if response.status_code == 200:
                        print(f"      ✅ Notification sent to chat {chat_id}")
                    else:
                        print(f"      ❌ Failed to send notification to chat {chat_id}")
            
            return True
        except Exception as e:
            print(f"   ❌ Error sending notification: {e}")
            return False
    
    def renew_all_certificates(self):
        """
        Renew all configured certificates
        """
        print("🔐 XVPN Certificate Renewal")
        print("=" * 35)
        
        certificates = self.config["certificates"]
        success_count = 0
        total_count = len(certificates)
        
        for cert_name, cert_config in certificates.items():
            print(f"\n🔄 Processing certificate: {cert_name}")
            
            # Renew certificate
            if self.renew_certificate(cert_name):
                # Deploy certificate
                if self.deploy_certificate(cert_config):
                    # Reload services
                    if self.reload_services():
                        # Send notification
                        message = f"✅ XVPN Certificate Renewed\nCertificate: {cert_name}\nStatus: Successfully renewed and deployed"
                        self.send_notification(message)
                        
                        success_count += 1
                        print(f"✅ Certificate {cert_name} renewed and deployed successfully")
                    else:
                        print(f"❌ Failed to reload services for {cert_name}")
                else:
                    print(f"❌ Failed to deploy certificate {cert_name}")
            else:
                print(f"❌ Failed to renew certificate {cert_name}")
        
        print(f"\n📊 Renewal Summary: {success_count}/{total_count} certificates renewed successfully")
        
        if success_count == total_count:
            print("✅ All certificates renewed successfully!")
            return True
        else:
            print("❌ Some certificates failed to renew")
            return False

def main():
    """
    Main function to run certificate renewal
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN Certificate Renewal")
    parser.add_argument("certificate", nargs="?", help="Specific certificate to renew (default: all)")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize renewer
    renewer = CertificateRenewer(args.config)
    
    # Renew certificates
    if args.certificate:
        # Renew specific certificate
        success = renewer.renew_certificate(args.certificate)
    else:
        # Renew all certificates
        success = renewer.renew_all_certificates()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())