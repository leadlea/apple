#!/usr/bin/env python3
"""
Memory Usage Optimization Test for Mac Status PWA
Tests memory efficiency and prevents memory leaks
"""
import asyncio
import time
import psutil
import gc
import sys
import os
from typing import List, Dict, Any
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from elyza_model import ELYZAModelInterface, create_default_config
from m1_optimization import M1Optimizer
from response_optimizer import ResponseOptimizer


class MemoryProfiler:
    """Memory profiling utilities"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = 0
        self.peak_memory = 0
        self.measurements = []
    
    def start_profiling(self):
        """Start memory profiling"""
        gc.collect()  # Force garbage collection
        self.baseline_memory = self.get_memory_usage()
        self.peak_memory = self.baseline_memory
        self.measurements = [self.baseline_memory]
        print(f"📊 Memory profiling started - Baseline: {self.baseline_memory:.1f} MB")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def record_measurement(self, label: str = ""):
        """Record a memory measurement"""
        current_memory = self.get_memory_usage()
        self.measurements.append(current_memory)
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        delta = current_memory - self.baseline_memory
        print(f"💾 {label}: {current_memory:.1f} MB (Δ{delta:+.1f} MB)")
        
        return current_memory
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        if not self.measurements:
            return {}
        
        return {
            'baseline_mb': self.baseline_memory,
            'current_mb': self.get_memory_usage(),
            'peak_mb': self.peak_memory,
            'delta_mb': self.get_memory_usage() - self.baseline_memory,
            'peak_delta_mb': self.peak_memory - self.baseline_memory,
            'avg_mb': sum(self.measurements) / len(self.measurements),
            'measurements_count': len(self.measurements)
        }


async def test_model_memory_usage():
    """Test ELYZA model memory usage patterns"""
    
    print("🧠 Testing ELYZA Model Memory Usage")
    print("=" * 50)
    
    profiler = MemoryProfiler()
    profiler.start_profiling()
    
    # Test 1: Model initialization
    print("\n1. Model Initialization Test")
    config = create_default_config()
    model = ELYZAModelInterface(config)
    
    profiler.record_measurement("After model creation")
    
    # Initialize model
    init_success = await model.initialize_model()
    profiler.record_measurement("After model initialization")
    
    if not init_success:
        print(f"❌ Model initialization failed: {model.initialization_error}")
        return False
    
    # Test 2: Single response generation
    print("\n2. Single Response Generation Test")
    system_data = {
        'cpu_percent': 25.0,
        'memory_percent': 60.0,
        'memory_used': 8 * 1024**3,
        'memory_total': 16 * 1024**3
    }
    
    response = await model.generate_system_response(
        "システムの状態を教えて",
        system_data
    )
    
    profiler.record_measurement("After single response")
    
    # Test 3: Multiple responses (memory leak test)
    print("\n3. Multiple Responses Test (Memory Leak Detection)")
    
    for i in range(5):
        response = await model.generate_system_response(
            f"テスト {i+1}: システムの状態を教えて",
            system_data
        )
        
        if i % 2 == 0:  # Record every other measurement
            profiler.record_measurement(f"After response {i+1}")
        
        # Small delay
        await asyncio.sleep(0.1)
    
    # Force garbage collection
    gc.collect()
    profiler.record_measurement("After garbage collection")
    
    # Test 4: Model cleanup
    print("\n4. Model Cleanup Test")
    await model.cleanup()
    
    # Force garbage collection again
    gc.collect()
    profiler.record_measurement("After model cleanup")
    
    # Memory statistics
    stats = profiler.get_memory_stats()
    
    print(f"\n📈 Memory Usage Summary:")
    print(f"   Baseline: {stats['baseline_mb']:.1f} MB")
    print(f"   Peak: {stats['peak_mb']:.1f} MB")
    print(f"   Final: {stats['current_mb']:.1f} MB")
    print(f"   Peak Delta: {stats['peak_delta_mb']:.1f} MB")
    print(f"   Final Delta: {stats['delta_mb']:.1f} MB")
    
    # Memory leak detection
    memory_leak_threshold = 50  # MB
    potential_leak = stats['delta_mb'] > memory_leak_threshold
    
    if potential_leak:
        print(f"⚠️  Potential memory leak detected (>{memory_leak_threshold} MB retained)")
    else:
        print(f"✅ No significant memory leak detected")
    
    return not potential_leak


async def test_response_optimizer_memory():
    """Test ResponseOptimizer memory usage"""
    
    print("\n🚀 Testing Response Optimizer Memory Usage")
    print("=" * 50)
    
    profiler = MemoryProfiler()
    profiler.start_profiling()
    
    # Create optimizer
    optimizer = ResponseOptimizer()
    profiler.record_measurement("After optimizer creation")
    
    # Mock model for testing
    class MockModel:
        async def generate_system_response(self, user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.1)  # Simulate processing
            from elyza_model import ModelResponse
            from datetime import datetime
            return ModelResponse(
                content=f"Mock response to: {user_message}",
                timestamp=datetime.now(),
                processing_time_ms=100.0,
                token_count=20,
                model_info={'mock': True}
            )
    
    mock_model = MockModel()
    system_data = {'cpu_percent': 30.0, 'memory_percent': 50.0}
    
    # Test cache memory usage
    print("\n1. Cache Memory Usage Test")
    
    # Generate responses to fill cache
    for i in range(10):
        response, metrics = await optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message=f"テスト質問 {i}",
            system_data=system_data
        )
        
        if i % 3 == 0:
            profiler.record_measurement(f"After {i+1} cached responses")
    
    # Test cache hits (should not increase memory significantly)
    print("\n2. Cache Hit Memory Test")
    
    for i in range(5):
        response, metrics = await optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message="テスト質問 0",  # Same as first query - should hit cache
            system_data=system_data
        )
    
    profiler.record_measurement("After cache hit tests")
    
    # Clear cache and test cleanup
    print("\n3. Cache Cleanup Test")
    optimizer.cache.clear()
    gc.collect()
    profiler.record_measurement("After cache clear")
    
    # Cleanup optimizer
    optimizer.cleanup()
    gc.collect()
    profiler.record_measurement("After optimizer cleanup")
    
    # Memory statistics
    stats = profiler.get_memory_stats()
    
    print(f"\n📈 Optimizer Memory Summary:")
    print(f"   Peak Delta: {stats['peak_delta_mb']:.1f} MB")
    print(f"   Final Delta: {stats['delta_mb']:.1f} MB")
    
    # Check for memory efficiency
    efficient_threshold = 100  # MB
    is_efficient = stats['peak_delta_mb'] < efficient_threshold
    
    if is_efficient:
        print(f"✅ Memory usage is efficient (<{efficient_threshold} MB)")
    else:
        print(f"⚠️  High memory usage detected (>{efficient_threshold} MB)")
    
    return is_efficient


async def test_concurrent_memory_usage():
    """Test memory usage under concurrent load"""
    
    print("\n⚡ Testing Concurrent Memory Usage")
    print("=" * 50)
    
    profiler = MemoryProfiler()
    profiler.start_profiling()
    
    # Create multiple optimizers (simulating concurrent users)
    optimizers = []
    for i in range(3):
        optimizer = ResponseOptimizer()
        optimizers.append(optimizer)
    
    profiler.record_measurement("After creating 3 optimizers")
    
    # Mock model
    class MockModel:
        async def generate_system_response(self, user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.05)  # Faster for concurrent test
            from elyza_model import ModelResponse
            from datetime import datetime
            return ModelResponse(
                content=f"Concurrent response: {user_message}",
                timestamp=datetime.now(),
                processing_time_ms=50.0,
                token_count=15,
                model_info={'concurrent': True}
            )
    
    mock_model = MockModel()
    system_data = {'cpu_percent': 40.0, 'memory_percent': 65.0}
    
    # Run concurrent requests
    async def generate_responses(optimizer_id: int, count: int):
        optimizer = optimizers[optimizer_id]
        for i in range(count):
            await optimizer.generate_optimized_response(
                model_interface=mock_model,
                user_message=f"並行テスト {optimizer_id}-{i}",
                system_data=system_data
            )
    
    # Run concurrent tasks
    tasks = [
        generate_responses(0, 5),
        generate_responses(1, 5),
        generate_responses(2, 5)
    ]
    
    await asyncio.gather(*tasks)
    profiler.record_measurement("After concurrent requests")
    
    # Cleanup all optimizers
    for optimizer in optimizers:
        optimizer.cleanup()
    
    gc.collect()
    profiler.record_measurement("After concurrent cleanup")
    
    # Memory statistics
    stats = profiler.get_memory_stats()
    
    print(f"\n📈 Concurrent Memory Summary:")
    print(f"   Peak Delta: {stats['peak_delta_mb']:.1f} MB")
    print(f"   Final Delta: {stats['delta_mb']:.1f} MB")
    
    # Check concurrent efficiency
    concurrent_threshold = 150  # MB for 3 concurrent optimizers
    is_efficient = stats['peak_delta_mb'] < concurrent_threshold
    
    if is_efficient:
        print(f"✅ Concurrent memory usage is efficient (<{concurrent_threshold} MB)")
    else:
        print(f"⚠️  High concurrent memory usage (>{concurrent_threshold} MB)")
    
    return is_efficient


async def main():
    """Main memory optimization test"""
    
    print("🧠 Memory Optimization Test Suite")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    results = []
    
    try:
        # Test 1: Model memory usage
        print("Running model memory test...")
        model_result = await test_model_memory_usage()
        results.append(('Model Memory Usage', model_result))
        
        # Test 2: Response optimizer memory
        print("\nRunning optimizer memory test...")
        optimizer_result = await test_response_optimizer_memory()
        results.append(('Response Optimizer Memory', optimizer_result))
        
        # Test 3: Concurrent memory usage
        print("\nRunning concurrent memory test...")
        concurrent_result = await test_concurrent_memory_usage()
        results.append(('Concurrent Memory Usage', concurrent_result))
        
    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Memory Optimization Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All memory optimization tests passed!")
        print("   System memory usage is within acceptable limits.")
    else:
        print("⚠️  Some memory optimization tests failed.")
        print("   Consider optimizing memory usage before production.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)