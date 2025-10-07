#!/usr/bin/env python3
"""
XVPN Performance Testing Script
Tests performance and load handling of XVPN API
"""

import os
import sys
import time
import json
import threading
import requests
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

class XVPNPerformanceTester:
    """
    Performance testing for XVPN API
    """
    
    def __init__(self, base_url="https://localhost:8443"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        
        # Test results
        self.results = {
            "timestamp": time.time(),
            "performance_tests": {},
            "load_tests": {},
            "stress_tests": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "total": 0
            }
        }
    
    def add_result(self, test_category, test_name, status, message="", details=None):
        """
        Add test result to results
        """
        if test_category not in self.results:
            self.results[test_category] = {}
            
        self.results[test_category][test_name] = {
            "status": status,  # pass, fail
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        
        self.results["summary"]["total"] += 1
        if status == "pass":
            self.results["summary"]["passed"] += 1
        elif status == "fail":
            self.results["summary"]["failed"] += 1
    
    def measure_response_time(self, endpoint, method="GET", data=None):
        """
        Measure response time for an endpoint
        """
        try:
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}", json=data or {}, timeout=30)
            
            end_time = time.time()
            
            return {
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "response_time": None,
                "status_code": None,
                "success": False,
                "error": str(e)
            }
    
    def test_basic_performance(self):
        """
        Test basic API performance
        """
        print("🚀 Testing basic API performance...")
        
        # Test endpoints
        endpoints = [
            ("/mcp/v1/vpn.health", "GET"),
            ("/transports/manifest.json", "GET")
        ]
        
        results = []
        for endpoint, method in endpoints:
            result = self.measure_response_time(endpoint, method)
            results.append({
                "endpoint": endpoint,
                "method": method,
                "response_time": result["response_time"],
                "status_code": result["status_code"],
                "success": result["success"]
            })
            
            if result["success"]:
                self.add_result(
                    "performance_tests",
                    f"Basic Performance - {endpoint}",
                    "pass",
                    f"Response time: {result['response_time']:.3f}s",
                    result
                )
            else:
                self.add_result(
                    "performance_tests",
                    f"Basic Performance - {endpoint}",
                    "fail",
                    f"Error: {result.get('error', 'Unknown')}",
                    result
                )
        
        # Calculate average response time
        successful_responses = [r for r in results if r["success"]]
        if successful_responses:
            avg_response_time = sum(r["response_time"] for r in successful_responses) / len(successful_responses)
            
            if avg_response_time < 1.0:  # Less than 1 second
                self.add_result(
                    "performance_tests",
                    "Average Response Time",
                    "pass",
                    f"Average response time: {avg_response_time:.3f}s (< 1s target)"
                )
            else:
                self.add_result(
                    "performance_tests",
                    "Average Response Time",
                    "fail",
                    f"Average response time: {avg_response_time:.3f}s (>= 1s target)"
                )
        else:
            self.add_result(
                "performance_tests",
                "Average Response Time",
                "fail",
                "No successful responses to calculate average"
            )
    
    def test_concurrent_requests(self, num_threads=10):
        """
        Test concurrent request handling
        """
        print(f"🚀 Testing concurrent requests ({num_threads} threads)...")
        
        def make_request():
            return self.measure_response_time("/mcp/v1/vpn.health", "GET")
        
        # Measure baseline
        baseline_result = self.measure_response_time("/mcp/v1/vpn.health", "GET")
        baseline_time = baseline_result["response_time"] or 0
        
        # Concurrent requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = num_threads - successful_requests
        
        # Calculate average response time under load
        successful_times = [r["response_time"] for r in results if r["success"] and r["response_time"] is not None]
        if successful_times:
            avg_load_time = sum(successful_times) / len(successful_times)
            time_increase = ((avg_load_time - baseline_time) / baseline_time) * 100 if baseline_time > 0 else 0
            
            if time_increase < 50:  # Less than 50% increase
                self.add_result(
                    "load_tests",
                    f"Concurrent Requests ({num_threads} threads)",
                    "pass",
                    f"{successful_requests}/{num_threads} requests successful, avg time: {avg_load_time:.3f}s (+{time_increase:.1f}%)",
                    {
                        "successful_requests": successful_requests,
                        "failed_requests": failed_requests,
                        "total_requests": num_threads,
                        "average_response_time": avg_load_time,
                        "time_increase_percent": time_increase,
                        "total_test_time": total_time
                    }
                )
            else:
                self.add_result(
                    "load_tests",
                    f"Concurrent Requests ({num_threads} threads)",
                    "fail",
                    f"{successful_requests}/{num_threads} requests successful, avg time: {avg_load_time:.3f}s (+{time_increase:.1f}%)",
                    {
                        "successful_requests": successful_requests,
                        "failed_requests": failed_requests,
                        "total_requests": num_threads,
                        "average_response_time": avg_load_time,
                        "time_increase_percent": time_increase,
                        "total_test_time": total_time
                    }
                )
        else:
            self.add_result(
                "load_tests",
                f"Concurrent Requests ({num_threads} threads)",
                "fail",
                f"{successful_requests}/{num_threads} requests successful, no response times recorded",
                {
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "total_requests": num_threads,
                    "total_test_time": total_time
                }
            )
    
    def test_resource_usage(self):
        """
        Test system resource usage during API operations
        """
        print("🚀 Testing system resource usage...")
        
        # Baseline measurements
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = psutil.virtual_memory().percent
        baseline_disk = psutil.disk_usage('/').percent
        
        # Perform API operations
        for _ in range(50):  # Make 50 requests
            self.measure_response_time("/mcp/v1/vpn.health", "GET")
            time.sleep(0.1)  # Small delay between requests
        
        # Post-measurements
        post_cpu = psutil.cpu_percent(interval=1)
        post_memory = psutil.virtual_memory().percent
        post_disk = psutil.disk_usage('/').percent
        
        # Calculate differences
        cpu_increase = post_cpu - baseline_cpu
        memory_increase = post_memory - baseline_memory
        
        # Resource usage results
        resource_data = {
            "baseline": {
                "cpu_percent": baseline_cpu,
                "memory_percent": baseline_memory,
                "disk_percent": baseline_disk
            },
            "post_test": {
                "cpu_percent": post_cpu,
                "memory_percent": post_memory,
                "disk_percent": post_disk
            },
            "increase": {
                "cpu_percent": cpu_increase,
                "memory_percent": memory_increase
            }
        }
        
        # Evaluate resource usage
        if cpu_increase < 10 and memory_increase < 5:  # Reasonable increases
            self.add_result(
                "performance_tests",
                "Resource Usage",
                "pass",
                f"CPU: +{cpu_increase:.1f}%, Memory: +{memory_increase:.1f}%",
                resource_data
            )
        else:
            self.add_result(
                "performance_tests",
                "Resource Usage",
                "fail",
                f"CPU: +{cpu_increase:.1f}%, Memory: +{memory_increase:.1f}%",
                resource_data
            )
    
    def test_stress_scenarios(self):
        """
        Test stress scenarios
        """
        print("🚀 Testing stress scenarios...")
        
        # Test high load
        self.test_concurrent_requests(50)  # 50 concurrent threads
        
        # Test sustained load
        print("   🔄 Testing sustained load...")
        
        successful_requests = 0
        total_requests = 100
        start_time = time.time()
        
        for i in range(total_requests):
            result = self.measure_response_time("/mcp/v1/vpn.health", "GET")
            if result["success"]:
                successful_requests += 1
            
            # Small delay to simulate realistic usage
            if i % 10 == 0:
                time.sleep(0.5)
        
        end_time = time.time()
        total_time = end_time - start_time
        success_rate = (successful_requests / total_requests) * 100
        
        if success_rate >= 95:  # 95% success rate
            self.add_result(
                "stress_tests",
                "Sustained Load",
                "pass",
                f"{successful_requests}/{total_requests} requests successful ({success_rate:.1f}%)",
                {
                    "successful_requests": successful_requests,
                    "total_requests": total_requests,
                    "success_rate": success_rate,
                    "total_time": total_time
                }
            )
        else:
            self.add_result(
                "stress_tests",
                "Sustained Load",
                "fail",
                f"{successful_requests}/{total_requests} requests successful ({success_rate:.1f}%)",
                {
                    "successful_requests": successful_requests,
                    "total_requests": total_requests,
                    "success_rate": success_rate,
                    "total_time": total_time
                }
            )
    
    def run_all_tests(self):
        """
        Run all performance tests
        """
        print("⚡ XVPN API Performance Testing Suite")
        print("=" * 40)
        print(f"Testing server: {self.base_url}")
        print()
        
        # Run all tests
        self.test_basic_performance()
        self.test_concurrent_requests(10)  # Normal load
        self.test_resource_usage()
        self.test_stress_scenarios()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        return self.results["summary"]["failed"] == 0
    
    def print_summary(self):
        """
        Print performance test summary
        """
        print("\n" + "=" * 40)
        print("📊 Performance Test Summary")
        print("=" * 40)
        
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        total = self.results["summary"]["total"]
        
        print(f"✅ Passed:     {passed}/{total} tests")
        print(f"❌ Failed:     {failed}/{total} tests")
        print()
        
        # Overall status
        if failed == 0:
            print("🎉 All performance tests PASSED! API performs well.")
            overall_status = "PASS"
        else:
            print("❌ Some performance tests FAILED! Performance issues detected.")
            overall_status = "FAIL"
        
        print()
        print(f"Overall Status: {overall_status}")
        
        # Detailed results by category
        categories = ["performance_tests", "load_tests", "stress_tests"]
        category_names = ["Performance Tests", "Load Tests", "Stress Tests"]
        
        for category, name in zip(categories, category_names):
            if category in self.results and self.results[category]:
                print(f"\n📋 {name}:")
                for test_name, result in self.results[category].items():
                    status_symbol = "✅" if result["status"] == "pass" else "❌"
                    print(f"   {status_symbol} {test_name}: {result['message']}")
    
    def save_results(self):
        """
        Save test results to file
        """
        results_file = Path.home() / "chatvpn" / "performance" / "api_performance_test_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📝 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run performance tests
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="XVPN API Performance Testing")
    parser.add_argument("--url", default="https://localhost:8443", 
                       help="Base URL for API testing (default: https://localhost:8443)")
    parser.add_argument("--threads", type=int, default=10,
                       help="Number of concurrent threads for load testing (default: 10)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = XVPNPerformanceTester(base_url=args.url)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())