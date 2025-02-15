# virtual-env

Build-Python environment management. 

## Overview

`virtual-env` virtual environment lifecicle management, create, remove, execute calls on the fly.

## Features

- Easy virtual environment creation and management
- Automatic environment loading and consistency checking
- Cross-platform support (Windows and Unix-like systems)
- Command execution within virtual environments
- Detailed logging and error handling
- Configuration-based environment validation

## Installation

```bash
pip install .
```

## Usage

### Basic Virtual Environment Management

```python
from virtual_env.env_manager import VirtualEnvironmentManager

# Create a virtual environment
venv_manager = VirtualEnvironmentManager(".venv")
venv_manager.create()

# Run commands within the virtual environment
venv_manager.run_command("pip", "install", "requests")

# Check environment consistency
is_consistent = venv_manager.check_consistency()
```

### Advanced Usage with Context Manager

```python
with VirtualEnvironmentManager(".venv") as venv_manager:
    # Automatically loads the environment
    venv_manager.run_command("python", "-m", "pip", "list")
```

## Key Methods

- `create()`: Create a new virtual environment
- `exists()`: Check if the virtual environment exists
- `remove()`: Remove the virtual environment
- `run_command()`: Execute commands within the virtual environment
- `check_consistency()`: Validate the virtual environment configuration

## Development Setup

1. Users:
```bash
pip install .
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- pip

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## License

[MIT](LICENSE)