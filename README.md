# Mac Status PWA

A personalized Mac monitoring and status reporting Progressive Web Application (PWA) powered by the ELYZA-japanese-Llama-2-7b local language model.

## 概要 (Overview)

Mac Status PWAは、ローカルで動作するELYZA日本語言語モデルを使用して、Macのシステム状態を自然言語で報告するProgressive Web Applicationです。Apple風の洗練されたデザインを採用し、チャットインターフェースを通じてユーザーとやり取りします。

## ✨ Features

- 🖥️ **Real-time System Monitoring**: CPU, memory, disk usage, and running processes
- 🤖 **AI-Powered Chat Interface**: Natural language interaction using ELYZA-japanese-Llama-2-7b
- 🎨 **Apple-inspired Design**: Native macOS look and feel
- 📱 **Progressive Web App**: Installable, offline-capable, responsive
- 🔒 **Privacy-First**: All processing happens locally, no data leaves your Mac
- ⚡ **M1 Optimized**: Optimized for Apple Silicon performance
- 🌐 **Japanese Language Support**: Native Japanese language model and interface

## 🚀 Quick Start

### Prerequisites

- macOS (recommended) or other Unix-like system
- Python 3.12 or higher
- 8GB+ RAM (recommended for optimal model performance)
- 5GB+ free disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mac-status-pwa.git
   cd mac-status-pwa
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Download the ELYZA model**
   - Visit: [ELYZA-japanese-Llama-2-7b-instruct-gguf](https://huggingface.co/elyza/ELYZA-japanese-Llama-2-7b-instruct-gguf)
   - Download: `ELYZA-japanese-Llama-2-7b-instruct.Q4_0.gguf`
   - Place in: `models/elyza7b/`

4. **Start the application**
   ```bash
   ./start.sh
   # or
   source venv/bin/activate
   python backend/main.py
   ```

5. **Access the PWA**
   - Open your browser to: http://localhost:8000
   - Install as PWA for the best experience

## 📁 Project Structure

```
mac-status-pwa/
├── backend/                 # Python backend server
│   ├── main.py             # FastAPI application entry point
│   ├── system_monitor.py   # System monitoring functionality
│   ├── elyza_model.py      # ELYZA model interface
│   ├── websocket_server.py # WebSocket communication
│   ├── chat_context_manager.py # Chat context and personalization
│   └── ...
├── frontend/               # PWA frontend
│   ├── index.html         # Main HTML file
│   ├── app.js             # JavaScript application logic
│   ├── styles.css         # Apple-inspired styling
│   ├── manifest.json      # PWA manifest
│   ├── sw.js              # Service worker
│   └── icons/             # PWA icons
├── config/                 # Configuration files
│   ├── production.py      # Production settings
│   └── security.py        # Security configuration
├── tests/                  # Test suite
├── models/                 # Model files directory
│   └── elyza7b/           # ELYZA model location
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── setup.py               # Setup script
└── README.md              # This file
```

## 🔧 Configuration

### Production Settings

Edit `config/production.py` to customize:

- **Server Configuration**: Host, port, workers
- **Model Settings**: Context size, GPU layers, temperature
- **Security Settings**: CORS, rate limiting, CSP headers
- **Monitoring**: Update intervals, thresholds, alerts

### Security Configuration

The application includes comprehensive security features:

- **Rate Limiting**: Prevents abuse and ensures fair usage
- **Content Security Policy**: Protects against XSS attacks
- **Input Sanitization**: Validates and cleans user input
- **Local Processing**: No data leaves your machine

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Run specific test categories
python -m pytest tests/test_integration_*.py  # Integration tests
python -m pytest tests/test_performance.py    # Performance tests
python test_pwa_functionality.py              # PWA functionality
```

## 📊 Performance

The application is optimized for Apple Silicon (M1/M2) Macs:

- **Response Time**: < 5 seconds for most queries
- **Memory Usage**: ~2-4GB (depending on model configuration)
- **CPU Usage**: Optimized for M1 GPU acceleration
- **Startup Time**: < 30 seconds (including model loading)

## 🛠️ Development

### Setting up Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/mac-status-pwa.git
cd mac-status-pwa
python setup.py

# Install development dependencies
pip install pytest pytest-cov black flake8 isort

# Run in development mode
python backend/main.py --reload
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **Pytest**: Testing framework

```bash
# Format code
black backend/ config/

# Lint code
flake8 backend/ config/

# Sort imports
isort backend/ config/
```

## 🚀 Deployment

### GitHub Actions CI/CD

The project includes a comprehensive CI/CD pipeline:

- **Automated Testing**: Unit, integration, and performance tests
- **Security Scanning**: Bandit and Safety checks
- **Code Quality**: Linting and formatting validation
- **Release Automation**: Automatic packaging and deployment

### Manual Deployment

1. **Prepare the environment**
   ```bash
   python config/production.py  # Validate configuration
   ```

2. **Start the production server**
   ```bash
   source venv/bin/activate
   python backend/main.py
   ```

3. **Monitor the application**
   - Check logs in `logs/`
   - Monitor system resources
   - Verify PWA functionality

## 🔍 Troubleshooting

### Common Issues

**Model not loading**
- Ensure the ELYZA model file is in `models/elyza7b/`
- Check available memory (8GB+ recommended)
- Verify file permissions

**WebSocket connection failed**
- Check if port 8000 is available
- Verify firewall settings
- Try accessing via `127.0.0.1:8000` instead of `localhost:8000`

**High memory usage**
- Reduce `n_ctx` in model configuration
- Adjust `n_gpu_layers` setting
- Monitor with Activity Monitor

**PWA not installing**
- Ensure HTTPS or localhost access
- Check browser PWA support
- Verify manifest.json is accessible

### Logs and Debugging

- **Application logs**: `logs/app.log`
- **Error logs**: `logs/error.log`
- **Debug mode**: Set `debug=True` in configuration
- **Verbose logging**: Adjust log levels in `config/production.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ELYZA**: For the excellent Japanese language model
- **llama.cpp**: For the efficient model inference engine
- **FastAPI**: For the modern web framework
- **Apple**: For the design inspiration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mac-status-pwa/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mac-status-pwa/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/mac-status-pwa/wiki)

---

**Made with ❤️ for Mac users who love clean, functional, and private system monitoring.**