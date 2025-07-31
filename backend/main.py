#!/usr/bin/env python3
"""
Mac Status PWA - Main Application
Macステータス PWA - メインアプリケーション

Production-ready main application with comprehensive configuration,
security, monitoring, and error handling.
"""

import asyncio
import logging
import logging.config
import signal
import sys
import os
import time
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
try:
    from config.production import (
        SERVER_CONFIG, SECURITY_CONFIG, MODEL_CONFIG, 
        MONITORING_CONFIG, LOGGING_CONFIG, HEALTH_CONFIG,
        validate_environment
    )
    from config.security import security_manager, SECURITY_HEADERS
    PRODUCTION_MODE = True
except ImportError:
    # Fallback configuration for development
    SERVER_CONFIG = {"host": "127.0.0.1", "port": 8000, "debug": True}
    SECURITY_CONFIG = {"allowed_origins": ["*"]}
    MODEL_CONFIG = {}
    MONITORING_CONFIG = {}
    LOGGING_CONFIG = None
    HEALTH_CONFIG = {"enabled": True, "endpoint": "/health"}
    security_manager = None
    SECURITY_HEADERS = {}
    PRODUCTION_MODE = False

# Import application components
try:
    from backend.websocket_server import WebSocketServer
    from backend.system_monitor import SystemMonitor
    from backend.elyza_model import ELYZAModelInterface
    from backend.chat_context_manager import ChatContextManager
    from backend.message_router import MessageRouter
    from backend.connection_manager import ConnectionManager
    from backend.error_handler import ErrorHandler
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some components not available: {e}")
    COMPONENTS_AVAILABLE = False

# Global application state
app_state = {
    "system_monitor": None,
    "model_interface": None,
    "chat_context": None,
    "message_router": None,
    "connection_manager": None,
    "websocket_server": None,
    "error_handler": None,
    "startup_time": time.time()
}

