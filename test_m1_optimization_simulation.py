#!/usr/bin/env python3
"""
M1 Optimization Simulation Test
Tests M1 optimization features without requiring actual model installation
"""
import asyncio
import time
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from m1_optimization import M1Optimizer, print_optimization_report
from response_optimizer import ResponseOptimizer, OptimizationStrategy


async def test_m1_optimization_detection():
    """Test M1 system detection and optimization settings"""
    
    print("🍎 Testing M1 Optimization Detection")
    print("=" * 50)
    
    # Test M1 optimizer
    optimizer = M1Optimizer()
    report = optimizer.get_optimization_report()
    
    print("📱 System Detection Results:")
    system = report['system_detection']
    print(f"   M1 Mac: {'✅ Yes' if system['is_m1_mac'] else '❌ No'}")
    print(f"   CPU Cores: {system['cpu_cores']} total")
    print(f"   Performance Cores: {system['performance_cores']}")
    print(f"   Efficiency Cores: {system['efficiency_cores']}")
    print(f"   Memory: {system['memory_gb']} GB")
    print(f"   Metal Available: {'✅ Yes' if system['metal_available'] else '❌ No'}")
    
    print(f"\n⚙️  Recommended Settings:")
    settings = report['recommended_settings']
    print(f"   GPU Layers: {settings['gpu_layers']}")
    print(f"   Threads: {settings['threads']}")
    print(f"   Batch Size: {settings['batch_size']}")
    print(f"   Context Size: {settings['context_size']}")
    
    print(f"\n💡 Optimization Notes:")
    for note in report['optimization_notes']:
        print(f"   {note}")
    
    # Test configuration creation
    print(f"\n🔧 Testing Configuration Creation:")
    config = optimizer.create_optimized_config()
    
    print(f"   Model Path: {config.model_path}")
    print(f"   Context Size: {config.n_ctx}")
    print(f"   GPU Layers: {config.n_gpu_layers}")
    print(f"   Threads: {config.n_threads}")
    print(f"   Temperature: {config.temperature}")
    print(f"   Max Tokens: {config.max_tokens}")
    
    # Validate settings are appropriate for M1
    validation_results = {
        'gpu_layers_set': config.n_gpu_layers != 0 if system['is_m1_mac'] and system['metal_available'] else config.n_gpu_layers == 0,
        'threads_optimized': 1 <= config.n_threads <= system['cpu_cores'],
        'context_reasonable': 1024 <= config.n_ctx <= 4096,
        'temperature_valid': 0.1 <= config.temperature <= 1.0
    }
    
    print(f"\n✅ Configuration Validation:")
    for check, passed in validation_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        check_name = check.replace('_', ' ').title()
        print(f"   {status} {check_name}")
    
    all_passed = all(validation_results.values())
    return all_passed, report


