# Storage Analyzer

A CLI tool to analyze storage space on Linux and get actionable cleanup suggestions.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        STORAGE ANALYZER                                       ║
║              Analyze storage on Linux and get cleanup suggestions           ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Features

- **Scan directories** - See size breakdown by subdirectories
- **Find largest files** - Identify the biggest files consuming space
- **Find largest directories** - See which directories use the most space
- **List cleanable items** - Detect caches, logs, and other cleanable items
- **Get suggestions** - Actionable recommendations with copy-paste commands
- **Device filtering** - Get suggestions for specific partitions/drives
- **Package manager cleanup** - Suggestions for apt, flatpak, snap, etc.
- **System cleanup** - Journal logs, old kernels, crash reports, etc.

## Quick Demo

### List Drives
```bash
$ storage-analyzer drives

Available Block Devices:

Disk: /dev/sda (238.5G)
  └── /dev/sda1  976M   /boot/efi
  └── /dev/sda2  65.2G  /
  └── /dev/sda3  7.9G   [SWAP]
  └── /dev/sda4  145.3G /home
```

### Get Cleanup Suggestions
```bash
$ storage-analyzer suggest --device /dev/sda2

Analyzing storage for cleanup suggestions on: /dev/sda2 (mounted at /)

⠧ Found 3 suggestions
╭───────────────────── 1. systemd journal logs (160.0 MB) ─────────────────────╮
│ Path: /var/log/journal                                                       │
│                                                                              │
│ Command to run:                                                              │
│ sudo journalctl --vacuum-size=100M                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭────────────────────── 2. APT package cache (132.7 MB) ───────────────────────╮
│ Path: /var/cache/apt                                                         │
│                                                                              │
│ Command to run:                                                              │
│ sudo apt-get clean                                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────── 3. Old kernel images (0 B) ─────────────────────────╮
│ Path: /boot                                                                  │
│                                                                              │
│ Command to run:                                                              │
│ sudo apt-get autoremove --purge                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────── Summary ───────────────────────────────────╮
│ Total potential savings: 292.7 MB                                           ║
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Scan Directory
```bash
$ storage-analyzer scan /home --depth 2

Scanning: /home
Depth: 2

⠸ Scanned 1234 files, 567 directories
╭────────────────────────────────── Summary ───────────────────────────────────╮
│ Total Size: 45.3 GB                                                          │
│ Files: 1234                                                                  │
│ Directories: 567                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

Top Directories:
                                                                                
  Path                                                    Size                   ───────────────────────────────────────────────────────────────────── 
  /home/user/Downloads                            15.2 GB                   
  /home/user/.cache                                8.3 GB                    
  /home/user/Videos                                12.1 GB                    
  ...
```

### Show Disk Usage
```bash
$ storage-analyzer disk

Disk Usage:

  Metric      Value  
 ─────────────────── 
  Total    238.5 GB 
  Used     127.3 GB 
  Free     111.2 GB 
  Usage     53.4%   
```

## Safety

This tool is **read-only by default**:
- All analysis commands only read data
- Suggestions provide **commands to run manually**
- No files are automatically deleted

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           ⚠️  SAFETY NOTE                                     ║
║  All suggestions show commands for you to run MANUALLY.                     ║
║  No files are deleted automatically.                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Installation

```bash
pip install -e .
```

Or run directly:
```bash
python -m storage_analyzer <command>
```

## Usage

### List all drives/partitions
```bash
storage-analyzer drives
```

### Scan a directory
```bash
storage-analyzer scan /home
storage-analyzer scan . --depth 3
storage-analyzer scan /home /tmp
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
storage-analyzer clean                              # All cleanable items
storage-analyzer clean --device /dev/sda2            # Only for root partition
storage-analyzer clean --device /dev/sda4            # Only for /home partition
```

### Get cleanup suggestions
```bash
storage-analyzer suggest                           # All suggestions
storage-analyzer suggest --device /dev/sda2        # Only for root partition
storage-analyzer suggest --device /dev/sda4        # Only for /home partition
```

### Show disk usage
```bash
storage-analyzer disk
```

## How to Filter by Device

1. First, list all available devices:
   ```bash
   storage-analyzer drives
   ```

2. Find the device you want (e.g., `/dev/sda2` for root, `/dev/sda4` for `/home`)

3. Use `--device` option:
   ```bash
   storage-analyzer suggest --device /dev/sda2
   ```

## Detected Cleanable Items

### User Cache Files
- pip cache (~/.cache/pip)
- npm cache (~/.cache/npm)
- yarn cache (~/.cache/yarn)
- Thumbnail cache (~/.cache/thumbnails)
- Firefox cache (~/.cache/mozilla/firefox)
- Chrome cache (~/.cache/google-chrome)
- Trash (~/.local/share/Trash)

### System/Package Manager
- APT package cache (/var/cache/apt)
- APT autoremove candidates
- Deborphan orphaned libraries
- Flatpak unused runtimes
- Docker unused images

### System Cleanup (requires root/sudo)
- systemd journal logs (`journalctl --vacuum-size`)
- Old kernel images (`apt-get autoremove --purge`)
- Crash reports (/var/crash)
- Old rotated log files

## Examples

### Clean up root partition
```bash
# Find root device
storage-analyzer drives

# Get cleanup suggestions for root
storage-analyzer suggest --device /dev/sda2
```

### Clean up home partition
```bash
storage-analyzer suggest --device /dev/sda4
```

### Find what's using space
```bash
storage-analyzer scan /home --depth 2
storage-analyzer large-files /home --top 20
storage-analyzer large-dirs /home --top 10
```

## Development

### Run tests
```bash
python -m pytest tests/ -v
```

### Run specific test
```bash
python -m pytest tests/test_suggestions.py -v
```

## License

MIT

---

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  Thanks for using Storage Analyzer!                                          ║
║  Star us on GitHub: https://github.com/activatethefud/storage_analyzer       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```