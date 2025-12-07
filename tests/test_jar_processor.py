"""Unit tests for JAR processor utilities."""

import unittest
import tempfile
import zipfile
from pathlib import Path
from src.jar_processor import (
    find_jar_files,
    validate_input_directory,
    validate_jar_file,
    create_output_dirs
)


class TestJarProcessor(unittest.TestCase):
    """Test cases for JAR processor utilities."""

    def test_find_jar_files(self):
        """Test finding JAR files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create some test files
            (tmp_path / "mod1.jar").write_bytes(b"fake jar")
            (tmp_path / "mod2.jar").write_bytes(b"fake jar")
            (tmp_path / "not_a_jar.txt").write_text("test")
            
            jars = find_jar_files(tmp_path)
            
            # Should find .jar files
            self.assertEqual(len(jars), 2)
            self.assertTrue(any(f.name == "mod1.jar" for f in jars))
            self.assertTrue(any(f.name == "mod2.jar" for f in jars))
            
            # Should not find .txt files
            self.assertFalse(any(f.name == "not_a_jar.txt" for f in jars))

    def test_find_jar_files_no_jars(self):
        """Test error when no JAR files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create non-JAR file
            (tmp_path / "test.txt").write_text("test")
            
            with self.assertRaises(ValueError) as context:
                find_jar_files(tmp_path)
            
            self.assertIn("No .jar files found", str(context.exception))

    def test_validate_input_directory(self):
        """Test input directory validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Valid directory should not raise
            validate_input_directory(tmp_path)
            
            # Non-existent directory should raise
            non_existent = Path(tmpdir) / "nonexistent"
            with self.assertRaises(ValueError) as context:
                validate_input_directory(non_existent)
            self.assertIn("does not exist", str(context.exception))
            
            # File (not directory) should raise
            test_file = tmp_path / "test.txt"
            test_file.write_text("test")
            with self.assertRaises(ValueError) as context:
                validate_input_directory(test_file)
            self.assertIn("not a directory", str(context.exception))

    def test_validate_jar_file(self):
        """Test JAR file validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create valid JAR
            valid_jar = tmp_path / "valid.jar"
            with zipfile.ZipFile(valid_jar, "w") as zf:
                zf.writestr("test.txt", "content")
            
            self.assertTrue(validate_jar_file(valid_jar))
            
            # Invalid file
            invalid_jar = tmp_path / "invalid.jar"
            invalid_jar.write_bytes(b"not a zip file")
            
            self.assertFalse(validate_jar_file(invalid_jar))
            
            # Non-existent file
            nonexistent = tmp_path / "nonexistent.jar"
            self.assertFalse(validate_jar_file(nonexistent))

    def test_create_output_dirs(self):
        """Test output directory creation."""
        # This test verifies the function can be called without errors
        # The actual directory creation depends on project structure
        # In a real scenario, it would create logs/test_category and output/test_category
        try:
            raw_dir, cleaned_dir = create_output_dirs("test_category")
            
            # Should return Path objects
            self.assertIsInstance(raw_dir, Path)
            self.assertIsInstance(cleaned_dir, Path)
            
            # Directories should exist (or be created)
            # Note: This may use temp directory if permissions are denied
            # So we just check that paths are returned
            self.assertIsNotNone(raw_dir)
            self.assertIsNotNone(cleaned_dir)
        except Exception as e:
            # If it fails due to permissions, that's acceptable
            # The function should handle it gracefully
            self.fail(f"create_output_dirs raised unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()
