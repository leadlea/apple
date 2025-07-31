"""
Production configuration for Mac Status PWA
本番環境用設定ファイル
"""

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent.parent
MODEL_DIR = BASE_DIR / "models" / "elyza7b"
LOGS_DIR = BASE_DIR / "logs"

# Server configuration
SERVER_CONFIG = {
    "host": "127.0.0.1",  # Localhost only for security
    "port": int(os.getenv("PORT", 8000)),
    "debug": False,
    "reload": False,
    "workers": 1,  # Single worker for model consistency
    "log_level": "info",
    "access_log": True,
    "error_log": True
}

# Security settings
SECURITY_CONFIG = {
    "allowed_origins": [
        "http://localhost:8000",
        "https://localhost:8000",
        "http://127.0.0.1:8000",
        "https://127.0.0.1:8000"
    ],
    "allowed_methods": ["GET", "POST", "OPTIONS"],
    "allowed_headers": ["*"],
    "allow_credentials": True,
    "max_message_size": 1024 * 1024,  # 1MB max message size
    "rate_limit": {
        "requests_per_minute": 60,
        "burst_size": 10
    }
}

# Model configuration
MODEL_CONFIG = {
    "model_path": MODEL_DIR / "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf",
    "n_ctx": 2048,
    "n_gpu_layers": -1,  # Use all available GPU layers on M1
    "n_threads": None,  # Auto-detect optimal thread count
    "verbose": False,
    "use_mlock": True,  # Lock model in memory for performance
    "use_mmap": True,   # Memory map for efficiency
    "response_timeout": 30.0,  # 30 second timeout
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}

# System monitoring configuration
MONITORING_CONFIG = {
    "update_interval": 5.0,  # 5 seconds
    "history_size": 100,     # Keep last 100 readings
    "cpu_threshold": 80.0,   # Alert if CPU > 80%
    "memory_threshold": 85.0, # Alert if memory > 85%
    "disk_threshold": 90.0,   # Alert if disk > 90%
    "process_count": 10       # Show top 10 processes
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "error_file"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["file"],
            "propagate": False
        }
    }
}

# PWA configuration
PWA_CONFIG = {
    "cache_strategy": "cache_first",
    "cache_max_age": 86400,  # 24 hours
    "offline_fallback": True,
    "update_check_interval": 3600,  # 1 hour
    "precache_resources": [
        "/",
        "/index.html",
        "/styles.css",
        "/app.js",
        "/manifest.json"
    ]
}

# Health check configuration
HEALTH_CONFIG = {
    "enabled": True,
    "endpoint": "/health",
    "checks": {
        "model_loaded": True,
        "system_monitor": True,
        "websocket_server": True,
        "disk_space": True,
        "memory_usage": True
    }
}

# Environment validation
def validate_environment():
    """Validate production environment requirements"""
    errors = []
    
    # Check Python version
    import sys
    if sys.version_info < (3, 12):
        errors.append("Python 3.12 or higher is required")
    
    # Check model file exists
    if not MODEL_CONFIG["model_path"].exists():
        errors.append(f"Model file not found: {MODEL_CONFIG['model_path']}")
    
    # Check required directories
    required_dirs = [LOGS_DIR, MODEL_DIR]
    for dir_path in required_dirs:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")
    
    # Check disk space (minimum 2GB free)
    import shutil
    try:
        free_space = shutil.disk_usage(BASE_DIR).free
        if free_space < 2 * 1024 * 1024 * 1024:  # 2GB
            errors.append("Insufficient disk space (minimum 2GB required)")
    except Exception as e:
        errors.append(f"Cannot check disk space: {e}")
    
    return errors

if __name__ == "__main__":
    errors = validate_environment()
    if errors:
        print("Environment validation failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    else:
        print("Environment validation passed")