#!/usr/bin/env python3
"""
Test script for system status display component
Tests the frontend system status display functionality
"""
import asyncio
import json
import websockets
import time
from datetime import datetime

async def test_system_status_display():
    """Test the system status display by sending mock data"""
    
    # Mock system status data
    mock_status = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": 45.2,
        "cpu_count": 8,
        "cpu_freq": 2400.0,
        "memory_used": 8589934592,  # 8GB in bytes
        "memory_total": 17179869184,  # 16GB in bytes
        "memory_percent": 50.0,
        "disk_used": 107374182400,  # 100GB in bytes
        "disk_total": 536870912000,  # 500GB in bytes
        "disk_percent": 20.0,
        "top_processes": [
            {
                "pid": 1234,
                "name": "Chrome",
                "cpu_percent": 15.5,
                "memory_percent": 8.2,
                "memory_rss": 1073741824,
                "status": "running",
                "create_time": time.time() - 3600,
                "cmdline": ["chrome", "--no-sandbox"]
            }
        ],
        "network_io": {
            "bytes_sent": 1048576,
            "bytes_recv": 2097152,
            "packets_sent": 1000,
            "packets_recv": 1500
        },
        "temperature": None,
        "uptime": time.time() - 86400,
        "load_average": [1.2, 1.5, 1.8]
    }
    
    print("Mock system status data:")
    print(json.dumps(mock_status, indent=2))
    print("\nThis data would be sent to the frontend system status display.")
    print("The display should show:")
    print(f"- CPU: {mock_status['cpu_percent']}%")
    print(f"- Memory: {mock_status['memory_percent']}% ({mock_status['memory_used'] / (1024**3):.1f}GB / {mock_status['memory_total'] / (1024**3):.1f}GB)")
    print(f"- Disk: {mock_status['disk_percent']}% ({mock_status['disk_used'] / (1024**3):.1f}GB / {mock_status['disk_total'] / (1024**3):.1f}GB)")
    
    # Test different usage levels
    print("\n--- Testing different usage levels ---")
    
    # High CPU usage
    high_cpu_status = mock_status.copy()
    high_cpu_status['cpu_percent'] = 85.0
    print(f"High CPU usage: {high_cpu_status['cpu_percent']}% (should show warning)")
    
    # Critical memory usage
    critical_memory_status = mock_status.copy()
    critical_memory_status['memory_percent'] = 95.0
    print(f"Critical memory usage: {critical_memory_status['memory_percent']}% (should show alert)")
    
    # High disk usage
    high_disk_status = mock_status.copy()
    high_disk_status['disk_percent'] = 88.0
    print(f"High disk usage: {high_disk_status['disk_percent']}% (should show warning)")
    
    print("\n--- Animation Test ---")
    print("Testing value changes that should trigger animations:")
    
    # Simulate changing values
    old_cpu = 45.2
    new_cpu = 67.8
    print(f"CPU change: {old_cpu}% -> {new_cpu}% (should animate)")
    
    old_memory = 50.0
    new_memory = 72.5
    print(f"Memory change: {old_memory}% -> {new_memory}% (should animate)")
    
    print("\nTest completed. The frontend should handle these status updates correctly.")

if __name__ == "__main__":
    asyncio.run(test_system_status_display())