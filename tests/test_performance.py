#!/usr/bin/env python3
"""
Performance tests for real-time monitoring system
Tests memory usage, callback performance, and system impact
"""
import asyncio
import time
import tracemalloc
import psutil
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from system_monitor import SystemMonitor, SystemStatus


async def test_basic_performance():
    """Test basic performance metrics"""
    print("=== Basic Performance Test ===")
    
    monitor = SystemMonitor()
    
    # Test single call performance
    start_time = time.time()
    status = await monitor.get_system_info()
    end_time = time.time()
    
    call_time_ms = (end_time - start_time) * 1000
    print(f"Single system info call: {call_time_ms:.1f}ms")
    
    # Test multiple calls
    tracemalloc.start()
    
    start_time = time.time()
    for _ in range(10):
        await monitor.get_system_info()
    end_time = time.time()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    avg_call_time = ((end_time - start_time) / 10) * 1000
    print(f"Average call time (10 calls): {avg_call_time:.1f}ms")
    print(f"Memory usage - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")
    
    # Performance assertions
    assert call_time_ms < 1000, f"Single call too slow: {call_time_ms:.1f}ms"
    assert avg_call_time < 500, f"Average call too slow: {avg_call_time:.1f}ms"
    assert peak / 1024 / 1024 < 50, f"Memory usage too high: {peak / 1024 / 1024:.1f}MB"
    
    print("✅ Basic performance test passed!")
    return {
        'single_call_ms': call_time_ms,
        'avg_call_ms': avg_call_time,
        'memory_peak_mb': peak / 1024 / 1024
    }


async def test_realtime_monitoring_performance():
    """Test real-time monitoring performance"""
    print("\n=== Real-time Monitoring Performance Test ===")
    
    monitor = SystemMonitor(update_interval=1.0)
    performance_data = []
    
    async def performance_callback(status, alerts, changes):
        """Callback to measure performance metrics"""
        callback_start = time.time()
        
        # Simulate processing
        await asyncio.sleep(0.01)  # 10ms processing time
        
        callback_end = time.time()
        performance_data.append({
            'timestamp': status.timestamp,
            'callback_time_ms': (callback_end - callback_start) * 1000,
            'cpu_percent': status.cpu_percent,
            'memory_percent': status.memory_percent,
            'alerts_count': len(alerts),
            'changes_count': len(changes)
        })
    
    monitor.add_callback(performance_callback)
    
    # Start memory tracking
    tracemalloc.start()
    
    print("Starting real-time monitoring for 10 seconds...")
    await monitor.start_monitoring()
    await asyncio.sleep(10)
    await monitor.stop_monitoring()
    
    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Analyze performance data
    if performance_data:
        avg_callback_time = sum(d['callback_time_ms'] for d in performance_data) / len(performance_data)
        max_callback_time = max(d['callback_time_ms'] for d in performance_data)
        total_alerts = sum(d['alerts_count'] for d in performance_data)
        total_changes = sum(d['changes_count'] for d in performance_data)
        
        print(f"Results:")
        print(f"  - Monitoring cycles: {len(performance_data)}")
        print(f"  - Average callback time: {avg_callback_time:.2f}ms")
        print(f"  - Maximum callback time: {max_callback_time:.2f}ms")
        print(f"  - Total alerts: {total_alerts}")
        print(f"  - Total changes: {total_changes}")
        print(f"  - Memory - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")
        
        # Performance assertions
        assert avg_callback_time < 50.0, f"Average callback time too high: {avg_callback_time:.2f}ms"
        assert peak / 1024 / 1024 < 100.0, f"Peak memory usage too high: {peak / 1024 / 1024:.1f}MB"
        
        print("✅ Real-time monitoring performance test passed!")
        return {
            'cycles': len(performance_data),
            'avg_callback_time_ms': avg_callback_time,
            'max_callback_time_ms': max_callback_time,
            'total_alerts': total_alerts,
            'total_changes': total_changes,
            'memory_peak_mb': peak / 1024 / 1024
        }
    else:
        print("❌ No performance data collected")
        return None


