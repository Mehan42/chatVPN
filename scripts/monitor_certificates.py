#!/usr/bin/env python3
"""
XVPN Certificate Expiration Monitor
Monitors certificate expiration and triggers renewal when needed
"""

import ssl
import socket
import json
import time
import subprocess
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

class CertificateMonitor:
    """
    Monitors certificate expiration and handles renewal
    """
    
    def __init__(self, config_file=None):
        self.config_file = config_file or "/opt/xvpn/data/cert_monitor_config.json"
        self.config = self._load_config()
        self.alerts_sent = set()  # Track sent alerts to avoid duplicates
    
    def _load_config(self):
        """
        Load monitor configuration
        """
        default_config = {
            "servers": [
                {"hostname": "77.110.123.27", "port": 8443, "name": "Production API"},
                {"hostname": "api.uss.hopto.org", "port": 443, "name": "Legacy API"}
            ],
            "alert_thresholds": {
                "critical": 7,    # Days before expiration for critical alert
                "warning": 30,    # Days before expiration for warning alert
                "info": 90        # Days before expiration for info alert
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "xvpn@localhost",
                    "to_emails": ["admin@localhost"]
                },
                "telegram": {
                    "enabled": True,
                    "bot_token": "",
                    "chat_ids": []
                }
            },
            "renewal": {
                "auto_renew": True,
                "renew_days_before": 30,
                "script_path": "/home/uss/chatvpn/scripts/renew_certificates.sh"
            }
        }
        
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
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
        Save monitor configuration
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
    
    def get_certificate_info(self, hostname, port=443):
        """
        Get certificate information including expiration date
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Don't verify for monitoring
            
            # Connect to server and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get certificate details
                    cert_info = ssock.getpeercert()
                    
                    # Parse dates
                    not_before = datetime.strptime(cert_info['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert_info['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days until expiration
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    return {
                        "hostname": hostname,
                        "port": port,
                        "subject": dict(x[0] for x in cert_info['subject']),
                        "issuer": dict(x[0] for x in cert_info['issuer']),
                        "serial_number": cert_info['serialNumber'],
                        "not_before": cert_info['notBefore'],
                        "not_after": cert_info['notAfter'],
                        "not_before_parsed": not_before.isoformat(),
                        "not_after_parsed": not_after.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "is_expired": days_until_expiry < 0,
                        "checked_at": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            print(f"❌ Error getting certificate info for {hostname}:{port} - {e}")
            return None
    
    def check_all_certificates(self):
        """
        Check expiration for all configured servers
        """
        print("🔍 Checking certificate expiration for all servers...")
        
        results = []
        for server in self.config.get("servers", []):
            hostname = server["hostname"]
            port = server["port"]
            name = server["name"]
            
            print(f"   Checking {name} ({hostname}:{port})...")
            
            cert_info = self.get_certificate_info(hostname, port)
            if cert_info:
                cert_info["server_name"] = name
                results.append(cert_info)
                print(f"      Days until expiry: {cert_info['days_until_expiry']}")
            else:
                print(f"      ❌ Failed to get certificate info")
        
        return results
    
    def categorize_certificates(self, cert_results):
        """
        Categorize certificates by expiration status
        """
        critical = []
        warning = []
        info = []
        valid = []
        
        critical_days = self.config["alert_thresholds"]["critical"]
        warning_days = self.config["alert_thresholds"]["warning"]
        info_days = self.config["alert_thresholds"]["info"]
        
        for cert in cert_results:
            days = cert["days_until_expiry"]
            
            if days < 0:
                critical.append(cert)  # Already expired
            elif days <= critical_days:
                critical.append(cert)  # Expiring very soon
            elif days <= warning_days:
                warning.append(cert)   # Expiring soon
            elif days <= info_days:
                info.append(cert)     # Expiring in a while
            else:
                valid.append(cert)    # Valid for a long time
        
        return {
            "critical": critical,
            "warning": warning,
            "info": info,
            "valid": valid
        }
    
    def send_alert(self, cert_info, alert_type):
        """
        Send alert for certificate expiration
        """
        alert_key = f"{cert_info['hostname']}:{cert_info['port']}_{alert_type}_{cert_info['days_until_expiry']}"
        
        # Avoid duplicate alerts
        if alert_key in self.alerts_sent:
            return False
        
        print(f"🔔 Sending {alert_type} alert for {cert_info['server_name']}...")
        
        # Prepare alert message
        days = cert_info["days_until_expiry"]
        if days < 0:
            status_msg = f"EXPIRED {abs(days)} days ago"
        else:
            status_msg = f"expires in {days} days"
        
        message = f"""
🚨 XVPN Certificate Alert 🚨

Server: {cert_info['server_name']} ({cert_info['hostname']}:{cert_info['port']})
Status: {status_msg}
Subject: {cert_info.get('subject', {}).get('commonName', 'Unknown')}
Issuer: {cert_info.get('issuer', {}).get('commonName', 'Unknown')}
Not After: {cert_info['not_after']}
Checked At: {cert_info['checked_at']}

