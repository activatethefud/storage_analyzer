"""Utility functions for storage analyzer."""
import os
import subprocess
import json
from dataclasses import dataclass
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


@dataclass
class BlockDevice:
    """Represents a block device."""
    device: str
    size: str
    mountpoint: Optional[str]
    device_type: str
    children: list['BlockDevice']
    
    @property
    def is_partition(self) -> bool:
        return self.device_type == 'part'
    
    @property
    def is_disk(self) -> bool:
        return self.device_type == 'disk'


def get_device_for_path(path: str) -> Optional[str]:
    """
    Get the device (e.g., /dev/sda2) for a given path.
    
    Args:
        path: Any path on the filesystem
        
    Returns:
        Device path (e.g., /dev/sda2) or None if not found
    """
    try:
        result = subprocess.run(
            ['df', '-P', path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None
        
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return None
        
        parts = lines[1].split()
        if len(parts) < 1:
            return None
        
        device = parts[0]
        if device.startswith('/dev/'):
            return device
        return None
    except (subprocess.TimeoutExpired, OSError, IndexError):
        return None


def get_mount_point_for_device(device: str) -> Optional[str]:
    """
    Get the mount point for a device.
    
    Args:
        device: Device path (e.g., /dev/sda2)
        
    Returns:
        Mount point (e.g., /, /home) or None if not mounted
    """
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'MOUNTPOINT', device],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        blockdevices = data.get('blockdevices', [])
        if not blockdevices:
            return None
        
        return blockdevices[0].get('mountpoint')
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, KeyError):
        return None


def get_all_devices() -> list[BlockDevice]:
    """
    Get all block devices with their mount points.
    
    Returns:
        List of BlockDevice objects
    """
    devices = []
    
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,PATH'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return devices
        
        data = json.loads(result.stdout)
        blockdevices = data.get('blockdevices', [])
        
        for bd in blockdevices:
            device = BlockDevice(
                device=bd.get('path', ''),
                size=bd.get('size', ''),
                mountpoint=bd.get('mountpoint'),
                device_type=bd.get('type', 'disk'),
                children=[]
            )
            
            for child in bd.get('children', []):
                child_device = BlockDevice(
                    device=child.get('path', ''),
                    size=child.get('size', ''),
                    mountpoint=child.get('mountpoint'),
                    device_type=child.get('type', 'part'),
                    children=[]
                )
                device.children.append(child_device)
            
            devices.append(device)
        
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass
    
    return devices


def validate_device(device: str) -> tuple[bool, Optional[str]]:
    """
    Validate a device exists and is mounted.
    
    Args:
        device: Device path (e.g., /dev/sda2)
        
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
    """
    if not device.startswith('/dev/'):
        return False, f"Invalid device format: '{device}'. Device must start with /dev/"
    
    if not os.path.exists(device):
        return False, f"Device '{device}' not found. Use 'lsblk' to list available devices."
    
    mountpoint = get_mount_point_for_device(device)
    if mountpoint is None:
        return False, f"Device '{device}' is not mounted. Cannot analyze unmounted devices."
    
    return True, None


def get_device_info(device: str) -> Optional[dict]:
    """
    Get detailed information about a device.
    
    Args:
        device: Device path (e.g., /dev/sda2)
        
    Returns:
        Dictionary with device info or None if not found
    """
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,PATH,MODEL,SERIAL'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        def find_device(blockdevices, target_device):
            for bd in blockdevices:
                if bd.get('path') == target_device:
                    return bd
                if bd.get('children'):
                    found = find_device(bd['children'], target_device)
                    if found:
                        return found
            return None
        
        blockdevices = data.get('blockdevices', [])
        bd = find_device(blockdevices, device)
        
        if bd:
            return {
                'device': bd.get('path', ''),
                'size': bd.get('size', ''),
                'type': bd.get('type', ''),
                'mountpoint': bd.get('mountpoint'),
                'model': bd.get('model'),
                'serial': bd.get('serial')
            }
        
        return None
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return None


def detect_distro() -> Optional[str]:
    """
    Detect the Linux distribution from /etc/os-release.
    
    Returns:
        Distro ID (e.g., 'ubuntu', 'fedora', 'arch') or None
    """
    try:
        os_release_file = Path('/etc/os-release')
        if not os_release_file.exists():
            return None
        
        distro_id = None
        id_like = None
        
        for line in os_release_file.read_text().splitlines():
            if line.startswith('ID='):
                distro_id = line.split('=')[1].strip().strip('"')
            elif line.startswith('ID_LIKE='):
                id_like = line.split('=')[1].strip().strip('"')
        
        if distro_id:
            return distro_id
        
        if id_like:
            return id_like.split()[0]
        
        return None
    except (OSError, IOError):
        return None


def detect_package_managers() -> list[str]:
    """
    Detect all available package managers on the system.
    
    Returns:
        List of detected package manager names (e.g., ['apt', 'snap', 'flatpak'])
    """
    package_managers = {
        'apt': 'apt',
        'dnf': 'dnf',
        'pacman': 'pacman',
        'zypper': 'zypper',
        'apk': 'apk',
        'flatpak': 'flatpak',
        'snap': 'snap',
        'docker': 'docker',
    }
    
    detected = []
    
    for name, command in package_managers.items():
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                detected.append(name)
        except (subprocess.TimeoutExpired, OSError):
            continue
    
    return detected
