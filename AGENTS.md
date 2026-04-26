# Storage Analyzer - Development Guide

## Project Structure

```
storage_analyzer/
├── storage_analyzer/
│   ├── __init__.py
│   ├── main.py          # CLI entry point (Click + Rich)
│   ├── scanner.py       # Directory traversal
│   ├── analyzer.py      # Size calculation
│   ├── suggestions.py   # Cleanup recommendations
│   └── utils.py         # Helpers (size formatting, etc.)
├── tests/
│   ├── test_scanner.py
│   ├── test_analyzer.py
│   ├── test_suggestions.py
│   ├── test_utils.py
│   └── test_main.py
├── pyproject.toml
└── README.md
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Adding New Cleanable Items

To add new cleanable items detection:

1. Edit `storage_analyzer/suggestions.py`
2. Add the path to `cleanable_paths` list in `get_user_cleanable_items()`
3. Follow the pattern: `(relative_path, name, command)`
4. Add tests in `tests/test_suggestions.py`

## Adding New CLI Commands

To add new commands:

1. Edit `storage_analyzer/main.py`
2. Add new function with `@cli.command()` decorator
3. Use Rich tables and panels for output
4. Add tests in `tests/test_main.py`

## Code Style

- Use type hints
- Add docstrings to public functions
- Keep functions small and focused
- Always write tests for new features
