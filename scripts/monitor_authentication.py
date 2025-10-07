#!/usr/bin/env python3
"""
XVPN Authentication Monitoring Script
Monitors authentication events and detects suspicious activity
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

class AuthMonitor:
    """
    Monitors authentication events and detects suspicious activity
    """
    
    def __init__(self, db_path="/opt/xvpn/data/xvpn.db", log_path="/opt/xvpn/logs/auth.log"):
        self.db_path = db_path
        self.log_path = log_path
        self.alert_threshold = 5  # Number of failed attempts before alert
        self.time_window = 300    # Time window in seconds (5 minutes)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_recent_auth_events(self, hours=1):
        """
        Get recent authentication events from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate time threshold
            time_threshold = time.time() - (hours * 3600)
            
            # Query recent auth events
            cursor.execute("""
                SELECT timestamp, component, state, action, result 
                FROM events 
                WHERE timestamp > ? 
                AND (action LIKE '%auth%' OR action LIKE '%token%')
                ORDER BY timestamp DESC
            """, (time_threshold,))
            
            events = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            auth_events = []
            for row in events:
                auth_events.append({
                    "timestamp": row[0],
                    "component": row[1],
                    "state": row[2],
                    "action": row[3],
                    "result": row[4]
                })
            
            return auth_events
            
        except Exception as e:
            self.log_error(f"Error getting auth events: {e}")
            return []
    
    def detect_suspicious_activity(self, auth_events):
        """
        Detect suspicious authentication activity
        """
        suspicious_activities = []
        
        # Group events by IP or component
        event_groups = {}
        for event in auth_events:
            component = event["component"]
            if component not in event_groups:
                event_groups[component] = []
            event_groups[component].append(event)
        
        # Check each group for suspicious patterns
        for component, events in event_groups.items():
            # Sort events by timestamp
            events.sort(key=lambda x: x["timestamp"])
            
            # Check for failed login attempts
            failed_attempts = [e for e in events if "fail" in e["result"].lower()]
            
            if len(failed_attempts) >= self.alert_threshold:
                # Check if failures happened in short time window
                if len(failed_attempts) > 1:
                    time_span = failed_attempts[-1]["timestamp"] - failed_attempts[0]["timestamp"]
                    if time_span <= self.time_window:
                        suspicious_activities.append({
                            "type": "brute_force",
                            "component": component,
                            "count": len(failed_attempts),
                            "time_span": time_span,
                            "first_attempt": failed_attempts[0]["timestamp"],
                            "last_attempt": failed_attempts[-1]["timestamp"],
                            "events": failed_attempts
                        })
            
            # Check for token abuse
            token_events = [e for e in events if "token" in e["action"].lower()]
            
            # Look for rapid token usage
            if len(token_events) > 10:
                time_span = token_events[-1]["timestamp"] - token_events[0]["timestamp"]
                if time_span < 60:  # Less than 1 minute for 10+ requests
                    suspicious_activities.append({
                        "type": "token_abuse",
                        "component": component,
                        "count": len(token_events),
                        "time_span": time_span,
                        "first_request": token_events[0]["timestamp"],
                        "last_request": token_events[-1]["timestamp"],
                        "events": token_events
                    })
        
        return suspicious_activities
    
    def log_auth_event(self, component, action, result, details=None):
        """
        Log authentication event
        """
        try:
            # Log to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO events (timestamp, component, state, action, result) VALUES (?, ?, ?, ?, ?)",
                (time.time(), component, "auth", action, result)
            )
            
            conn.commit()
            conn.close()
            
            # Log to file
            log_entry = {
                "timestamp": time.time(),
                "component": component,
                "action": action,
                "result": result,
                "details": details or {}
            }
            
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            self.log_error(f"Error logging auth event: {e}")
    
    def log_error(self, message):
        """
        Log error message
        """
        error_entry = {
            "timestamp": time.time(),
            "level": "ERROR",
            "message": message
        }
        
        # Log to file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(error_entry) + "\n")
        
        # Print to stderr
        print(f"❌ {message}", file=sys.stderr)
    
    def log_alert(self, alert_type, details):
        """
        Log security alert
        """
        alert_entry = {
            "timestamp": time.time(),
            "level": "ALERT",
            "type": alert_type,
            "details": details
        }
        
        # Log to file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(alert_entry) + "\n")
        
        # Print to stdout
        print(f"🚨 ALERT: {alert_type}")
        print(f"   Details: {details}")
    
    def run_monitoring_cycle(self):
        """
        Run a complete monitoring cycle
        """
        print("🔍 XVPN Authentication Monitoring")
        print("=" * 35)
        
        # Get recent auth events
        auth_events = self.get_recent_auth_events(hours=1)
        print(f"📊 Analyzed {len(auth_events)} authentication events in the last hour")
        
        # Detect suspicious activity
        suspicious_activities = self.detect_suspicious_activity(auth_events)
        
        if suspicious_activities:
            print(f"🚨 Detected {len(suspicious_activities)} suspicious activities:")
            for activity in suspicious_activities:
                self.log_alert(activity["type"], activity)
        else:
            print("✅ No suspicious authentication activity detected")
        
        # Summary
        print(f"\n📈 Monitoring Summary:")
        print(f"   Total Events: {len(auth_events)}")
        print(f"   Suspicious Activities: {len(suspicious_activities)}")
        print(f"   Log File: {self.log_path}")
        print(f"   Database: {self.db_path}")
        
        return len(suspicious_activities) == 0
    
    def continuous_monitoring(self, interval=300):
        """
        Run continuous monitoring
        """
        print("🔄 Starting continuous authentication monitoring...")
        print(f"   Interval: {interval} seconds")
        print(f"   Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_monitoring_cycle()
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping authentication monitoring...")
            return 0
        except Exception as e:
            self.log_error(f"Error in continuous monitoring: {e}")
            return 1

def main():
    """
    Main function to run authentication monitoring
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN Authentication Monitoring")
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=300,
                       help="Monitoring interval in seconds (default: 300)")
    parser.add_argument("--db-path", default="/opt/xvpn/data/xvpn.db",
                       help="Database path (default: /opt/xvpn/data/xvpn.db)")
    parser.add_argument("--log-path", default="/opt/xvpn/logs/auth.log",
                       help="Log file path (default: /opt/xvpn/logs/auth.log)")
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = AuthMonitor(db_path=args.db_path, log_path=args.log_path)
    
    if args.continuous:
        # Run continuous monitoring
        return monitor.continuous_monitoring(interval=args.interval)
    else:
        # Run single monitoring cycle
        success = monitor.run_monitoring_cycle()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())