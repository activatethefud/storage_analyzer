"""Cleanup suggestions and cleanable item detection."""
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from storage_analyzer.utils import format_size, get_home_directory, get_device_for_path, detect_package_managers


PACKAGE_MANAGER_COMMANDS = {
    'apt': {
        'clean': 'apt-get clean',
        'autoremove': 'apt-get autoremove',
        'old_kernels': 'apt-get autoremove --purge',
    },
    'dnf': {
        'clean': 'dnf clean all',
        'autoremove': 'dnf autoremove',
        'old_kernels': 'dnf remove oldest-kernel',
    },
    'pacman': {
        'clean': 'pacman -Scc',
        'autoremove': 'pacman -Rsn $(pacman -Qtdq)',
        'old_kernels': 'pacman -Rsn $(pacman -Qqtd)',
    },
    'zypper': {
        'clean': 'zypper clean',
        'autoremove': 'zypper rm -u',
        'old_kernels': 'zypper rm -u kernel-default-base',
    },
    'apk': {
        'clean': 'apk clean',
        'autoremove': 'apk del -r $(apk info -e)',
        'old_kernels': 'apk del linux-lts',
    },
}


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


def get_system_cleanup_suggestions() -> list[CleanableItem]:
    """
    Find additional system cleanup suggestions.
    
    Includes journal cleanup, old kernels, crash reports, etc.
    """
    items = []
    detected_pms = detect_package_managers()
    
    journal_dir = Path("/var/log/journal")
    if journal_dir.exists() and os.access(journal_dir, os.R_OK):
        try:
            size = get_directory_size(str(journal_dir))
            if size > 50 * 1024 * 1024:
                items.append(CleanableItem(
                    name="systemd journal logs",
                    path="/var/log/journal",
                    size=size,
                    command="sudo journalctl --vacuum-size=100M",
                    description=f"Clean systemd journal logs (keep 100MB)"
                ))
        except (PermissionError, OSError):
            pass
    
    if 'apt' in detected_pms:
        try:
            result = subprocess.run(
                ["dpkg", "-l", "linux-image-*"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if l.startswith("ii") and "linux-image" in l]
                if len(lines) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (APT)",
                        path="/boot",
                        size=0,
                        command="sudo apt-get autoremove --purge",
                        description=f"Remove {len(lines)-1} old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'dnf' in detected_pms:
        try:
            result = subprocess.run(
                ["dnf", "list", "installed", "kernel"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if l.startswith("kernel")]
                if len(lines) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (DNF)",
                        path="/boot",
                        size=0,
                        command="sudo dnf remove oldest-kernel",
                        description=f"Remove {len(lines)-1} old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'pacman' in detected_pms:
        try:
            result = subprocess.run(
                ["pacman", "-Q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                kernels = [l for l in result.stdout.split("\n") if l.startswith("linux")]
                if len(kernels) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (Pacman)",
                        path="/boot",
                        size=0,
                        command="sudo pacman -Rsn $(pacman -Qqtd)",
                        description=f"Remove old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'zypper' in detected_pms:
        try:
            result = subprocess.run(
                ["zypper", "packages", "--installed-only", "--sort-by-name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if "kernel-default" in l]
                if len(lines) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (Zypper)",
                        path="/boot",
                        size=0,
                        command="sudo zypper rm -u kernel-default",
                        description=f"Remove old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'apk' in detected_pms:
        try:
            result = subprocess.run(
                ["apk", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                kernels = [l for l in result.stdout.split("\n") if l.startswith("linux")]
                if len(kernels) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (APK)",
                        path="/boot",
                        size=0,
                        command="apk del linux-lts",
                        description=f"Remove old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    crash_dir = Path("/var/crash")
    if crash_dir.exists() and os.access(crash_dir, os.R_OK):
        try:
            crash_files = list(crash_dir.glob("*.crash"))
            if crash_files:
                size = sum(f.stat().st_size for f in crash_files)
                if size > 1024 * 1024:
                    items.append(CleanableItem(
                        name="Crash reports",
                        path="/var/crash",
                        size=size,
                        command="sudo rm /var/crash/*.crash",
                        description=f"Remove {len(crash_files)} crash report files"
                    ))
        except (PermissionError, OSError):
            pass
    
    old_logs_dir = Path("/var/log")
    if old_logs_dir.exists() and os.access(old_logs_dir, os.R_OK):
        try:
            total_old_logs = 0
            old_log_files = []
            for entry in old_logs_dir.glob("*.[0-9]"):
                if entry.is_file() and entry.stat().st_size > 1024 * 1024:
                    total_old_logs += entry.stat().st_size
                    old_log_files.append(entry.name)
            
            if total_old_logs > 10 * 1024 * 1024:
                items.append(CleanableItem(
                    name="Old rotated log files",
                    path="/var/log",
                    size=total_old_logs,
                    command="sudo find /var/log -name '*.gz' -o -name '*.[0-9]' | xargs sudo rm",
                    description=f"Remove {len(old_log_files)} old rotated log files"
                ))
        except (PermissionError, OSError):
            pass
    
    try:
        result = subprocess.run(
            ["systemd-analyze", "disk-usage"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "disk usage" in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "GB" in part and i > 0:
                            try:
                                size_gb = float(part.replace("GB", ""))
                                if size_gb > 0.5:
                                    items.append(CleanableItem(
                                        name="systemd journal (analyze)",
                                        path="/var/log/journal",
                                        size=int(size_gb * 1024 * 1024 * 1024),
                                        command="sudo journalctl --vacuum-time=7d",
                                        description=f"Systemd journal uses {size_gb:.1f}GB"
                                    ))
                            except ValueError:
                                pass
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    
    return items


def get_package_cleanup_suggestions() -> list[CleanableItem]:
    """
    Find cleanup suggestions from package managers.
    
    Detects all available package managers and provides appropriate cleanup commands.
    """
    items = []
    
    detected_pms = detect_package_managers()
    
    if 'apt' in detected_pms:
        apt_cache = Path("/var/cache/apt")
        if apt_cache.exists() and os.access(apt_cache, os.R_OK):
            try:
                size = get_directory_size(str(apt_cache))
                if size > 10 * 1024 * 1024:
                    items.append(CleanableItem(
                        name="APT package cache",
                        path="/var/cache/apt",
                        size=size,
                        command="sudo apt-get clean",
                        description="Clean APT download cache"
                    ))
            except (PermissionError, OSError):
                pass
        
        try:
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                try:
                    autoremove_result = subprocess.run(
                        ["apt-get", "autoremove", "--dry-run"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if autoremove_result.returncode == 0:
                        lines = autoremove_result.stdout.split("\n")
                        packages = [l for l in lines if l.strip().startswith("Remv ")]
                        if packages:
                            items.append(CleanableItem(
                                name="APT autoremove candidates",
                                path="/var/lib/dpkg",
                                size=0,
                                command="sudo apt-get autoremove",
                                description=f"{len(packages)} packages can be removed (dry-run shown)"
                            ))
                except (subprocess.TimeoutExpired, OSError):
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        
        try:
            result = subprocess.run(
                ["deborphan"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                orphans = result.stdout.strip().split("\n")
                if orphans and orphans[0]:
                    items.append(CleanableItem(
                        name="Deborphan orphaned libraries",
                        path="/var/lib/dpkg",
                        size=0,
                        command="sudo deborphan | xargs apt-get remove --purge -y",
                        description=f"{len(orphans)} orphaned libraries found"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'dnf' in detected_pms:
        dnf_cache = Path("/var/cache/dnf")
        if dnf_cache.exists() and os.access(dnf_cache, os.R_OK):
            try:
                size = get_directory_size(str(dnf_cache))
                if size > 10 * 1024 * 1024:
                    items.append(CleanableItem(
                        name="DNF package cache",
                        path="/var/cache/dnf",
                        size=size,
                        command="sudo dnf clean all",
                        description="Clean DNF download cache"
                    ))
            except (PermissionError, OSError):
                pass
        
        try:
            result = subprocess.run(
                ["dnf", "autoremove", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                items.append(CleanableItem(
                    name="DNF autoremove candidates",
                    path="/var/lib/dnf",
                    size=0,
                    command="sudo dnf autoremove",
                    description="Remove unused packages"
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'pacman' in detected_pms:
        try:
            result = subprocess.run(
                ["pacman", "-Qtdq"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                orphans = result.stdout.strip().split("\n")
                items.append(CleanableItem(
                    name="Pacman orphaned packages",
                    path="/var/lib/pacman",
                    size=0,
                    command="sudo pacman -Rsn $(pacman -Qtdq)",
                    description=f"{len(orphans)} orphaned packages"
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        
        try:
            result = subprocess.run(
                ["pacman", "-Q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                kernels = [l for l in result.stdout.split("\n") if l.startswith("linux")]
                if len(kernels) > 1:
                    items.append(CleanableItem(
                        name="Old kernel images (Pacman)",
                        path="/boot",
                        size=0,
                        command="sudo pacman -Rsn $(pacman -Qqtd)",
                        description="Remove old kernel versions"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'zypper' in detected_pms:
        zypper_cache = Path("/var/cache/zypper")
        if zypper_cache.exists() and os.access(zypper_cache, os.R_OK):
            try:
                size = get_directory_size(str(zypper_cache))
                if size > 10 * 1024 * 1024:
                    items.append(CleanableItem(
                        name="Zypper package cache",
                        path="/var/cache/zypper",
                        size=size,
                        command="sudo zypper clean",
                        description="Clean Zypper download cache"
                    ))
            except (PermissionError, OSError):
                pass
        
        try:
            result = subprocess.run(
                ["zypper", "packages", "--uninstalled"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                items.append(CleanableItem(
                    name="Zypper unused packages",
                    path="/var/lib/zypper",
                    size=0,
                    command="sudo zypper rm -u",
                    description="Remove unused packages"
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'apk' in detected_pms:
        apk_cache = Path("/var/cache/apk")
        if apk_cache.exists() and os.access(apk_cache, os.R_OK):
            try:
                size = get_directory_size(str(apk_cache))
                if size > 10 * 1024 * 1024:
                    items.append(CleanableItem(
                        name="APK package cache",
                        path="/var/cache/apk",
                        size=size,
                        command="apk clean",
                        description="Clean APK download cache"
                    ))
            except (PermissionError, OSError):
                pass
        
        try:
            result = subprocess.run(
                ["apk", "info", "-e"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                items.append(CleanableItem(
                    name="APK orphaned packages",
                    path="/var/lib/apk",
                    size=0,
                    command="apk del -r $(apk info -e)",
                    description="Remove unused packages"
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'flatpak' in detected_pms:
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                items.append(CleanableItem(
                    name="Flatpak apps",
                    path="/var/lib/flatpak",
                    size=0,
                    command="flatpak remove --unused",
                    description="Remove unused Flatpak runtimes"
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    if 'snap' in detected_pms:
        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    items.append(CleanableItem(
                        name="Snap packages",
                        path="/snap",
                        size=0,
                        command="snap list --all",
                        description=f"{len(lines)-1} snap packages installed"
                    ))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    
    return items


def get_all_suggestions(device: Optional[str] = None) -> list[CleanableItem]:
    """
    Get all cleanup suggestions.
    
    Args:
        device: Optional device path (e.g., /dev/sda2) to filter suggestions
        
    Returns:
        List of CleanableItem, filtered to specified device if provided
    """
    items = []
    
    items.extend(get_user_cleanable_items())
    items.extend(get_docker_items())
    items.extend(get_package_cleanup_suggestions())
    items.extend(get_system_cleanup_suggestions())
    
    if os.geteuid() == 0:
        items.extend(get_system_cleanable_items())
    
    if device:
        filtered_items = []
        for item in items:
            item_device = get_device_for_path(item.path)
            if item_device == device:
                filtered_items.append(item)
        items = filtered_items
    
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
