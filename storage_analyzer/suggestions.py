"""Cleanup suggestions and cleanable item detection."""
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from storage_analyzer.utils import format_size, get_home_directory


@dataclass
class CleanableItem:
    """A cleanable item with size and cleanup command."""
    name: str
    path: str
    size: int
    command: str
    description: str
    
    @property
    def formatted_size(self) -> str:
        return format_size(self.size)
    
    @property
    def is_safe(self) -> bool:
        """Check if this is generally safe to clean."""
        return True


def get_directory_size(path: str) -> int:
    """Get total size of a directory."""
    if not os.path.exists(path):
        return 0
    
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    total += get_directory_size(entry.path)
                else:
                    total += entry.stat(follow_symlinks=False).st_size
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total


def get_user_cleanable_items() -> list[CleanableItem]:
    """
    Find cleanable items in user's home directory.
    
    Returns:
        List of CleanableItem objects
    """
    items = []
    home = Path.home()
    
    cleanable_paths = [
        (".cache/pip", "pip cache", "pip cache clean"),
        (".cache/npm", "npm cache", "npm cache clean --force"),
        (".cache/yarn", "yarn cache", "yarn cache clean"),
        (".cache/thumbnails", "thumbnail cache", "rm -rf ~/.cache/thumbnails"),
        (".local/share/Trash", "trash", "rm -rf ~/.local/share/Trash/*"),
    ]
    
    for relative_path, name, cmd in cleanable_paths:
        full_path = home / relative_path
        if full_path.exists():
            size = get_directory_size(str(full_path))
            if size > 0:
                items.append(CleanableItem(
                    name=name,
                    path=str(full_path),
                    size=size,
                    command=cmd,
                    description=f"Clean {name}"
                ))
    
    firefox_cache = home / ".cache" / "mozilla" / "firefox"
    if firefox_cache.exists():
        size = get_directory_size(str(firefox_cache))
        if size > 0:
            items.append(CleanableItem(
                name="Firefox cache",
                path=str(firefox_cache),
                size=size,
                command="rm -rf ~/.cache/mozilla/firefox/*",
                description="Clean Firefox browser cache"
            ))
    
    chrome_cache = home / ".cache" / "google-chrome"
    if chrome_cache.exists():
        size = get_directory_size(str(chrome_cache))
        if size > 0:
            items.append(CleanableItem(
                name="Chrome cache",
                path=str(chrome_cache),
                size=size,
                command="rm -rf ~/.cache/google-chrome/*",
                description="Clean Chrome browser cache"
            ))
    
    return items


def get_docker_items() -> list[CleanableItem]:
    """Find cleanable Docker items."""
    items = []
    
    try:
        result = subprocess.run(
            ["docker", "images", "-q"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            images = result.stdout.strip().split("\n")
            if len(images) > 0:
                size = 0
                try:
                    size_result = subprocess.run(
                        ["docker", "system", "df"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if size_result.returncode == 0:
                        for line in size_result.stdout.split("\n"):
                            if "Images" in line:
                                parts = line.split()
                                for i, part in enumerate(parts):
                                    if part.isdigit() and i > 0:
                                        size = int(part) * 1024 * 1024
                                        break
                except (subprocess.TimeoutExpired, OSError):
                    pass
                
                if size > 0:
                    items.append(CleanableItem(
                        name="Docker unused images",
                        path="/var/lib/docker",
                        size=size,
                        command="docker image prune -a",
                        description="Remove unused Docker images"
                    ))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    
    return items


def get_system_cleanable_items() -> list[CleanableItem]:
    """Find cleanable system items (requires root)."""
    items = []
    
    log_dir = Path("/var/log")
    if log_dir.exists() and os.access(log_dir, os.R_OK):
        try:
            for entry in log_dir.glob("*.gz"):
                if entry.is_file():
                    size = entry.stat().st_size
                    if size > 1024 * 1024:
                        items.append(CleanableItem(
                            name=f"Compressed log: {entry.name}",
                            path=str(entry),
                            size=size,
                            command=f"sudo rm {entry}",
                            description=f"Remove compressed log {entry.name}"
                        ))
        except (PermissionError, OSError):
            pass
    
    return items


def get_all_suggestions() -> list[CleanableItem]:
    """Get all cleanup suggestions."""
    items = []
    
    items.extend(get_user_cleanable_items())
    items.extend(get_docker_items())
    
    if os.geteuid() == 0:
        items.extend(get_system_cleanable_items())
    
    items.sort(key=lambda x: x.size, reverse=True)
    return items


def format_suggestions(items: list[CleanableItem]) -> str:
    """Format cleanup suggestions as a string."""
    if not items:
        return "No cleanable items found."
    
    lines = []
    total = 0
    
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item.name} ({item.formatted_size})")
        lines.append(f"   Path: {item.path}")
        lines.append(f"   Command: {item.command}")
        lines.append("")
        total += item.size
    
    lines.append(f"Total potential savings: {format_size(total)}")
    
    return "\n".join(lines)
