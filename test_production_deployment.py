#!/usr/bin/env python3
"""
Production Deployment Test Suite
本番デプロイメントテストスイート

This script tests the production deployment configuration and validates
that all components are properly configured for production use.
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import requests
import websocket
from pathlib import Path
from typing import Dict, List, Any

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{Colors.GREEN}PASS{Colors.ENDC}" if passed else f"{Colors.RED}FAIL{Colors.ENDC}"
    print(f"[{status}] {test_name}")
    if details:
        print(f"        {details}")

def print_section(section_name: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE} {section_name}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}")

class ProductionDeploymentTester:
    """Test suite for production deployment"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.test_results = []
        self.server_process = None
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results"""
        try:
            result = test_func(*args, **kwargs)
            self.test_results.append((test_name, result, ""))
            print_test_result(test_name, result)
            return result
        except Exception as e:
            self.test_results.append((test_name, False, str(e)))
            print_test_result(test_name, False, str(e))
            return False
    
    def test_configuration_files(self) -> bool:
        """Test that all configuration files exist and are valid"""
        print_section("Configuration Files")
        
        # Test production config
        config_files = [
            "config/production.py",
            "config/security.py"
        ]
        
        all_passed = True
        for config_file in config_files:
            exists = Path(config_file).exists()
            self.run_test(f"Config file exists: {config_file}", lambda: exists)
            if not exists:
                all_passed = False
        
        # Test config validation
        try:
            from config.production import validate_environment
            errors = validate_environment()
            validation_passed = len(errors) == 0
            self.run_test("Production config validation", lambda: validation_passed, 
                         f"Errors: {errors}" if errors else "")
            if not validation_passed:
                all_passed = False
        except Exception as e:
            self.run_test("Production config validation", lambda: False, str(e))
            all_passed = False
        
        return all_passed
    
    def test_directory_structure(self) -> bool:
        """Test that all required directories exist"""
        print_section("Directory Structure")
        
        required_dirs = [
            "backend",
            "frontend",
            "config",
            "tests",
            "logs",
            "models/elyza7b"
        ]
        
        all_passed = True
        for directory in required_dirs:
            exists = Path(directory).exists()
            self.run_test(f"Directory exists: {directory}", lambda: exists)
            if not exists:
                all_passed = False
        
        return all_passed
    
    def test_dependencies(self) -> bool:
        """Test that all required dependencies are installed"""
        print_section("Dependencies")
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "websockets",
            "psutil",
            "llama-cpp-python"
        ]
        
        all_passed = True
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.run_test(f"Package installed: {package}", lambda: True)
            except ImportError:
                self.run_test(f"Package installed: {package}", lambda: False)
                all_passed = False
        
        return all_passed
    
    def test_security_configuration(self) -> bool:
        """Test security configuration"""
        print_section("Security Configuration")
        
        all_passed = True
        
        try:
            from config.security import (
                security_manager, SECURITY_HEADERS, 
                SECURITY_MIDDLEWARE_CONFIG, generate_csp_header
            )
            
            # Test security manager
            self.run_test("Security manager initialized", 
                         lambda: security_manager is not None)
            
            # Test CSP header generation
            csp_header = generate_csp_header()
            self.run_test("CSP header generation", 
                         lambda: len(csp_header) > 0)
            
            # Test security headers
            self.run_test("Security headers configured", 
                         lambda: len(SECURITY_HEADERS) > 0)
            
        except Exception as e:
            self.run_test("Security configuration", lambda: False, str(e))
            all_passed = False
        
        return all_passed
    
    def start_test_server(self) -> bool:
        """Start the application server for testing"""
        print_section("Server Startup")
        
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                [sys.executable, "backend/main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            max_wait = 30  # 30 seconds
            for i in range(max_wait):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=1)
                    if response.status_code == 200:
                        self.run_test("Server startup", lambda: True)
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            self.run_test("Server startup", lambda: False, "Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            self.run_test("Server startup", lambda: False, str(e))
            return False
    
    def test_http_endpoints(self) -> bool:
        """Test HTTP endpoints"""
        print_section("HTTP Endpoints")
        
        all_passed = True
        
        endpoints = [
            ("/", "Main page"),
            ("/health", "Health check"),
            ("/api/status", "System status API")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                passed = response.status_code == 200
                self.run_test(f"{description} ({endpoint})", lambda: passed,
                             f"Status: {response.status_code}")
                if not passed:
                    all_passed = False
            except Exception as e:
                self.run_test(f"{description} ({endpoint})", lambda: False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_websocket_connection(self) -> bool:
        """Test WebSocket connection"""
        print_section("WebSocket Connection")
        
        try:
            ws = websocket.create_connection(self.ws_url, timeout=5)
            
            # Test sending a message
            test_message = json.dumps({
                "type": "chat",
                "content": "Hello, test message"
            })
            ws.send(test_message)
            
            # Wait for response
            response = ws.recv()
            response_data = json.loads(response)
            
            ws.close()
            
            self.run_test("WebSocket connection", lambda: True)
            self.run_test("WebSocket message exchange", 
                         lambda: "content" in response_data or "error" in response_data)
            return True
            
        except Exception as e:
            self.run_test("WebSocket connection", lambda: False, str(e))
            return False
    
    def test_pwa_functionality(self) -> bool:
        """Test PWA functionality"""
        print_section("PWA Functionality")
        
        all_passed = True
        
        # Test manifest.json
        try:
            response = requests.get(f"{self.base_url}/static/manifest.json", timeout=5)
            manifest_valid = response.status_code == 200
            self.run_test("PWA manifest accessible", lambda: manifest_valid)
            
            if manifest_valid:
                manifest_data = response.json()
                has_required_fields = all(field in manifest_data for field in 
                                        ["name", "short_name", "start_url", "display"])
                self.run_test("PWA manifest valid", lambda: has_required_fields)
                if not has_required_fields:
                    all_passed = False
            else:
                all_passed = False
                
        except Exception as e:
            self.run_test("PWA manifest", lambda: False, str(e))
            all_passed = False
        
        # Test service worker
        try:
            response = requests.get(f"{self.base_url}/static/sw.js", timeout=5)
            sw_valid = response.status_code == 200
            self.run_test("Service worker accessible", lambda: sw_valid)
            if not sw_valid:
                all_passed = False
        except Exception as e:
            self.run_test("Service worker", lambda: False, str(e))
            all_passed = False
        
        return all_passed
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        print_section("Security Headers")
        
        all_passed = True
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            headers = response.headers
            
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection"
            ]
            
            for header in expected_headers:
                has_header = header in headers
                self.run_test(f"Security header: {header}", lambda: has_header)
                if not has_header:
                    all_passed = False
            
        except Exception as e:
            self.run_test("Security headers", lambda: False, str(e))
            all_passed = False
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test basic performance metrics"""
        print_section("Performance")
        
        all_passed = True
        
        # Test response time
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            fast_response = response_time < 2.0  # Should respond within 2 seconds
            self.run_test("Health endpoint response time", lambda: fast_response,
                         f"{response_time:.2f}s")
            if not fast_response:
                all_passed = False
                
        except Exception as e:
            self.run_test("Response time test", lambda: False, str(e))
            all_passed = False
        
        return all_passed
    
    def stop_test_server(self):
        """Stop the test server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
    
    def generate_report(self):
        """Generate test report"""
        print_section("Test Report")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.ENDC}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.ENDC}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n{Colors.RED}Failed tests:{Colors.ENDC}")
            for test_name, passed, details in self.test_results:
                if not passed:
                    print(f"  - {test_name}: {details}")
        
        return failed_tests == 0
    
    def run_all_tests(self) -> bool:
        """Run all production deployment tests"""
        print(f"{Colors.BLUE}Mac Status PWA - Production Deployment Test Suite{Colors.ENDC}")
        print(f"{Colors.BLUE}本番デプロイメントテストスイート{Colors.ENDC}\n")
        
        # Pre-server tests
        config_ok = self.test_configuration_files()
        dirs_ok = self.test_directory_structure()
        deps_ok = self.test_dependencies()
        security_ok = self.test_security_configuration()
        
        # Server-dependent tests
        server_started = False
        if config_ok and dirs_ok and deps_ok:
            server_started = self.start_test_server()
            
            if server_started:
                self.test_http_endpoints()
                self.test_websocket_connection()
                self.test_pwa_functionality()
                self.test_security_headers()
                self.test_performance()
        
        # Cleanup
        if server_started:
            self.stop_test_server()
        
        # Generate report
        return self.generate_report()

def main():
    """Main test function"""
    tester = ProductionDeploymentTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.ENDC}")
        tester.stop_test_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {e}{Colors.ENDC}")
        tester.stop_test_server()
        sys.exit(1)

if __name__ == "__main__":
    main()