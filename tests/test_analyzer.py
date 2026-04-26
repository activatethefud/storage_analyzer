import os
import tempfile
import pytest
from pathlib import Path
from storage_analyzer.analyzer import (
    analyze_directory, get_path_disk_usage, 
    scan_directory_tree, DirectorySize, AnalysisResult
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestAnalyzeDirectory:
    """Tests for analyze_directory function."""
    
    def test_analyze_empty_directory(self, temp_dir):
        """Test analyzing an empty directory."""
        result = analyze_directory(temp_dir)
        
        assert isinstance(result, AnalysisResult)
        assert result.total_size >= 0
        assert result.file_count >= 0
    
    def test_analyze_with_files(self, temp_dir):
        """Test analyzing a directory with files."""
        (Path(temp_dir) / "file1.txt").write_text("a" * 100)
        (Path(temp_dir) / "file2.txt").write_text("b" * 200)
        
        result = analyze_directory(temp_dir)
        
        assert result.file_count >= 2
        assert result.total_size >= 300
    
    def test_analyze_nested_directories(self, temp_dir):
        """Test analyzing nested directories."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")
        
        result = analyze_directory(temp_dir)
        
        assert result.dir_count >= 1
    
    def test_analyze_nonexistent(self):
        """Test analyzing non-existent directory."""
        with pytest.raises(FileNotFoundError):
            analyze_directory("/nonexistent/path/xyz")


class TestGetPathDiskUsage:
    """Tests for disk usage function."""
    
    def test_returns_dict(self, temp_dir):
        """Test that disk usage returns expected keys."""
        result = get_path_disk_usage(temp_dir)
        
        assert isinstance(result, dict)
        assert "total" in result
        assert "used" in result
        assert "free" in result
        assert "percent_used" in result
    
    def test_values_positive(self, temp_dir):
        """Test that values are non-negative."""
        result = get_path_disk_usage(temp_dir)
        
        assert result["total"] >= 0
        assert result["used"] >= 0
        assert result["free"] >= 0
        assert 0 <= result["percent_used"] <= 100
    
    def test_formatted_sizes(self, temp_dir):
        """Test formatted size strings."""
        result = get_path_disk_usage(temp_dir)
        
        assert " " in result["total_formatted"]
        assert " " in result["used_formatted"]
        assert " " in result["free_formatted"]


class TestScanDirectoryTree:
    """Tests for directory tree scanning."""
    
    def test_returns_directory_sizes(self, temp_dir):
        """Test that result contains DirectorySize objects."""
        (Path(temp_dir) / "dir1").mkdir()
        (Path(temp_dir) / "dir2").mkdir()
        
        result = scan_directory_tree(temp_dir)
        
        assert all(isinstance(d, DirectorySize) for d in result)
    
    def test_sorted_by_size(self, temp_dir):
        """Test that results are sorted by size descending."""
        small = Path(temp_dir) / "small"
        large = Path(temp_dir) / "large"
        small.mkdir()
        large.mkdir()
        (small / "f.txt").write_text("x")
        (large / "f.txt").write_text("y" * 1000)
        
        result = scan_directory_tree(temp_dir)
        
        if len(result) >= 2:
            assert result[0].size >= result[1].size
    
    def test_empty_directory(self, temp_dir):
        """Test scanning empty directory."""
        result = scan_directory_tree(temp_dir)
        
        assert isinstance(result, list)
