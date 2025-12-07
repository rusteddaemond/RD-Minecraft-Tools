"""Unit tests for asset scanner."""

import unittest
import tempfile
import zipfile
from pathlib import Path
from tools.asset_scanner import (
    clean_identifier,
    AFFIXES,
    EXTENSIONS
)


class TestAssetScanner(unittest.TestCase):
    """Test cases for asset scanner."""

    def test_clean_identifier_removes_extensions(self):
        """Test that file extensions are removed."""
        self.assertEqual(clean_identifier("dirt.png"), "dirt")
        self.assertEqual(clean_identifier("stone.jpg"), "stone")
        self.assertEqual(clean_identifier("wood.jpeg"), "wood")
        self.assertEqual(clean_identifier("glass.gif"), "glass")

    def test_clean_identifier_removes_affixes(self):
        """Test that affixes are removed."""
        self.assertEqual(clean_identifier("dirt_top"), "dirt")
        self.assertEqual(clean_identifier("stone_bottom"), "stone")
        self.assertEqual(clean_identifier("wood_side"), "wood")
        self.assertEqual(clean_identifier("glass_open"), "glass")
        self.assertEqual(clean_identifier("door_closed"), "door")

    def test_clean_identifier_multiple_passes(self):
        """Test that multiple passes remove nested affixes."""
        # Single pass might not remove all
        result_1 = clean_identifier("dirt_top_side", passes=1)
        result_3 = clean_identifier("dirt_top_side", passes=3)
        
        # With 3 passes, both affixes should be removed
        self.assertEqual(result_3, "dirt")
        # With 1 pass, might still have affixes
        self.assertNotEqual(result_1, "dirt_top_side")  # At least one removed

    def test_clean_identifier_preserves_base(self):
        """Test that base identifier is preserved."""
        self.assertEqual(clean_identifier("dirt"), "dirt")
        self.assertEqual(clean_identifier("stone"), "stone")
        self.assertEqual(clean_identifier("minecraft_dirt"), "minecraft_dirt")  # Not an affix

    def test_clean_identifier_complex_cases(self):
        """Test complex cleaning scenarios."""
        # Multiple affixes
        self.assertEqual(clean_identifier("dirt_top_side_bottom", passes=3), "dirt")
        
        # Extension + affix
        self.assertEqual(clean_identifier("dirt_top.png", passes=3), "dirt")
        
        # State progression
        self.assertEqual(clean_identifier("crop_stage0", passes=3), "crop")
        self.assertEqual(clean_identifier("crop_age5", passes=3), "crop")

    def test_affixes_list_not_empty(self):
        """Test that affixes list is populated."""
        self.assertGreater(len(AFFIXES), 0)
        self.assertIn("_top", AFFIXES)
        self.assertIn("_bottom", AFFIXES)
        self.assertIn("_open", AFFIXES)

    def test_extensions_list_not_empty(self):
        """Test that extensions list is populated."""
        self.assertGreater(len(EXTENSIONS), 0)
        self.assertIn(".png", EXTENSIONS)
        self.assertIn(".jpg", EXTENSIONS)

    def test_jar_structure(self):
        """Test that test JAR has correct structure."""
        with tempfile.NamedTemporaryFile(suffix=".jar", delete=False) as tmp:
            jar_path = Path(tmp.name)
        
        try:
            with zipfile.ZipFile(jar_path, "w") as zf:
                # Add a test asset
                zf.writestr("assets/minecraft/models/block/dirt.json", "{}")
                zf.writestr("assets/minecraft/textures/block/dirt.png", b"fake")
                zf.writestr("assets/minecraft/models/item/diamond.json", "{}")
            
            with zipfile.ZipFile(jar_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("assets/minecraft/models/block/dirt.json", names)
                self.assertIn("assets/minecraft/textures/block/dirt.png", names)
        finally:
            if jar_path.exists():
                jar_path.unlink()


if __name__ == "__main__":
    unittest.main()