async def test_stress_monitoring():
    """Stress test with multiple callbacks and high frequency"""
    print("\n=== Stress Test ===")
    
    monitor = SystemMonitor(update_interval=0.5)  # High frequency
    callback_counters = {'cpu_intensive': 0, 'io_intensive': 0, 'memory_intensive': 0}
    
    async def cpu_intensive_callback(status, alerts, changes):
        callback_counters['cpu_intensive'] += 1
        # CPU-intensive work
        sum(i * i for i in range(1000))
    
    async def io_intensive_callback(status, alerts, changes):
        callback_counters['io_intensive'] += 1
        # I/O simulation
        await asyncio.sleep(0.005)  # 5ms delay
    
    async def memory_intensive_callback(status, alerts, changes):
        callback_counters['memory_intensive'] += 1
        # Memory allocation
        temp_data = [i for i in range(1000)]
        del temp_data
    
    # Add all callbacks
    monitor.add_callback(cpu_intensive_callback)
    monitor.add_callback(io_intensive_callback)
    monitor.add_callback(memory_intensive_callback)
    
    # Set aggressive thresholds for more alerts
    monitor.set_alert_thresholds(cpu_percent=10.0, memory_percent=10.0, disk_percent=10.0)
    
    # Start memory tracking
    tracemalloc.start()
    
    start_time = time.time()
    print("Starting stress test for 5 seconds...")
    await monitor.start_monitoring()
    await asyncio.sleep(5)
    await monitor.stop_monitoring()
    end_time = time.time()
    
    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Analyze results
    total_time = end_time - start_time
    total_callbacks = sum(callback_counters.values())
    
    print(f"Results:")
    print(f"  - Test duration: {total_time:.2f}s")
    print(f"  - Total callbacks: {total_callbacks}")
    print(f"  - CPU intensive: {callback_counters['cpu_intensive']}")
    print(f"  - I/O intensive: {callback_counters['io_intensive']}")
    print(f"  - Memory intensive: {callback_counters['memory_intensive']}")
    print(f"  - Callbacks/second: {total_callbacks / total_time:.1f}")
    print(f"  - Memory - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")
    
    # Stress test assertions
    assert total_callbacks > 0, "No callbacks executed"
    assert peak / 1024 / 1024 < 200.0, f"Peak memory too high: {peak / 1024 / 1024:.1f}MB"
    
    print("✅ Stress test passed!")
    return {
        'duration_s': total_time,
        'total_callbacks': total_callbacks,
        'callbacks_per_second': total_callbacks / total_time,
        'memory_peak_mb': peak / 1024 / 1024
    }


async def test_system_impact():
    """Test system impact of monitoring"""
    print("\n=== System Impact Test ===")
    
    # Get baseline system usage
    print("Measuring baseline system usage...")
    baseline_cpu = psutil.cpu_percent(interval=1)
    baseline_memory = psutil.virtual_memory().percent
    
    print(f"Baseline - CPU: {baseline_cpu:.1f}%, Memory: {baseline_memory:.1f}%")
    
    # Start monitoring with callbacks
    monitor = SystemMonitor(update_interval=1.0)
    
    async def monitoring_callback(status, alerts, changes):
        # Light processing
        pass
    
    monitor.add_callback(monitoring_callback)
    
    print("Starting monitoring to measure impact...")
    await monitor.start_monitoring()
    
    # Let it run and measure
    await asyncio.sleep(5)
    
    # Measure system usage during monitoring
    monitoring_cpu = psutil.cpu_percent(interval=1)
    monitoring_memory = psutil.virtual_memory().percent
    
    await monitor.stop_monitoring()
    
    # Calculate impact
    cpu_impact = monitoring_cpu - baseline_cpu
    memory_impact = monitoring_memory - baseline_memory
    
    print(f"During monitoring - CPU: {monitoring_cpu:.1f}%, Memory: {monitoring_memory:.1f}%")
    print(f"Impact - CPU: {cpu_impact:+.1f}%, Memory: {memory_impact:+.1f}%")
    
    # Impact should be minimal
    assert abs(cpu_impact) < 15.0, f"CPU impact too high: {cpu_impact:.1f}%"
    assert abs(memory_impact) < 10.0, f"Memory impact too high: {memory_impact:.1f}%"
    
    print("✅ System impact test passed!")
    return {
        'baseline_cpu': baseline_cpu,
        'monitoring_cpu': monitoring_cpu,
        'cpu_impact': cpu_impact,
        'baseline_memory': baseline_memory,
        'monitoring_memory': monitoring_memory,
        'memory_impact': memory_impact
    }


