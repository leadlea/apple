# Installation Guide - Mac Status PWA

This guide provides detailed installation instructions for the Mac Status PWA application.

## 📋 Prerequisites

### System Requirements

- **Operating System**: macOS 10.15+ (recommended), Linux, or Windows
- **Python**: 3.12 or higher
- **Memory**: 8GB RAM minimum (16GB recommended for optimal performance)
- **Storage**: 5GB free disk space
- **Processor**: Apple Silicon (M1/M2) recommended for optimal performance

### Required Software

1. **Python 3.12+**
   ```bash
   # Check your Python version
   python3 --version
   
   # Install Python 3.12 via Homebrew (macOS)
   brew install python@3.12
   
   # Or download from python.org
   # https://www.python.org/downloads/
   ```

2. **Git** (for cloning the repository)
   ```bash
   # Install via Homebrew (macOS)
   brew install git
   
   # Or download from git-scm.com
   # https://git-scm.com/downloads
   ```

## 🚀 Installation Methods

### Method 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mac-status-pwa.git
   cd mac-status-pwa
   ```

2. **Run the setup script**
   ```bash
   python3 setup.py
   ```
   
   The setup script will:
   - Check system requirements
   - Create a virtual environment
   - Install Python dependencies
   - Create necessary directories
   - Generate startup scripts
   - Validate the installation

3. **Download the ELYZA model** (Manual step required)
   - Visit: [ELYZA Hugging Face Repository](https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf)
   - Download: `ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf` (~3.8GB)
   - Place the file in: `models/elyza7b/ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf`

4. **Start the application**
   ```bash
   ./start.sh
   ```

### Method 2: Manual Installation

1. **Clone and prepare the environment**
   ```bash
   git clone https://github.com/yourusername/mac-status-pwa.git
   cd mac-status-pwa
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Upgrade pip
   pip install --upgrade pip
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create required directories**
   ```bash
   mkdir -p logs models/elyza7b frontend/icons tests config
   ```

4. **Download and place the model**
   - Download `ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf` from Hugging Face
   - Place in `models/elyza7b/`

5. **Validate configuration**
   ```bash
   python config/production.py
   ```

6. **Start the application**
   ```bash
   python backend/main.py
   ```

### Method 3: Production Deployment

For production or system-wide deployment:

1. **Run the deployment script**
   ```bash
   # For system-wide deployment (requires sudo)
   sudo ./deploy.sh
   
   # For user-level deployment
   ./deploy.sh
   ```

2. **The deployment script will:**
   - Create a deployment directory
   - Set up the virtual environment
   - Configure system services (systemd/launchd)
   - Set up log rotation
   - Validate the deployment

## 🔧 Configuration

### Basic Configuration

The application uses configuration files in the `config/` directory:

- `config/production.py`: Main production settings
- `config/security.py`: Security and rate limiting settings

### Model Configuration

Edit `config/production.py` to adjust model settings:

```python
MODEL_CONFIG = {
    "model_path": MODEL_DIR / "ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf",
    "n_ctx": 2048,          # Context window size
    "n_gpu_layers": -1,     # Use all GPU layers (M1 optimization)
    "temperature": 0.7,     # Response creativity (0.0-1.0)
    "max_tokens": 512,      # Maximum response length
}
```

### Server Configuration

Adjust server settings in `config/production.py`:

```python
SERVER_CONFIG = {
    "host": "127.0.0.1",    # Bind address
    "port": 8000,           # Port number
    "workers": 1,           # Number of worker processes
    "log_level": "info",    # Logging level
}
```

## 🧪 Verification

### Test the Installation

1. **Run the test suite**
   ```bash
   source venv/bin/activate
   python -m pytest tests/ -v
   ```

2. **Test PWA functionality**
   ```bash
   python test_pwa_functionality.py
   ```

3. **Check system monitoring**
   ```bash
   python test_system_status_display.py
   ```

4. **Verify model loading**
   ```bash
   python -c "from backend.elyza_model import ELYZAModelInterface; print('Model interface OK')"
   ```

### Access the Application

1. **Start the server**
   ```bash
   ./start.sh
   # or
   source venv/bin/activate && python backend/main.py
   ```

2. **Open in browser**
   - Navigate to: http://localhost:8000
   - You should see the Mac Status PWA interface

3. **Install as PWA**
   - Click the install button in your browser
   - Or use the browser's "Add to Home Screen" option

## 🔍 Troubleshooting

### Common Issues

#### Model Not Loading
```
Error: Model file not found
```
**Solution**: Ensure the ELYZA model file is downloaded and placed in `models/elyza7b/`

#### Memory Issues
```
Error: Not enough memory to load model
```
**Solutions**:
- Close other applications to free memory
- Reduce `n_ctx` in model configuration
- Use a smaller model variant if available

#### Port Already in Use
```
Error: Address already in use
```
**Solutions**:
- Change the port in `config/production.py`
- Kill the process using port 8000: `lsof -ti:8000 | xargs kill -9`

#### Permission Denied
```
Error: Permission denied
```
**Solutions**:
- Ensure you have write permissions to the installation directory
- Run with appropriate permissions
- Check file ownership: `ls -la`

#### WebSocket Connection Failed
```
Error: WebSocket connection failed
```
**Solutions**:
- Check if the server is running
- Verify firewall settings
- Try accessing via 127.0.0.1 instead of localhost

### Diagnostic Commands

```bash
# Check Python version
python3 --version

# Check virtual environment
source venv/bin/activate && python -c "import sys; print(sys.prefix)"

# Check installed packages
pip list

# Check model file
ls -la models/elyza7b/

# Check logs
tail -f logs/app.log

# Test configuration
python config/production.py

# Check system resources
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().available/1024**3:.1f}GB available')"
```

### Getting Help

If you encounter issues:

1. **Check the logs**: `logs/app.log` and `logs/error.log`
2. **Run diagnostics**: `python config/production.py`
3. **Search issues**: [GitHub Issues](https://github.com/yourusername/mac-status-pwa/issues)
4. **Create an issue**: Include logs, system info, and steps to reproduce

## 🔄 Updates

### Updating the Application

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Update dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt --upgrade
   ```

3. **Run database migrations** (if any)
   ```bash
   # Currently no database migrations needed
   ```

4. **Restart the service**
   ```bash
   # If using systemd
   sudo systemctl restart mac-status-pwa
   
   # If using manual startup
   ./start.sh
   ```

### Backup and Restore

**Backup**:
```bash
# Backup configuration and logs
tar -czf mac-status-pwa-backup.tar.gz config/ logs/ models/
```

**Restore**:
```bash
# Extract backup
tar -xzf mac-status-pwa-backup.tar.gz
```

## 🚀 Next Steps

After successful installation:

1. **Explore the interface**: Try asking questions about your Mac's status
2. **Customize settings**: Adjust configuration files to your preferences
3. **Set up monitoring**: Configure alerts and thresholds
4. **Install as PWA**: For the best user experience
5. **Read the documentation**: Check out the full README.md

## 📞 Support

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mac-status-pwa/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mac-status-pwa/discussions)

---

**Happy monitoring! 🖥️✨**