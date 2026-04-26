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
