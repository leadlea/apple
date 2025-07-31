# Demo Data for Mac Status PWA

This directory contains sample data and configuration for demonstrating the Mac Status PWA.

## Files

- `sample_system_data.json`: Sample system monitoring data
- `sample_chat_history.json`: Example chat conversations
- `sample_performance_metrics.json`: Performance benchmarking data
- `user_scenarios.json`: User interaction scenarios
- `screenshot_preparation.json`: Guide for creating screenshots
- `demo_config.json`: Demo configuration settings

## Usage

### Loading Sample Data

```python
import json

# Load system data
with open('demo_data/sample_system_data.json') as f:
    system_data = json.load(f)

# Load chat history
with open('demo_data/sample_chat_history.json') as f:
    chat_history = json.load(f)
```

### Running Demo Mode

```bash
# Start server with demo data
python backend/main.py --demo-mode

# Run integration demo
python demo_system_integration.py
```

### Screenshot Preparation

See `screenshot_preparation.json` for detailed instructions on creating demonstration screenshots.

## Demo Scenarios

The demo data includes several user scenarios:

1. **First Time User**: New user exploring the PWA
2. **Performance Investigation**: User investigating system issues
3. **Regular Monitoring**: Daily system health check routine

Each scenario includes realistic user interactions and expected outcomes.
