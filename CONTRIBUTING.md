# Contributing to SuperVincent InvoiceBot

Thank you for your interest in contributing to SuperVincent InvoiceBot! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct. By participating, you agree to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Docker (optional)
- Redis (for development)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/supervincent-invoicebot.git
   cd supervincent-invoicebot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Setup Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Run Tests**
   ```bash
   pytest
   ```

## Contributing Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow our coding standards
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

```bash
git add .
git commit -m "feat: add new invoice parser"
```

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Code Organization

```
src/
├── core/           # Business logic, models, parsers
├── services/       # Service layer (API, tax, etc.)
├── api/           # API endpoints (future)
└── utils/         # Utilities
```

### Naming Conventions

- **Classes**: PascalCase (`InvoiceProcessor`)
- **Functions/Variables**: snake_case (`process_invoice`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`)
- **Private methods**: Leading underscore (`_parse_invoice`)

### Documentation

- Use docstrings for all public functions/classes
- Follow Google docstring format
- Include type hints for all parameters and return values

Example:
```python
def process_invoice(self, file_path: str) -> ProcessingResult:
    """Process invoice file end-to-end.
    
    Args:
        file_path: Path to invoice file (PDF, JPG, PNG)
        
    Returns:
        ProcessingResult with success status and data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
```

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test data
└── conftest.py    # Pytest configuration
```

### Writing Tests

1. **Unit Tests**: Test individual functions/classes
2. **Integration Tests**: Test service interactions
3. **E2E Tests**: Test complete workflows

Example unit test:
```python
def test_parse_pdf_invoice():
    """Test PDF invoice parsing."""
    parser = PDFParser()
    result = parser.parse("tests/fixtures/sample_invoice.pdf")
    
    assert result is not None
    assert result.invoice_type == InvoiceType.PURCHASE
    assert result.total > 0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_parsers.py

# Run with specific marker
pytest -m "not slow"
```

### Test Coverage

- Minimum 80% code coverage required
- New code must have tests
- All tests must pass before merging

## Documentation

### Code Documentation

- Use docstrings for all public APIs
- Include examples in docstrings
- Document complex algorithms
- Explain business logic

### User Documentation

- Update README.md for user-facing changes
- Add/update API documentation
- Include migration guides for breaking changes

### Developer Documentation

- Document architecture decisions
- Explain design patterns used
- Provide setup/development guides

## Pull Request Guidelines

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Check Coverage**: Maintain 80%+ coverage
3. **Lint Code**: Run `black`, `isort`, `flake8`
4. **Type Check**: Run `mypy`
5. **Update Docs**: Update relevant documentation

### PR Description

Include:
- **What**: Brief description of changes
- **Why**: Motivation for the change
- **How**: Implementation details
- **Testing**: How you tested the changes
- **Breaking Changes**: Any breaking changes

### Review Process

1. **Automated Checks**: CI/CD pipeline runs
2. **Code Review**: At least one reviewer required
3. **Testing**: Manual testing for complex changes
4. **Documentation**: Ensure docs are updated

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update Version**: Update version in `pyproject.toml`
2. **Update Changelog**: Add entry to `CHANGELOG.md`
3. **Create Tag**: `git tag v1.0.0`
4. **Push Tag**: `git push origin v1.0.0`
5. **GitHub Release**: Create release on GitHub

## Getting Help

- **Documentation**: Check README.md and docs/
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **Email**: dev@supervincent.com

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to SuperVincent InvoiceBot! 🚀
