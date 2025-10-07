#!/usr/bin/env python3
"""
XVPN Real-time Performance Monitoring
Monitors API performance and system resources in real-time
"""

import os
import sys
import time
import json
import psutil
import requests
import threading
from pathlib import Path
from datetime import datetime

class XVPNPerformanceMonitor:
    """
    Real-time performance monitoring for XVPN API
    """
    
    def __init__(self, base_url="https://localhost:8443", interval=5):
        self.base_url = base_url
        self.interval = interval
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        self.running = False
        self.monitor_thread = None
        
        # Metrics storage
        self.metrics = {
            "timestamps": [],
            "response_times": [],
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_io": []
        }
        
        # Create logs directory
        self.logs_dir = Path.home() / "chatvpn" / "logs" / "performance"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self):
        """
        Start real-time monitoring
        """
        print(f"📊 Starting XVPN Performance Monitoring")
        print(f"   URL: {self.base_url}")
        print(f"   Interval: {self.interval} seconds")
        print(f"   Logs: {self.logs_dir}")
        print(f"   Press Ctrl+C to stop")
        print()
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """
        Stop real-time monitoring
        """
        print("\n🛑 Stopping XVPN Performance Monitoring...")
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        # Save final metrics
        self.save_metrics()
        self.generate_report()
    
    def _monitor_loop(self):
        """
        Main monitoring loop
        """
        while self.running:
            try:
                # Collect metrics
                timestamp = time.time()
                
                # API response time
                response_time = self._measure_api_response()
                
                # System resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Network I/O
                net_io = psutil.net_io_counters()
                network_data = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
                
                # Store metrics
                self.metrics["timestamps"].append(timestamp)
                self.metrics["response_times"].append(response_time)
                self.metrics["cpu_usage"].append(cpu_percent)
                self.metrics["memory_usage"].append(memory_percent)
                self.metrics["disk_usage"].append(disk_percent)
                self.metrics["network_io"].append(network_data)
                
                # Log metrics
                self._log_metrics(timestamp, response_time, cpu_percent, memory_percent, disk_percent, network_data)
                
                # Wait for next interval
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(self.interval)
    
    def _measure_api_response(self):
        """
        Measure API response time
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/mcp/v1/vpn.health", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                return end_time - start_time
            else:
                return None
        except Exception as e:
            print(f"❌ API request failed: {e}")
            return None
    
    def _log_metrics(self, timestamp, response_time, cpu_percent, memory_percent, disk_percent, network_data):
        """
        Log metrics to file
        """
        # Format timestamp
        dt = datetime.fromtimestamp(timestamp)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create log entry
        log_entry = {
            "timestamp": timestamp,
            "datetime": formatted_time,
            "response_time": response_time,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "network_io": network_data
        }
        
        # Write to log file
        log_file = self.logs_dir / f"performance_{dt.strftime('%Y%m%d')}.log"
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"❌ Error writing to log file: {e}")
        
        # Print to console
        rt_str = f"{response_time:.3f}s" if response_time is not None else "N/A"
        print(f"[{formatted_time}] API: {rt_str} | CPU: {cpu_percent:5.1f}% | MEM: {memory_percent:5.1f}% | DISK: {disk_percent:5.1f}%")
    
    def save_metrics(self):
        """
        Save all metrics to file
        """
        metrics_file = self.logs_dir / "performance_metrics.json"
        
        try:
            with open(metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2)
            print(f"✅ Metrics saved to: {metrics_file}")
        except Exception as e:
            print(f"❌ Error saving metrics: {e}")
    
    def generate_report(self):
        """
        Generate performance report
        """
        if not self.metrics["timestamps"]:
            print("⚠️  No metrics collected, skipping report generation")
            return
        
        # Calculate statistics
        response_times = [rt for rt in self.metrics["response_times"] if rt is not None]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = None
        
        avg_cpu = sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"]) if self.metrics["cpu_usage"] else 0
        avg_memory = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0
        avg_disk = sum(self.metrics["disk_usage"]) / len(self.metrics["disk_usage"]) if self.metrics["disk_usage"] else 0
        
        # Create report
        report = {
            "generated_at": time.time(),
            "duration_seconds": self.metrics["timestamps"][-1] - self.metrics["timestamps"][0] if len(self.metrics["timestamps"]) > 1 else 0,
            "total_samples": len(self.metrics["timestamps"]),
            "api_performance": {
                "average_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "samples_collected": len(response_times),
                "success_rate": len(response_times) / len(self.metrics["timestamps"]) * 100 if self.metrics["timestamps"] else 0
            },
            "system_resources": {
                "average_cpu_percent": avg_cpu,
                "average_memory_percent": avg_memory,
                "average_disk_percent": avg_disk,
                "peak_cpu_percent": max(self.metrics["cpu_usage"]) if self.metrics["cpu_usage"] else 0,
                "peak_memory_percent": max(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0
            },
            "network_io": self.metrics["network_io"][-1] if self.metrics["network_io"] else {}
        }
        
        # Save report
        report_file = self.logs_dir / "performance_report.json"
        
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"✅ Performance report saved to: {report_file}")
            
            # Print summary
            self._print_report_summary(report)
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def _print_report_summary(self, report):
        """
        Print performance report summary
        """
        print("\n" + "=" * 50)
        print("📈 XVPN Performance Report Summary")
        print("=" * 50)
        
        # API Performance
        api_perf = report["api_performance"]
        print(f"\n🚀 API Performance:")
        if api_perf["average_response_time"] is not None:
            print(f"   Average Response Time: {api_perf['average_response_time']:.3f}s")
            print(f"   Min Response Time:     {api_perf['min_response_time']:.3f}s")
            print(f"   Max Response Time:     {api_perf['max_response_time']:.3f}s")
        print(f"   Success Rate:          {api_perf['success_rate']:.1f}%")
        print(f"   Samples Collected:     {api_perf['samples_collected']}")
        
        # System Resources
        sys_res = report["system_resources"]
        print(f"\n🖥️  System Resources:")
        print(f"   Average CPU:    {sys_res['average_cpu_percent']:5.1f}%")
        print(f"   Average Memory: {sys_res['average_memory_percent']:5.1f}%")
        print(f"   Average Disk:   {sys_res['average_disk_percent']:5.1f}%")
        print(f"   Peak CPU:       {sys_res['peak_cpu_percent']:5.1f}%")
        print(f"   Peak Memory:    {sys_res['peak_memory_percent']:5.1f}%")
        
        # Duration
        duration = report["duration_seconds"]
        print(f"\n⏱️  Monitoring Duration: {duration:.1f} seconds")
        print(f"📊 Total Samples: {report['total_samples']}")

def main():
    """
    Main function to run performance monitor
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN Real-time Performance Monitoring")
    parser.add_argument("--url", default="https://localhost:8443",
                       help="Base URL for API monitoring (default: https://localhost:8443)")
    parser.add_argument("--interval", type=int, default=5,
                       help="Monitoring interval in seconds (default: 5)")
    parser.add_argument("--duration", type=int, default=300,
                       help="Monitoring duration in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = XVPNPerformanceMonitor(base_url=args.url, interval=args.interval)
    
    try:
        # Start monitoring
        monitor.start_monitoring()
        
        # Run for specified duration
        time.sleep(args.duration)
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⌨️  Keyboard interrupt received")
        monitor.stop_monitoring()
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        monitor.stop_monitoring()
        return 1

if __name__ == "__main__":
    sys.exit(main())