#!/usr/bin/env python3
"""
Deployment Validation Script
デプロイメント検証スクリプト

This script validates that the Mac Status PWA is properly configured
and ready for production deployment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def print_header(title: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD} {title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_check(description: str, passed: bool, details: str = ""):
    """Print validation check result"""
    status = f"{Colors.GREEN}✓{Colors.ENDC}" if passed else f"{Colors.RED}✗{Colors.ENDC}"
    print(f"{status} {description}")
    if details:
        print(f"    {details}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

class DeploymentValidator:
    """Validates deployment readiness"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path.cwd()
    
    def validate_file_structure(self) -> bool:
        """Validate project file structure"""
        print_header("File Structure Validation")
        
        required_files = [
            "backend/main.py",
            "frontend/index.html",
            "frontend/app.js",
            "frontend/styles.css",
            "frontend/manifest.json",
            "frontend/sw.js",
            "config/production.py",
            "config/security.py",
            "requirements.txt",
            "setup.py",
            "deploy.sh",
            "README.md",
            "INSTALL.md"
        ]
        
        required_dirs = [
            "backend",
            "frontend",
            "config",
            "tests",
            "logs",
            "models/elyza7b"
        ]
        
        all_good = True
        
        # Check files
        for file_path in required_files:
            exists = (self.project_root / file_path).exists()
            print_check(f"File: {file_path}", exists)
            if not exists:
                self.errors.append(f"Missing required file: {file_path}")
                all_good = False
        
        # Check directories
        for dir_path in required_dirs:
            exists = (self.project_root / dir_path).exists()
            print_check(f"Directory: {dir_path}", exists)
            if not exists:
                self.errors.append(f"Missing required directory: {dir_path}")
                all_good = False
        
        return all_good
    
    def validate_python_environment(self) -> bool:
        """Validate Python environment"""
        print_header("Python Environment Validation")
        
        all_good = True
        
        # Check Python version
        python_version = sys.version_info
        version_ok = python_version >= (3, 12)
        print_check(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}", 
                   version_ok)
        if not version_ok:
            self.errors.append("Python 3.12+ required")
            all_good = False
        
        # Check virtual environment
        venv_exists = (self.project_root / "venv").exists()
        print_check("Virtual environment", venv_exists)
        if not venv_exists:
            self.warnings.append("Virtual environment not found - run setup.py")
        
        # Check requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file) as f:
                    requirements = f.read().strip().split('\n')
                print_check(f"Requirements file ({len(requirements)} packages)", True)
            except Exception as e:
                print_check("Requirements file", False, str(e))
                self.errors.append(f"Cannot read requirements.txt: {e}")
                all_good = False
        
        return all_good
    
    def validate_configuration(self) -> bool:
        """Validate configuration files"""
        print_header("Configuration Validation")
        
        all_good = True
        
        # Test production config
        try:
            sys.path.insert(0, str(self.project_root))
            from config.production import (
                SERVER_CONFIG, SECURITY_CONFIG, MODEL_CONFIG,
                validate_environment
            )
            print_check("Production config import", True)
            
            # Validate environment
            try:
                errors = validate_environment()
                env_valid = len(errors) == 0
                print_check("Environment validation", env_valid)
                if not env_valid:
                    for error in errors:
                        self.warnings.append(f"Environment: {error}")
            except Exception as e:
                print_check("Environment validation", False, str(e))
                self.errors.append(f"Environment validation failed: {e}")
                all_good = False
                
        except ImportError as e:
            print_check("Production config import", False, str(e))
            self.errors.append(f"Cannot import production config: {e}")
            all_good = False
        
        # Test security config
        try:
            from config.security import security_manager, SECURITY_HEADERS
            print_check("Security config import", True)
        except ImportError as e:
            print_check("Security config import", False, str(e))
            self.errors.append(f"Cannot import security config: {e}")
            all_good = False
        
        return all_good
    
    def validate_model_setup(self) -> bool:
        """Validate model setup"""
        print_header("Model Setup Validation")
        
        all_good = True
        
        model_dir = self.project_root / "models" / "elyza7b"
        model_file = model_dir / "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
        
        # Check model directory
        print_check("Model directory", model_dir.exists())
        
        # Check model file
        model_exists = model_file.exists()
        print_check("ELYZA model file", model_exists)
        
        if model_exists:
            # Check file size (should be around 3.8GB)
            file_size = model_file.stat().st_size / (1024**3)  # GB
            size_ok = 3.0 < file_size < 5.0
            print_check(f"Model file size ({file_size:.1f}GB)", size_ok)
            if not size_ok:
                self.warnings.append(f"Model file size unusual: {file_size:.1f}GB")
        else:
            self.warnings.append("Model file not found - download required")
        
        # Test model loading (if available)
        try:
            import llama_cpp
            print_check("llama-cpp-python available", True)
        except ImportError:
            print_check("llama-cpp-python available", False)
            self.errors.append("llama-cpp-python not installed")
            all_good = False
        
        return all_good
    
    def validate_frontend(self) -> bool:
        """Validate frontend files"""
        print_header("Frontend Validation")
        
        all_good = True
        
        # Check PWA manifest
        manifest_file = self.project_root / "frontend" / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                
                required_fields = ["name", "short_name", "start_url", "display", "icons"]
                manifest_valid = all(field in manifest for field in required_fields)
                print_check("PWA manifest valid", manifest_valid)
                
                if not manifest_valid:
                    missing = [f for f in required_fields if f not in manifest]
                    self.errors.append(f"Manifest missing fields: {missing}")
                    all_good = False
                    
            except json.JSONDecodeError as e:
                print_check("PWA manifest valid", False, str(e))
                self.errors.append(f"Invalid manifest.json: {e}")
                all_good = False
        else:
            print_check("PWA manifest exists", False)
            self.errors.append("manifest.json not found")
            all_good = False
        
        # Check service worker
        sw_file = self.project_root / "frontend" / "sw.js"
        sw_exists = sw_file.exists()
        print_check("Service worker", sw_exists)
        if not sw_exists:
            self.errors.append("Service worker (sw.js) not found")
            all_good = False
        
        # Check icons directory
        icons_dir = self.project_root / "frontend" / "icons"
        icons_exist = icons_dir.exists() and any(icons_dir.iterdir())
        print_check("PWA icons", icons_exist)
        if not icons_exist:
            self.warnings.append("PWA icons not found")
        
        return all_good
    
    def validate_security(self) -> bool:
        """Validate security configuration"""
        print_header("Security Validation")
        
        all_good = True
        
        # Check file permissions
        sensitive_files = [
            "config/production.py",
            "config/security.py",
            "deploy.sh"
        ]
        
        for file_path in sensitive_files:
            file_obj = self.project_root / file_path
            if file_obj.exists():
                # Check if file is readable by others (basic check)
                stat = file_obj.stat()
                mode = stat.st_mode
                others_readable = bool(mode & 0o004)
                print_check(f"File permissions: {file_path}", not others_readable)
                if others_readable:
                    self.warnings.append(f"File {file_path} is readable by others")
        
        # Check for hardcoded secrets (basic scan)
        config_files = ["config/production.py", "config/security.py"]
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        content = f.read().lower()
                    
                    # Look for potential secrets
                    secret_patterns = ["password", "secret", "key", "token"]
                    found_patterns = [p for p in secret_patterns if p in content]
                    
                    if found_patterns:
                        print_check(f"No hardcoded secrets: {config_file}", False)
                        self.warnings.append(f"Potential secrets in {config_file}: {found_patterns}")
                    else:
                        print_check(f"No hardcoded secrets: {config_file}", True)
                        
                except Exception as e:
                    print_check(f"Security scan: {config_file}", False, str(e))
        
        return all_good
    
    def validate_deployment_scripts(self) -> bool:
        """Validate deployment scripts"""
        print_header("Deployment Scripts Validation")
        
        all_good = True
        
        scripts = [
            ("setup.py", "Setup script"),
            ("deploy.sh", "Deployment script"),
            ("start.sh", "Startup script")
        ]
        
        for script_file, description in scripts:
            script_path = self.project_root / script_file
            exists = script_path.exists()
            print_check(f"{description}", exists)
            
            if exists and script_file.endswith('.sh'):
                # Check if shell script is executable
                executable = os.access(script_path, os.X_OK)
                print_check(f"{description} executable", executable)
                if not executable:
                    self.warnings.append(f"{script_file} is not executable")
        
        return all_good
    
    def validate_ci_cd(self) -> bool:
        """Validate CI/CD configuration"""
        print_header("CI/CD Configuration Validation")
        
        all_good = True
        
        # Check GitHub Actions workflow
        workflow_file = self.project_root / ".github" / "workflows" / "ci.yml"
        workflow_exists = workflow_file.exists()
        print_check("GitHub Actions workflow", workflow_exists)
        
        if workflow_exists:
            try:
                with open(workflow_file) as f:
                    workflow_content = f.read()
                
                # Check for essential workflow components
                required_components = ["test", "build", "deploy"]
                has_components = all(comp in workflow_content.lower() 
                                   for comp in required_components)
                print_check("Workflow completeness", has_components)
                
            except Exception as e:
                print_check("Workflow validation", False, str(e))
                all_good = False
        
        return all_good
    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        print(f"{Colors.BLUE}{Colors.BOLD}Mac Status PWA - Deployment Validation{Colors.ENDC}")
        print(f"{Colors.BLUE}{Colors.BOLD}デプロイメント検証{Colors.ENDC}")
        
        validation_steps = [
            self.validate_file_structure,
            self.validate_python_environment,
            self.validate_configuration,
            self.validate_model_setup,
            self.validate_frontend,
            self.validate_security,
            self.validate_deployment_scripts,
            self.validate_ci_cd
        ]
        
        all_passed = True
        for step in validation_steps:
            try:
                if not step():
                    all_passed = False
            except Exception as e:
                print_error(f"Validation step failed: {e}")
                self.errors.append(f"Validation error: {e}")
                all_passed = False
        
        # Print summary
        self.print_summary()
        
        return all_passed and len(self.errors) == 0
    
    def print_summary(self):
        """Print validation summary"""
        print_header("Validation Summary")
        
        if not self.errors and not self.warnings:
            print_success("All validation checks passed! ✨")
            print_success("Your Mac Status PWA is ready for deployment.")
        else:
            if self.errors:
                print(f"\n{Colors.RED}{Colors.BOLD}Errors ({len(self.errors)}):{Colors.ENDC}")
                for error in self.errors:
                    print(f"  {Colors.RED}✗{Colors.ENDC} {error}")
            
            if self.warnings:
                print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings ({len(self.warnings)}):{Colors.ENDC}")
                for warning in self.warnings:
                    print(f"  {Colors.YELLOW}⚠{Colors.ENDC} {warning}")
        
        print(f"\n{Colors.BLUE}Next steps:{Colors.ENDC}")
        if self.errors:
            print("1. Fix the errors listed above")
            print("2. Re-run this validation script")
        else:
            print("1. Download the ELYZA model if not already done")
            print("2. Run: python setup.py (if not already done)")
            print("3. Start the application: ./start.sh")
            print("4. Run production tests: python test_production_deployment.py")

def main():
    """Main validation function"""
    validator = DeploymentValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Validation error: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()