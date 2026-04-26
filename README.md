# Storage Analyzer

A CLI tool to analyze storage space on Linux and get actionable cleanup suggestions.

## Features

- **Scan directories** - See size breakdown by subdirectories
- **Find largest files** - Identify the biggest files consuming space
- **Find largest directories** - See which directories use the most space
- **List cleanable items** - Detect caches, logs, and other cleanable items
- **Get suggestions** - Actionable recommendations with copy-paste commands

## Safety

This tool is **read-only by default**:
- All analysis commands only read data
- Suggestions provide **commands to run manually**
- No files are automatically deleted

## Installation

```bash
pip install -e .
```

## Usage

### Scan a directory
```bash
storage-analyzer scan /home
storage-analyzer scan . --depth 3
```

### Find largest files
```bash
storage-analyzer large-files /home
storage-analyzer large-files /home --top 20
```

### Find largest directories
```bash
storage-analyzer large-dirs /home
storage-analyzer large-dirs /home --top 5
```

### List cleanable items
```bash
storage-analyzer clean
```

### Get cleanup suggestions
```bash
storage-analyzer suggest
```

### Show disk usage
```bash
storage-analyzer disk
```

## Detected Cleanable Items

- pip cache (~/.cache/pip)
- npm cache (~/.cache/npm)
- yarn cache (~/.cache/yarn)
- Thumbnail cache (~/.cache/thumbnails)
- Firefox cache (~/.cache/mozilla/firefox)
- Chrome cache (~/.cache/google-chrome)
- Trash (~/.local/share/Trash)
- Docker unused images

## Development

### Run tests
```bash
python -m pytest tests/ -v
```

## License

MIT
