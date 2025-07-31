#!/bin/bash

# Mac Status PWA Deployment Script
# デプロイメントスクリプト

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
APP_NAME="mac-status-pwa"
DEPLOY_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"
USER="$(whoami)"
PYTHON_VERSION="3.12"

print_header() {
    echo "=================================================="
    echo "  Mac Status PWA Deployment Script"
    echo "  Macステータス PWA デプロイメントスクリプト"
    echo "=================================================="
    echo
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if running as root for system-wide deployment
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root - will deploy system-wide"
        SYSTEM_DEPLOY=true
    else
        log_info "Running as user - will deploy to user directory"
        DEPLOY_DIR="$HOME/${APP_NAME}"
        SYSTEM_DEPLOY=false
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VER >= 3.12" | bc -l) -eq 0 ]]; then
        log_error "Python 3.12+ is required, found $PYTHON_VER"
        exit 1
    fi
    
    log_success "Python $PYTHON_VER found"
    
    # Check available disk space (5GB minimum)
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    REQUIRED_SPACE=5242880  # 5GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        log_error "Insufficient disk space. Required: 5GB, Available: $((AVAILABLE_SPACE/1024/1024))GB"
        exit 1
    fi
    
    log_success "Sufficient disk space available"
}

create_deployment_directory() {
    log_info "Creating deployment directory: $DEPLOY_DIR"
    
    if [[ -d "$DEPLOY_DIR" ]]; then
        log_warning "Deployment directory already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
        rm -rf "$DEPLOY_DIR"
    fi
    
    mkdir -p "$DEPLOY_DIR"
    log_success "Deployment directory created"
}

copy_application_files() {
    log_info "Copying application files..."
    
    # Copy main application directories
    cp -r backend/ "$DEPLOY_DIR/"
    cp -r frontend/ "$DEPLOY_DIR/"
    cp -r config/ "$DEPLOY_DIR/"
    cp -r tests/ "$DEPLOY_DIR/"
    
    # Copy configuration files
    cp requirements.txt "$DEPLOY_DIR/"
    cp setup.py "$DEPLOY_DIR/"
    cp README.md "$DEPLOY_DIR/"
    
    # Copy startup script if it exists
    if [[ -f "start.sh" ]]; then
        cp start.sh "$DEPLOY_DIR/"
        chmod +x "$DEPLOY_DIR/start.sh"
    fi
    
    # Create necessary directories
    mkdir -p "$DEPLOY_DIR/logs"
    mkdir -p "$DEPLOY_DIR/models/elyza7b"
    
    log_success "Application files copied"
}

setup_virtual_environment() {
    log_info "Setting up virtual environment..."
    
    cd "$DEPLOY_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Virtual environment setup complete"
}

create_systemd_service() {
    if [[ "$SYSTEM_DEPLOY" != true ]]; then
        log_info "Skipping systemd service creation (not running as root)"
        return
    fi
    
    log_info "Creating systemd service..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Mac Status PWA
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR
Environment=PATH=$DEPLOY_DIR/venv/bin
ExecStart=$DEPLOY_DIR/venv/bin/python backend/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    log_success "Systemd service created and enabled"
}

create_launch_agent() {
    if [[ "$SYSTEM_DEPLOY" == true ]]; then
        return
    fi
    
    log_info "Creating macOS Launch Agent..."
    
    LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_AGENTS_DIR"
    
    cat > "$LAUNCH_AGENTS_DIR/com.macstatuspwa.app.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macstatuspwa.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DEPLOY_DIR/venv/bin/python</string>
        <string>$DEPLOY_DIR/backend/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DEPLOY_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$DEPLOY_DIR/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$DEPLOY_DIR/logs/stderr.log</string>
</dict>
</plist>
EOF
    
    log_success "Launch Agent created"
}

setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    if [[ "$SYSTEM_DEPLOY" == true ]]; then
        # System-wide logrotate configuration
        cat > "/etc/logrotate.d/${SERVICE_NAME}" << EOF
