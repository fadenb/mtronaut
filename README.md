# 🚀 Mtronaut: Your Web-Based Network Diagnostics Hub

Welcome to Mtronaut! This project delivers a modern, real-time web interface for essential network diagnostic tools like `mtr`, `tracepath`, `ping`, and `traceroute`. Say goodbye to command-line juggling and hello to seamless, interactive network analysis right in your browser.

## ✨ Features

*   **CI/CD**: Fully automated testing with GitHub Actions. [![CI](https://github.com/fadenb/mtronaut/actions/workflows/test.yml/badge.svg)](https://github.com/fadenb/mtronaut/actions/workflows/test.yml)
*   **Real-time Output Streaming**: Live terminal output directly to your browser. ⚡
*   **Interactive Terminal**: Powered by xterm.js for a true terminal experience with ANSI colors. 🌈
*   **Robust Session Management**: Run multiple diagnostic sessions concurrently. 📊
*   **Dynamic Resizing**: Terminal adapts to your browser window size. 📏
*   **Clipboard Integration**: Easily copy output for analysis or sharing. 📋
*   **Connection Recovery**: Smart reconnection logic for uninterrupted monitoring. 🔗
*   **Auto-Target Detection**: Automatically detects and uses your IP address for diagnostics. 🎯

## 🛠️ Tech Stack

*   **Backend**: Python 🐍, FastAPI, Uvicorn, WebSockets, `ptyprocess`
*   **Frontend**: Vanilla JavaScript, HTML, CSS, xterm.js

## ⚡ Quick Start

1.  **Clone the repository:**
    `git clone https://github.com/fadenb/mtronaut.git`
    `cd mtronaut`
2.  **Backend Setup:**
    `poetry install`
    `poetry run uvicorn backend.mtronaut.main:app --reload`
3.  **Access Frontend:** Open `http://localhost:8000` in your browser.

## 👨‍💻 For Developers

### Project Structure

```
mtronaut/
├── backend/              # Backend source code
│   └── mtronaut/         # Main Python package
│       ├── main.py       # FastAPI application entry point
│       ├── session.py    # Session management
│       ├── terminal.py   # Terminal handling with PTY
│       └── tools.py      # Network tool configurations
├── frontend/             # Frontend source code
│   ├── index.html        # Main HTML file
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── tests/                # Test suite
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration and dependencies
└── README.md             # This file
```

### Development Environment Setup

1. **Prerequisites:**
   - Python 3.9 or higher
   - [Poetry](https://python-poetry.org/docs/#installation) for dependency management

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Run the development server:**
   ```bash
   poetry run uvicorn backend.mtronaut.main:app --reload
   ```

### Running Tests

Mtronaut uses pytest for testing with several plugins for enhanced functionality:

```bash
# Run all tests
poetry run pytest

# Run tests in parallel for faster execution
poetry run pytest -n auto

# Run tests with coverage report
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_api.py
```

The test suite includes unit tests, integration tests, and edge case testing to ensure the reliability of the application.

### Code Quality

- The project uses pytest with several plugins for testing:
  - `pytest-asyncio` for async tests
  - `pytest-cov` for coverage reporting
  - `pytest-xdist` for parallel test execution
  - `pytest-timeout` to prevent hanging tests

- Tests are configured to run with a timeout of 11 seconds to prevent hanging
- Specific warnings are filtered out in `pytest.ini` for known non-actionable issues

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request

Please ensure your code follows the existing style and includes appropriate tests.

## 💡 Why Mtronaut?

Ever found yourself troubleshooting a network issue, only to be met with "it's slow" or "the internet is broken" without any useful details? 😩 As someone who often helps with network woes, I know the struggle! Mtronaut is here to bridge that information gap. It empowers users (and those helping them!) to quickly gather precise, real-time network diagnostic data, making "what's going on?" a question with an immediate, clear answer. Get the insights you need to pinpoint problems, fast. 🎯