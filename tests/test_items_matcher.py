"""Unit tests for items matcher."""

import unittest
import tempfile
import json
from pathlib import Path
from tools.items_matcher import (
    validate_config,
    load_config,
    create_datapack_structure,
    generate_replacements_file,
    create_pack_mcmeta
)


class TestItemsMatcher(unittest.TestCase):
    """Test cases for items matcher."""

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = [
            {
                "matchItems": ["minecraft:potato", "minecraft:carrot"],
                "resultItems": "minecraft:egg"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")

    def test_validate_config_not_list(self):
        """Test validation fails when config is not a list."""
        config = {"matchItems": [], "resultItems": "test"}
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("must be a list", error_msg)

    def test_validate_config_missing_match_items(self):
        """Test validation fails when matchItems is missing."""
        config = [{"resultItems": "minecraft:egg"}]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("missing 'matchItems'", error_msg)

    def test_validate_config_missing_result_items(self):
        """Test validation fails when resultItems is missing."""
        config = [{"matchItems": ["minecraft:potato"]}]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("missing 'resultItems'", error_msg)

    def test_validate_config_match_items_not_list(self):
        """Test validation fails when matchItems is not a list."""
        config = [
            {
                "matchItems": "minecraft:potato",
                "resultItems": "minecraft:egg"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("must be a list", error_msg)

    def test_validate_config_empty_match_items(self):
        """Test validation fails when matchItems is empty."""
        config = [
            {
                "matchItems": [],
                "resultItems": "minecraft:egg"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("cannot be empty", error_msg)

    def test_validate_config_result_items_not_string(self):
        """Test validation fails when resultItems is not a string."""
        config = [
            {
                "matchItems": ["minecraft:potato"],
                "resultItems": ["minecraft:egg"]
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("must be a string", error_msg)

    def test_validate_config_self_replacement(self):
        """Test validation fails when item replaces itself."""
        config = [
            {
                "matchItems": ["minecraft:potato", "minecraft:egg"],
                "resultItems": "minecraft:egg"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertFalse(is_valid)
        self.assertIn("Cannot replace item with itself", error_msg)
        self.assertIn("minecraft:egg", error_msg)

    def test_validate_config_multiple_entries(self):
        """Test validation with multiple entries."""
        config = [
            {
                "matchItems": ["minecraft:potato"],
                "resultItems": "minecraft:egg"
            },
            {
                "matchItems": ["#forge:ore"],
                "resultItems": "minecraft:iron_ore"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertTrue(is_valid)

    def test_validate_config_with_tags(self):
        """Test validation accepts item tags (starting with #)."""
        config = [
            {
                "matchItems": ["#forge:ore", "minecraft:potato"],
                "resultItems": "minecraft:egg"
            }
        ]
        
        is_valid, error_msg = validate_config(config)
        self.assertTrue(is_valid)

    def test_load_config_valid(self):
        """Test loading valid configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "config.json"
            
            config_data = [
                {
                    "matchItems": ["minecraft:potato"],
                    "resultItems": "minecraft:egg"
                }
            ]
            
            with config_file.open("w", encoding="utf-8") as f:
                json.dump(config_data, f)
            
            loaded = load_config(config_file)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["resultItems"], "minecraft:egg")

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "config.json"
            
            config_file.write_text("{ invalid json }")
            
            # Should exit with error
            import sys
            from io import StringIO
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            try:
                with self.assertRaises(SystemExit):
                    load_config(config_file)
            finally:
                sys.stderr = old_stderr

    def test_create_datapack_structure(self):
        """Test creating datapack directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            replacements_dir = create_datapack_structure(tmp_path)
            
            self.assertTrue(replacements_dir.exists())
            self.assertTrue(replacements_dir.is_dir())
            self.assertEqual(replacements_dir.name, "replacements")
            self.assertEqual(replacements_dir.parent.name, "oei")
            self.assertEqual(replacements_dir.parent.parent.name, "data")

    def test_generate_replacements_file(self):
        """Test generating replacements JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            replacements_dir = create_datapack_structure(tmp_path)
            
            config = [
                {
                    "matchItems": ["minecraft:potato", "minecraft:carrot"],
                    "resultItems": "minecraft:egg"
                }
            ]
            
            output_file = generate_replacements_file(config, replacements_dir)
            
            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.name, "replacements.json")
            
            # Verify content
            with output_file.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["resultItems"], "minecraft:egg")
            self.assertEqual(len(loaded[0]["matchItems"]), 2)

    def test_generate_replacements_file_custom_filename(self):
        """Test generating replacements file with custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            replacements_dir = create_datapack_structure(tmp_path)
            
            config = [{"matchItems": ["test"], "resultItems": "result"}]
            
            output_file = generate_replacements_file(
                config, replacements_dir, filename="custom.json"
            )
            
            self.assertEqual(output_file.name, "custom.json")

    def test_create_pack_mcmeta(self):
        """Test creating pack.mcmeta file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            create_pack_mcmeta(tmp_path, pack_format=15)
            
            pack_mcmeta = tmp_path / "pack.mcmeta"
            self.assertTrue(pack_mcmeta.exists())
            
            # Verify content
            with pack_mcmeta.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            
            self.assertIn("pack", meta)
            self.assertEqual(meta["pack"]["pack_format"], 15)
            self.assertIn("description", meta["pack"])

    def test_create_pack_mcmeta_default_format(self):
        """Test pack.mcmeta uses default format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            create_pack_mcmeta(tmp_path)
            
            pack_mcmeta = tmp_path / "pack.mcmeta"
            with pack_mcmeta.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            
            self.assertEqual(meta["pack"]["pack_format"], 10)


if __name__ == "__main__":
    unittest.main()
