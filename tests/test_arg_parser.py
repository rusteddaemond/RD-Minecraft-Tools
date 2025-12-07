"""Unit tests for argument parser utilities."""

import unittest
import argparse
from pathlib import Path
from src.arg_parser import (
    add_common_jar_args,
    add_namespace_filter_arg,
    get_thread_count
)


class TestArgParser(unittest.TestCase):
    """Test cases for argument parser utilities."""

    def test_add_common_jar_args(self):
        """Test adding common JAR arguments."""
        parser = argparse.ArgumentParser()
        add_common_jar_args(parser)
        
        # Parse with defaults
        args = parser.parse_args([])
        
        # Check that arguments exist
        self.assertTrue(hasattr(args, 'input_dir'))
        self.assertTrue(hasattr(args, 'threads'))
        self.assertTrue(hasattr(args, 'verbose'))
        self.assertTrue(hasattr(args, 'skip_raw'))
        
        # Check defaults
        self.assertIsNone(args.threads)
        self.assertFalse(args.verbose)
        self.assertFalse(args.skip_raw)
        self.assertIsInstance(args.input_dir, Path)

    def test_add_common_jar_args_with_values(self):
        """Test parsing with provided values."""
        parser = argparse.ArgumentParser()
        add_common_jar_args(parser)
        
        args = parser.parse_args([
            "--input-dir", "/test/path",
            "--threads", "8",
            "--verbose",
            "--skip-raw"
        ])
        
        self.assertEqual(args.input_dir, Path("/test/path"))
        self.assertEqual(args.threads, 8)
        self.assertTrue(args.verbose)
        self.assertTrue(args.skip_raw)

    def test_add_namespace_filter_arg(self):
        """Test adding namespace filter argument."""
        parser = argparse.ArgumentParser()
        add_namespace_filter_arg(parser)
        
        args = parser.parse_args([])
        self.assertIsNone(args.namespace)
        
        args = parser.parse_args(["--namespace", "minecraft"])
        self.assertEqual(args.namespace, "minecraft")

    def test_get_thread_count(self):
        """Test thread count calculation."""
        # Mock args object
        class Args:
            def __init__(self, threads=None):
                self.threads = threads
        
        # With explicit thread count
        args = Args(threads=8)
        self.assertEqual(get_thread_count(args), 8)
        
        # With None (should use CPU count or default)
        args = Args(threads=None)
        result = get_thread_count(args)
        # Should return at least 1
        self.assertGreaterEqual(result, 1)
        
        # With 0 (edge case)
        args = Args(threads=0)
        self.assertEqual(get_thread_count(args), 0)

    def test_combined_arguments(self):
        """Test combining all argument functions."""
        parser = argparse.ArgumentParser()
        add_common_jar_args(parser)
        add_namespace_filter_arg(parser)
        
        args = parser.parse_args([
            "--input-dir", "/mods",
            "--threads", "4",
            "--namespace", "testmod",
            "--verbose"
        ])
        
        self.assertEqual(args.input_dir, Path("/mods"))
        self.assertEqual(args.threads, 4)
        self.assertEqual(args.namespace, "testmod")
        self.assertTrue(args.verbose)
        self.assertFalse(args.skip_raw)


if __name__ == "__main__":
    unittest.main()
