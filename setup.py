#!/usr/bin/env python3
"""
Mac Status PWA Setup Script
Macステータス PWA セットアップスクリプト

This script sets up the Mac Status PWA application with all required dependencies,
model files, and configuration.
"""

import os
import sys
import subprocess
import platform
import shutil
import urllib.request
from pathlib import Path
import json

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKGREEN):
    """Print colored message"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Print header message"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f" {message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)

def print_step(step_num, message):
    """Print step message"""
    print_colored(f"\n[Step {step_num}] {message}", Colors.OKBLUE)

def print_success(message):
    """Print success message"""
    print_colored(f"✓ {message}", Colors.OKGREEN)

def print_warning(message):
    """Print warning message"""
    print_colored(f"⚠ {message}", Colors.WARNING)

def print_error(message):
    """Print error message"""
    print_colored(f"✗ {message}", Colors.FAIL)

def run_command(command, description="", check=True):
    """Run shell command with error handling"""
    if description:
        print(f"  Running: {description}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print_error(f"Error: {e.stderr}")
        return False

def check_system_requirements():
    """Check system requirements"""
    print_step(1, "Checking system requirements")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 12):
        print_error(f"Python 3.12+ required, found {python_version.major}.{python_version.minor}")
        return False
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check macOS
    if platform.system() != "Darwin":
        print_warning("This application is optimized for macOS")
    else:
        print_success(f"macOS {platform.mac_ver()[0]}")
    
    # Check available memory (minimum 8GB recommended)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 8:
            print_warning(f"Low memory: {memory_gb:.1f}GB (8GB+ recommended)")
        else:
            print_success(f"Memory: {memory_gb:.1f}GB")
    except ImportError:
        print_warning("Cannot check memory (psutil not installed)")
    
    # Check disk space (minimum 5GB)
    free_space = shutil.disk_usage(".").free / (1024**3)
    if free_space < 5:
        print_error(f"Insufficient disk space: {free_space:.1f}GB (5GB+ required)")
        return False
    print_success(f"Disk space: {free_space:.1f}GB available")
    
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print_step(2, "Setting up virtual environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        return True
    
    # Create virtual environment
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    print_success("Virtual environment created")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step(3, "Installing dependencies")
    
    # Determine pip path
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    # Upgrade pip
    if not run_command(f"{pip_path} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing requirements"):
        return False
    
    print_success("Dependencies installed")
    return True

def download_model():
    """Download ELYZA model if not present"""
    print_step(4, "Setting up ELYZA model")
    
    model_dir = Path("models/elyza7b")
    model_file = model_dir / "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
    
    # Create model directory
    model_dir.mkdir(parents=True, exist_ok=True)
    
    if model_file.exists():
        print_success("Model file already exists")
        return True
    
    print_warning("Model file not found")
    print("Please download the ELYZA model manually:")
    print(f"1. Visit: https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf")
    print(f"2. Download: ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf")
    print(f"3. Place it in: {model_file}")
    
    # Check if download script exists
    download_script = Path("download_model.sh")
    if download_script.exists():
        print("\nAlternatively, run the download script:")
        print("  chmod +x download_model.sh")
        print("  ./download_model.sh")
    
    return False  # Manual step required

def setup_directories():
    """Create required directories"""
    print_step(5, "Setting up directories")
    
    directories = [
        "logs",
        "models/elyza7b",
        "frontend/icons",
        "tests",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print_success("Directories created")
    return True

def create_startup_script():
    """Create startup script"""
    print_step(6, "Creating startup script")
    
    if platform.system() == "Windows":
        script_content = """@echo off
echo Starting Mac Status PWA...
venv\\Scripts\\python backend\\main.py
pause
"""
        script_path = "start.bat"
    else:
        script_content = """#!/bin/bash
echo "Starting Mac Status PWA..."
source venv/bin/activate
python backend/main.py
"""
        script_path = "start.sh"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(script_path, 0o755)
    
    print_success(f"Startup script created: {script_path}")
    return True

def validate_installation():
    """Validate installation"""
    print_step(7, "Validating installation")
    
    # Check if all required files exist
    required_files = [
        "backend/main.py",
        "frontend/index.html",
        "frontend/app.js",
        "frontend/styles.css",
        "frontend/manifest.json",
        "requirements.txt",
        "config/production.py",
        "config/security.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print_error("Missing required files:")
        for file_path in missing_files:
            print_error(f"  - {file_path}")
        return False
    
    # Test import of main modules
    try:
        sys.path.insert(0, str(Path("venv/lib/python3.12/site-packages")))
        import fastapi
        import uvicorn
        import psutil
        print_success("Core dependencies available")
    except ImportError as e:
        print_error(f"Import error: {e}")
        return False
    
    print_success("Installation validated")
    return True

def print_next_steps():
    """Print next steps for user"""
    print_header("Setup Complete!")
    
    print_colored("\nNext steps:", Colors.OKBLUE)
    print("1. Download the ELYZA model (if not done already):")
    print("   - Visit: https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf")
    print("   - Download: ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf")
    print("   - Place in: models/elyza7b/")
    
    print("\n2. Start the application:")
    if platform.system() == "Windows":
        print("   - Double-click: start.bat")
        print("   - Or run: venv\\Scripts\\python backend\\main.py")
    else:
        print("   - Run: ./start.sh")
        print("   - Or run: source venv/bin/activate && python backend/main.py")
    
    print("\n3. Access the PWA:")
    print("   - Open browser: http://localhost:8000")
    print("   - Install as PWA for best experience")
    
    print("\n4. Troubleshooting:")
    print("   - Check logs in: logs/")
    print("   - Run tests: python -m pytest tests/")
    print("   - Validate config: python config/production.py")
    
    print_colored("\nEnjoy your Mac Status PWA! 🚀", Colors.OKGREEN)

def main():
    """Main setup function"""
    print_header("Mac Status PWA Setup")
    print_colored("Setting up your personalized Mac monitoring PWA", Colors.OKCYAN)
    
    # Run setup steps
    steps = [
        check_system_requirements,
        setup_virtual_environment,
        install_dependencies,
        setup_directories,
        create_startup_script,
        validate_installation
    ]
    
    for step_func in steps:
        if not step_func():
            print_error("Setup failed. Please check the errors above.")
            sys.exit(1)
    
    # Model download is optional but recommended
    download_model()
    
    print_next_steps()

if __name__ == "__main__":
    main()