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

## 💡 Why Mtronaut?

Ever found yourself troubleshooting a network issue, only to be met with "it's slow" or "the internet is broken" without any useful details? 😩 As someone who often helps with network woes, I know the struggle! Mtronaut is here to bridge that information gap. It empowers users (and those helping them!) to quickly gather precise, real-time network diagnostic data, making "what's going on?" a question with an immediate, clear answer. Get the insights you need to pinpoint problems, fast. 🎯