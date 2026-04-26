import os
import tempfile
import pytest
from pathlib import Path
from storage_analyzer.scanner import (
    FileInfo, scan_directory, get_directory_size, 
    get_largest_files, get_largest_directories
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_scan_directory_basic(temp_dir):
    """Test basic directory scanning."""
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("hello world")
    
    results = list(scan_directory(temp_dir))
    
    assert len(results) >= 1
    file_info = next(r for r in results if not r.is_dir)
    assert file_info.size == 11


def test_scan_directory_nested(temp_dir):
    """Test scanning nested directories."""
    subdir = Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("content")
    
    results = list(scan_directory(temp_dir))
    paths = [r.path for r in results]
    
    assert any("subdir" in p for p in paths)


def test_scan_directory_with_max_depth(temp_dir):
    """Test scanning with max_depth limit."""
    Path(temp_dir).joinpath("level1").mkdir()
    Path(temp_dir).joinpath("level1", "level2").mkdir()
    Path(temp_dir).joinpath("level1", "level2", "file.txt").write_text("x")
    
    results_depth_1 = list(scan_directory(temp_dir, max_depth=1))
    results_unlimited = list(scan_directory(temp_dir))
    
    assert len(results_depth_1) <= len(results_unlimited)


def test_scan_nonexistent_directory():
    """Test scanning non-existent directory raises error."""
    with pytest.raises(FileNotFoundError):
        list(scan_directory("/nonexistent/path/abc123"))


def test_get_directory_size(temp_dir):
    """Test directory size calculation."""
    (Path(temp_dir) / "file1.txt").write_text("a" * 100)
    (Path(temp_dir) / "file2.txt").write_text("b" * 200)
    
    size = get_directory_size(temp_dir)
    
    assert size >= 300


def test_get_largest_files(temp_dir):
    """Test finding largest files."""
    (Path(temp_dir) / "small.txt").write_text("x")
    (Path(temp_dir) / "large.txt").write_text("y" * 1000)
    
    largest = get_largest_files(temp_dir, top=2)
    
    assert len(largest) <= 2
    assert all(not f.is_dir for f in largest)


def test_get_largest_directories(temp_dir):
    """Test finding largest directories."""
    dir1 = Path(temp_dir) / "dir1"
    dir2 = Path(temp_dir) / "dir2"
    dir1.mkdir()
    dir2.mkdir()
    (dir1 / "file.txt").write_text("a" * 100)
    (dir2 / "file.txt").write_text("b" * 200)
    
    largest = get_largest_directories(temp_dir, top=2)
    
    assert len(largest) <= 2
    assert all(isinstance(d, tuple) for d in largest)
