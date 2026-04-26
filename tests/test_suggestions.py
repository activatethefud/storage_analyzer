import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from storage_analyzer.suggestions import (
    get_directory_size, get_user_cleanable_items,
    get_docker_items, get_all_suggestions,
    format_suggestions, CleanableItem
)


class TestGetDirectorySize:
    """Tests for directory size calculation."""
    
    def test_empty_directory(self, tmp_path):
        """Test size of empty directory."""
        size = get_directory_size(str(tmp_path))
        assert size == 0
    
    def test_directory_with_files(self, tmp_path):
        """Test size of directory with files."""
        (tmp_path / "file1.txt").write_text("a" * 100)
        (tmp_path / "file2.txt").write_text("b" * 200)
        
        size = get_directory_size(str(tmp_path))
        assert size >= 300
    
    def test_nonexistent_directory(self):
        """Test nonexistent directory returns 0."""
        size = get_directory_size("/nonexistent/path/xyz")
        assert size == 0


class TestGetUserCleanableItems:
    """Tests for finding user cleanable items."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        items = get_user_cleanable_items()
        assert isinstance(items, list)
    
    def test_cleanable_item_attributes(self):
        """Test CleanableItem has required attributes."""
        items = get_user_cleanable_items()
        
        for item in items:
            assert hasattr(item, 'name')
            assert hasattr(item, 'path')
            assert hasattr(item, 'size')
            assert hasattr(item, 'command')
            assert hasattr(item, 'formatted_size')
            assert hasattr(item, 'is_safe')
    
    def test_pip_cache_detected(self):
        """Test pip cache detection."""
        home = Path.home()
        pip_cache = home / ".cache" / "pip"
        
        if pip_cache.exists():
            items = get_user_cleanable_items()
            names = [item.name for item in items]
            assert any("pip" in n.lower() for n in names)


class TestGetDockerItems:
    """Tests for Docker cleanup detection."""
    
    @patch('subprocess.run')
    def test_docker_not_available(self, mock_run):
        """Test when docker command not found."""
        mock_run.side_effect = FileNotFoundError()
        
        items = get_docker_items()
        assert items == []
    
    @patch('subprocess.run')
    def test_docker_available_no_images(self, mock_run):
        """Test docker available but no images."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        items = get_docker_items()
        assert isinstance(items, list)


class TestFormatSuggestions:
    """Tests for formatting suggestions."""
    
    def test_empty_list(self):
        """Test formatting empty list."""
        result = format_suggestions([])
        assert "No cleanable items" in result
    
    def test_single_item(self):
        """Test formatting single item."""
        items = [CleanableItem(
            name="Test item",
            path="/tmp/test",
            size=1024,
            command="rm /tmp/test",
            description="Test"
        )]
        
        result = format_suggestions(items)
        assert "Test item" in result
        assert "1.0 KB" in result
        assert "rm /tmp/test" in result
    
    def test_multiple_items(self):
        """Test formatting multiple items."""
        items = [
            CleanableItem(name="Item 1", path="/p1", size=1000, command="c1", description="d1"),
            CleanableItem(name="Item 2", path="/p2", size=2000, command="c2", description="d2"),
        ]
        
        result = format_suggestions(items)
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Total" in result
    
    def test_total_calculation(self):
        """Test that total is calculated correctly."""
        items = [
            CleanableItem(name="Item 1", path="/p1", size=1000, command="c1", description="d1"),
            CleanableItem(name="Item 2", path="/p2", size=2000, command="c2", description="d2"),
        ]
        
        result = format_suggestions(items)
        assert "2.9 KB" in result


class TestGetAllSuggestions:
    """Tests for getting all suggestions."""
    
    def test_returns_list(self):
        """Test function returns a list."""
        items = get_all_suggestions()
        assert isinstance(items, list)
    
    def test_sorted_by_size(self):
        """Test items are sorted by size descending."""
        items = get_all_suggestions()
        
        if len(items) >= 2:
            for i in range(len(items) - 1):
                assert items[i].size >= items[i + 1].size


