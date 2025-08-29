# Contributing to Mtronaut

Thank you for your interest in contributing to Mtronaut! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### Development Environment Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/mtronaut.git
   cd mtronaut
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Run the development server:
   ```bash
   poetry run uvicorn backend.mtronaut.main:app --reload
   ```

## Project Structure

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
└── README.md             # Project overview
```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them following our [commit message conventions](#commit-messages)

3. Run tests to ensure nothing is broken:
   ```bash
   poetry run pytest
   ```

4. Push your branch and open a pull request

## Coding Standards

### Python Code

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Write clear, self-documenting code
- Keep functions and classes focused on a single responsibility

### JavaScript Code

- Use modern ES6+ features
- Follow consistent indentation (2 spaces)
- Write modular, reusable code

### HTML/CSS

- Semantic HTML structure
- Mobile-responsive design
- Accessible UI components

## Testing

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

### Test Categories

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test the interaction between components
- **WebSocket Tests**: Test real-time communication functionality
- **Edge Case Tests**: Test boundary conditions and error handling

### Code Quality

- The project uses pytest with several plugins for testing:
  - `pytest-asyncio` for async tests
  - `pytest-cov` for coverage reporting
  - `pytest-xdist` for parallel test execution
  - `pytest-timeout` to prevent hanging tests

- Tests are configured to run with a timeout of 11 seconds to prevent hanging
- Specific warnings are filtered out in `pytest.ini` for known non-actionable issues

## Documentation

- Keep the README.md up to date with user-facing changes
- Document new features in the appropriate files in the `docs/` directory
- Update docstrings for new or modified functions and classes
- Ensure documentation is clear, concise, and grammatically correct

## Commit Messages

We follow a structured commit message format to maintain a clean and readable git history:

### Format

```
type(scope): brief description

 detailed description (optional)
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries

### Scope

The scope should be the part of the codebase that was affected (e.g., `api`, `ui`, `docs`, `tests`).

### Examples

```
feat(api): add auto-target detection endpoint

- Add new REST endpoint /api/client-ip to retrieve client's IP address
- Modify WebSocket handler to automatically use client's IP when no target provided
- Update frontend to fetch and display client's IP in target field by default
```

```
fix(ui): prevent terminal content overwriting

- Add dedicated status bar with connection and tool status indicators
- Separate status messages from terminal output to prevent content overwriting
- Improve notification positioning to top-right corner
```

```
docs: add comprehensive developer section to README.md

- Add detailed 'For Developers' section with project structure
- Document development environment setup with Poetry
- Include instructions for running tests
- Add code quality practices and contributing guidelines
- Improve onboarding experience for new developers
```

### Best Practices

1. Use the imperative, present tense ("change" not "changed" or "changes")
2. Don't capitalize the first letter of the subject line
3. No period at the end of the subject line
4. Keep the subject line under 50 characters
5. Use a blank line between the subject and body
6. Wrap the body at 72 characters
7. Use the body to explain what and why, not how

## Pull Requests

1. **Title**: Use a descriptive title that summarizes the changes

2. **Description**: Include a detailed description of:
   - What changes were made
   - Why these changes were necessary
   - How these changes were implemented
   - Any potential side effects or breaking changes

3. **Related Issues**: Reference any related issues using GitHub's closing keywords (e.g., "Closes #123")

4. **Checklist**:
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] Code follows project standards
   - [ ] Commit messages follow conventions

5. **Review Process**:
   - All PRs require review before merging
   - Address all review comments
   - Squash fixup commits after review

## Getting Help

If you need help or have questions:

1. Check existing issues and pull requests
2. Open a new issue with your question
3. Be as detailed as possible in your description

Thank you for contributing to Mtronaut!