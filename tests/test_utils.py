"""Unit tests for shared utilities."""

import unittest
from pathlib import Path
import tempfile
import os
from src.utils import (
    get_lock,
    write_entry,
    log,
    utc_now_str,
    get_project_root,
    create_directory_with_fallback
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_utc_now_str(self):
        """Test UTC timestamp generation."""
        timestamp = utc_now_str()
        self.assertIsInstance(timestamp, str)
        self.assertIn("T", timestamp)  # ISO format contains 'T'
        self.assertIn("Z", timestamp)  # UTC timezone indicator

    def test_get_lock(self):
        """Test lock creation and retrieval."""
        test_path = Path("/test/path")
        lock1 = get_lock(test_path)
        lock2 = get_lock(test_path)
        
        # Should return the same lock for the same path
        self.assertIs(lock1, lock2)
        
        # Different paths should get different locks
        test_path2 = Path("/test/path2")
        lock3 = get_lock(test_path2)
        self.assertIsNot(lock1, lock3)

    def test_write_entry(self):
        """Test thread-safe file writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            lines = ["line1\n", "line2\n", "line3\n"]
            
            write_entry(test_file, lines)
            
            # Verify file was created and contains expected content
            self.assertTrue(test_file.exists())
            with test_file.open("r") as f:
                content = f.read()
                self.assertEqual(content, "".join(lines))

    def test_write_entry_multiple_calls(self):
        """Test multiple writes to same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            write_entry(test_file, ["line1\n"])
            write_entry(test_file, ["line2\n"])
            write_entry(test_file, ["line3\n"])
            
            with test_file.open("r") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 3)
                self.assertEqual(lines[0], "line1\n")
                self.assertEqual(lines[1], "line2\n")
                self.assertEqual(lines[2], "line3\n")

    def test_log(self):
        """Test logging function (basic smoke test)."""
        # Just verify it doesn't crash
        log("Test message")
        log("Test message with prefix", "PREFIX")

    def test_get_project_root(self):
        """Test project root resolution."""
        root = get_project_root()
        
        # Should be a Path object
        self.assertIsInstance(root, Path)
        
        # Should exist
        self.assertTrue(root.exists())
        
        # Should be a directory
        self.assertTrue(root.is_dir())
        
        # Should contain src directory
        self.assertTrue((root / "src").exists())
        self.assertTrue((root / "src").is_dir())

    def test_create_directory_with_fallback(self):
        """Test directory creation with fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Normal case - should create directory
            result = create_directory_with_fallback(
                base_path,
                ["test", "subdir"]
            )
            
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())
            self.assertEqual(result.name, "subdir")
            self.assertEqual(result.parent.name, "test")
            
            # Should work with existing directory
            result2 = create_directory_with_fallback(
                base_path,
                ["test", "subdir"]
            )
            
            # Should return same path
            self.assertEqual(result, result2)


if __name__ == "__main__":
    unittest.main()

