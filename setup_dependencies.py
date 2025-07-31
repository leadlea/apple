#!/usr/bin/env python3
"""
Setup script for Mac Status PWA dependencies
Installs and configures required packages for M1 optimization
"""
import subprocess
import sys
import os
import platform
from typing import List, Dict, Any


def run_command(command: List[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(command)}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version() -> bool:
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False


def check_system_compatibility() -> Dict[str, Any]:
    """Check system compatibility for M1 optimizations"""
    system_info = {
        'platform': platform.system(),
        'machine': platform.machine(),
        'is_macos': platform.system() == 'Darwin',
        'is_apple_silicon': False,
        'has_metal': False
    }
    
    print(f"💻 System: {system_info['platform']} {system_info['machine']}")
    
    if system_info['is_macos']:
        # Check for Apple Silicon
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            cpu_brand = result.stdout.strip()
            
            if 'Apple' in cpu_brand:
                system_info['is_apple_silicon'] = True
                print(f"✅ Apple Silicon detected: {cpu_brand}")
                
                # Check for Metal
                try:
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                          capture_output=True, text=True)
                    if 'Metal' in result.stdout or 'Apple' in result.stdout:
                        system_info['has_metal'] = True
                        print("✅ Metal GPU support available")
                    else:
                        print("⚠️  Metal GPU support not detected")
                except subprocess.CalledProcessError:
                    print("⚠️  Could not check Metal support")
            else:
                print(f"ℹ️  Intel Mac detected: {cpu_brand}")
        except subprocess.CalledProcessError:
            print("⚠️  Could not detect CPU type")
    else:
        print("ℹ️  Non-macOS system - M1 optimizations not available")
    
    return system_info


def install_basic_requirements() -> bool:
    """Install basic Python requirements"""
    requirements = [
        'fastapi',
        'uvicorn',
        'websockets',
        'psutil',
        'asyncio',
        'dataclasses',
        'typing-extensions'
    ]
    
    print("📦 Installing basic requirements...")
    
    for package in requirements:
        success = run_command(
            [sys.executable, '-m', 'pip', 'install', package],
            f"Installing {package}"
        )
        if not success:
            return False
    
    return True


def install_llama_cpp_python(system_info: Dict[str, Any]) -> bool:
    """Install llama-cpp-python with appropriate optimizations"""
    
    if system_info['is_apple_silicon'] and system_info['has_metal']:
        print("🚀 Installing llama-cpp-python with Metal support for M1...")
        
        # Set environment variables for Metal support
        env = os.environ.copy()
        env['CMAKE_ARGS'] = '-DLLAMA_METAL=on'
        
        try:
            # Uninstall existing version first
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'llama-cpp-python', '-y'],
                         capture_output=True)
            
            # Install with Metal support
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                'llama-cpp-python', '--upgrade', '--force-reinstall', '--no-cache-dir'
            ], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ llama-cpp-python with Metal support installed")
                return True
            else:
                print(f"❌ Metal installation failed: {result.stderr}")
                print("🔄 Falling back to CPU-only installation...")
                
        except Exception as e:
            print(f"❌ Metal installation error: {e}")
            print("🔄 Falling back to CPU-only installation...")
    
    # Fallback to CPU-only installation
    print("📦 Installing llama-cpp-python (CPU-only)...")
    return run_command(
        [sys.executable, '-m', 'pip', 'install', 'llama-cpp-python'],
        "Installing llama-cpp-python"
    )


def verify_installation() -> bool:
    """Verify that all components are installed correctly"""
    print("\n🔍 Verifying installation...")
    
    # Test basic imports
    test_imports = [
        ('fastapi', 'FastAPI'),
        ('psutil', 'System monitoring'),
        ('llama_cpp', 'LLAMA CPP Python')
    ]
    
    all_good = True
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description} import successful")
        except ImportError as e:
            print(f"❌ {description} import failed: {e}")
            all_good = False
    
    # Test llama-cpp-python Metal support
    if all_good:
        try:
            from llama_cpp import Llama
            
            # Try to create a dummy instance with GPU layers
            # This will fail due to missing model, but we can check the error
            try:
                Llama(model_path="/nonexistent", n_gpu_layers=1, verbose=False)
            except Exception as e:
                error_msg = str(e).lower()
                if 'metal' in error_msg or 'gpu' in error_msg or 'file not found' in error_msg:
                    print("✅ llama-cpp-python Metal support appears to be working")
                else:
                    print("⚠️  llama-cpp-python Metal support may not be available")
                    print(f"   Error: {e}")
                    
        except ImportError:
            print("❌ llama-cpp-python verification failed")
            all_good = False
    
    return all_good


def create_model_directory():
    """Create model directory structure"""
    model_dir = os.path.join("models", "elyza7b")
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        print(f"📁 Created model directory: {model_dir}")
        
        # Create README with download instructions
        readme_content = """# ELYZA Model Directory

This directory should contain the ELYZA-japanese-Llama-2-7b model file.

## Download Instructions

1. Download the model file from Hugging Face:
   https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf

2. Download the Q4_0 quantized version:
   ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf

3. Place the file in this directory

## Alternative: Use download script

Run the download script from the project root:
```bash
./download_model.sh
```

## File Size
The model file is approximately 4.1 GB.
"""
        
        readme_path = os.path.join(model_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"📝 Created README: {readme_path}")
    else:
        print(f"✅ Model directory already exists: {model_dir}")


def main():
    """Main setup function"""
    print("🚀 Mac Status PWA Dependency Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return 1
    
    # Check system compatibility
    print("\n🔍 Checking system compatibility...")
    system_info = check_system_compatibility()
    
    # Install basic requirements
    print("\n📦 Installing basic requirements...")
    if not install_basic_requirements():
        print("\n❌ Setup failed: Could not install basic requirements")
        return 1
    
    # Install llama-cpp-python
    print("\n🦙 Installing llama-cpp-python...")
    if not install_llama_cpp_python(system_info):
        print("\n❌ Setup failed: Could not install llama-cpp-python")
        return 1
    
    # Create model directory
    print("\n📁 Setting up model directory...")
    create_model_directory()
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Setup completed with warnings")
        print("Some components may not work correctly.")
        return 1
    
    # Success summary
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("1. Download the ELYZA model:")
    print("   ./download_model.sh")
    print("   (or manually download to models/elyza7b/)")
    
    print("\n2. Run performance benchmark:")
    print("   python test_performance_benchmark.py")
    
    print("\n3. Test memory optimization:")
    print("   python test_memory_optimization.py")
    
    if system_info['is_apple_silicon']:
        print("\n🍎 M1 Optimizations:")
        print("✅ Your system supports M1 optimizations")
        if system_info['has_metal']:
            print("✅ Metal GPU acceleration should be available")
        else:
            print("⚠️  Metal GPU acceleration may not be available")
    else:
        print("\n💻 Non-M1 System:")
        print("ℹ️  M1-specific optimizations will be disabled")
        print("ℹ️  CPU-only mode will be used")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)