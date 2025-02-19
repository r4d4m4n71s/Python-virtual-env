# 🐍 Virtual Environment Manager

[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org/project/virtual-env-manager/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Elevate Your Python Development Workflow

`venv_py` virtual environment lifecycle manager.

---

### ✨ Key Features

- 🚀 **Effortless Environment Management**
  - Create and run commands in virtual environments on the fly
  - Cross-platform support (Windows and Unix-like systems)

- 🔍 **Smart Consistency Checking**
  - Validate environment configurations
  - Ensure package and file integrity

- 🛡️ **Robust Error Handling**
  - Detailed logging
  - Comprehensive error messages

- 🔧 **Flexible Command Execution**
  - Run commands directly within virtual environments
  - Retrieve and inspect command results

---
### Usage

```python
from venv_py import EnvManager

# Installing libraries
EnvManager(".some_env").run("pip", "install", "requests", "pandas").result()

# Reset the state, flushing libraries
EnvManager(".some_env").flush().run("python script.py").result()

```

### Context Manager Usage

```python
with EnvManager(".venv") as venv:
    # Automatic environment lifecycle management
    venv.run("python", "my_script.py").result()
```

## 📦 Requirements

- **Python**: 3.8+
- **Platforms**: Windows, macOS, Linux

---

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. 🔨 Make your changes
4. ✅ Run tests
5. 📤 Submit a pull request

---

## 📄 License

[MIT License](LICENSE) - Free to use, modify, and distribute

---

## 🌈 Powered By

- Pure Python
- Standard Library
- Community Love ❤️