# Configure logging
if LOGGING_CONFIG and PRODUCTION_MODE:
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.config.dictConfig(LOGGING_CONFIG)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Mac Status PWA...")
    
    # Validate environment
    if PRODUCTION_MODE:
        try:
            errors = validate_environment()
            if errors:
                logger.error("Environment validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                raise RuntimeError("Environment validation failed")
        except Exception as e:
            logger.error(f"Environment validation error: {e}")
    
    # Initialize components
    if COMPONENTS_AVAILABLE:
        try:
            # Initialize error handler
            app_state["error_handler"] = ErrorHandler()
            
            # Initialize system monitor
            app_state["system_monitor"] = SystemMonitor()
            await app_state["system_monitor"].start_monitoring()
            
            # Initialize model interface
            if MODEL_CONFIG:
                app_state["model_interface"] = ELYZAModelInterface(
                    model_path=str(MODEL_CONFIG.get("model_path", ""))
                )
                await app_state["model_interface"].initialize()
            
            # Initialize chat context manager
            app_state["chat_context"] = ChatContextManager()
            
            # Initialize connection manager
            app_state["connection_manager"] = ConnectionManager()
            
            # Initialize message router
            app_state["message_router"] = MessageRouter(
                system_monitor=app_state["system_monitor"],
                model_interface=app_state["model_interface"],
                chat_context=app_state["chat_context"],
                error_handler=app_state["error_handler"]
            )
            
            # Initialize WebSocket server
            app_state["websocket_server"] = WebSocketServer(
                connection_manager=app_state["connection_manager"],
                message_router=app_state["message_router"]
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            # Continue with limited functionality
    
    yield
    
    # Cleanup
    logger.info("Shutting down Mac Status PWA...")
    
    if app_state["system_monitor"]:
        await app_state["system_monitor"].stop_monitoring()
    
    if app_state["model_interface"]:
        await app_state["model_interface"].cleanup()
    
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Mac Status PWA",
    description="Personalized Mac monitoring PWA with ELYZA LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Security middleware
if PRODUCTION_MODE and security_manager:
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Security middleware for rate limiting and validation"""
        client_ip = request.client.host
        
        # Check if IP is blocked
        if security_manager.is_blocked(client_ip):
            raise HTTPException(status_code=429, detail="IP blocked due to rate limiting")
        
        # Check rate limits
        if not security_manager.check_rate_limit(
            client_ip, 
            SECURITY_CONFIG.get("rate_limit", {}).get("requests_per_minute", 60)
        ):
            security_manager.block_ip(client_ip)
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        response = await call_next(request)
        
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=SECURITY_CONFIG.get("allowed_origins", ["*"]),
    allow_credentials=SECURITY_CONFIG.get("allow_credentials", True),
    allow_methods=SECURITY_CONFIG.get("allowed_methods", ["*"]),
    allow_headers=SECURITY_CONFIG.get("allowed_headers", ["*"]),
)

# Trusted host middleware for production
if PRODUCTION_MODE:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_pwa():
    """Serve the PWA main page"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        logger.error("Frontend index.html not found")
        return HTMLResponse(
            content="<h1>Mac Status PWA</h1><p>Frontend files not found</p>",
            status_code=200
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    if app_state["websocket_server"]:
        await app_state["websocket_server"].handle_websocket(websocket)
    else:
        # Fallback WebSocket handler
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
        except WebSocketDisconnect:
            pass

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    if not HEALTH_CONFIG.get("enabled", True):
        raise HTTPException(status_code=404, detail="Health check disabled")
    
    health_status = {
        "status": "healthy",
        "service": "Mac Status PWA",
        "timestamp": time.time(),
        "uptime": time.time() - app_state["startup_time"],
        "version": "1.0.0"
    }
    
    # Check component health
    checks = HEALTH_CONFIG.get("checks", {})
    
    if checks.get("model_loaded") and app_state["model_interface"]:
        health_status["model_loaded"] = app_state["model_interface"].is_loaded()
    
    if checks.get("system_monitor") and app_state["system_monitor"]:
        health_status["system_monitor"] = app_state["system_monitor"].is_running()
    
    if checks.get("websocket_server") and app_state["websocket_server"]:
        health_status["websocket_connections"] = len(
            app_state["connection_manager"].active_connections
            if app_state["connection_manager"] else []
        )
    
    # Check system resources
    if checks.get("memory_usage"):
        try:
            import psutil
            memory = psutil.virtual_memory()
            health_status["memory_usage"] = {
                "percent": memory.percent,
                "available_gb": memory.available / (1024**3)
            }
        except ImportError:
            health_status["memory_usage"] = "unavailable"
    
    if checks.get("disk_space"):
        try:
            import shutil
            disk_usage = shutil.disk_usage(".")
            health_status["disk_space"] = {
                "free_gb": disk_usage.free / (1024**3),
                "total_gb": disk_usage.total / (1024**3)
            }
        except Exception:
            health_status["disk_space"] = "unavailable"
    
    return health_status

@app.get("/api/status")
async def get_system_status():
    """Get current system status"""
    if app_state["system_monitor"]:
        try:
            status = await app_state["system_monitor"].get_system_info()
            return status
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system status")
    else:
        raise HTTPException(status_code=503, detail="System monitor not available")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if app_state["error_handler"]:
        error_response = app_state["error_handler"].handle_error(exc)
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main application entry point"""
    setup_signal_handlers()
    
    logger.info("Starting Mac Status PWA server...")
    logger.info(f"Production mode: {PRODUCTION_MODE}")
    logger.info(f"Components available: {COMPONENTS_AVAILABLE}")
    
    # Run the server
    uvicorn.run(
        "backend.main:app",
        host=SERVER_CONFIG.get("host", "127.0.0.1"),
        port=SERVER_CONFIG.get("port", 8000),
        reload=SERVER_CONFIG.get("reload", False),
        workers=SERVER_CONFIG.get("workers", 1),
        log_level=SERVER_CONFIG.get("log_level", "info"),
        access_log=SERVER_CONFIG.get("access_log", True)
    )

if __name__ == "__main__":
    main()