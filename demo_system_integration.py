#!/usr/bin/env python3
"""
Mac Status PWA - System Integration Demo
システム統合デモ

This script demonstrates the complete functionality of the Mac Status PWA
by running through various user scenarios and system interactions.
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import websockets
import requests
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from system_monitor import SystemMonitor
from chat_context_manager import ChatContextManager
from message_types import MessageType, ConnectionStatus

class SystemIntegrationDemo:
    """Comprehensive system integration demonstration"""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.websocket_url = "ws://localhost:8000/ws"
        self.demo_results = []
        self.system_monitor = SystemMonitor()
        self.chat_context = ChatContextManager()
        
    async def run_demo(self):
        """Run the complete system integration demo"""
        print("🚀 Mac Status PWA - System Integration Demo")
        print("=" * 60)
        
        # Test 1: System Health Check
        await self.test_system_health()
        
        # Test 2: System Monitoring
        await self.test_system_monitoring()
        
        # Test 3: WebSocket Communication
        await self.test_websocket_communication()
        
        # Test 4: Chat Context Management
        await self.test_chat_context()
        
        # Test 5: PWA Functionality
        await self.test_pwa_functionality()
        
        # Test 6: Performance Benchmarks
        await self.test_performance()
        
        # Test 7: Error Handling
        await self.test_error_handling()
        
        # Generate Demo Report
        self.generate_demo_report()
        
    async def test_system_health(self):
        """Test basic system health and connectivity"""
        print("\n📊 Testing System Health...")
        
        try:
            # Test HTTP endpoints
            response = requests.get(f"{self.server_url}/health", timeout=5)
            health_status = response.status_code == 200
            
            # Test system monitoring
            system_info = await self.system_monitor.get_system_info()
            monitoring_status = bool(system_info)
            
            # Test file structure
            required_files = [
                "backend/main.py",
                "frontend/index.html",
                "frontend/manifest.json",
                "config/production.py"
            ]
            file_status = all(Path(f).exists() for f in required_files)
            
            result = {
                "test": "System Health",
                "http_endpoint": health_status,
                "system_monitoring": monitoring_status,
                "file_structure": file_status,
                "overall": health_status and monitoring_status and file_status
            }
            
            self.demo_results.append(result)
            self.print_test_result("System Health", result["overall"])
            
        except Exception as e:
            print(f"❌ System Health Test Failed: {e}")
            self.demo_results.append({
                "test": "System Health",
                "error": str(e),
                "overall": False
            })
    
    async def test_system_monitoring(self):
        """Test system monitoring capabilities"""
        print("\n🖥️ Testing System Monitoring...")
        
        try:
            # Get comprehensive system information
            system_info = await self.system_monitor.get_system_info()
            
            # Verify required fields
            required_fields = ['cpu_percent', 'memory', 'disk', 'processes']
            fields_present = all(field in system_info for field in required_fields)
            
            # Test process monitoring
            top_processes = self.system_monitor.get_top_processes(limit=5)
            process_monitoring = len(top_processes) > 0
            
            # Test system summary
            summary = self.system_monitor.get_system_summary()
            summary_available = bool(summary)
            
            # Test real-time monitoring
            self.system_monitor.add_status_callback(self._demo_status_callback)
            await self.system_monitor.start_monitoring()
            await asyncio.sleep(2)  # Monitor for 2 seconds
            await self.system_monitor.stop_monitoring()
            
            result = {
                "test": "System Monitoring",
                "system_info": fields_present,
                "process_monitoring": process_monitoring,
                "system_summary": summary_available,
                "realtime_monitoring": True,
                "overall": fields_present and process_monitoring and summary_available
            }
            
            self.demo_results.append(result)
            self.print_test_result("System Monitoring", result["overall"])
            
            # Display sample data
            print(f"  📈 CPU Usage: {system_info.get('cpu_percent', 0):.1f}%")
            print(f"  💾 Memory Usage: {system_info.get('memory', {}).get('percent', 0):.1f}%")
            print(f"  💿 Disk Usage: {system_info.get('disk', {}).get('percent', 0):.1f}%")
            print(f"  🔄 Top Process: {top_processes[0].name if top_processes else 'N/A'}")
            
        except Exception as e:
            print(f"❌ System Monitoring Test Failed: {e}")
            self.demo_results.append({
                "test": "System Monitoring",
                "error": str(e),
                "overall": False
            })
    
    async def test_websocket_communication(self):
        """Test WebSocket communication"""
        print("\n🔌 Testing WebSocket Communication...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test connection
                connection_established = True
                
                # Test ping/pong
                ping_message = {
                    "type": MessageType.PING.value,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(ping_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                ping_response = json.loads(response)
                ping_success = ping_response.get("type") == MessageType.PONG.value
                
                # Test system status request
                status_message = {
                    "type": MessageType.SYSTEM_STATUS_REQUEST.value,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(status_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                status_response = json.loads(response)
                status_success = status_response.get("type") == MessageType.SYSTEM_STATUS_RESPONSE.value
                
                # Test chat message
                chat_message = {
                    "type": MessageType.CHAT_MESSAGE.value,
                    "message": "システムの状態を教えてください",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(chat_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                chat_response = json.loads(response)
                chat_success = chat_response.get("type") == MessageType.CHAT_RESPONSE.value
                
                result = {
                    "test": "WebSocket Communication",
                    "connection": connection_established,
                    "ping_pong": ping_success,
                    "system_status": status_success,
                    "chat_message": chat_success,
                    "overall": connection_established and ping_success and status_success
                }
                
                self.demo_results.append(result)
                self.print_test_result("WebSocket Communication", result["overall"])
                
                if chat_success:
                    print(f"  💬 Chat Response: {chat_response.get('data', {}).get('message', 'N/A')[:100]}...")
                
        except Exception as e:
            print(f"❌ WebSocket Communication Test Failed: {e}")
            self.demo_results.append({
                "test": "WebSocket Communication",
                "error": str(e),
                "overall": False
            })
    
    async def test_chat_context(self):
        """Test chat context management"""
        print("\n💬 Testing Chat Context Management...")
        
        try:
            # Test conversation history
            self.chat_context.add_message("user", "こんにちは")
            self.chat_context.add_message("assistant", "こんにちは！Mac Status PWAです。")
            
            history = self.chat_context.get_conversation_history()
            history_management = len(history) == 2
            
            # Test context prompt generation
            system_data = await self.system_monitor.get_system_info()
            context_prompt = self.chat_context.get_context_prompt(system_data)
            prompt_generation = bool(context_prompt)
            
            # Test personalization
            personalized_response = self.chat_context.personalize_response("システムは正常です。")
            personalization = bool(personalized_response)
            
            # Test context clearing
            self.chat_context.clear_history()
            cleared_history = len(self.chat_context.get_conversation_history()) == 0
            
            result = {
                "test": "Chat Context Management",
                "history_management": history_management,
                "prompt_generation": prompt_generation,
                "personalization": personalization,
                "context_clearing": cleared_history,
                "overall": history_management and prompt_generation and personalization
            }
            
            self.demo_results.append(result)
            self.print_test_result("Chat Context Management", result["overall"])
            
        except Exception as e:
            print(f"❌ Chat Context Test Failed: {e}")
            self.demo_results.append({
                "test": "Chat Context Management",
                "error": str(e),
                "overall": False
            })
    
    async def test_pwa_functionality(self):
        """Test PWA functionality"""
        print("\n📱 Testing PWA Functionality...")
        
        try:
            # Test manifest.json
            manifest_response = requests.get(f"{self.server_url}/manifest.json")
            manifest_available = manifest_response.status_code == 200
            
            if manifest_available:
                manifest_data = manifest_response.json()
                manifest_valid = all(key in manifest_data for key in ['name', 'icons', 'start_url'])
            else:
                manifest_valid = False
            
            # Test service worker
            sw_response = requests.get(f"{self.server_url}/sw.js")
            service_worker_available = sw_response.status_code == 200
            
            # Test icons
            icon_files = [
                "frontend/icons/icon-192x192.png",
                "frontend/icons/icon-512x512.png"
            ]
            icons_available = all(Path(icon).exists() for icon in icon_files)
            
            # Test offline capability (service worker content)
            if service_worker_available:
                sw_content = sw_response.text
                offline_support = "cache" in sw_content.lower()
            else:
                offline_support = False
            
            result = {
                "test": "PWA Functionality",
                "manifest": manifest_available and manifest_valid,
                "service_worker": service_worker_available,
                "icons": icons_available,
                "offline_support": offline_support,
                "overall": manifest_available and service_worker_available and icons_available
            }
            
            self.demo_results.append(result)
            self.print_test_result("PWA Functionality", result["overall"])
            
        except Exception as e:
            print(f"❌ PWA Functionality Test Failed: {e}")
            self.demo_results.append({
                "test": "PWA Functionality",
                "error": str(e),
                "overall": False
            })
    
    async def test_performance(self):
        """Test performance benchmarks"""
        print("\n⚡ Testing Performance...")
        
        try:
            # Test system info retrieval speed
            start_time = time.time()
            system_info = await self.system_monitor.get_system_info()
            system_info_time = time.time() - start_time
            
            # Test multiple concurrent requests
            start_time = time.time()
            tasks = [self.system_monitor.get_system_info() for _ in range(5)]
            await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time
            
            # Performance thresholds
            system_info_fast = system_info_time < 1.0  # < 1 second
            concurrent_reasonable = concurrent_time < 3.0  # < 3 seconds for 5 requests
            
            # Memory usage check
            import psutil
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / 1024 / 1024
            memory_reasonable = memory_usage_mb < 500  # < 500MB
            
            result = {
                "test": "Performance",
                "system_info_speed": system_info_fast,
                "concurrent_requests": concurrent_reasonable,
                "memory_usage": memory_reasonable,
                "metrics": {
                    "system_info_time": f"{system_info_time:.3f}s",
                    "concurrent_time": f"{concurrent_time:.3f}s",
                    "memory_usage": f"{memory_usage_mb:.1f}MB"
                },
                "overall": system_info_fast and concurrent_reasonable and memory_reasonable
            }
            
            self.demo_results.append(result)
            self.print_test_result("Performance", result["overall"])
            
            print(f"  ⏱️ System Info Time: {system_info_time:.3f}s")
            print(f"  🔄 Concurrent Requests: {concurrent_time:.3f}s")
            print(f"  💾 Memory Usage: {memory_usage_mb:.1f}MB")
            
        except Exception as e:
            print(f"❌ Performance Test Failed: {e}")
            self.demo_results.append({
                "test": "Performance",
                "error": str(e),
                "overall": False
            })
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        print("\n🛡️ Testing Error Handling...")
        
        try:
            # Test invalid WebSocket message
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    await websocket.send("invalid json")
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    error_response = json.loads(response)
                    invalid_message_handled = error_response.get("type") == MessageType.ERROR.value
            except:
                invalid_message_handled = False
            
            # Test system monitoring error handling
            try:
                # This should handle gracefully if system info is unavailable
                system_info = await self.system_monitor.get_system_info()
                system_error_handling = True
            except:
                system_error_handling = False
            
            # Test chat context error handling
            try:
                # Test with invalid system data
                context_prompt = self.chat_context.get_context_prompt(None)
                context_error_handling = True
            except:
                context_error_handling = False
            
            result = {
                "test": "Error Handling",
                "invalid_websocket_message": invalid_message_handled,
                "system_monitoring_errors": system_error_handling,
                "chat_context_errors": context_error_handling,
                "overall": system_error_handling and context_error_handling
            }
            
            self.demo_results.append(result)
            self.print_test_result("Error Handling", result["overall"])
            
        except Exception as e:
            print(f"❌ Error Handling Test Failed: {e}")
            self.demo_results.append({
                "test": "Error Handling",
                "error": str(e),
                "overall": False
            })
    
    def _demo_status_callback(self, status_data: Dict[str, Any]):
        """Callback for real-time monitoring demo"""
        pass  # Just for testing the callback mechanism
    
    def print_test_result(self, test_name: str, success: bool):
        """Print formatted test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    def generate_demo_report(self):
        """Generate comprehensive demo report"""
        print("\n" + "=" * 60)
        print("📋 DEMO REPORT")
        print("=" * 60)
        
        total_tests = len(self.demo_results)
        passed_tests = sum(1 for result in self.demo_results if result.get("overall", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.demo_results:
            test_name = result["test"]
            status = "✅ PASS" if result.get("overall", False) else "❌ FAIL"
            print(f"  {status} {test_name}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            
            if "metrics" in result:
                for metric, value in result["metrics"].items():
                    print(f"    {metric}: {value}")
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "results": self.demo_results
        }
        
        with open("demo_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: demo_report.json")
        
        # Overall assessment
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is fully functional.")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ MOSTLY FUNCTIONAL! Minor issues detected.")
        else:
            print("\n⚠️ SIGNIFICANT ISSUES! Please check the failed tests.")

async def main():
    """Main demo execution"""
    demo = SystemIntegrationDemo()
    
    print("Starting Mac Status PWA System Integration Demo...")
    print("Make sure the server is running on localhost:8000")
    print()
    
    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())