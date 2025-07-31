#!/usr/bin/env python3
"""
Model setup and validation utilities for ELYZA integration
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add backend to path for imports
sys.path.append(os.path.dirname(__file__))

from elyza_model import (
    ELYZAModelInterface,
    ModelConfig,
    create_default_config,
    get_default_model_path
)


def check_model_file() -> Dict[str, Any]:
    """
    Check if ELYZA model file exists and get file information
    
    Returns:
        Dictionary with model file status information
    """
    model_path = get_default_model_path()
    
    result = {
        'model_path': model_path,
        'exists': False,
        'size_mb': 0,
        'readable': False,
        'error': None
    }
    
    try:
        if os.path.exists(model_path):
            result['exists'] = True
            
            # Get file size
            file_size = os.path.getsize(model_path)
            result['size_mb'] = round(file_size / (1024 * 1024), 1)
            
            # Check if readable
            result['readable'] = os.access(model_path, os.R_OK)
            
        else:
            result['error'] = f"Model file not found at {model_path}"
            
    except Exception as e:
        result['error'] = f"Error checking model file: {str(e)}"
    
    return result


def check_llama_cpp_installation() -> Dict[str, Any]:
    """
    Check if llama-cpp-python is properly installed
    
    Returns:
        Dictionary with installation status
    """
    result = {
        'installed': False,
        'version': None,
        'error': None
    }
    
    try:
        import llama_cpp
        result['installed'] = True
        
        # Try to get version
        if hasattr(llama_cpp, '__version__'):
            result['version'] = llama_cpp.__version__
        else:
            result['version'] = 'unknown'
            
    except ImportError as e:
        result['error'] = f"llama-cpp-python not installed: {str(e)}"
    except Exception as e:
        result['error'] = f"Error checking llama-cpp-python: {str(e)}"
    
    return result


async def test_model_initialization() -> Dict[str, Any]:
    """
    Test ELYZA model initialization
    
    Returns:
        Dictionary with initialization test results
    """
    result = {
        'success': False,
        'error': None,
        'model_status': None,
        'initialization_time_ms': 0
    }
    
    try:
        # Create model interface
        config = create_default_config()
        model = ELYZAModelInterface(config)
        
        # Test initialization
        import time
        start_time = time.time()
        
        success = await model.initialize_model()
        
        end_time = time.time()
        result['initialization_time_ms'] = round((end_time - start_time) * 1000, 1)
        
        result['success'] = success
        result['model_status'] = model.get_model_status()
        
        if not success:
            result['error'] = model.initialization_error
        
        # Cleanup
        await model.cleanup()
        
    except Exception as e:
        result['error'] = f"Initialization test failed: {str(e)}"
    
    return result


async def run_system_diagnostics() -> Dict[str, Any]:
    """
    Run comprehensive system diagnostics for ELYZA model setup
    
    Returns:
        Dictionary with all diagnostic results
    """
    print("🔍 Running ELYZA Model System Diagnostics")
    print("=" * 50)
    
    diagnostics = {
        'timestamp': asyncio.get_event_loop().time(),
        'model_file': None,
        'llama_cpp': None,
        'initialization': None,
        'recommendations': []
    }
    
    # Check model file
    print("1. Checking model file...")
    diagnostics['model_file'] = check_model_file()
    
    if diagnostics['model_file']['exists']:
        print(f"   ✅ Model file found ({diagnostics['model_file']['size_mb']} MB)")
    else:
        print(f"   ❌ {diagnostics['model_file']['error']}")
        diagnostics['recommendations'].append(
            "Download ELYZA model file to models/elyza7b/ directory"
        )
    
    # Check llama-cpp-python
    print("2. Checking llama-cpp-python installation...")
    diagnostics['llama_cpp'] = check_llama_cpp_installation()
    
    if diagnostics['llama_cpp']['installed']:
        version = diagnostics['llama_cpp']['version']
        print(f"   ✅ llama-cpp-python installed (version: {version})")
    else:
        print(f"   ❌ {diagnostics['llama_cpp']['error']}")
        diagnostics['recommendations'].append(
            "Install llama-cpp-python: pip install llama-cpp-python"
        )
    
    # Test model initialization
    print("3. Testing model initialization...")
    diagnostics['initialization'] = await test_model_initialization()
    
    if diagnostics['initialization']['success']:
        time_ms = diagnostics['initialization']['initialization_time_ms']
        print(f"   ✅ Model initialization successful ({time_ms} ms)")
    else:
        error = diagnostics['initialization']['error']
        print(f"   ❌ Model initialization failed: {error}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary")
    print("=" * 50)
    
    all_checks = [
        diagnostics['model_file']['exists'],
        diagnostics['llama_cpp']['installed'],
        diagnostics['initialization']['success']
    ]
    
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    print(f"Checks passed: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("🎉 All systems ready! ELYZA model is fully operational.")
    else:
        print("⚠️  Some issues found. See recommendations below:")
        for i, rec in enumerate(diagnostics['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    return diagnostics


def create_model_download_script():
    """Create a script to download the ELYZA model"""
    script_content = '''#!/bin/bash
# ELYZA Model Download Script

echo "🚀 Downloading ELYZA-japanese-Llama-2-7b model..."
echo "This may take several minutes (file size: ~4.1GB)"

# Create directory if it doesn't exist
mkdir -p models/elyza7b

# Download the model file
cd models/elyza7b

# Option 1: Using wget
if command -v wget &> /dev/null; then
    echo "Using wget to download..."
    wget -O ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf \\
        "https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"

# Option 2: Using curl
elif command -v curl &> /dev/null; then
    echo "Using curl to download..."
    curl -L -o ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf \\
        "https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf/resolve/main/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"

else
    echo "❌ Neither wget nor curl found. Please install one of them."
    echo "   macOS: brew install wget"
    echo "   Or download manually from:"
    echo "   https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf"
    exit 1
fi

# Verify download
if [ -f "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf" ]; then
    file_size=$(du -h ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf | cut -f1)
    echo "✅ Download completed! File size: $file_size"
    echo "🎉 ELYZA model is ready to use!"
else
    echo "❌ Download failed. Please try again or download manually."
    exit 1
fi
'''
    
    script_path = "download_model.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    print(f"📝 Created model download script: {script_path}")
    print("   Run with: ./download_model.sh")


async def main():
    """Main function for model setup diagnostics"""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run diagnostics
    results = await run_system_diagnostics()
    
    # Create download script if model is missing
    if not results['model_file']['exists']:
        print("\n📝 Creating model download script...")
        create_model_download_script()
    
    # Show next steps
    print("\n🚀 Next Steps:")
    if not results['llama_cpp']['installed']:
        print("   1. Install llama-cpp-python:")
        print("      pip install llama-cpp-python")
    
    if not results['model_file']['exists']:
        print("   2. Download ELYZA model:")
        print("      ./download_model.sh")
        print("      (or follow instructions in models/elyza7b/README.md)")
    
    if results['llama_cpp']['installed'] and results['model_file']['exists']:
        print("   ✅ System is ready! You can now use the ELYZA model interface.")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())