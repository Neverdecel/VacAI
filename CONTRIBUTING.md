# Contributing to VacAI

Thank you for your interest in contributing to VacAI! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Docker version if applicable)
- **Relevant logs or error messages**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description** of the proposed feature
- **Use cases** explaining why this would be valuable
- **Possible implementation approach** (optional)

### Pull Requests

We actively welcome your pull requests! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests as needed
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/vacai.git
   cd vacai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

4. **Set up environment variables**
   ```bash
   cp config/.env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Run tests** (when available)
   ```bash
   pytest
   ```

### Docker Development

```bash
# Build local image
docker build -t vacai:dev .

# Test the image
docker run --rm vacai:dev python --version
```

## Pull Request Process

1. **Update documentation** - Ensure README.md and other docs reflect your changes
2. **Add tests** - Add tests for new features or bug fixes
3. **Follow style guidelines** - Use Black for formatting, follow PEP 8
4. **Write clear commit messages** - Use conventional commit format when possible
5. **Update CHANGELOG** - Add entry describing your changes (when applicable)
6. **Squash commits** - Clean up commit history before merging

### PR Title Format

Use conventional commit format for PR titles:
- `feat: Add new feature`
- `fix: Fix bug in job scoring`
- `docs: Update installation guide`
- `refactor: Restructure database module`
- `test: Add tests for resume analyzer`
- `chore: Update dependencies`

## Style Guidelines

### Python Code Style

- **Formatting**: Use [Black](https://black.readthedocs.io/) for code formatting
  ```bash
  black .
  ```

- **Imports**: Use [isort](https://pycqa.github.io/isort/) for import sorting
  ```bash
  isort .
  ```

- **Linting**: Follow PEP 8, use [Flake8](https://flake8.pycqa.org/)
  ```bash
  flake8 src/
  ```

- **Type hints**: Use type hints where possible for better code clarity

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

### Documentation

- Use clear, concise language
- Include code examples where helpful
- Update README.md if adding user-facing features
- Document all public functions and classes
- Use docstrings following Google or NumPy style

## Code Review Process

- All submissions require review before merging
- Maintainers may ask for changes or improvements
- Be open to feedback and constructive criticism
- Reviews typically happen within 3-5 business days

## Development Guidelines

### Adding New Features

1. **Discuss first** - Open an issue to discuss major features before implementing
2. **Keep PRs focused** - One feature/fix per PR when possible
3. **Add tests** - Ensure new code is covered by tests
4. **Update docs** - Document new features and configuration options

### Modifying Existing Features

1. **Maintain backward compatibility** when possible
2. **Add deprecation warnings** before removing features
3. **Update migration guides** for breaking changes

### Working with AI/LLM Features

- **Be mindful of API costs** when adding features that call OpenAI
- **Add configuration options** for model selection and parameters
- **Include error handling** for API failures and rate limits
- **Test with different models** when possible

## Project Structure

```
vacai/
├── src/
│   ├── agents/          # AI agents (resume analyzer, job scorer)
│   ├── cli/             # CLI commands and interfaces
│   ├── database/        # Database models and managers
│   ├── notifier/        # Notification services (Telegram, etc.)
│   └── scraper/         # Job scraping logic
├── config/              # Configuration files and examples
├── tests/               # Test suite
├── docs/                # Documentation
└── k8s/                 # Kubernetes manifests
```

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting PR
- Aim for high code coverage on critical paths
- Include integration tests for major features

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_resume_analyzer.py
```

## Getting Help

- **Documentation**: Check existing docs in `/docs` and README.md
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions and ideas

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special thanks in README.md for major features

Thank you for contributing to VacAI!