async def test_alert_performance():
    """Test alert detection performance"""
    print("\n=== Alert Performance Test ===")
    
    monitor = SystemMonitor(update_interval=0.5)
    alert_data = []
    
    async def alert_callback(status, alerts, changes):
        alert_data.append({
            'timestamp': time.time(),
            'alerts_count': len(alerts),
            'alert_types': [alert['type'] for alert in alerts]
        })
    
    # Set thresholds that will trigger alerts
    monitor.set_alert_thresholds(cpu_percent=5.0, memory_percent=5.0, disk_percent=5.0)
    monitor.add_callback(alert_callback)
    
    print("Testing alert detection for 3 seconds...")
    await monitor.start_monitoring()
    await asyncio.sleep(3)
    await monitor.stop_monitoring()
    
    # Analyze alert performance
    total_alerts = sum(d['alerts_count'] for d in alert_data)
    cycles_with_alerts = sum(1 for d in alert_data if d['alerts_count'] > 0)
    
    print(f"Results:")
    print(f"  - Monitoring cycles: {len(alert_data)}")
    print(f"  - Total alerts: {total_alerts}")
    print(f"  - Cycles with alerts: {cycles_with_alerts}")
    print(f"  - Alert rate: {cycles_with_alerts / len(alert_data) * 100:.1f}%")
    
    # Alert system should work efficiently
    assert len(alert_data) > 0, "No monitoring cycles recorded"
    
    print("✅ Alert performance test passed!")
    return {
        'cycles': len(alert_data),
        'total_alerts': total_alerts,
        'cycles_with_alerts': cycles_with_alerts,
        'alert_rate_percent': cycles_with_alerts / len(alert_data) * 100 if alert_data else 0
    }


async def run_all_performance_tests():
    """Run all performance tests"""
    print("🚀 Starting Performance Test Suite")
    print("=" * 50)
    
    results = {}
    
    try:
        # Run all tests
        results['basic'] = await test_basic_performance()
        results['realtime'] = await test_realtime_monitoring_performance()
        results['stress'] = await test_stress_monitoring()
        results['system_impact'] = await test_system_impact()
        results['alerts'] = await test_alert_performance()
        
        print("\n" + "=" * 50)
        print("🎉 All Performance Tests Completed Successfully!")
        print("=" * 50)
        
        # Summary
        print("\n📊 Performance Summary:")
        if results['basic']:
            print(f"  - Single call time: {results['basic']['single_call_ms']:.1f}ms")
        if results['realtime']:
            print(f"  - Real-time monitoring cycles: {results['realtime']['cycles']}")
            print(f"  - Average callback time: {results['realtime']['avg_callback_time_ms']:.2f}ms")
        if results['stress']:
            print(f"  - Stress test callbacks/sec: {results['stress']['callbacks_per_second']:.1f}")
        if results['system_impact']:
            print(f"  - CPU impact: {results['system_impact']['cpu_impact']:+.1f}%")
            print(f"  - Memory impact: {results['system_impact']['memory_impact']:+.1f}%")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        raise


if __name__ == "__main__":
    # Run the performance tests
    asyncio.run(run_all_performance_tests())