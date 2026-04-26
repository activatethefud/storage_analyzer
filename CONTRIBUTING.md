# Contributing to Storage Analyzer

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/activatethefud/storage_analyzer
cd storage_analyzer

# Install in development mode
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_suggestions.py -v
```

## Code Style

- Use type hints
- Add docstrings to public functions
- Keep functions small and focused
- Always write tests for new features

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure everything passes
5. Submit a pull request

## Reporting Issues

Please include:
- Python version
- Linux distribution
- Steps to reproduce
- Expected vs actual behavior