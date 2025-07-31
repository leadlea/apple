#!/usr/bin/env python3
"""
Demo script to test real-time monitoring functionality
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from system_monitor import SystemMonitor


async def demo_callback(status, alerts, changes):
    """Demo callback to show real-time monitoring in action"""
    timestamp = status.timestamp.strftime('%H:%M:%S')
    print(f"[{timestamp}] CPU: {status.cpu_percent:5.1f}% | Memory: {status.memory_percent:5.1f}% | Disk: {status.disk_percent:5.1f}%")
    
    # Show alerts
    if alerts:
        for alert in alerts:
            severity_icon = "🚨" if alert['severity'] == 'critical' else "⚠️"
            print(f"  {severity_icon} {alert['message']}")
    
    # Show changes
    if changes:
        for change in changes:
            print(f"  📊 {change['message']}")


async def main():
    """Main demo function"""
    print("🔍 Real-time System Monitoring Demo")
    print("=" * 50)
    
    # Create monitor with 2-second intervals
    monitor = SystemMonitor(update_interval=2.0)
    
    # Set alert thresholds (lower for demo purposes)
    monitor.set_alert_thresholds(
        cpu_percent=20.0,    # Alert if CPU > 20%
        memory_percent=60.0, # Alert if Memory > 60%
        disk_percent=80.0    # Alert if Disk > 80%
    )
    
    # Add callback
    monitor.add_callback(demo_callback)
    
    print("Starting real-time monitoring...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print("Stopping monitoring...")
        await monitor.stop_monitoring()
        
        # Show final stats
        stats = await monitor.get_monitoring_stats()
        print(f"Final stats: {stats}")
        
        print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())