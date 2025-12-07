"""Integration tests for services."""

import unittest
import tempfile
import zipfile
from pathlib import Path

from src.models.scanner import ScannerConfig, ScannerResult
from src.models.matcher import MatcherConfig
from src.processors.scanner import AssetScannerProcessor, BlockEntryFilter
from src.processors.cleaner import IdentifierCleaner
from src.processors.file_io import FileIOProcessor
from src.processors.jar.reader import JarReader
from src.services.scanner_service import ScannerService
from src.processors.matcher import DuplicateMatcherProcessor
from src.services.matcher_service import MatcherService


class TestScannerService(unittest.TestCase):
    """Integration tests for ScannerService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.file_io = FileIOProcessor()
        self.cleaner = IdentifierCleaner()
        self.entry_filter = BlockEntryFilter()
        self.processor = AssetScannerProcessor(self.entry_filter, self.cleaner)
        self.service = ScannerService(self.processor, self.file_io, self.cleaner)
    
    def test_service_initialization(self):
        """Test that service can be initialized."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.processor)
        self.assertIsNotNone(self.service.file_io)
    
    def test_process_jar_with_test_jar(self):
        """Test processing a test JAR file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a test JAR with block assets
            test_jar = tmp_path / "test.jar"
            with zipfile.ZipFile(test_jar, "w") as zf:
                zf.writestr("assets/minecraft/models/block/dirt.json", "{}")
                zf.writestr("assets/minecraft/textures/block/stone.png", "")
                zf.writestr("assets/minecraft/models/item/sword.json", "{}")  # Not a block
            
            # Create config
            raw_dir = tmp_path / "raw"
            cleaned_dir = tmp_path / "cleaned"
            raw_dir.mkdir()
            cleaned_dir.mkdir()
            
            config = ScannerConfig(
                input_dir=tmp_path,
                output_dir=cleaned_dir,
                raw_dir=raw_dir,
                category="blocks",
                category_suffix="_blocks",
                max_workers=1,
                namespace_filter=None,
                skip_raw=False,
                verbose=False
            )
            
            # Process JAR
            results = self.processor.process_jar(test_jar, config)
            
            # Should find block assets
            self.assertGreater(len(results), 0)
            
            # Check that minecraft namespace is found
            minecraft_results = [r for r in results if r.namespace == "minecraft"]
            self.assertGreater(len(minecraft_results), 0)
            
            # Check that block objects are found
            all_objects = []
            for result in minecraft_results:
                all_objects.extend(result.objects)
            
            self.assertIn("dirt", all_objects)
            self.assertIn("stone", all_objects)
            self.assertNotIn("sword", all_objects)  # Should not include items


class TestMatcherService(unittest.TestCase):
    """Integration tests for MatcherService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.file_io = FileIOProcessor()
        self.processor = DuplicateMatcherProcessor(self.file_io)
        self.service = MatcherService(self.processor, self.file_io)
    
    def test_service_initialization(self):
        """Test that service can be initialized."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.processor)
        self.assertIsNotNone(self.service.file_io)
    
    def test_find_duplicates(self):
        """Test finding duplicates using processor."""
        objects = {
            "dirt": ["minecraft", "modname"],  # Duplicate
            "stone": ["minecraft"],  # Not duplicate
            "copper": ["modname", "othermod"],  # Duplicate
        }
        
        dupes = self.processor.find_duplicates(objects)
        
        self.assertIn("dirt", dupes)
        self.assertIn("copper", dupes)
        self.assertNotIn("stone", dupes)
    
    def test_load_objects_from_files(self):
        """Test loading objects from files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            file1 = tmp_path / "mod1.txt"
            file1.write_text("minecraft:dirt\nminecraft:stone\n")
            
            file2 = tmp_path / "mod2.txt"
            file2.write_text("minecraft:dirt\nmodname:copper\n")
            
            objects = self.processor.load_objects_from_files([file1, file2])
            
            # Should find dirt in both namespaces
            self.assertIn("dirt", objects)
            self.assertIn("minecraft", objects["dirt"])
            self.assertIn("modname", objects["dirt"] or [])


if __name__ == "__main__":
    unittest.main()
