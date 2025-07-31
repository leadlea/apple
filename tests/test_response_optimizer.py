"""
Unit tests for ResponseOptimizer class
"""
import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from response_optimizer import (
    ResponseOptimizer,
    ResponseCache,
    ResponseMetrics,
    OptimizationConfig,
    ResponsePriority,
    OptimizationStrategy,
    generate_fast_response,
    generate_quality_response,
    generate_balanced_response
)


class MockModelInterface:
    """Mock model interface for testing"""
    
    def __init__(self, response_delay: float = 0.1, should_fail: bool = False):
        self.response_delay = response_delay
        self.should_fail = should_fail
        self.call_count = 0
    
    async def generate_system_response(self, user_message, system_data, conversation_history=None):
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mock model failure")
        
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        
        # Import here to avoid circular imports
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from elyza_model import ModelResponse
        
        return ModelResponse(
            content=f"Mock response to: {user_message}",
            timestamp=datetime.now(),
            processing_time_ms=self.response_delay * 1000,
            token_count=len(user_message.split()),
            model_info={'model': 'mock'}
        )


class TestResponseCache:
    """Test cases for ResponseCache class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.cache = ResponseCache(ttl_seconds=60)
    
    def test_cache_init(self):
        """Test cache initialization"""
        assert self.cache.ttl_seconds == 60
        assert len(self.cache.cache) == 0
    
    def test_cache_set_get(self):
        """Test basic cache set and get operations"""
        prompt = "Test prompt"
        system_data = {'cpu_percent': 50.0}
        response = "Test response"
        
        # Set cache
        self.cache.set(prompt, system_data, response)
        
        # Get from cache
        cached_response = self.cache.get(prompt, system_data)
        assert cached_response == response
    
    def test_cache_miss(self):
        """Test cache miss scenarios"""
        prompt = "Test prompt"
        system_data = {'cpu_percent': 50.0}
        
        # Cache miss - no entry
        cached_response = self.cache.get(prompt, system_data)
        assert cached_response is None
        
        # Cache miss - different system data
        self.cache.set(prompt, system_data, "response")
        different_data = {'cpu_percent': 60.0}
        cached_response = self.cache.get(prompt, different_data)
        assert cached_response is None
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = ResponseCache(ttl_seconds=0.1)  # Very short TTL
        
        prompt = "Test prompt"
        system_data = {'cpu_percent': 50.0}
        response = "Test response"
        
        # Set cache
        cache.set(prompt, system_data, response)
        
        # Should get response immediately
        cached_response = cache.get(prompt, system_data)
        assert cached_response == response
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired now
        cached_response = cache.get(prompt, system_data)
        assert cached_response is None
    
    def test_cache_clear(self):
        """Test cache clearing"""
        prompt = "Test prompt"
        system_data = {'cpu_percent': 50.0}
        response = "Test response"
        
        self.cache.set(prompt, system_data, response)
        assert self.cache.get(prompt, system_data) == response
        
        self.cache.clear()
        assert self.cache.get(prompt, system_data) is None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        stats = self.cache.get_stats()
        assert 'total_entries' in stats
        assert 'valid_entries' in stats
        assert 'expired_entries' in stats
        assert stats['total_entries'] == 0
        
        # Add some entries
        self.cache.set("prompt1", {'cpu_percent': 50.0}, "response1")
        self.cache.set("prompt2", {'cpu_percent': 60.0}, "response2")
        
        stats = self.cache.get_stats()
        assert stats['total_entries'] == 2
        assert stats['valid_entries'] == 2


class TestOptimizationConfig:
    """Test cases for OptimizationConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = OptimizationConfig()
        
        assert config.max_response_time_ms == 5000.0
        assert config.max_prompt_length == 2048
        assert config.max_response_tokens == 512
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 300
        assert config.enable_parallel_processing is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = OptimizationConfig(
            max_response_time_ms=3000.0,
            max_prompt_length=1024,
            enable_caching=False
        )
        
        assert config.max_response_time_ms == 3000.0
        assert config.max_prompt_length == 1024
        assert config.enable_caching is False


