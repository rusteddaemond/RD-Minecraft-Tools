"""Unit tests for block matcher using new architecture."""

import unittest
import tempfile
from pathlib import Path
from src.config_loader import find_txt_files
from src.processors.matcher import DuplicateMatcherProcessor
from src.processors.file_io import FileIOProcessor
from src.models.scanner import NamespaceObject


class TestBlockMatcher(unittest.TestCase):
    """Test cases for block matcher using new architecture."""

    def test_find_txt_files(self):
        """Test finding text files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create some test files
            (tmp_path / "file1.txt").write_text("test")
            (tmp_path / "file2.txt").write_text("test")
            (tmp_path / "file3.log").write_text("test")  # Not .txt
            (tmp_path / "subdir").mkdir()
            (tmp_path / "subdir" / "file4.txt").write_text("test")
            
            files = find_txt_files(tmp_path)
            
            # Should find .txt files recursively
            self.assertGreaterEqual(len(files), 2)
            self.assertTrue(any(f.name == "file1.txt" for f in files))
            self.assertTrue(any(f.name == "file2.txt" for f in files))
            self.assertFalse(any(f.name == "file3.log" for f in files))

    def test_load_objects_from_files(self):
        """Test loading objects from text files using DuplicateMatcherProcessor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            file1 = tmp_path / "mod1.txt"
            file1.write_text("minecraft:dirt\nminecraft:stone\n")
            
            file2 = tmp_path / "mod2.txt"
            file2.write_text("minecraft:dirt\nmodname:copper\n")
            
            files = [file1, file2]
            file_io = FileIOProcessor()
            processor = DuplicateMatcherProcessor(file_io)
            
            objects = processor.load_objects_from_files(files)
            
            # dirt should appear in both namespaces
            self.assertIn("dirt", objects)
            self.assertGreaterEqual(len(objects["dirt"]), 1)
            self.assertIn("minecraft", objects["dirt"])
            
            # stone only in minecraft
            self.assertIn("stone", objects)
            self.assertIn("minecraft", objects["stone"])
            
            # copper only in modname
            self.assertIn("copper", objects)
            self.assertIn("modname", objects["copper"])

    def test_find_duplicates(self):
        """Test finding duplicate objects."""
        processor = DuplicateMatcherProcessor(FileIOProcessor())
        
        objects = {
            "dirt": ["minecraft", "modname"],  # Duplicate
            "stone": ["minecraft"],  # Not duplicate
            "copper": ["modname", "othermod", "minecraft"],  # Duplicate
        }
        
        dupes = processor.find_duplicates(objects)
        
        # Should only contain objects with multiple namespaces
        self.assertIn("dirt", dupes)
        self.assertIn("copper", dupes)
        self.assertNotIn("stone", dupes)

    def test_find_duplicates_same_namespace(self):
        """Test that same namespace multiple times doesn't count as duplicate."""
        processor = DuplicateMatcherProcessor(FileIOProcessor())
        
        objects = {
            "dirt": ["minecraft", "minecraft"],  # Same namespace twice
        }
        
        dupes = processor.find_duplicates(objects)
        
        # Should not be considered duplicate (uses set internally)
        self.assertNotIn("dirt", dupes)

    def test_build_match_rules(self):
        """Test building match rules."""
        processor = DuplicateMatcherProcessor(FileIOProcessor())
        
        dupes = {
            "dirt": ["minecraft", "modname", "othermod"],
            "stone": ["minecraft", "modname"],
        }
        result_ns = "minecraft"
        
        match_rules = processor.build_match_rules(
            dupes,
            result_ns,
            "matchBlock",
            "resultBlock"
        )
        
        # Should create match rules for all non-result namespaces
        self.assertGreaterEqual(len(match_rules), 2)
        
        # Check that rules are properly formatted
        for rule in match_rules:
            self.assertIn("matchBlock", rule.to_dict())
            self.assertIn("resultBlock", rule.to_dict())
            self.assertTrue(rule.match_items)  # Should have match items
            self.assertTrue(rule.result_item)  # Should have result item

    def test_build_match_rules_result_not_in_dupes(self):
        """Test that objects without result namespace are skipped."""
        processor = DuplicateMatcherProcessor(FileIOProcessor())
        
        dupes = {
            "dirt": ["modname", "othermod"],  # No minecraft
            "stone": ["minecraft", "modname"],
        }
        result_ns = "minecraft"
        
        match_rules = processor.build_match_rules(
            dupes,
            result_ns,
            "matchBlock",
            "resultBlock"
        )
        
        # Should only include stone (dirt doesn't have minecraft)
        self.assertEqual(len(match_rules), 1)
        self.assertIn("modname:stone", match_rules[0].match_items)
        self.assertEqual(match_rules[0].result_item, "minecraft:stone")

    def test_build_match_rules_empty(self):
        """Test building match rules with empty duplicates."""
        processor = DuplicateMatcherProcessor(FileIOProcessor())
        
        dupes = {}
        result_ns = "minecraft"
        
        match_rules = processor.build_match_rules(
            dupes,
            result_ns,
            "matchBlock",
            "resultBlock"
        )
        
        self.assertEqual(len(match_rules), 0)


if __name__ == "__main__":
    unittest.main()