Action Required: {'URGENT - Certificate has expired!' if days < 0 else 'Renew certificate soon'}
"""
        
        # Send Telegram notification
        if self.config["notifications"]["telegram"]["enabled"]:
            self._send_telegram_alert(message, alert_type)
        
        # Send email notification
        if self.config["notifications"]["email"]["enabled"]:
            self._send_email_alert(message, alert_type)
        
        # Mark alert as sent
        self.alerts_sent.add(alert_key)
        return True
    
    def _send_telegram_alert(self, message, alert_type):
        """
        Send alert via Telegram
        """
        try:
            import requests
            
            bot_token = self.config["notifications"]["telegram"]["bot_token"]
            chat_ids = self.config["notifications"]["telegram"]["chat_ids"]
            
            if not bot_token or not chat_ids:
                print("⚠️  Telegram bot token or chat IDs not configured")
                return False
            
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                
                response = requests.post(url, data=data)
                if response.status_code != 200:
                    print(f"❌ Failed to send Telegram alert to chat {chat_id}")
                else:
                    print(f"✅ Telegram alert sent to chat {chat_id}")
            
            return True
        except Exception as e:
            print(f"❌ Error sending Telegram alert: {e}")
            return False
    
    def _send_email_alert(self, message, alert_type):
        """
        Send alert via email
        """
        try:
            smtp_config = self.config["notifications"]["email"]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_config["from_email"]
            msg['To'] = ", ".join(smtp_config["to_emails"])
            msg['Subject'] = f"XVPN Certificate Alert - {alert_type.upper()}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(msg)
            server.quit()
            
            print("✅ Email alert sent")
            return True
        except Exception as e:
            print(f"❌ Error sending email alert: {e}")
            return False
    
    def renew_certificate(self, cert_info):
        """
        Attempt to renew certificate
        """
        print(f"🔄 Attempting to renew certificate for {cert_info['server_name']}...")
        
        try:
            # Check if auto-renewal is enabled
            if not self.config["renewal"]["auto_renew"]:
                print("⚠️  Auto-renewal is disabled")
                return False
            
            # Check if renewal script exists
            script_path = self.config["renewal"]["script_path"]
            if not Path(script_path).exists():
                print(f"❌ Renewal script not found: {script_path}")
                return False
            
            # Run renewal script
            result = subprocess.run(
                [script_path, cert_info["hostname"]],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Certificate renewed successfully")
                print(f"   Output: {result.stdout}")
                return True
            else:
                print("❌ Certificate renewal failed")
                print(f"   Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Certificate renewal timed out")
            return False
        except Exception as e:
            print(f"❌ Error during certificate renewal: {e}")
            return False
    
    def generate_report(self, categorized_certs):
        """
        Generate a summary report of certificate status
        """
        report = []
        report.append("📊 XVPN Certificate Status Report")
        report.append("=" * 40)
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        
        # Critical certificates
        if categorized_certs["critical"]:
            report.append("🚨 CRITICAL CERTIFICATES (Require Immediate Attention)")
            report.append("-" * 50)
            for cert in categorized_certs["critical"]:
                days = cert["days_until_expiry"]
                if days < 0:
                    status = f"EXPIRED {abs(days)} days ago"
                else:
                    status = f"Expires in {days} days"
                report.append(f"  • {cert['server_name']}: {status}")
            report.append("")
        
        # Warning certificates
        if categorized_certs["warning"]:
            report.append("⚠️  WARNING CERTIFICATES (Renew Soon)")
            report.append("-" * 35)
            for cert in categorized_certs["warning"]:
                report.append(f"  • {cert['server_name']}: Expires in {cert['days_until_expiry']} days")
            report.append("")
        
        # Info certificates
        if categorized_certs["info"]:
            report.append("ℹ️  INFO CERTIFICATES (Valid)")
            report.append("-" * 25)
            for cert in categorized_certs["info"]:
                report.append(f"  • {cert['server_name']}: Expires in {cert['days_until_expiry']} days")
            report.append("")
        
        # Valid certificates
        if categorized_certs["valid"]:
            report.append("✅ VALID CERTIFICATES (Long-term)")
            report.append("-" * 30)
            for cert in categorized_certs["valid"]:
                report.append(f"  • {cert['server_name']}: Expires in {cert['days_until_expiry']} days")
            report.append("")
        
        return "\n".join(report)
    
    def run_monitoring_cycle(self):
        """
        Run a complete monitoring cycle
        """
        print("🔐 XVPN Certificate Expiration Monitor")
        print("=" * 45)
        
        # Check all certificates
        cert_results = self.check_all_certificates()
        
        if not cert_results:
            print("❌ No certificates found to monitor")
            return False
        
        # Categorize certificates
        categorized = self.categorize_certificates(cert_results)
        
        # Generate and print report
        report = self.generate_report(categorized)
        print(report)
        
        # Send alerts for critical/warning certificates
        alerts_sent = 0
        
        # Critical alerts (and auto-renewal attempts)
        for cert in categorized["critical"]:
            self.send_alert(cert, "critical")
            alerts_sent += 1
            
            # Attempt auto-renewal for critical certificates
            if self.config["renewal"]["auto_renew"]:
                if self.renew_certificate(cert):
                    print(f"✅ Auto-renewal successful for {cert['server_name']}")
                else:
                    print(f"❌ Auto-renewal failed for {cert['server_name']}")
        
        # Warning alerts
        for cert in categorized["warning"]:
            self.send_alert(cert, "warning")
            alerts_sent += 1
        
        # Info alerts
        for cert in categorized["info"]:
            self.send_alert(cert, "info")
            alerts_sent += 1
        
        print(f"\n🔔 Monitoring cycle completed. Sent {alerts_sent} alerts.")
        
        # Check if any action is needed
        if categorized["critical"] or categorized["warning"]:
            print("⚠️  Action required for some certificates!")
            return False
        else:
            print("✅ All certificates are in good standing")
            return True

def main():
    """
    Main function to run certificate monitoring
    """
    monitor = CertificateMonitor()
    return 0 if monitor.run_monitoring_cycle() else 1

if __name__ == "__main__":
    exit(main())