"""Storage analysis logic."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from storage_analyzer.scanner import (
    scan_directory, get_largest_files, get_largest_directories, FileInfo
)
from storage_analyzer.utils import format_size, get_disk_usage


@dataclass
class DirectorySize:
    """Directory with its total size."""
    path: str
    size: int
    
    @property
    def formatted_size(self) -> str:
        return format_size(self.size)


@dataclass
class AnalysisResult:
    """Result of storage analysis."""
    root_path: str
    total_size: int
    file_count: int
    dir_count: int
    largest_files: list[FileInfo]
    largest_dirs: list[DirectorySize]


def analyze_directory(path: str, max_depth: Optional[int] = None) -> AnalysisResult:
    """
    Analyze a directory and return comprehensive statistics.
    
    Args:
        path: Directory to analyze
        max_depth: Maximum depth to scan
        
    Returns:
        AnalysisResult with statistics
    """
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    total_size = 0
    file_count = 0
    dir_count = 0
    
    for info in scan_directory(path, max_depth=max_depth):
        if info.is_dir:
            dir_count += 1
        else:
            file_count += 1
            total_size += info.size
    
    largest_files = get_largest_files(path, top=10)
    
    raw_dirs = get_largest_directories(path, top=10)
    largest_dirs = [DirectorySize(p, s) for p, s in raw_dirs]
    
    return AnalysisResult(
        root_path=str(root),
        total_size=total_size,
        file_count=file_count,
        dir_count=dir_count,
        largest_files=largest_files,
        largest_dirs=largest_dirs
    )


def get_path_disk_usage(path: str) -> dict:
    """
    Get disk usage for the filesystem containing the path.
    
    Args:
        path: Any path on the filesystem to check
        
    Returns:
        Dictionary with total, used, free keys
    """
    total, used, free = get_disk_usage(path)
    return {
        "total": total,
        "used": used,
        "free": free,
        "total_formatted": format_size(total),
        "used_formatted": format_size(used),
        "free_formatted": format_size(free),
        "percent_used": round((used / total) * 100, 1) if total > 0 else 0
    }


def scan_directory_tree(path: str, depth: int = 2) -> list[DirectorySize]:
    """
    Scan directory tree and return sizes for each subdirectory.
    
    Args:
        path: Root directory
        depth: How deep to scan
        
    Returns:
        List of DirectorySize objects sorted by size
    """
    results = []
    root = Path(path).resolve()
    
    if not root.is_dir():
        return [DirectorySize(str(root), 0)]
    
    for entry in os.scandir(root):
        try:
            if entry.is_dir(follow_symlinks=False):
                size = sum(
                    f.stat(follow_symlinks=False).st_size
                    for f in Path(entry.path).rglob('*')
                    if f.is_file()
                )
                results.append(DirectorySize(entry.path, size))
        except (PermissionError, OSError):
            continue
    
    results.sort(key=lambda x: x.size, reverse=True)
    return results
