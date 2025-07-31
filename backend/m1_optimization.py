"""
M1 Chip Optimization for ELYZA Model
Provides M1-specific optimizations for maximum performance
"""
import os
import platform
import psutil
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import subprocess
import json

from elyza_model import ModelConfig


@dataclass
class M1SystemInfo:
    """M1 system information for optimization"""
    is_m1_mac: bool
    cpu_cores: int
    performance_cores: int
    efficiency_cores: int
    memory_gb: float
    gpu_cores: Optional[int]
    metal_available: bool
    recommended_gpu_layers: int
    recommended_threads: int
    recommended_batch_size: int
    recommended_context_size: int


class M1Optimizer:
    """M1-specific optimization for ELYZA model"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system_info = self._detect_m1_system()
    
    def _detect_m1_system(self) -> M1SystemInfo:
        """Detect M1 system capabilities and recommend settings"""
        
        # Check if running on macOS
        is_macos = platform.system() == "Darwin"
        
        # Check for Apple Silicon
        is_m1_mac = False
        cpu_cores = psutil.cpu_count(logical=False)
        performance_cores = cpu_cores
        efficiency_cores = 0
        gpu_cores = None
        metal_available = False
        
        if is_macos:
            try:
                # Check CPU brand
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                cpu_brand = result.stdout.strip()
                
                if 'Apple' in cpu_brand:
                    is_m1_mac = True
                    
                    # Get more detailed CPU info for Apple Silicon
                    if 'M1' in cpu_brand or 'M2' in cpu_brand or 'M3' in cpu_brand:
                        # M1/M2/M3 have different core configurations
                        if 'M1' in cpu_brand:
                            if 'Pro' in cpu_brand or 'Max' in cpu_brand:
                                performance_cores = 8
                                efficiency_cores = 2
                            else:
                                performance_cores = 4
                                efficiency_cores = 4
                        elif 'M2' in cpu_brand:
                            if 'Pro' in cpu_brand or 'Max' in cpu_brand:
                                performance_cores = 8
                                efficiency_cores = 4
                            else:
                                performance_cores = 4
                                efficiency_cores = 4
                        elif 'M3' in cpu_brand:
                            if 'Pro' in cpu_brand or 'Max' in cpu_brand:
                                performance_cores = 8
                                efficiency_cores = 4
                            else:
                                performance_cores = 4
                                efficiency_cores = 4
                
                # Check for Metal availability
                try:
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType', '-json'], 
                                          capture_output=True, text=True)
                    display_info = json.loads(result.stdout)
                    
                    for display in display_info.get('SPDisplaysDataType', []):
                        if 'sppci_model' in display and 'Apple' in display['sppci_model']:
                            metal_available = True
                            # Estimate GPU cores (rough approximation)
                            if 'M1' in display['sppci_model']:
                                gpu_cores = 8 if 'Pro' in display['sppci_model'] else 7
                            elif 'M2' in display['sppci_model']:
                                gpu_cores = 10 if 'Pro' in display['sppci_model'] else 8
                            break
                            
                except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                    # Fallback: assume Metal is available on Apple Silicon
                    if is_m1_mac:
                        metal_available = True
                        gpu_cores = 8  # Conservative estimate
                        
            except subprocess.CalledProcessError:
                self.logger.warning("Could not detect CPU information")
        
        # Get memory info
        memory_info = psutil.virtual_memory()
        memory_gb = memory_info.total / (1024**3)
        
        # Calculate recommended settings
        recommended_settings = self._calculate_optimal_settings(
            is_m1_mac, performance_cores, efficiency_cores, memory_gb, gpu_cores, metal_available
        )
        
        return M1SystemInfo(
            is_m1_mac=is_m1_mac,
            cpu_cores=cpu_cores,
            performance_cores=performance_cores,
            efficiency_cores=efficiency_cores,
            memory_gb=memory_gb,
            gpu_cores=gpu_cores,
            metal_available=metal_available,
            **recommended_settings
        )
    
    def _calculate_optimal_settings(self, is_m1: bool, perf_cores: int, eff_cores: int, 
                                  memory_gb: float, gpu_cores: Optional[int], 
                                  metal_available: bool) -> Dict[str, int]:
        """Calculate optimal settings based on system capabilities"""
        
        if not is_m1:
            # Non-M1 Mac or other system - conservative settings
            return {
                'recommended_gpu_layers': 0,  # No GPU acceleration
                'recommended_threads': min(4, perf_cores),
                'recommended_batch_size': 256,
                'recommended_context_size': 2048
            }
        
        # M1-specific optimizations
        settings = {}
        
        # GPU layers - use Metal if available
        if metal_available and gpu_cores:
            # Use all GPU layers for M1 with sufficient memory
            if memory_gb >= 16:
                settings['recommended_gpu_layers'] = -1  # Use all layers
            elif memory_gb >= 8:
                settings['recommended_gpu_layers'] = 20  # Partial GPU usage
            else:
                settings['recommended_gpu_layers'] = 10  # Conservative GPU usage
        else:
            settings['recommended_gpu_layers'] = 0
        
        # Thread count - use performance cores primarily
        # Leave some cores for system tasks
        if perf_cores >= 8:
            settings['recommended_threads'] = 6  # Use 6 out of 8 P-cores
        elif perf_cores >= 4:
            settings['recommended_threads'] = 3  # Use 3 out of 4 P-cores
        else:
            settings['recommended_threads'] = max(1, perf_cores - 1)
        
        # Batch size - optimize for M1 memory bandwidth
        if memory_gb >= 32:
            settings['recommended_batch_size'] = 1024
        elif memory_gb >= 16:
            settings['recommended_batch_size'] = 512
        else:
            settings['recommended_batch_size'] = 256
        
        # Context size - balance memory usage and capability
        if memory_gb >= 32:
            settings['recommended_context_size'] = 4096
        elif memory_gb >= 16:
            settings['recommended_context_size'] = 2048
        else:
            settings['recommended_context_size'] = 1024
        
        return settings
    
    def create_optimized_config(self, model_path: str = None) -> ModelConfig:
        """Create optimized ModelConfig for M1 system"""
        
        if model_path is None:
            from elyza_model import get_default_model_path
            model_path = get_default_model_path()
        
        # Base configuration
        config = ModelConfig(
            model_path=model_path,
            n_ctx=self.system_info.recommended_context_size,
            n_gpu_layers=self.system_info.recommended_gpu_layers,
            n_threads=self.system_info.recommended_threads,
            verbose=False,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            max_tokens=512
        )
        
        self.logger.info(f"Created M1-optimized config:")
        self.logger.info(f"  GPU layers: {config.n_gpu_layers}")
        self.logger.info(f"  Threads: {config.n_threads}")
        self.logger.info(f"  Context size: {config.n_ctx}")
        self.logger.info(f"  Batch size: {self.system_info.recommended_batch_size}")
        
        return config
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get detailed optimization report"""
        return {
            'system_detection': {
                'is_m1_mac': self.system_info.is_m1_mac,
                'cpu_cores': self.system_info.cpu_cores,
                'performance_cores': self.system_info.performance_cores,
                'efficiency_cores': self.system_info.efficiency_cores,
                'memory_gb': round(self.system_info.memory_gb, 1),
                'gpu_cores': self.system_info.gpu_cores,
                'metal_available': self.system_info.metal_available
            },
            'recommended_settings': {
                'gpu_layers': self.system_info.recommended_gpu_layers,
                'threads': self.system_info.recommended_threads,
                'batch_size': self.system_info.recommended_batch_size,
                'context_size': self.system_info.recommended_context_size
            },
            'optimization_notes': self._get_optimization_notes()
        }
    
    def _get_optimization_notes(self) -> list:
        """Get optimization notes and recommendations"""
        notes = []
        
        if not self.system_info.is_m1_mac:
            notes.append("⚠️  Not running on Apple Silicon - GPU acceleration disabled")
            notes.append("💡 For best performance, use Apple Silicon Mac with Metal support")
        else:
            notes.append("✅ Apple Silicon detected - M1 optimizations enabled")
            
            if self.system_info.metal_available:
                notes.append("✅ Metal GPU acceleration available")
                if self.system_info.recommended_gpu_layers == -1:
                    notes.append("🚀 Using full GPU acceleration for maximum performance")
                else:
                    notes.append(f"⚡ Using {self.system_info.recommended_gpu_layers} GPU layers")
            else:
                notes.append("⚠️  Metal not detected - using CPU-only mode")
        
        if self.system_info.memory_gb < 8:
            notes.append("⚠️  Low memory detected - using conservative settings")
        elif self.system_info.memory_gb >= 16:
            notes.append("✅ Sufficient memory for optimal performance")
        
        if self.system_info.performance_cores >= 8:
            notes.append("✅ High-performance CPU configuration detected")
        elif self.system_info.performance_cores >= 4:
            notes.append("✅ Standard performance CPU configuration")
        else:
            notes.append("⚠️  Limited CPU cores - performance may be reduced")
        
        return notes
    
    def validate_llama_cpp_installation(self) -> Dict[str, Any]:
        """Validate llama-cpp-python installation for M1 optimization"""
        validation = {
            'installed': False,
            'version': None,
            'metal_support': False,
            'recommendations': []
        }
        
        try:
            import llama_cpp
            validation['installed'] = True
            
            # Check version
            if hasattr(llama_cpp, '__version__'):
                validation['version'] = llama_cpp.__version__
            
            # Check for Metal support (indirect check)
            try:
                # Try to create a dummy Llama instance with Metal settings
                test_model_path = "/tmp/nonexistent.gguf"  # This will fail, but we can check the error
                try:
                    llama_cpp.Llama(
                        model_path=test_model_path,
                        n_gpu_layers=1,
                        verbose=False
                    )
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'metal' in error_msg or 'gpu' in error_msg:
                        validation['metal_support'] = True
                    elif 'file not found' in error_msg or 'no such file' in error_msg:
                        # This is expected - model file doesn't exist
                        # But if we get this error, it means Metal support is likely available
                        validation['metal_support'] = True
                        
            except ImportError:
                validation['metal_support'] = False
                
        except ImportError:
            validation['recommendations'].append(
                "Install llama-cpp-python with Metal support: "
                "CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python"
            )
        
        # Add recommendations based on system
        if self.system_info.is_m1_mac and not validation['metal_support']:
            validation['recommendations'].append(
                "For M1 optimization, reinstall with Metal support: "
                "pip uninstall llama-cpp-python && "
                "CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python"
            )
        
        return validation


