# AI Agent Guidelines

This document provides guidelines for AI agents working with the Mtronaut codebase.

## Commit Message Formatting

When making commits, please follow these specific formatting rules to ensure consistency with the project's conventions:

### Structure

```
type(scope): brief description

- First bullet point
- Second bullet point
- Additional bullet points...
```

### Key Formatting Rules

1. **No empty lines between bullet points** - All bullet points should be directly sequential
2. **Use hyphens for bullet points** - Not asterisks or other markers
3. **One bullet point per line** - Each bullet point should be on its own line
4. **Start with imperative verb** - Use present tense ("add" not "adds" or "added")
5. **Subject line under 50 characters** - Keep the main description concise
6. **Body lines under 72 characters** - Wrap longer text appropriately

### Technical Note: Creating Multi-line Commits Correctly

When using `git commit` with the `-m` flag for multi-line commit messages, use a single `-m` flag with literal newlines in the string:

```bash
# CORRECT: Single -m flag with newlines
git commit -m "docs: add comprehensive contributing guide" -m "- Add detailed contributing guide with development workflow
- Document coding standards, testing practices, and commit conventions
- Standardize documentation file naming with hyphens
- Update README to reference contributing guide in docs folder"
```

Avoid using multiple `-m` flags for bullet points as this creates unwanted empty lines:

```bash
# INCORRECT: Multiple -m flags create empty lines between bullet points
git commit -m "docs: add comprehensive contributing guide" -m "- Add detailed contributing guide" -m "- Document coding standards"
```

For longer commit messages, you can also use `git commit` without `-m` flags and write the message in the default text editor:

```bash
# Alternative: Use editor for complex commit messages
git commit
```

### Examples

#### Correct Format:
```
docs: add comprehensive contributing guide and standardize documentation

- Add detailed contributing guide with development workflow
- Document coding standards, testing practices, and commit conventions
- Standardize documentation file naming with hyphens
- Update README to reference contributing guide in docs folder
```

#### Incorrect Formats:
```
# DON'T: Empty lines between bullet points
docs: add comprehensive contributing guide

- Add detailed contributing guide

- Document coding standards
```

```
# DON'T: All bullet points on one line
docs: add comprehensive contributing guide

- Add detailed contributing guide - Document coding standards
```

```
# DON'T: Using asterisks instead of hyphens
docs: add comprehensive contributing guide

* Add detailed contributing guide
* Document coding standards
```

## File Naming Conventions

- Use lowercase for all documentation files
- Use hyphens (-) instead of underscores (_) to separate words
- Use .md extension for Markdown files

### Examples

#### Correct:
- docs/contributing.md
- docs/deployment-systemd.md
- docs/architecture.md

#### Incorrect:
- docs/CONTRIBUTING.md
- docs/deployment_systemd.md
- docs/architecture.MD

## Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length of 88 characters (Black formatter standard)
- Use type hints where possible

### JavaScript
- Use 2 spaces for indentation
- Use camelCase for variables and functions
- Use PascalCase for constructors and classes

### HTML/CSS
- Use 2 spaces for indentation
- Use hyphens for CSS class names (kebab-case)
- Semantic HTML structure

## Testing

When adding new features or fixing bugs, ensure appropriate tests are included:

1. Unit tests for individual functions
2. Integration tests for component interactions
3. Edge case tests for boundary conditions
4. Update existing tests if functionality changes

Run tests with:
```bash
poetry run pytest
```

## Documentation Updates

When making changes that affect user-facing functionality:

1. Update README.md if necessary
2. Add or modify appropriate files in the docs/ directory
3. Ensure docstrings are updated for new or modified functions
4. Keep documentation clear and concise