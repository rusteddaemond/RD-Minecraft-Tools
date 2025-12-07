"""Unit tests for recipe scanner."""

import unittest
import json
from tools.recipe_scanner import extract_results_from_json


class TestRecipeScanner(unittest.TestCase):
    """Test cases for recipe scanner."""

    def test_extract_results_single_string(self):
        """Test extraction of single string result."""
        recipe = {"result": "minecraft:iron_ingot"}
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "minecraft:iron_ingot")

    def test_extract_results_object_with_id(self):
        """Test extraction of result object with id field."""
        recipe = {"result": {"id": "minecraft:gold_ingot", "count": 2}}
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "minecraft:gold_ingot")

    def test_extract_results_multiple_results(self):
        """Test extraction of multiple results array."""
        recipe = {
            "results": [
                {"id": "minecraft:iron_ingot"},
                {"id": "minecraft:gold_ingot"}
            ]
        }
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 2)
        self.assertIn("minecraft:iron_ingot", results)
        self.assertIn("minecraft:gold_ingot", results)

    def test_extract_results_combined(self):
        """Test extraction when both result and results exist."""
        recipe = {
            "result": "minecraft:iron_ingot",
            "results": [
                {"id": "minecraft:gold_ingot"}
            ]
        }
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        # Should extract both
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("minecraft:iron_ingot", results)

    def test_extract_results_empty(self):
        """Test extraction from recipe with no results."""
        recipe = {"type": "crafting_shaped"}
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 0)

    def test_extract_results_invalid_json(self):
        """Test handling of invalid JSON."""
        content = "not valid json {"
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 0)

    def test_extract_results_malformed_structure(self):
        """Test handling of malformed recipe structure."""
        # Result is not a string or object
        recipe = {"result": 123}
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 0)

    def test_extract_results_missing_id(self):
        """Test handling of result object without id."""
        recipe = {"result": {"count": 2}}  # No id field
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 0)

    def test_extract_results_real_world_example(self):
        """Test with a realistic recipe structure."""
        recipe = {
            "type": "minecraft:crafting_shaped",
            "pattern": [
                "###",
                "# #",
                "###"
            ],
            "key": {
                "#": {"item": "minecraft:iron_ingot"}
            },
            "result": {
                "id": "minecraft:iron_block",
                "count": 1
            }
        }
        content = json.dumps(recipe)
        results = extract_results_from_json(content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "minecraft:iron_block")


if __name__ == "__main__":
    unittest.main()

