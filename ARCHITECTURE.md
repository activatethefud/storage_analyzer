# Storage Analyzer Architecture

## Overview

Storage Analyzer is a CLI tool for analyzing disk space usage on Linux systems and providing cleanup suggestions. It supports multiple Linux distributions and package managers.

## Module Structure

```
storage_analyzer/
├── main.py          # CLI entry point (Click + Rich)
├── scanner.py       # Directory traversal and file discovery
├── analyzer.py      # Size calculation and analysis
├── suggestions.py   # Cleanup recommendations with distro-aware commands
└── utils.py         # Helpers (size formatting, distro detection, device info)
```

## Module Responsibilities

### main.py
- CLI commands using Click framework
- Rich console output (tables, panels, progress bars)
- Commands: scan, large-files, large-dirs, clean, suggest, disk, drives

### scanner.py
- `scan_directory()` - Recursive directory scanning with depth control
- `get_largest_files()` - Find largest files
- `get_largest_directories()` - Find largest directories by size

### analyzer.py
- `analyze_directory()` - Comprehensive directory analysis
- `get_path_disk_usage()` - Get disk usage for a path
- `scan_directory_tree()` - Tree-style directory scanning

### suggestions.py
- `get_user_cleanable_items()` - User-specific caches (pip, npm, yarn, thumbnails)
- `get_docker_items()` - Docker cleanup
- `get_package_cleanup_suggestions()` - Package manager cleanup (distro-aware)
- `get_system_cleanup_suggestions()` - System cleanup (journal, kernels)

### utils.py
- `format_size()` - Human-readable size formatting
- `get_home_directory()` - Get user home directory
- `get_all_devices()` - List block devices
- `detect_package_managers()` - Detect available package managers
- Device validation and disk usage utilities

## Package Manager Support

The tool detects and provides cleanup commands for multiple package managers:

| Manager | Detection | Clean Command | Autoremove | Old Kernels |
|---------|-----------|---------------|------------|-------------|
| apt | `which apt` | `apt-get clean` | `apt-get autoremove` | `apt-get autoremove --purge` |
| dnf | `which dnf` | `dnf clean all` | `dnf autoremove` | `dnf remove oldest-kernel` |
| pacman | `which pacman` | `pacman -Scc` | `pacman -Rsn $(pacman -Qtdq)` | (auto by pacman) |
| zypper | `which zypper` | `zypper clean` | `zypper rm -u` | `zypper rm -u kernel-*` |
| apk | `which apk` | `apk clean` | `apk del -r $(apk info -e)` | `apk del linux-lts` |
| flatpak | `which flatpak` | `flatpak remove --unused` | - | - |
| snap | `which snap` | `snap list --all` | - | - |
| docker | `which docker` | `docker image prune -a` | - | - |

## Distro Detection

Primary distro detection reads from `/etc/os-release`:
- `ID` field (e.g., ubuntu, fedora, arch, opensuse, alpine)
- `ID_LIKE` field for derivatives (e.g., debian for ubuntu)

Package manager detection uses `which <command>` to find available managers.

## Cleanable Items Categories

1. **User caches**: pip, npm, yarn, thumbnails, browser caches
2. **Package managers**: apt, dnf, pacman, zypper, apk, flatpak, snap
3. **Containers**: Docker images
4. **System logs**: journalctl, rotated logs, crash reports
5. **Old kernels**: Distro-specific removal commands

## Testing

Tests are located in `tests/`:
- `test_scanner.py` - Directory scanning tests
- `test_analyzer.py` - Analysis tests
- `test_suggestions.py` - Cleanup suggestion tests
- `test_utils.py` - Utility function tests
- `test_main.py` - CLI command tests

Run tests with: `python3 -m pytest tests/ -v`