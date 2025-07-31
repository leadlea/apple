"""
Response Generation and Performance Optimization for Mac Status PWA
Optimizes ELYZA model response generation for 5-second response time requirement
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import queue


class ResponsePriority(Enum):
    """Priority levels for response generation"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class OptimizationStrategy(Enum):
    """Different optimization strategies"""
    SPEED_FIRST = "speed_first"      # Prioritize response time
    QUALITY_FIRST = "quality_first"  # Prioritize response quality
    BALANCED = "balanced"            # Balance speed and quality


@dataclass
class ResponseMetrics:
    """Metrics for response generation performance"""
    request_id: str
    start_time: float
    end_time: float
    total_time_ms: float
    prompt_length: int
    response_length: int
    token_count: int
    optimization_strategy: OptimizationStrategy
    cache_hit: bool = False
    timeout_occurred: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None


@dataclass
class OptimizationConfig:
    """Configuration for response optimization"""
    max_response_time_ms: float = 5000.0  # 5 seconds
    max_prompt_length: int = 2048
    max_response_tokens: int = 512
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    enable_parallel_processing: bool = True
    thread_pool_size: int = 4
    enable_response_streaming: bool = False
    quality_threshold: float = 0.8


class ResponseCache:
    """Simple in-memory cache for responses"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
    
    def _generate_key(self, prompt: str, system_data: Dict[str, Any]) -> str:
        """Generate cache key from prompt and system data"""
        # Create a simplified key based on prompt and key system metrics
        key_data = {
            'prompt_hash': hash(prompt[:200]),  # First 200 chars of prompt
            'cpu': system_data.get('cpu_percent', 0),
            'memory': system_data.get('memory_percent', 0),
            'disk': system_data.get('disk_percent', 0)
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def get(self, prompt: str, system_data: Dict[str, Any]) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, system_data)
        
        with self._lock:
            if key in self.cache:
                response, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    return response
                else:
                    # Remove expired entry
                    del self.cache[key]
        
        return None
    
    def set(self, prompt: str, system_data: Dict[str, Any], response: Any):
        """Cache response"""
        key = self._generate_key(prompt, system_data)
        
        with self._lock:
            self.cache[key] = (response, time.time())
    
    def clear(self):
        """Clear all cached responses"""
        with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            valid_entries = sum(
                1 for _, timestamp in self.cache.values()
                if current_time - timestamp < self.ttl_seconds
            )
            
            return {
                'total_entries': len(self.cache),
                'valid_entries': valid_entries,
                'expired_entries': len(self.cache) - valid_entries,
                'ttl_seconds': self.ttl_seconds
            }


class ResponseOptimizer:
    """
    Optimizes response generation for performance and quality
    Ensures 5-second response time requirement is met
    """
    
    def __init__(self, config: OptimizationConfig = None):
        """
        Initialize response optimizer
        
        Args:
            config: Optimization configuration
        """
        self.config = config or OptimizationConfig()
        self.cache = ResponseCache(self.config.cache_ttl_seconds) if self.config.enable_caching else None
        self.metrics_history: List[ResponseMetrics] = []
        self.logger = logging.getLogger(__name__)
        
        # Thread pool for parallel processing
        if self.config.enable_parallel_processing:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.thread_pool_size)
        else:
            self.thread_pool = None
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.timeout_requests = 0
        self.cache_hits = 0
        
    async def generate_optimized_response(self,
                                        model_interface,
                                        user_message: str,
                                        system_data: Dict[str, Any],
                                        conversation_history: List[Dict[str, str]] = None,
                                        priority: ResponsePriority = ResponsePriority.NORMAL,
                                        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> Tuple[Optional[Any], ResponseMetrics]:
        """
        Generate optimized response with performance monitoring
        
        Args:
            model_interface: ELYZA model interface
            user_message: User's input message
            system_data: Current system status
            conversation_history: Previous conversation
            priority: Request priority level
            strategy: Optimization strategy
            
        Returns:
            Tuple of (response, metrics)
        """
        request_id = f"req_{int(time.time() * 1000)}_{self.total_requests}"
        start_time = time.time()
        
        self.total_requests += 1
        
        # Initialize metrics
        metrics = ResponseMetrics(
            request_id=request_id,
            start_time=start_time,
            end_time=0,
            total_time_ms=0,
            prompt_length=0,
            response_length=0,
            token_count=0,
            optimization_strategy=strategy
        )
        
        try:
            # Check cache first
            if self.cache and strategy != OptimizationStrategy.QUALITY_FIRST:
                cached_response = self.cache.get(user_message, system_data)
                if cached_response:
                    metrics.cache_hit = True
                    metrics.end_time = time.time()
                    metrics.total_time_ms = (metrics.end_time - start_time) * 1000
                    metrics.response_length = len(str(cached_response.content)) if hasattr(cached_response, 'content') else 0
                    
                    self.cache_hits += 1
                    self.successful_requests += 1
                    self.metrics_history.append(metrics)
                    
                    self.logger.info(f"Cache hit for request {request_id} ({metrics.total_time_ms:.1f}ms)")
                    return cached_response, metrics
            
            # Apply optimization strategy
            optimized_params = self._apply_optimization_strategy(strategy, priority)
            
            # Generate response with timeout
            response = await self._generate_with_timeout(
                model_interface,
                user_message,
                system_data,
                conversation_history,
                optimized_params,
                metrics
            )
            
            # Cache successful response
            if response and self.cache and not metrics.error_occurred:
                self.cache.set(user_message, system_data, response)
            
            # Update metrics
            metrics.end_time = time.time()
            metrics.total_time_ms = (metrics.end_time - start_time) * 1000
            
            if response:
                metrics.response_length = len(response.content) if hasattr(response, 'content') else 0
                metrics.token_count = response.token_count if hasattr(response, 'token_count') else 0
                self.successful_requests += 1
            
            self.metrics_history.append(metrics)
            
            # Log performance
            if metrics.total_time_ms > self.config.max_response_time_ms:
                self.logger.warning(f"Response time exceeded limit: {metrics.total_time_ms:.1f}ms > {self.config.max_response_time_ms}ms")
            else:
                self.logger.info(f"Response generated in {metrics.total_time_ms:.1f}ms")
            
            return response, metrics
            
        except Exception as e:
            metrics.error_occurred = True
            metrics.error_message = str(e)
            metrics.end_time = time.time()
            metrics.total_time_ms = (metrics.end_time - start_time) * 1000
            
            self.metrics_history.append(metrics)
            self.logger.error(f"Error generating response for {request_id}: {e}")
            
            return None, metrics
    
    def _apply_optimization_strategy(self, strategy: OptimizationStrategy, priority: ResponsePriority) -> Dict[str, Any]:
        """Apply optimization parameters based on strategy and priority"""
        base_params = {
            'max_tokens': self.config.max_response_tokens,
            'temperature': 0.7,
            'top_p': 0.9,
            'timeout_ms': self.config.max_response_time_ms
        }
        
        if strategy == OptimizationStrategy.SPEED_FIRST:
            # Optimize for speed
            base_params.update({
                'max_tokens': min(256, self.config.max_response_tokens),
                'temperature': 0.5,  # More deterministic
                'top_p': 0.8,
                'timeout_ms': self.config.max_response_time_ms * 0.8  # Stricter timeout
            })
        
        elif strategy == OptimizationStrategy.QUALITY_FIRST:
            # Optimize for quality
            base_params.update({
                'max_tokens': self.config.max_response_tokens,
                'temperature': 0.8,  # More creative
                'top_p': 0.95,
                'timeout_ms': self.config.max_response_time_ms * 1.2  # More lenient timeout
            })
        
        # Adjust based on priority
        if priority == ResponsePriority.URGENT:
            base_params['timeout_ms'] *= 0.7  # Faster response needed
            base_params['max_tokens'] = min(128, base_params['max_tokens'])
        elif priority == ResponsePriority.LOW:
            base_params['timeout_ms'] *= 1.5  # Can take longer
        
        return base_params
    
    async def _generate_with_timeout(self,
                                   model_interface,
                                   user_message: str,
                                   system_data: Dict[str, Any],
                                   conversation_history: List[Dict[str, str]],
                                   params: Dict[str, Any],
                                   metrics: ResponseMetrics) -> Optional[Any]:
        """Generate response with timeout handling"""
        timeout_seconds = params['timeout_ms'] / 1000.0
        
        try:
            # Use direct generation method to avoid recursion
            if hasattr(model_interface, '_generate_direct_response'):
                generation_task = model_interface._generate_direct_response(
                    user_message=user_message,
                    system_data=system_data,
                    conversation_history=conversation_history or []
                )
            else:
                # Fallback to regular method
                generation_task = model_interface.generate_system_response(
                    user_message=user_message,
                    system_data=system_data,
                    conversation_history=conversation_history or []
                )
            
            # Wait for response with timeout
            response = await asyncio.wait_for(generation_task, timeout=timeout_seconds)
            
            return response
            
        except asyncio.TimeoutError:
            metrics.timeout_occurred = True
            self.timeout_requests += 1
            self.logger.warning(f"Response generation timed out after {timeout_seconds:.1f}s")
            return None
        except Exception as e:
            self.logger.error(f"Error in response generation: {e}")
            raise
    
    def optimize_prompt_length(self, prompt: str) -> str:
        """Optimize prompt length for better performance"""
        if len(prompt) <= self.config.max_prompt_length:
            return prompt
        
        # Simple truncation strategy - keep system role and recent context
        lines = prompt.split('\n')
        
        # Keep system role (first few lines)
        system_lines = []
        context_lines = []
        user_query_lines = []
        
        in_context = False
        in_user_query = False
        
        for line in lines:
            if '会話履歴:' in line:
                in_context = True
            elif 'ユーザー:' in line:
                in_user_query = True
                in_context = False
            
            if in_user_query:
                user_query_lines.append(line)
            elif in_context:
                context_lines.append(line)
            else:
                system_lines.append(line)
        
        # Reconstruct with truncated context if needed
        optimized_lines = system_lines[:]
        
        # Add truncated context if it exists
        if context_lines:
            # Keep only recent context
            context_text = '\n'.join(context_lines)
            if len(context_text) > 500:  # Truncate long context
                context_lines = context_lines[-10:]  # Keep last 10 lines
            optimized_lines.extend(context_lines)
        
        # Always keep user query
        optimized_lines.extend(user_query_lines)
        
        optimized_prompt = '\n'.join(optimized_lines)
        
        # Final length check
        if len(optimized_prompt) > self.config.max_prompt_length:
            optimized_prompt = optimized_prompt[:self.config.max_prompt_length - 3] + "..."
        
        return optimized_prompt
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.metrics_history:
            return {
                'total_requests': self.total_requests,
                'no_data': True
            }
        
        # Calculate statistics
        response_times = [m.total_time_ms for m in self.metrics_history if not m.error_occurred]
        successful_times = [m.total_time_ms for m in self.metrics_history if not m.error_occurred and not m.timeout_occurred]
        
        stats = {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'timeout_requests': self.timeout_requests,
            'error_requests': len([m for m in self.metrics_history if m.error_occurred]),
            'cache_hits': self.cache_hits,
            'cache_hit_rate': (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
        }
        
        if response_times:
            stats.update({
                'avg_response_time_ms': sum(response_times) / len(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'median_response_time_ms': sorted(response_times)[len(response_times) // 2],
            })
        
        if successful_times:
            under_5s = len([t for t in successful_times if t <= 5000])
            stats['under_5s_rate'] = (under_5s / len(successful_times) * 100)
        
        # Cache statistics
        if self.cache:
            stats['cache_stats'] = self.cache.get_stats()
        
        return stats
    
    def get_recent_metrics(self, limit: int = 10) -> List[ResponseMetrics]:
        """Get recent response metrics"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def clear_metrics(self):
        """Clear metrics history"""
        self.metrics_history.clear()
        self.total_requests = 0
        self.successful_requests = 0
        self.timeout_requests = 0
        self.cache_hits = 0
    
    def cleanup(self):
        """Cleanup resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        if self.cache:
            self.cache.clear()


# Utility functions for common optimization scenarios
async def generate_fast_response(model_interface, user_message: str, system_data: Dict[str, Any]) -> Tuple[Optional[Any], ResponseMetrics]:
    """Generate response optimized for speed"""
    optimizer = ResponseOptimizer()
    return await optimizer.generate_optimized_response(
        model_interface=model_interface,
        user_message=user_message,
        system_data=system_data,
        priority=ResponsePriority.HIGH,
        strategy=OptimizationStrategy.SPEED_FIRST
    )


async def generate_quality_response(model_interface, user_message: str, system_data: Dict[str, Any], 
                                  conversation_history: List[Dict[str, str]] = None) -> Tuple[Optional[Any], ResponseMetrics]:
    """Generate response optimized for quality"""
    optimizer = ResponseOptimizer()
    return await optimizer.generate_optimized_response(
        model_interface=model_interface,
        user_message=user_message,
        system_data=system_data,
        conversation_history=conversation_history,
        priority=ResponsePriority.NORMAL,
        strategy=OptimizationStrategy.QUALITY_FIRST
    )


async def generate_balanced_response(model_interface, user_message: str, system_data: Dict[str, Any],
                                   conversation_history: List[Dict[str, str]] = None) -> Tuple[Optional[Any], ResponseMetrics]:
    """Generate response with balanced speed and quality"""
    optimizer = ResponseOptimizer()
    return await optimizer.generate_optimized_response(
        model_interface=model_interface,
        user_message=user_message,
        system_data=system_data,
        conversation_history=conversation_history,
        priority=ResponsePriority.NORMAL,
        strategy=OptimizationStrategy.BALANCED
    )


# Performance testing functions
async def test_response_performance():
    """Test response generation performance"""
    print("🚀 Testing Response Generation Performance")
    print("=" * 50)
    
    # Mock model interface for testing
    class MockModelInterface:
        async def generate_system_response(self, user_message, system_data, conversation_history=None):
            # Simulate processing time
            await asyncio.sleep(0.5)  # 500ms simulation
            
            from elyza_model import ModelResponse
            return ModelResponse(
                content=f"Mock response to: {user_message[:50]}...",
                timestamp=datetime.now(),
                processing_time_ms=500.0,
                token_count=25,
                model_info={'model': 'mock'}
            )
    
    mock_model = MockModelInterface()
    optimizer = ResponseOptimizer()
    
    # Test data
    test_system_data = {
        'cpu_percent': 45.0,
        'memory_percent': 60.0,
        'disk_percent': 70.0
    }
    
    test_cases = [
        ("システムの状態を教えて", OptimizationStrategy.SPEED_FIRST),
        ("詳細な分析をお願いします", OptimizationStrategy.QUALITY_FIRST),
        ("現在の状況は？", OptimizationStrategy.BALANCED),
        ("CPUの使用率について", OptimizationStrategy.SPEED_FIRST),
        ("メモリの状況を確認したい", OptimizationStrategy.BALANCED)
    ]
    
    print("Running performance tests...")
    results = []
    
    for i, (query, strategy) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {strategy.value}")
        print(f"   Query: {query}")
        
        response, metrics = await optimizer.generate_optimized_response(
            model_interface=mock_model,
            user_message=query,
            system_data=test_system_data,
            strategy=strategy
        )
        
        results.append(metrics)
        
        print(f"   Time: {metrics.total_time_ms:.1f}ms")
        print(f"   Success: {'✅' if response else '❌'}")
        print(f"   Cache: {'Hit' if metrics.cache_hit else 'Miss'}")
    
    # Test cache performance
    print(f"\n6. Testing cache performance...")
    response, metrics = await optimizer.generate_optimized_response(
        model_interface=mock_model,
        user_message="システムの状態を教えて",  # Same as first query
        system_data=test_system_data,
        strategy=OptimizationStrategy.BALANCED
    )
    
    print(f"   Time: {metrics.total_time_ms:.1f}ms")
    print(f"   Cache: {'Hit ✅' if metrics.cache_hit else 'Miss ❌'}")
    
    # Performance summary
    print(f"\n" + "=" * 50)
    print("📊 Performance Summary")
    print("=" * 50)
    
    stats = optimizer.get_performance_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    print(f"Average response time: {stats.get('avg_response_time_ms', 0):.1f}ms")
    print(f"Under 5s rate: {stats.get('under_5s_rate', 0):.1f}%")
    
    # Cleanup
    optimizer.cleanup()
    
    print("\n✅ Performance testing completed!")
    return results


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run performance tests
    asyncio.run(test_response_performance())