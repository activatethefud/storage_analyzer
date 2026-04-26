"""Utility functions for storage analyzer."""
import os
from pathlib import Path
from typing import Optional


def format_size(bytes_size: int) -> str:
    """
    Format bytes into human-readable size string.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string like "1.5 MB" or "500 KB"
    """
    if bytes_size < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_size)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def get_home_directory() -> str:
    """Get user's home directory."""
    return os.path.expanduser("~")


def sanitize_path(path: str, base: Optional[str] = None) -> str:
    """
    Sanitize a path to prevent directory traversal.
    
    Args:
        path: Path to sanitize
        base: Base directory to restrict to (default: current directory)
    
    Returns:
        Sanitized absolute path
        
    Raises:
        ValueError: If path attempts to escape base directory
    """
    resolved = Path(path).resolve()
    
    if base:
        base_path = Path(base).resolve()
        try:
            resolved.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Path '{path}' escapes base directory '{base}'")
    
    return str(resolved)


def is_safe_to_delete(path: str) -> bool:
    """
    Check if a path is generally safe to consider for deletion.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is in a known safe-to-clean location
    """
    path_obj = Path(path).resolve()
    home = Path.home()
    
    safe_patterns = [
        home / ".cache",
        home / ".local" / "share" / "Trash",
    ]
    
    for pattern in safe_patterns:
        try:
            path_obj.relative_to(pattern)
            return True
        except ValueError:
            continue
    
    return False


def get_disk_usage(path: str) -> tuple[int, int, int]:
    """
    Get disk usage statistics for a path.
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (total, used, free) in bytes
    """
    stat = os.statvfs(path)
    total = stat.f_blocks * stat.f_frsize
    free = stat.f_bfree * stat.f_frsize
    used = total - free
    return (total, used, free)
