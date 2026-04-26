"""Directory and file scanning utilities."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    size: int
    is_dir: bool


def scan_directory(path: str, max_depth: Optional[int] = None) -> Iterator[FileInfo]:
    """
    Scan a directory recursively and yield file information.
    
    Args:
        path: Root directory to scan
        max_depth: Maximum depth to traverse (None for unlimited)
    
    Yields:
        FileInfo for each file/directory encountered
    """
    root = Path(path).resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    if not root.is_dir():
        yield FileInfo(str(root), os.path.getsize(root), False)
        return
    
    def walk_recursive(current: Path, depth: int):
        if max_depth is not None and depth > max_depth:
            return
        
        try:
            for entry in os.scandir(current):
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    size = 0 if is_dir else entry.stat(follow_symlinks=False).st_size
                    yield FileInfo(entry.path, size, is_dir)
                    if is_dir:
                        yield from walk_recursive(Path(entry.path), depth + 1)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            return
    
    yield from walk_recursive(root, 0)


def get_directory_size(path: str) -> int:
    """Get total size of a directory in bytes."""
    total = 0
    for info in scan_directory(path):
        total += info.size
    return total


def get_largest_files(path: str, top: int = 10) -> list[FileInfo]:
    """Get the largest files in a directory."""
    files = []
    for info in scan_directory(path):
        if not info.is_dir:
            files.append(info)
    
    files.sort(key=lambda x: x.size, reverse=True)
    return files[:top]


def get_largest_directories(path: str, top: int = 10) -> list[tuple[str, int]]:
    """Get the largest directories by total size."""
    dir_sizes: dict[str, int] = {}
    
    for info in scan_directory(path):
        parent = str(Path(info.path).parent)
        if parent not in dir_sizes:
            dir_sizes[parent] = 0
        dir_sizes[parent] += info.size
    
    sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)
    return sorted_dirs[:top]