class TestResponseOptimizer:
    """Test cases for ResponseOptimizer class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = OptimizationConfig(max_response_time_ms=2000.0)
        self.optimizer = ResponseOptimizer(self.config)
        self.mock_model = MockModelInterface(response_delay=0.1)
        self.sample_system_data = {
            'cpu_percent': 45.0,
            'memory_percent': 60.0,
            'disk_percent': 70.0
        }
    
    def test_optimizer_init(self):
        """Test optimizer initialization"""
        assert self.optimizer.config.max_response_time_ms == 2000.0
        assert self.optimizer.cache is not None
        assert self.optimizer.total_requests == 0
    
    def test_optimizer_init_no_cache(self):
        """Test optimizer initialization without cache"""
        config = OptimizationConfig(enable_caching=False)
        optimizer = ResponseOptimizer(config)
        assert optimizer.cache is None
    
    @pytest.mark.asyncio
    async def test_generate_optimized_response_success(self):
        """Test successful response generation"""
        response, metrics = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message="Test message",
            system_data=self.sample_system_data
        )
        
        assert response is not None
        assert response.content == "Mock response to: Test message"
        assert metrics.total_time_ms > 0
        assert metrics.total_time_ms < 2000  # Should be under limit
        assert not metrics.error_occurred
        assert not metrics.timeout_occurred
        assert metrics.optimization_strategy == OptimizationStrategy.BALANCED
    
    @pytest.mark.asyncio
    async def test_generate_optimized_response_with_cache(self):
        """Test response generation with caching"""
        user_message = "Cached test message"
        
        # First request - should miss cache
        response1, metrics1 = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        
        assert response1 is not None
        assert not metrics1.cache_hit
        assert self.mock_model.call_count == 1
        
        # Second request - should hit cache
        response2, metrics2 = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        
        assert response2 is not None
        assert metrics2.cache_hit
        assert self.mock_model.call_count == 1  # No additional call
        assert metrics2.total_time_ms < metrics1.total_time_ms  # Faster due to cache
    
    @pytest.mark.asyncio
    async def test_generate_optimized_response_timeout(self):
        """Test response generation with timeout"""
        # Create slow mock model
        slow_model = MockModelInterface(response_delay=3.0)  # 3 seconds
        
        response, metrics = await self.optimizer.generate_optimized_response(
            model_interface=slow_model,
            user_message="Slow test message",
            system_data=self.sample_system_data,
            strategy=OptimizationStrategy.SPEED_FIRST  # Stricter timeout
        )
        
        assert response is None
        assert metrics.timeout_occurred
        assert metrics.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_optimized_response_error(self):
        """Test response generation with model error"""
        error_model = MockModelInterface(should_fail=True)
        
        response, metrics = await self.optimizer.generate_optimized_response(
            model_interface=error_model,
            user_message="Error test message",
            system_data=self.sample_system_data
        )
        
        assert response is None
        assert metrics.error_occurred
        assert metrics.error_message is not None
    
    def test_apply_optimization_strategy(self):
        """Test optimization strategy application"""
        # Speed first strategy
        speed_params = self.optimizer._apply_optimization_strategy(
            OptimizationStrategy.SPEED_FIRST, 
            ResponsePriority.NORMAL
        )
        assert speed_params['max_tokens'] <= 256
        assert speed_params['temperature'] == 0.5
        
        # Quality first strategy
        quality_params = self.optimizer._apply_optimization_strategy(
            OptimizationStrategy.QUALITY_FIRST,
            ResponsePriority.NORMAL
        )
        assert quality_params['temperature'] == 0.8
        assert quality_params['top_p'] == 0.95
        
        # Urgent priority
        urgent_params = self.optimizer._apply_optimization_strategy(
            OptimizationStrategy.BALANCED,
            ResponsePriority.URGENT
        )
        assert urgent_params['max_tokens'] <= 128
    
    def test_optimize_prompt_length(self):
        """Test prompt length optimization"""
        # Short prompt - should remain unchanged
        short_prompt = "Short prompt"
        optimized = self.optimizer.optimize_prompt_length(short_prompt)
        assert optimized == short_prompt
        
        # Long prompt - should be truncated
        long_prompt = "A" * 3000  # Longer than max_prompt_length
        optimized = self.optimizer.optimize_prompt_length(long_prompt)
        assert len(optimized) <= self.config.max_prompt_length
        
        # Structured prompt - should preserve structure
        structured_prompt = """System role here
        
現在のシステム状態:
CPU: 50%
Memory: 60%

会話履歴:
ユーザー: 前の質問
アシスタント: 前の回答