async def test_response_optimizer_performance():
    """Test response optimizer performance characteristics"""
    
    print("\n🚀 Testing Response Optimizer Performance")
    print("=" * 50)
    
    # Create optimizer
    optimizer = ResponseOptimizer()
    
    # Mock model interface for testing
    class MockModelInterface:
        def __init__(self, response_time_ms: float = 1000):
            self.response_time_ms = response_time_ms
            self.call_count = 0
        
        async def generate_system_response(self, user_message, system_data, conversation_history=None):
            self.call_count += 1
            
            # Simulate processing time
            await asyncio.sleep(self.response_time_ms / 1000.0)
            
            # Mock response
            class MockResponse:
                def __init__(self, content, processing_time_ms, token_count):
                    self.content = content
                    self.processing_time_ms = processing_time_ms
                    self.token_count = token_count
                    self.timestamp = time.time()
                    self.model_info = {'mock': True}
            
            return MockResponse(
                content=f"Mock response to: {user_message}",
                processing_time_ms=self.response_time_ms,
                token_count=len(user_message.split()) * 2  # Rough estimate
            )
    
    # Test different optimization strategies
    strategies = [
        (OptimizationStrategy.SPEED_FIRST, 500),    # Fast model
        (OptimizationStrategy.BALANCED, 1000),      # Medium model
        (OptimizationStrategy.QUALITY_FIRST, 2000)  # Slower model
    ]
    
    test_results = []
    
    for strategy, base_time in strategies:
        print(f"\n🧪 Testing {strategy.value} strategy:")
        
        mock_model = MockModelInterface(base_time)
        system_data = {
            'cpu_percent': 30.0,
            'memory_percent': 50.0,
            'disk_percent': 40.0
        }
        
        # Test multiple requests
        start_time = time.time()
        
        for i in range(3):
            response, metrics = await optimizer.generate_optimized_response(
                model_interface=mock_model,
                user_message=f"テスト質問 {i+1}",
                system_data=system_data,
                strategy=strategy
            )
            
            print(f"   Request {i+1}: {metrics.total_time_ms:.1f}ms (Cache: {'Hit' if metrics.cache_hit else 'Miss'})")
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Test cache performance (should be faster)
        cache_start = time.time()
        response, metrics = await optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message="テスト質問 1",  # Same as first request
            system_data=system_data,
            strategy=strategy
        )
        cache_end = time.time()
        cache_time = (cache_end - cache_start) * 1000
        
        print(f"   Cache test: {cache_time:.1f}ms (Cache: {'Hit' if metrics.cache_hit else 'Miss'})")
        print(f"   Total time: {total_time:.1f}ms")
        
        test_results.append({
            'strategy': strategy.value,
            'total_time_ms': total_time,
            'cache_time_ms': cache_time,
            'cache_hit': metrics.cache_hit,
            'model_calls': mock_model.call_count
        })
    
    # Performance statistics
    stats = optimizer.get_performance_stats()
    
    print(f"\n📊 Performance Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
    
    if 'avg_response_time_ms' in stats:
        print(f"   Average Response Time: {stats['avg_response_time_ms']:.1f}ms")
        print(f"   Under 5s Rate: {stats.get('under_5s_rate', 0):.1f}%")
    
    # Cleanup
    optimizer.cleanup()
    
    # Validate performance requirements
    performance_checks = {
        'cache_working': stats['cache_hit_rate'] > 0,
        'success_rate_high': stats['success_rate'] >= 90,
        'under_5s_target': stats.get('under_5s_rate', 0) >= 80
    }
    
    print(f"\n✅ Performance Validation:")
    for check, passed in performance_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        check_name = check.replace('_', ' ').title()
        print(f"   {status} {check_name}")
    
    return all(performance_checks.values()), test_results


async def test_memory_usage_simulation():
    """Test simulated memory usage patterns"""
    
    print("\n🧠 Testing Memory Usage Simulation")
    print("=" * 50)
    
    import psutil
    
    # Get baseline memory
    process = psutil.Process()
    baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    print(f"📊 Baseline Memory: {baseline_memory:.1f} MB")
    
    # Simulate memory usage patterns
    memory_tests = []
    
    # Test 1: Create multiple optimizers (simulating concurrent users)
    print(f"\n1. Testing Multiple Optimizers:")
    optimizers = []
    
    for i in range(3):
        optimizer = ResponseOptimizer()
        optimizers.append(optimizer)
        
        current_memory = process.memory_info().rss / (1024 * 1024)
        delta = current_memory - baseline_memory
        print(f"   Optimizer {i+1}: {current_memory:.1f} MB (Δ{delta:+.1f} MB)")
    
    peak_memory = process.memory_info().rss / (1024 * 1024)
    peak_delta = peak_memory - baseline_memory
    
    # Cleanup optimizers
    for optimizer in optimizers:
        optimizer.cleanup()
    
    # Force garbage collection
    import gc
    gc.collect()
    
    final_memory = process.memory_info().rss / (1024 * 1024)
    final_delta = final_memory - baseline_memory
    
    print(f"\n📈 Memory Usage Summary:")
    print(f"   Baseline: {baseline_memory:.1f} MB")
    print(f"   Peak: {peak_memory:.1f} MB (Δ{peak_delta:+.1f} MB)")
    print(f"   Final: {final_memory:.1f} MB (Δ{final_delta:+.1f} MB)")
    
    # Memory efficiency checks
    memory_checks = {
        'peak_reasonable': peak_delta < 100,  # Less than 100MB increase
        'cleanup_effective': final_delta < 20,  # Less than 20MB retained
        'no_major_leak': final_delta < peak_delta * 0.5  # Less than 50% of peak retained
    }
    
    print(f"\n✅ Memory Validation:")
    for check, passed in memory_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        check_name = check.replace('_', ' ').title()
        print(f"   {status} {check_name}")
    
    return all(memory_checks.values()), {
        'baseline_mb': baseline_memory,
        'peak_mb': peak_memory,
        'final_mb': final_memory,
        'peak_delta_mb': peak_delta,
        'final_delta_mb': final_delta
    }


async def main():
    """Main test function"""
    
    print("🚀 M1 Optimization and Performance Test Suite")
    print("=" * 60)
    print("Note: This is a simulation test that doesn't require model installation")
    print("=" * 60)
    
    results = []
    
    try:
        # Test 1: M1 optimization detection
        m1_passed, m1_report = await test_m1_optimization_detection()
        results.append(('M1 Optimization Detection', m1_passed))
        
        # Test 2: Response optimizer performance
        perf_passed, perf_results = await test_response_optimizer_performance()
        results.append(('Response Optimizer Performance', perf_passed))
        
        # Test 3: Memory usage simulation
        mem_passed, mem_results = await test_memory_usage_simulation()
        results.append(('Memory Usage Simulation', mem_passed))
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 M1 Optimization Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All M1 optimization tests passed!")
        print("   System is optimized for M1 performance.")
        
        # Show M1 optimization report
        print("\n" + "=" * 60)
        print_optimization_report()
        
    else:
        print("⚠️  Some optimization tests failed.")
        print("   Review the results above for optimization opportunities.")
    
    print("\n💡 Next Steps:")
    print("1. Install llama-cpp-python with Metal support:")
    print("   CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python")
    print("2. Download ELYZA model:")
    print("   ./download_model.sh")
    print("3. Run full performance benchmark:")
    print("   python test_performance_benchmark.py")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)