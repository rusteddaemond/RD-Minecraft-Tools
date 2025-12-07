"""Unit tests for processors."""

import unittest
from pathlib import Path
import tempfile
import zipfile

from src.processors.scanner.filters import BlockEntryFilter, ItemsEntryFilter, FluidEntryFilter
from src.processors.cleaner.identifier import IdentifierCleaner, FluidIdentifierCleaner
from src.processors.jar.reader import JarReader, JarValidator
from src.processors.file_io import FileIOProcessor
from src.models.scanner import NamespaceObject


class TestEntryFilters(unittest.TestCase):
    """Test cases for entry filters."""
    
    def test_block_entry_filter(self):
        """Test BlockEntryFilter."""
        filter_obj = BlockEntryFilter()
        
        # Valid block asset paths
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "models", "block", "dirt.json"]), "dirt")
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "textures", "block", "stone.png"]), "stone")
        
        # Invalid paths
        self.assertIsNone(filter_obj.filter(["assets", "minecraft", "models", "item", "sword.json"]))
        self.assertIsNone(filter_obj.filter(["data", "minecraft", "recipes", "test.json"]))
    
    def test_items_entry_filter(self):
        """Test ItemsEntryFilter."""
        filter_obj = ItemsEntryFilter()
        
        # Valid item asset paths
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "models", "item", "sword.json"]), "sword")
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "textures", "item", "apple.png"]), "apple")
        
        # Invalid paths
        self.assertIsNone(filter_obj.filter(["assets", "minecraft", "models", "block", "dirt.json"]))
    
    def test_fluid_entry_filter(self):
        """Test FluidEntryFilter."""
        filter_obj = FluidEntryFilter()
        
        # Valid fluid paths
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "fluid", "water.json"]), "water")
        self.assertEqual(filter_obj.filter(["assets", "minecraft", "fluid_types", "lava.json"]), "lava")
        
        # Invalid paths
        self.assertIsNone(filter_obj.filter(["assets", "minecraft", "models", "block", "dirt.json"]))


class TestIdentifierCleaner(unittest.TestCase):
    """Test cases for identifier cleaner."""
    
    def test_clean_basic(self):
        """Test basic identifier cleaning."""
        cleaner = IdentifierCleaner()
        
        # Remove extension
        self.assertEqual(cleaner.clean("dirt.png"), "dirt")
        
        # Remove affix
        self.assertEqual(cleaner.clean("dirt_top"), "dirt")
        
        # Multiple affixes
        self.assertEqual(cleaner.clean("dirt_top_side"), "dirt")
    
    def test_clean_namespace_object(self):
        """Test cleaning namespace:object pair."""
        cleaner = IdentifierCleaner()
        
        result = cleaner.clean_namespace_object("minecraft", "dirt.png")
        self.assertIsNotNone(result)
        self.assertEqual(result.namespace, "minecraft")
        self.assertEqual(result.object_id, "dirt")


class TestJarReader(unittest.TestCase):
    """Test cases for JarReader."""
    
    def test_validate(self):
        """Test JAR validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create valid JAR
            valid_jar = tmp_path / "valid.jar"
            with zipfile.ZipFile(valid_jar, "w") as zf:
                zf.writestr("test.txt", "content")
            
            reader = JarReader()
            self.assertTrue(reader.validate(valid_jar))
            
            # Invalid file
            invalid_jar = tmp_path / "invalid.jar"
            invalid_jar.write_bytes(b"not a zip file")
            self.assertFalse(reader.validate(invalid_jar))


class TestFileIOProcessor(unittest.TestCase):
    """Test cases for FileIOProcessor."""
    
    def test_read_write_namespace_objects(self):
        """Test reading and writing namespace objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            processor = FileIOProcessor()
            
            # Write objects
            objects = [
                NamespaceObject("minecraft", "dirt"),
                NamespaceObject("minecraft", "stone"),
                NamespaceObject("modname", "copper")
            ]
            processor.write_namespace_objects(test_file, objects)
            
            # Read back
            read_objects = processor.read_namespace_objects(test_file)
            
            # Should get back the same objects (sorted and deduplicated)
            self.assertEqual(len(read_objects), 3)
            read_strings = {obj.to_string() for obj in read_objects}
            self.assertIn("minecraft:dirt", read_strings)
            self.assertIn("minecraft:stone", read_strings)
            self.assertIn("modname:copper", read_strings)


if __name__ == "__main__":
    unittest.main()
