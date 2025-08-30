# Gemini Code Assistant Context

This document provides context for the AI assistant to effectively help with development tasks in the Mtronaut project.

## Project Overview

Mtronaut is a web-based network analysis interface that allows users to run diagnostic tools like `mtr`, `ping`, `traceroute`, and `tracepath` from a browser. It streams the real-time terminal output to a virtual terminal powered by xterm.js.

The project is designed to provide a clean, real-time view of network tool output without requiring direct shell access.

### Architecture

-   **Backend**: A Python application built with **FastAPI**. It handles:
    -   Serving the static frontend files.
    -   A WebSocket endpoint (`/ws`) for real-time communication.
    -   Spawning network tools in a **pseudo-terminal (PTY)** using the `ptyprocess` library. This is crucial for supporting interactive, curses-based tools like `mtr`.
    -   Managing user sessions and ensuring running tool processes are cleaned up on disconnect.
-   **Frontend**: A single-page application built with **vanilla JavaScript, HTML, and CSS**.
    -   Uses **xterm.js** to provide a full-featured terminal emulator in the browser.
    -   Communicates with the backend via WebSockets to receive the raw terminal stream.
    -   Dynamically renders UI elements for tool selection and parameter configuration.
-   **Communication**: The frontend and backend communicate over a WebSocket connection. The client sends JSON messages to start/stop tools, and the server streams raw terminal output back.

## Building and Running

The project uses [Poetry](https://python-poetry.org/) for dependency management.

### 1. Setup

First, install the dependencies from the `pyproject.toml` file:

```bash
poetry install
```

### 2. Running the Application

To run the development server, which includes the FastAPI backend and serves the frontend:

```bash
poetry run uvicorn backend.mtronaut.main:app --reload --port 8000
```

The application will be available at `http://127.0.0.1:8000`.

### 3. Running Tests

The project uses `pytest` for testing. To run the entire test suite:

```bash
poetry run pytest
```

For faster execution, tests can be run in parallel:

```bash
poetry run pytest -n auto
```

## Development Conventions

### Code Style

-   **Python**: Follows the PEP 8 style guide, with a maximum line length of 88 characters (enforced by a tool like Black, though not explicitly configured in `pyproject.toml`). Type hints are encouraged.
-   **JavaScript**: Uses 2-space indentation, camelCase for variables/functions, and PascalCase for classes.
-   **HTML/CSS**: Uses 2-space indentation and kebab-case for CSS class names.

### Commit Messages

Commit messages must follow a specific format to maintain a clean git history.

**Structure:**

```
type(scope): brief description

- First bullet point
- Second bullet point
```

-   **Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
-   **Scope**: The part of the codebase affected (e.g., `api`, `ui`, `docs`, `tests`).
-   **Rules**:
    -   Use imperative, present tense (e.g., "add" not "added").
    -   Subject line must be under 50 characters and lowercase.
    -   Body lines should wrap at 72 characters.
    -   Use hyphens for bullet points, with no empty lines between them.

**Example:**

```
feat(api): add auto-target detection endpoint

- Add new REST endpoint /api/client-ip to retrieve client's IP address
- Modify WebSocket handler to automatically use client's IP when no target provided
```

### Testing

-   New features and bug fixes should include corresponding tests.
-   The test suite is located in the `tests/` directory and includes unit, integration, and edge case tests.
-   Tests are written using `pytest` and leverage `pytest-asyncio` for asynchronous code.

## Important Project Documentation

The `docs/` folder contains crucial information about the project's architecture, design decisions, and conventions. Key files include:

-   `architecture.md`: A detailed overview of the system architecture, components, and data flow.
-   `agents.md`: Specific guidelines for AI agents, including detailed commit message formatting rules.
-   `contributing.md`: A guide for developers on how to contribute to the project.
-   `pty-terminal-research.md`: Research notes on the PTY implementation, which is a core part of this project.
-   `todo.md`: The project's task list, which gives insight into the development history and future plans.