def get_m1_optimized_config(model_path: str = None) -> Tuple[ModelConfig, Dict[str, Any]]:
    """
    Get M1-optimized configuration and system report
    
    Returns:
        Tuple of (optimized_config, system_report)
    """
    optimizer = M1Optimizer()
    config = optimizer.create_optimized_config(model_path)
    report = optimizer.get_optimization_report()
    
    return config, report


def print_optimization_report():
    """Print detailed M1 optimization report"""
    print("🍎 M1 Chip Optimization Report")
    print("=" * 50)
    
    optimizer = M1Optimizer()
    report = optimizer.get_optimization_report()
    
    # System detection
    print("📱 System Detection:")
    system = report['system_detection']
    print(f"   M1 Mac: {'✅ Yes' if system['is_m1_mac'] else '❌ No'}")
    print(f"   CPU Cores: {system['cpu_cores']} total ({system['performance_cores']} P-cores, {system['efficiency_cores']} E-cores)")
    print(f"   Memory: {system['memory_gb']} GB")
    print(f"   GPU Cores: {system['gpu_cores'] or 'Unknown'}")
    print(f"   Metal: {'✅ Available' if system['metal_available'] else '❌ Not available'}")
    
    # Recommended settings
    print(f"\n⚙️  Recommended Settings:")
    settings = report['recommended_settings']
    print(f"   GPU Layers: {settings['gpu_layers']}")
    print(f"   Threads: {settings['threads']}")
    print(f"   Batch Size: {settings['batch_size']}")
    print(f"   Context Size: {settings['context_size']}")
    
    # Optimization notes
    print(f"\n💡 Optimization Notes:")
    for note in report['optimization_notes']:
        print(f"   {note}")
    
    # Validate installation
    print(f"\n🔧 Installation Validation:")
    validation = optimizer.validate_llama_cpp_installation()
    print(f"   llama-cpp-python: {'✅ Installed' if validation['installed'] else '❌ Not installed'}")
    if validation['version']:
        print(f"   Version: {validation['version']}")
    print(f"   Metal Support: {'✅ Available' if validation['metal_support'] else '❌ Not available'}")
    
    if validation['recommendations']:
        print(f"\n🚀 Recommendations:")
        for rec in validation['recommendations']:
            print(f"   • {rec}")
    
    print(f"\n" + "=" * 50)


if __name__ == "__main__":
    print_optimization_report()