class TestPackageCleanupSuggestions:
    """Tests for package manager cleanup suggestions."""
    
    def test_returns_list(self):
        """Test function returns a list."""
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        items = get_package_cleanup_suggestions()
        assert isinstance(items, list)
    
    def test_cleanable_item_attributes(self):
        """Test CleanableItem has required attributes."""
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        items = get_package_cleanup_suggestions()
        
        for item in items:
            assert hasattr(item, 'name')
            assert hasattr(item, 'path')
            assert hasattr(item, 'size')
            assert hasattr(item, 'command')
            assert hasattr(item, 'description')
    
    @patch('subprocess.run')
    def test_apt_cache_detected(self, mock_run):
        """Test APT cache detection."""
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        items = get_package_cleanup_suggestions()
        names = [item.name for item in items]
        assert any("APT" in n for n in names)
    
    @patch('subprocess.run')
    def test_flatpak_checked(self, mock_run):
        """Test flatpak is checked."""
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        import subprocess
        
        def side_effect(*args, **kwargs):
            cmd = args[0]
            if 'flatpak' in cmd:
                raise FileNotFoundError()
            mock_result = MagicMock()
            mock_result.returncode = 0
            return mock_result
        
        mock_run.side_effect = side_effect
        items = get_package_cleanup_suggestions()
        assert isinstance(items, list)


class TestMultiPackageManager:
    """Tests for multi-package manager detection."""
    
    @patch('storage_analyzer.suggestions.detect_package_managers')
    @patch('subprocess.run')
    def test_apt_commands_when_detected(self, mock_run, mock_detect):
        """Test APT commands are generated when apt is detected."""
        mock_detect.return_value = ['apt']
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        items = get_package_cleanup_suggestions()
        
        names = [item.name for item in items]
        assert any("APT" in n for n in names)
    
    @patch('storage_analyzer.suggestions.detect_package_managers')
    @patch('subprocess.run')
    def test_dnf_commands_when_detected(self, mock_run, mock_detect):
        """Test DNF commands are generated when dnf is detected."""
        mock_detect.return_value = ['dnf']
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        items = get_package_cleanup_suggestions()
        
        names = [item.name for item in items]
        assert any("DNF" in n for n in names)
    
    @patch('storage_analyzer.suggestions.detect_package_managers')
    @patch('subprocess.run')
    def test_multiple_pms_all_generated(self, mock_run, mock_detect):
        """Test commands for multiple package managers."""
        mock_detect.return_value = ['apt', 'flatpak', 'snap']
        
        def side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()
            mock_result.returncode = 0
            
            if 'snap' in cmd:
                mock_result.stdout = "snap1\nsnap2\nsnap3\n"
            elif 'flatpak' in cmd:
                mock_result.stdout = "flatpak-app\n"
            else:
                mock_result.stdout = ""
            
            return mock_result
        
        mock_run.side_effect = side_effect
        
        from storage_analyzer.suggestions import get_package_cleanup_suggestions
        items = get_package_cleanup_suggestions()
        
        names = [item.name for item in items]
        assert any("APT" in n for n in names)
        assert any("Flatpak" in n for n in names)
        assert any("Snap" in n for n in names)
    
    def test_package_manager_commands_map(self):
        """Test PACKAGE_MANAGER_COMMANDS contains all expected managers."""
        from storage_analyzer.suggestions import PACKAGE_MANAGER_COMMANDS
        
        assert 'apt' in PACKAGE_MANAGER_COMMANDS
        assert 'dnf' in PACKAGE_MANAGER_COMMANDS
        assert 'pacman' in PACKAGE_MANAGER_COMMANDS
        assert 'zypper' in PACKAGE_MANAGER_COMMANDS
        assert 'apk' in PACKAGE_MANAGER_COMMANDS
        
        assert 'clean' in PACKAGE_MANAGER_COMMANDS['apt']
        assert 'autoremove' in PACKAGE_MANAGER_COMMANDS['apt']