ユーザー: 現在の質問
アシスタント: """
        
        optimized = self.optimizer.optimize_prompt_length(structured_prompt)
        assert "ユーザー: 現在の質問" in optimized  # Should preserve user query
    
    @pytest.mark.asyncio
    async def test_performance_stats(self):
        """Test performance statistics"""
        # Generate some responses
        for i in range(3):
            await self.optimizer.generate_optimized_response(
                model_interface=self.mock_model,
                user_message=f"Test message {i}",
                system_data=self.sample_system_data
            )
        
        stats = self.optimizer.get_performance_stats()
        
        assert stats['total_requests'] == 3
        assert stats['successful_requests'] == 3
        assert stats['success_rate'] == 100.0
        assert 'avg_response_time_ms' in stats
        assert 'under_5s_rate' in stats
    
    def test_get_recent_metrics(self):
        """Test getting recent metrics"""
        # Initially no metrics
        recent = self.optimizer.get_recent_metrics(5)
        assert len(recent) == 0
        
        # Add some mock metrics
        for i in range(10):
            metrics = ResponseMetrics(
                request_id=f"test_{i}",
                start_time=time.time(),
                end_time=time.time(),
                total_time_ms=100.0,
                prompt_length=50,
                response_length=100,
                token_count=20,
                optimization_strategy=OptimizationStrategy.BALANCED
            )
            self.optimizer.metrics_history.append(metrics)
        
        # Get recent metrics
        recent = self.optimizer.get_recent_metrics(5)
        assert len(recent) == 5
        assert recent[-1].request_id == "test_9"  # Most recent
    
    def test_clear_metrics(self):
        """Test clearing metrics"""
        # Add some metrics
        self.optimizer.total_requests = 5
        self.optimizer.successful_requests = 4
        self.optimizer.metrics_history = [Mock() for _ in range(5)]
        
        # Clear metrics
        self.optimizer.clear_metrics()
        
        assert self.optimizer.total_requests == 0
        assert self.optimizer.successful_requests == 0
        assert len(self.optimizer.metrics_history) == 0
    
    def test_cleanup(self):
        """Test cleanup"""
        # Should not raise exception
        self.optimizer.cleanup()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_model = MockModelInterface(response_delay=0.1)
        self.sample_system_data = {
            'cpu_percent': 45.0,
            'memory_percent': 60.0
        }
    
    @pytest.mark.asyncio
    async def test_generate_fast_response(self):
        """Test fast response generation utility"""
        response, metrics = await generate_fast_response(
            model_interface=self.mock_model,
            user_message="Fast test",
            system_data=self.sample_system_data
        )
        
        assert response is not None
        assert metrics.optimization_strategy == OptimizationStrategy.SPEED_FIRST
        assert metrics.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_quality_response(self):
        """Test quality response generation utility"""
        response, metrics = await generate_quality_response(
            model_interface=self.mock_model,
            user_message="Quality test",
            system_data=self.sample_system_data
        )
        
        assert response is not None
        assert metrics.optimization_strategy == OptimizationStrategy.QUALITY_FIRST
        assert metrics.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_balanced_response(self):
        """Test balanced response generation utility"""
        response, metrics = await generate_balanced_response(
            model_interface=self.mock_model,
            user_message="Balanced test",
            system_data=self.sample_system_data
        )
        
        assert response is not None
        assert metrics.optimization_strategy == OptimizationStrategy.BALANCED
        assert metrics.total_time_ms > 0


class TestPerformanceRequirements:
    """Test performance requirements compliance"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.optimizer = ResponseOptimizer()
        self.mock_model = MockModelInterface(response_delay=0.5)  # 500ms
        self.sample_system_data = {'cpu_percent': 50.0}
    
    @pytest.mark.asyncio
    async def test_5_second_requirement(self):
        """Test that responses are generated within 5 seconds"""
        start_time = time.time()
        
        response, metrics = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message="Performance test",
            system_data=self.sample_system_data
        )
        
        end_time = time.time()
        actual_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert response is not None
        assert actual_time < 5000  # Under 5 seconds
        assert metrics.total_time_ms < 5000
        assert not metrics.timeout_occurred
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        tasks = []
        
        # Create 5 concurrent requests
        for i in range(5):
            task = self.optimizer.generate_optimized_response(
                model_interface=self.mock_model,
                user_message=f"Concurrent test {i}",
                system_data=self.sample_system_data
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for response, metrics in results:
            assert response is not None
            assert metrics.total_time_ms < 5000
            assert not metrics.error_occurred
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self):
        """Test that caching improves performance"""
        user_message = "Cache performance test"
        
        # First request (cache miss)
        start_time = time.time()
        response1, metrics1 = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        first_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2, metrics2 = await self.optimizer.generate_optimized_response(
            model_interface=self.mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        second_time = time.time() - start_time
        
        assert response1 is not None
        assert response2 is not None
        assert not metrics1.cache_hit
        assert metrics2.cache_hit
        assert second_time < first_time  # Cache should be faster
        assert metrics2.total_time_ms < metrics1.total_time_ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])