import os
import tempfile
import pytest
from pathlib import Path
from storage_analyzer.utils import (
    format_size, get_home_directory, sanitize_path,
    is_safe_to_delete, get_disk_usage
)


class TestFormatSize:
    """Tests for format_size function."""
    
    def test_bytes(self):
        assert format_size(0) == "0 B"
        assert format_size(100) == "100 B"
        assert format_size(1023) == "1023 B"
    
    def test_kilobytes(self):
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
        assert format_size(10240) == "10.0 KB"
    
    def test_megabytes(self):
        assert format_size(1048576) == "1.0 MB"
        assert format_size(1572864) == "1.5 MB"
        assert format_size(10485760) == "10.0 MB"
    
    def test_gigabytes(self):
        assert format_size(1073741824) == "1.0 GB"
        assert format_size(1610612736) == "1.5 GB"
    
    def test_negative(self):
        assert format_size(-100) == "0 B"


class TestSanitizePath:
    """Tests for path sanitization."""
    
    def test_absolute_path(self):
        result = sanitize_path("/tmp")
        assert result == "/tmp"
    
    def test_relative_path(self):
        result = sanitize_path(".")
        assert Path(result).is_absolute()
    
    def test_path_traversal_blocked(self):
        with pytest.raises(ValueError):
            sanitize_path("../../../etc", base="/home/user")
    
    def test_path_within_base_allowed(self):
        result = sanitize_path("subdir/file.txt", base="/home/nikola/storage_analyzer")
        assert "storage_analyzer" in result


class TestIsSafeToDelete:
    """Tests for safe-to-delete checking."""
    
    def test_cache_dir_safe(self):
        path = str(Path.home() / ".cache" / "pip")
        assert is_safe_to_delete(path) is True
    
    def test_trash_safe(self):
        path = str(Path.home() / ".local" / "share" / "Trash")
        assert is_safe_to_delete(path) is True
    
    def test_home_not_safe(self):
        path = str(Path.home() / "Documents")
        assert is_safe_to_delete(path) is False


class TestGetDiskUsage:
    """Tests for disk usage."""
    
    def test_returns_tuple(self):
        result = get_disk_usage("/tmp")
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_values_positive(self):
        total, used, free = get_disk_usage("/tmp")
        assert total >= 0
        assert used >= 0
        assert free >= 0
