"""
Integration tests for performance optimization with ELYZA model
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

from elyza_model import ELYZAModelInterface, ModelConfig, ModelResponse
from response_optimizer import ResponseOptimizer, OptimizationStrategy, ResponsePriority
from prompt_generator import JapanesePromptGenerator, ConversationContext


class TestPerformanceIntegration:
    """Integration tests for performance optimization"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.model_config = ModelConfig(model_path="/test/model.gguf")
        self.model_interface = ELYZAModelInterface(self.model_config)
        self.optimizer = ResponseOptimizer()
        self.prompt_generator = JapanesePromptGenerator()
        
        self.sample_system_data = {
            'timestamp': datetime.now(),
            'cpu_percent': 55.3,
            'memory_percent': 72.1,
            'disk_percent': 68.4,
            'top_processes': [
                {'name': 'Google Chrome', 'cpu_percent': 28.5, 'memory_percent': 15.2}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance(self):
        """Test end-to-end performance from prompt generation to response"""
        # Mock the model interface to simulate response generation
        with patch.object(self.model_interface, '_generate_response') as mock_generate:
            mock_generate.return_value = "システムは正常に動作しています。CPUは55.3%、メモリは72.1%使用中です。"
            
            # Mock initialization
            self.model_interface.is_initialized = True
            self.model_interface.llm = Mock()
            
            start_time = time.time()
            
            # Generate response using the integrated system
            response = await self.model_interface.generate_system_response(
                user_message="システムの状態を教えてください",
                system_data=self.sample_system_data
            )
            
            end_time = time.time()
            total_time_ms = (end_time - start_time) * 1000
            
            # Verify response
            assert response is not None
            assert isinstance(response, ModelResponse)
            assert "システム" in response.content
            assert total_time_ms < 5000  # Under 5 seconds
    
    @pytest.mark.asyncio
    async def test_optimization_strategies_performance(self):
        """Test different optimization strategies"""
        # Mock model interface
        async def mock_generate_response(user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.1)  # Simulate processing time
            return ModelResponse(
                content=f"Response to: {user_message}",
                timestamp=datetime.now(),
                processing_time_ms=100.0,
                token_count=20,
                model_info={'model': 'test'}
            )
        
        mock_model = Mock()
        mock_model.generate_system_response = AsyncMock(side_effect=mock_generate_response)
        mock_model._generate_direct_response = AsyncMock(side_effect=mock_generate_response)
        
        strategies = [
            OptimizationStrategy.SPEED_FIRST,
            OptimizationStrategy.QUALITY_FIRST,
            OptimizationStrategy.BALANCED
        ]
        
        results = {}
        
        for strategy in strategies:
            start_time = time.time()
            
            response, metrics = await self.optimizer.generate_optimized_response(
                model_interface=mock_model,
                user_message="パフォーマンステスト",
                system_data=self.sample_system_data,
                strategy=strategy
            )
            
            end_time = time.time()
            
            results[strategy] = {
                'response': response,
                'metrics': metrics,
                'actual_time': (end_time - start_time) * 1000
            }
            
            assert response is not None
            assert metrics.total_time_ms < 5000
        
        # All strategies should complete successfully
        assert len(results) == 3
        for strategy, result in results.items():
            assert result['response'] is not None
            assert result['metrics'].optimization_strategy == strategy
    
    @pytest.mark.asyncio
    async def test_prompt_optimization_integration(self):
        """Test integration of prompt optimization with response generation"""
        # Create a very long conversation history
        long_history = []
        for i in range(50):
            long_history.extend([
                {"role": "user", "content": f"質問{i}: システムについて詳しく教えてください。"},
                {"role": "assistant", "content": f"回答{i}: システムは正常に動作しています。詳細な情報をお伝えします。"}
            ])
        
        context = ConversationContext(
            conversation_history=long_history,
            preferred_style=self.prompt_generator.templates.keys().__iter__().__next__()
        )
        
        # Generate prompt
        prompt = self.prompt_generator.generate_system_prompt(
            user_query="現在の詳細なシステム分析をお願いします",
            system_data=self.sample_system_data,
            context=context
        )
        
        # Optimize prompt length
        optimized_prompt = self.optimizer.optimize_prompt_length(prompt)
        
        # Verify optimization
        assert len(optimized_prompt) <= self.optimizer.config.max_prompt_length
        assert "現在の詳細なシステム分析をお願いします" in optimized_prompt  # User query preserved
    
    @pytest.mark.asyncio
    async def test_caching_performance_benefit(self):
        """Test that caching provides performance benefits"""
        # Mock model with realistic delay
        async def slow_generate_response(user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.5)  # 500ms delay
            return ModelResponse(
                content=f"Cached response to: {user_message}",
                timestamp=datetime.now(),
                processing_time_ms=500.0,
                token_count=25,
                model_info={'model': 'test'}
            )
        
        mock_model = Mock()
        mock_model.generate_system_response = AsyncMock(side_effect=slow_generate_response)
        mock_model._generate_direct_response = AsyncMock(side_effect=slow_generate_response)
        
        user_message = "キャッシュテスト用のメッセージ"
        
        # First request (cache miss)
        start_time = time.time()
        response1, metrics1 = await self.optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        first_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2, metrics2 = await self.optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message=user_message,
            system_data=self.sample_system_data
        )
        second_time = time.time() - start_time
        
        # Verify caching benefits
        assert response1 is not None
        assert response2 is not None
        assert not metrics1.cache_hit
        assert metrics2.cache_hit
        assert second_time < first_time  # Cache should be significantly faster
        assert metrics2.total_time_ms < 50  # Cache hit should be very fast
    
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self):
        """Test performance under concurrent load"""
        # Mock model
        async def concurrent_generate_response(user_message, system_data, conversation_history=None):
            await asyncio.sleep(0.2)  # 200ms delay
            return ModelResponse(
                content=f"Concurrent response to: {user_message}",
                timestamp=datetime.now(),
                processing_time_ms=200.0,
                token_count=15,
                model_info={'model': 'test'}
            )
        
        mock_model = Mock()
        mock_model.generate_system_response = AsyncMock(side_effect=concurrent_generate_response)
        mock_model._generate_direct_response = AsyncMock(side_effect=concurrent_generate_response)
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = self.optimizer.generate_optimized_response(
                model_interface=mock_model,
                user_message=f"並行テスト {i}",
                system_data=self.sample_system_data
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # Verify all requests completed successfully
        assert len(results) == 5
        for response, metrics in results:
            assert response is not None
            assert metrics.total_time_ms < 5000
            assert not metrics.error_occurred
        
        # Concurrent execution should be faster than sequential
        assert total_time < 1000  # Should complete in under 1 second due to concurrency
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling for slow responses"""
        # Mock very slow model
        async def very_slow_generate_response(user_message, system_data, conversation_history=None):
            await asyncio.sleep(10)  # 10 seconds - should timeout
            return ModelResponse(
                content="This should not be returned",
                timestamp=datetime.now(),
                processing_time_ms=10000.0,
                token_count=10,
                model_info={'model': 'test'}
            )
        
        mock_model = Mock()
        mock_model.generate_system_response = AsyncMock(side_effect=very_slow_generate_response)
        mock_model._generate_direct_response = AsyncMock(side_effect=very_slow_generate_response)
        
        # Configure optimizer with short timeout
        config = self.optimizer.config
        config.max_response_time_ms = 1000.0  # 1 second timeout
        
        start_time = time.time()
        response, metrics = await self.optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message="タイムアウトテスト",
            system_data=self.sample_system_data,
            strategy=OptimizationStrategy.SPEED_FIRST
        )
        end_time = time.time()
        
        actual_time = (end_time - start_time) * 1000
        
        # Should timeout and return None
        assert response is None
        assert metrics.timeout_occurred
        assert actual_time < 2000  # Should timeout quickly
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking"""
        # Add some mock metrics
        for i in range(10):
            from response_optimizer import ResponseMetrics
            metrics = ResponseMetrics(
                request_id=f"test_{i}",
                start_time=time.time(),
                end_time=time.time() + 0.5,
                total_time_ms=500.0 + i * 10,
                prompt_length=100,
                response_length=200,
                token_count=50,
                optimization_strategy=OptimizationStrategy.BALANCED,
                cache_hit=(i % 3 == 0)  # Every 3rd request is cache hit
            )
            self.optimizer.metrics_history.append(metrics)
            if metrics.cache_hit:
                self.optimizer.cache_hits += 1
            self.optimizer.total_requests += 1
            self.optimizer.successful_requests += 1
        
        # Get performance stats
        stats = self.optimizer.get_performance_stats()
        
        # Verify stats
        assert stats['total_requests'] == 10
        assert stats['successful_requests'] == 10
        assert stats['success_rate'] == 100.0
        assert stats['cache_hit_rate'] > 0
        assert 'avg_response_time_ms' in stats
        assert 'under_5s_rate' in stats
        assert stats['under_5s_rate'] == 100.0  # All under 5 seconds
    
    def test_optimization_config_impact(self):
        """Test impact of different optimization configurations"""
        configs = [
            # Speed-optimized config
            {
                'max_response_time_ms': 2000.0,
                'max_response_tokens': 256,
                'enable_caching': True
            },
            # Quality-optimized config
            {
                'max_response_time_ms': 8000.0,
                'max_response_tokens': 1024,
                'enable_caching': False
            },
            # Balanced config
            {
                'max_response_time_ms': 5000.0,
                'max_response_tokens': 512,
                'enable_caching': True
            }
        ]
        
        for config_dict in configs:
            from response_optimizer import OptimizationConfig
            config = OptimizationConfig(**config_dict)
            optimizer = ResponseOptimizer(config)
            
            # Verify configuration applied
            assert optimizer.config.max_response_time_ms == config_dict['max_response_time_ms']
            assert optimizer.config.max_response_tokens == config_dict['max_response_tokens']
            assert optimizer.config.enable_caching == config_dict['enable_caching']
            
            # Verify cache creation based on config
            if config_dict['enable_caching']:
                assert optimizer.cache is not None
            else:
                assert optimizer.cache is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])