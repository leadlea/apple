#!/usr/bin/env python3
"""
Performance Benchmark Test Suite for Mac Status PWA
Tests M1 optimization and ensures 5-second response time requirement
"""
import asyncio
import time
import statistics
import json
import logging
import sys
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from elyza_model import ELYZAModelInterface, create_default_config
from m1_optimization import M1Optimizer, get_m1_optimized_config
from response_optimizer import ResponseOptimizer, OptimizationStrategy, ResponsePriority


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test"""
    test_name: str
    success: bool
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    token_count: int
    response_length: int
    error_message: str = None
    optimization_strategy: str = None
    cache_hit: bool = False


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results"""
    timestamp: datetime
    system_info: Dict[str, Any]
    model_config: Dict[str, Any]
    individual_results: List[BenchmarkResult]
    summary_stats: Dict[str, Any]
    requirements_met: Dict[str, bool]
    recommendations: List[str]


class PerformanceBenchmark:
    """Comprehensive performance benchmark for ELYZA model"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimizer = M1Optimizer()
        self.response_optimizer = ResponseOptimizer()
        
        # Test scenarios
        self.test_scenarios = [
            {
                'name': 'Quick Status Check',
                'query': 'システムの状態を教えて',
                'expected_time_ms': 3000,
                'priority': ResponsePriority.HIGH,
                'strategy': OptimizationStrategy.SPEED_FIRST
            },
            {
                'name': 'Detailed Analysis',
                'query': 'CPUとメモリの詳細な分析をお願いします。現在のパフォーマンスについて詳しく説明してください。',
                'expected_time_ms': 5000,
                'priority': ResponsePriority.NORMAL,
                'strategy': OptimizationStrategy.QUALITY_FIRST
            },
            {
                'name': 'Process Information',
                'query': '現在実行中のプロセスで最もリソースを使用しているものを教えて',
                'expected_time_ms': 4000,
                'priority': ResponsePriority.NORMAL,
                'strategy': OptimizationStrategy.BALANCED
            },
            {
                'name': 'Memory Status',
                'query': 'メモリの使用状況はどうですか？',
                'expected_time_ms': 3500,
                'priority': ResponsePriority.HIGH,
                'strategy': OptimizationStrategy.SPEED_FIRST
            },
            {
                'name': 'Disk Analysis',
                'query': 'ディスクの容量と使用率について詳しく教えてください',
                'expected_time_ms': 4500,
                'priority': ResponsePriority.NORMAL,
                'strategy': OptimizationStrategy.BALANCED
            },
            {
                'name': 'Network Status',
                'query': 'ネットワークの状態を確認したい',
                'expected_time_ms': 3000,
                'priority': ResponsePriority.HIGH,
                'strategy': OptimizationStrategy.SPEED_FIRST
            },
            {
                'name': 'Overall Health',
                'query': 'システム全体の健康状態を総合的に評価してください',
                'expected_time_ms': 5000,
                'priority': ResponsePriority.NORMAL,
                'strategy': OptimizationStrategy.QUALITY_FIRST
            },
            {
                'name': 'Urgent Check',
                'query': '緊急：システムに問題はありませんか？',
                'expected_time_ms': 2000,
                'priority': ResponsePriority.URGENT,
                'strategy': OptimizationStrategy.SPEED_FIRST
            }
        ]
    
    def _get_system_data(self) -> Dict[str, Any]:
        """Get mock system data for testing"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used': psutil.virtual_memory().used,
            'memory_total': psutil.virtual_memory().total,
            'disk_percent': psutil.disk_usage('/').percent,
            'disk_used': psutil.disk_usage('/').used,
            'disk_total': psutil.disk_usage('/').total,
            'top_processes': [
                {'name': 'Python', 'cpu_percent': 15.2, 'memory_percent': 5.1},
                {'name': 'Chrome', 'cpu_percent': 12.8, 'memory_percent': 8.3},
                {'name': 'Code', 'cpu_percent': 8.5, 'memory_percent': 4.2}
            ],
            'network_io': {
                'bytes_sent': 1024 * 1024 * 100,  # 100MB
                'bytes_recv': 1024 * 1024 * 500   # 500MB
            }
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        import psutil
        return psutil.cpu_percent(interval=0.1)
    
    async def run_single_benchmark(self, model: ELYZAModelInterface, scenario: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark test"""
        
        self.logger.info(f"Running benchmark: {scenario['name']}")
        
        # Get baseline metrics
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()
        system_data = self._get_system_data()
        
        # Run the test
        start_time = time.time()
        
        try:
            response, metrics = await self.response_optimizer.generate_optimized_response(
                model_interface=model,
                user_message=scenario['query'],
                system_data=system_data,
                priority=scenario['priority'],
                strategy=scenario['strategy']
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Get post-test metrics
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()
            
            # Calculate resource usage
            memory_usage_mb = end_memory - start_memory
            cpu_usage_percent = max(0, end_cpu - start_cpu)
            
            # Extract response info
            token_count = 0
            response_length = 0
            
            if response:
                token_count = getattr(response, 'token_count', 0)
                response_length = len(getattr(response, 'content', ''))
            
            return BenchmarkResult(
                test_name=scenario['name'],
                success=response is not None,
                response_time_ms=response_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                token_count=token_count,
                response_length=response_length,
                optimization_strategy=scenario['strategy'].value,
                cache_hit=metrics.cache_hit if metrics else False
            )
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return BenchmarkResult(
                test_name=scenario['name'],
                success=False,
                response_time_ms=response_time_ms,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                token_count=0,
                response_length=0,
                error_message=str(e),
                optimization_strategy=scenario['strategy'].value
            )
    
    async def run_full_benchmark(self) -> BenchmarkSuite:
        """Run complete benchmark suite"""
        
        print("🚀 Starting Performance Benchmark Suite")
        print("=" * 60)
        
        # Get system information
        system_report = self.optimizer.get_optimization_report()
        
        # Create optimized model configuration
        config, _ = get_m1_optimized_config()
        
        print(f"📱 System: {'M1 Mac' if system_report['system_detection']['is_m1_mac'] else 'Other'}")
        print(f"💾 Memory: {system_report['system_detection']['memory_gb']} GB")
        print(f"⚙️  GPU Layers: {config.n_gpu_layers}")
        print(f"🧵 Threads: {config.n_threads}")
        print(f"📏 Context: {config.n_ctx}")
        print()
        
        # Initialize model
        print("🔧 Initializing ELYZA model...")
        model = ELYZAModelInterface(config)
        
        init_start = time.time()
        init_success = await model.initialize_model()
        init_time = (time.time() - init_start) * 1000
        
        if not init_success:
            print(f"❌ Model initialization failed: {model.initialization_error}")
            return BenchmarkSuite(
                timestamp=datetime.now(),
                system_info=system_report,
                model_config=asdict(config),
                individual_results=[],
                summary_stats={'initialization_failed': True, 'init_time_ms': init_time},
                requirements_met={'model_initialization': False},
                recommendations=['Fix model initialization issues before running benchmarks']
            )
        
        print(f"✅ Model initialized in {init_time:.1f}ms")
        print()
        
        # Run benchmark tests
        results = []
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"🧪 Test {i}/{len(self.test_scenarios)}: {scenario['name']}")
            
            result = await self.run_single_benchmark(model, scenario)
            results.append(result)
            
            # Display result
            status = "✅" if result.success else "❌"
            time_status = "✅" if result.response_time_ms <= 5000 else "⚠️"
            
            print(f"   {status} Success: {result.success}")
            print(f"   {time_status} Time: {result.response_time_ms:.1f}ms")
            print(f"   📝 Tokens: {result.token_count}")
            print(f"   💾 Memory: +{result.memory_usage_mb:.1f}MB")
            
            if result.error_message:
                print(f"   ❌ Error: {result.error_message}")
            
            print()
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Calculate summary statistics
        successful_results = [r for r in results if r.success]
        response_times = [r.response_time_ms for r in successful_results]
        
        summary_stats = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'failed_tests': len(results) - len(successful_results),
            'success_rate': (len(successful_results) / len(results)) * 100 if results else 0,
            'init_time_ms': init_time
        }
        
        if response_times:
            summary_stats.update({
                'avg_response_time_ms': statistics.mean(response_times),
                'median_response_time_ms': statistics.median(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'std_response_time_ms': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'under_5s_count': len([t for t in response_times if t <= 5000]),
                'under_5s_rate': (len([t for t in response_times if t <= 5000]) / len(response_times)) * 100
            })
        
        # Check requirements
        requirements_met = {
            'model_initialization': init_success,
            'response_time_5s': summary_stats.get('under_5s_rate', 0) >= 80,  # 80% of responses under 5s
            'success_rate_90': summary_stats.get('success_rate', 0) >= 90,     # 90% success rate
            'avg_response_under_4s': summary_stats.get('avg_response_time_ms', 6000) <= 4000  # Avg under 4s
        }
        
        # Generate recommendations
        recommendations = []
        
        if not requirements_met['model_initialization']:
            recommendations.append("Fix model initialization - check model file and dependencies")
        
        if not requirements_met['response_time_5s']:
            recommendations.append("Improve response time - consider increasing GPU layers or reducing context size")
        
        if not requirements_met['success_rate_90']:
            recommendations.append("Improve success rate - check error handling and model stability")
        
        if not requirements_met['avg_response_under_4s']:
            recommendations.append("Optimize average response time - tune model parameters for speed")
        
        if not system_report['system_detection']['is_m1_mac']:
            recommendations.append("For best performance, run on Apple Silicon Mac with Metal support")
        
        if not system_report['system_detection']['metal_available']:
            recommendations.append("Enable Metal GPU acceleration for better performance")
        
        # Cleanup
        await model.cleanup()
        self.response_optimizer.cleanup()
        
        return BenchmarkSuite(
            timestamp=datetime.now(),
            system_info=system_report,
            model_config=asdict(config),
            individual_results=results,
            summary_stats=summary_stats,
            requirements_met=requirements_met,
            recommendations=recommendations
        )
    
    def print_benchmark_report(self, suite: BenchmarkSuite):
        """Print detailed benchmark report"""
        
        print("📊 Performance Benchmark Report")
        print("=" * 60)
        print(f"🕐 Timestamp: {suite.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System information
        system = suite.system_info['system_detection']
        print("📱 System Information:")
        print(f"   Platform: {'Apple Silicon' if system['is_m1_mac'] else 'Other'}")
        print(f"   Memory: {system['memory_gb']} GB")
        print(f"   CPU Cores: {system['cpu_cores']} ({system['performance_cores']} P-cores)")
        print(f"   Metal: {'Available' if system['metal_available'] else 'Not available'}")
        print()
        
        # Model configuration
        config = suite.model_config
        print("⚙️  Model Configuration:")
        print(f"   GPU Layers: {config['n_gpu_layers']}")
        print(f"   Threads: {config['n_threads']}")
        print(f"   Context Size: {config['n_ctx']}")
        print(f"   Max Tokens: {config['max_tokens']}")
        print()
        
        # Summary statistics
        stats = suite.summary_stats
        print("📈 Performance Summary:")
        print(f"   Total Tests: {stats.get('total_tests', 0)}")
        print(f"   Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"   Initialization Time: {stats.get('init_time_ms', 0):.1f}ms")
        
        if 'avg_response_time_ms' in stats:
            print(f"   Average Response Time: {stats['avg_response_time_ms']:.1f}ms")
            print(f"   Median Response Time: {stats['median_response_time_ms']:.1f}ms")
            print(f"   Min/Max Response Time: {stats['min_response_time_ms']:.1f}ms / {stats['max_response_time_ms']:.1f}ms")
            print(f"   Under 5s Rate: {stats['under_5s_rate']:.1f}%")
        print()
        
        # Requirements check
        print("✅ Requirements Check:")
        req = suite.requirements_met
        for requirement, met in req.items():
            status = "✅ PASS" if met else "❌ FAIL"
            req_name = requirement.replace('_', ' ').title()
            print(f"   {status} {req_name}")
        print()
        
        # Individual test results
        print("🧪 Individual Test Results:")
        for result in suite.individual_results:
            status = "✅" if result.success else "❌"
            time_status = "🟢" if result.response_time_ms <= 5000 else "🟡" if result.response_time_ms <= 7000 else "🔴"
            
            print(f"   {status} {result.test_name}")
            print(f"      {time_status} Time: {result.response_time_ms:.1f}ms")
            print(f"      📝 Tokens: {result.token_count}, Length: {result.response_length}")
            print(f"      💾 Memory: +{result.memory_usage_mb:.1f}MB")
            print(f"      ⚡ Strategy: {result.optimization_strategy}")
            
            if result.error_message:
                print(f"      ❌ Error: {result.error_message}")
        print()
        
        # Recommendations
        if suite.recommendations:
            print("💡 Recommendations:")
            for i, rec in enumerate(suite.recommendations, 1):
                print(f"   {i}. {rec}")
            print()
        
        # Overall assessment
        all_requirements_met = all(suite.requirements_met.values())
        
        if all_requirements_met:
            print("🎉 OVERALL: All performance requirements met!")
            print("   System is ready for production use.")
        else:
            failed_requirements = [k for k, v in suite.requirements_met.items() if not v]
            print("⚠️  OVERALL: Some performance requirements not met.")
            print(f"   Failed requirements: {', '.join(failed_requirements)}")
            print("   Please address the recommendations above.")
        
        print("=" * 60)
    
    def save_benchmark_results(self, suite: BenchmarkSuite, filename: str = None):
        """Save benchmark results to JSON file"""
        
        if filename is None:
            timestamp = suite.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"benchmark_results_{timestamp}.json"
        
        # Convert dataclasses to dictionaries
        results_dict = {
            'timestamp': suite.timestamp.isoformat(),
            'system_info': suite.system_info,
            'model_config': suite.model_config,
            'individual_results': [asdict(result) for result in suite.individual_results],
            'summary_stats': suite.summary_stats,
            'requirements_met': suite.requirements_met,
            'recommendations': suite.recommendations
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Benchmark results saved to: {filename}")


async def main():
    """Main function to run performance benchmark"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create benchmark instance
    benchmark = PerformanceBenchmark()
    
    try:
        # Run benchmark suite
        results = await benchmark.run_full_benchmark()
        
        # Print report
        benchmark.print_benchmark_report(results)
        
        # Save results
        benchmark.save_benchmark_results(results)
        
        # Return exit code based on requirements
        all_met = all(results.requirements_met.values())
        return 0 if all_met else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Benchmark failed with error: {e}")
        logging.exception("Benchmark error")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)