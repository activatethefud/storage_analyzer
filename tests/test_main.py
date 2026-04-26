import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner
from storage_analyzer.main import cli


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCLI:
    """Tests for CLI commands."""
    
    @pytest.fixture(autouse=True)
    def runner(self):
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Storage Analyzer" in result.output
    
    def test_cli_version(self):
        """Test CLI version."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_scan_command(self, temp_dir):
        """Test scan command."""
        (Path(temp_dir) / "test.txt").write_text("hello")
        
        result = self.runner.invoke(cli, ['scan', temp_dir])
        
        assert result.exit_code == 0
        assert "Scanning" in result.output
    
    def test_scan_nonexistent(self):
        """Test scan with nonexistent path."""
        result = self.runner.invoke(cli, ['scan', '/nonexistent/path'])
        
        assert "Error" in result.output
    
    def test_large_files_command(self, temp_dir):
        """Test large-files command."""
        (Path(temp_dir) / "test.txt").write_text("test content")
        
        result = self.runner.invoke(cli, ['large-files', temp_dir])
        
        assert result.exit_code == 0
    
    def test_large_dirs_command(self, temp_dir):
        """Test large-dirs command."""
        (Path(temp_dir) / "subdir").mkdir()
        
        result = self.runner.invoke(cli, ['large-dirs', temp_dir])
        
        assert result.exit_code == 0
    
    def test_clean_command(self):
        """Test clean command."""
        result = self.runner.invoke(cli, ['clean'])
        
        assert result.exit_code == 0
    
    def test_suggest_command(self):
        """Test suggest command."""
        result = self.runner.invoke(cli, ['suggest'])
        
        assert result.exit_code == 0
    
    def test_disk_command(self):
        """Test disk command."""
        result = self.runner.invoke(cli, ['disk'])
        
        assert result.exit_code == 0
        assert "Total" in result.output
    
    def test_drives_command(self):
        """Test drives command."""
        result = self.runner.invoke(cli, ['drives'])
        
        assert result.exit_code == 0
        assert "Block Devices" in result.output or "/dev/" in result.output
    
    def test_suggest_with_device_valid(self):
        """Test suggest command with valid device."""
        result = self.runner.invoke(cli, ['suggest', '--device', '/dev/sda2'])
        
        assert result.exit_code == 0
        assert "mounted at" in result.output or "Analyzing" in result.output
    
    def test_suggest_with_device_not_found(self):
        """Test suggest command with non-existent device."""
        result = self.runner.invoke(cli, ['suggest', '--device', '/dev/sda999'])
        
        assert "not found" in result.output
    
    def test_suggest_with_device_invalid_format(self):
        """Test suggest command with invalid device format."""
        result = self.runner.invoke(cli, ['suggest', '--device', 'invalid'])
        
        assert "Invalid device format" in result.output
    
    def test_suggest_with_device_not_mounted(self):
        """Test suggest command with unmounted device."""
        result = self.runner.invoke(cli, ['suggest', '--device', '/dev/sda'])
        
        assert "not mounted" in result.output
    
    def test_clean_with_device_valid(self):
        """Test clean command with valid device."""
        result = self.runner.invoke(cli, ['clean', '--device', '/dev/sda2'])
        
        assert result.exit_code == 0
        assert "mounted at" in result.output or "Looking" in result.output
    
    def test_clean_with_device_not_found(self):
        """Test clean command with non-existent device."""
        result = self.runner.invoke(cli, ['clean', '--device', '/dev/sda999'])
        
        assert "not found" in result.output