$DEPLOY_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF
    else
        # User-level log rotation script
        cat > "$DEPLOY_DIR/rotate_logs.sh" << EOF
#!/bin/bash
cd "$DEPLOY_DIR/logs"
for log in *.log; do
    if [[ -f "\$log" ]]; then
        mv "\$log" "\$log.old"
        touch "\$log"
    fi
done
# Keep only last 7 days of logs
find . -name "*.log.old" -mtime +7 -delete
EOF
        chmod +x "$DEPLOY_DIR/rotate_logs.sh"
        
        # Add to crontab
        (crontab -l 2>/dev/null; echo "0 0 * * * $DEPLOY_DIR/rotate_logs.sh") | crontab -
    fi
    
    log_success "Log rotation configured"
}

validate_deployment() {
    log_info "Validating deployment..."
    
    cd "$DEPLOY_DIR"
    
    # Check if virtual environment works
    if ! source venv/bin/activate; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Check if main modules can be imported
    if ! python -c "import backend.main"; then
        log_error "Failed to import main application"
        exit 1
    fi
    
    # Validate configuration
    if ! python config/production.py; then
        log_error "Configuration validation failed"
        exit 1
    fi
    
    log_success "Deployment validation passed"
}

start_service() {
    log_info "Starting service..."
    
    if [[ "$SYSTEM_DEPLOY" == true ]]; then
        systemctl start "$SERVICE_NAME"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        launchctl load "$HOME/Library/LaunchAgents/com.macstatuspwa.app.plist"
        log_info "Service started via Launch Agent"
    fi
    
    # Wait a moment and check if service is running
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Service is running and responding"
    else
        log_warning "Service may not be responding yet (this is normal during first startup)"
    fi
}

print_completion_message() {
    echo
    echo "=================================================="
    echo "  Deployment Complete!"
    echo "=================================================="
    echo
    echo "Application deployed to: $DEPLOY_DIR"
    echo
    echo "Next steps:"
    echo "1. Download the ELYZA model:"
    echo "   - Visit: https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf"
    echo "   - Download: ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf"
    echo "   - Place in: $DEPLOY_DIR/models/elyza7b/"
    echo
    echo "2. Access the application:"
    echo "   - URL: http://localhost:8000"
    echo "   - Install as PWA for best experience"
    echo
    echo "3. Service management:"
    if [[ "$SYSTEM_DEPLOY" == true ]]; then
        echo "   - Start: sudo systemctl start $SERVICE_NAME"
        echo "   - Stop: sudo systemctl stop $SERVICE_NAME"
        echo "   - Status: sudo systemctl status $SERVICE_NAME"
        echo "   - Logs: sudo journalctl -u $SERVICE_NAME -f"
    else
        echo "   - Start: launchctl load ~/Library/LaunchAgents/com.macstatuspwa.app.plist"
        echo "   - Stop: launchctl unload ~/Library/LaunchAgents/com.macstatuspwa.app.plist"
        echo "   - Logs: tail -f $DEPLOY_DIR/logs/*.log"
    fi
    echo
    echo "4. Troubleshooting:"
    echo "   - Check logs in: $DEPLOY_DIR/logs/"
    echo "   - Validate config: cd $DEPLOY_DIR && python config/production.py"
    echo "   - Run tests: cd $DEPLOY_DIR && python -m pytest tests/"
    echo
    log_success "Enjoy your Mac Status PWA! 🚀"
}

# Main deployment flow
main() {
    print_header
    
    check_requirements
    create_deployment_directory
    copy_application_files
    setup_virtual_environment
    
    if [[ "$SYSTEM_DEPLOY" == true ]]; then
        create_systemd_service
    else
        create_launch_agent
    fi
    
    setup_log_rotation
    validate_deployment
    start_service
    print_completion_message
}

# Run main function
main "$@"