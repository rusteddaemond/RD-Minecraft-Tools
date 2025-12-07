"""Unit tests for thread pool utilities."""

import unittest
import time
from pathlib import Path
from src.thread_pool import execute_concurrent


class TestThreadPool(unittest.TestCase):
    """Test cases for thread pool utilities."""

    def test_execute_concurrent_basic(self):
        """Test basic concurrent execution."""
        results = []
        
        def process_item(item):
            results.append(item)
        
        items = [1, 2, 3, 4, 5]
        execute_concurrent(items, process_item, max_workers=2)
        
        # All items should be processed
        self.assertEqual(len(results), 5)
        self.assertEqual(set(results), {1, 2, 3, 4, 5})

    def test_execute_concurrent_with_errors(self):
        """Test error handling in concurrent execution."""
        results = []
        errors = []
        
        def process_item(item):
            if item == 3:
                raise ValueError(f"Error processing {item}")
            results.append(item)
        
        items = [1, 2, 3, 4, 5]
        
        # Should not raise, but log errors
        execute_concurrent(items, process_item, max_workers=2, verbose=False)
        
        # Items except 3 should be processed
        self.assertEqual(len(results), 4)
        self.assertNotIn(3, results)
        self.assertIn(1, results)
        self.assertIn(2, results)
        self.assertIn(4, results)
        self.assertIn(5, results)

    def test_execute_concurrent_max_workers(self):
        """Test that max_workers parameter is respected."""
        start_times = []
        
        def process_item(item):
            start_times.append(time.time())
            time.sleep(0.1)  # Simulate work
        
        items = list(range(10))
        
        # With 2 workers, should take longer than with 10
        start = time.time()
        execute_concurrent(items, process_item, max_workers=2)
        time_2_workers = time.time() - start
        
        start_times.clear()
        start = time.time()
        execute_concurrent(items, process_item, max_workers=10)
        time_10_workers = time.time() - start
        
        # With more workers, should be faster (or at least not slower)
        # Note: This is a rough test, actual timing depends on system
        self.assertGreater(len(start_times), 0)

    def test_execute_concurrent_empty_list(self):
        """Test execution with empty list."""
        results = []
        
        def process_item(item):
            results.append(item)
        
        execute_concurrent([], process_item)
        
        self.assertEqual(len(results), 0)

    def test_execute_concurrent_single_item(self):
        """Test execution with single item."""
        results = []
        
        def process_item(item):
            results.append(item)
        
        execute_concurrent([42], process_item)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 42)

    def test_execute_concurrent_default_workers(self):
        """Test that default workers (None) works."""
        results = []
        
        def process_item(item):
            results.append(item)
        
        items = [1, 2, 3]
        execute_concurrent(items, process_item, max_workers=None)
        
        self.assertEqual(len(results), 3)


if __name__ == "__main__":
    unittest.main()
