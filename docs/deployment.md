# Mtronaut Deployment and Setup Guide

This guide provides instructions on how to set up and run the Mtronaut application.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python 3.9+**: Mtronaut's backend is built with Python.
*   **Poetry**: Used for Python dependency management. Install it via `pip install poetry` or refer to the [Poetry documentation](https://python-poetry.org/docs/#installation).
*   **System Network Tools**: Ensure `mtr`, `ping`, `traceroute`, and `tracepath` are installed and available in your system's PATH. These are typically pre-installed on most Linux distributions.

## Setup Instructions

### 1. Clone the Repository

First, clone the Mtronaut repository to your local machine:

```bash
git clone https://github.com/fadenb/mtronaut.git
cd mtronaut
```

### 2. Install Dependencies

Install Python dependencies using Poetry from the project root directory:

```bash
poetry install
```

### 3. Running the Application

The FastAPI backend serves both the API/WebSocket and the static frontend files.

1.  **Start the Backend (API, WebSocket, and Static File Server)**
    From the project root directory:
    ```bash
    poetry run uvicorn backend.mtronaut.main:app --reload --port 8000
    ```
    This will start the FastAPI server, typically accessible at `http://127.0.0.1:8000`. The `--reload` flag is useful for development as it automatically reloads the server on code changes.

## Accessing the Application

Once the application is running, open your web browser and navigate to:

`http://127.0.0.1:8000`

You should see the Mtronaut interface.