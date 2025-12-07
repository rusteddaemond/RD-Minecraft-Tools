"""Unit tests for data models."""

import unittest
from pathlib import Path
from datetime import datetime

from src.models.scanner import NamespaceObject, ScannerResult, ScannerConfig
from src.models.matcher import MatchRule, MatcherConfig, DuplicateMatch
from src.models.datapack import DatapackMetadata, ReplacementRule


class TestNamespaceObject(unittest.TestCase):
    """Test cases for NamespaceObject model."""
    
    def test_to_string(self):
        """Test conversion to string."""
        obj = NamespaceObject(namespace="minecraft", object_id="dirt")
        self.assertEqual(obj.to_string(), "minecraft:dirt")
    
    def test_from_string(self):
        """Test parsing from string."""
        obj = NamespaceObject.from_string("minecraft:dirt")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.namespace, "minecraft")
        self.assertEqual(obj.object_id, "dirt")
    
    def test_from_string_invalid(self):
        """Test parsing invalid string."""
        obj = NamespaceObject.from_string("invalid")
        self.assertIsNone(obj)
    
    def test_immutability(self):
        """Test that NamespaceObject is immutable."""
        obj = NamespaceObject(namespace="minecraft", object_id="dirt")
        # Should not be able to modify (frozen dataclass)
        with self.assertRaises(Exception):
            obj.namespace = "modname"


class TestScannerResult(unittest.TestCase):
    """Test cases for ScannerResult model."""
    
    def test_to_namespace_objects(self):
        """Test conversion to NamespaceObject list."""
        result = ScannerResult(
            namespace="minecraft",
            objects=["dirt", "stone"],
            source_jar=Path("test.jar"),
            timestamp=datetime.now()
        )
        
        ns_objects = result.to_namespace_objects()
        self.assertEqual(len(ns_objects), 2)
        self.assertEqual(ns_objects[0].namespace, "minecraft")
        self.assertEqual(ns_objects[0].object_id, "dirt")


class TestMatchRule(unittest.TestCase):
    """Test cases for MatchRule model."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        rule = MatchRule(
            match_items=["modname:dirt", "othermod:dirt"],
            result_item="minecraft:dirt",
            match_field="matchBlock",
            result_field="resultBlock"
        )
        
        result = rule.to_dict()
        self.assertEqual(result["matchBlock"], ["modname:dirt", "othermod:dirt"])
        self.assertEqual(result["resultBlock"], "minecraft:dirt")


class TestDatapackMetadata(unittest.TestCase):
    """Test cases for DatapackMetadata model."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = DatapackMetadata(
            pack_format=10,
            description="Test datapack"
        )
        
        result = metadata.to_dict()
        self.assertEqual(result["pack"]["pack_format"], 10)
        self.assertEqual(result["pack"]["description"], "Test datapack")


if __name__ == "__main__":
    unittest.main()
