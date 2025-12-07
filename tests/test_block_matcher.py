"""Unit tests for block matcher."""

import unittest
import tempfile
from pathlib import Path
from tools.block_matcher import (
    find_txt_files,
    load_blocks,
    filter_duplicates,
    build_matches
)


class TestBlockMatcher(unittest.TestCase):
    """Test cases for block matcher."""

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
            
            # Should find .txt files in root, not subdirectories
            self.assertEqual(len(files), 2)
            self.assertTrue(any(f.name == "file1.txt" for f in files))
            self.assertTrue(any(f.name == "file2.txt" for f in files))
            self.assertFalse(any(f.name == "file3.log" for f in files))

    def test_load_blocks(self):
        """Test loading blocks from text files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            file1 = tmp_path / "mod1.txt"
            file1.write_text("minecraft:dirt\nminecraft:stone\n")
            
            file2 = tmp_path / "mod2.txt"
            file2.write_text("minecraft:dirt\nmodname:copper\n")
            
            files = [file1, file2]
            blocks = load_blocks(files)
            
            # dirt should appear in both namespaces
            self.assertIn("dirt", blocks)
            self.assertEqual(len(blocks["dirt"]), 2)
            self.assertIn("minecraft", blocks["dirt"])
            
            # stone only in minecraft
            self.assertIn("stone", blocks)
            self.assertEqual(len(blocks["stone"]), 1)
            
            # copper only in modname
            self.assertIn("copper", blocks)
            self.assertEqual(len(blocks["copper"]), 1)

    def test_load_blocks_case_insensitive(self):
        """Test that namespace and block_id are lowercased."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            file1 = tmp_path / "test.txt"
            file1.write_text("MINECRAFT:DIRT\nModName:Copper\n")
            
            blocks = load_blocks([file1])
            
            self.assertIn("dirt", blocks)
            self.assertIn("minecraft", blocks["dirt"])
            self.assertIn("copper", blocks)
            self.assertIn("modname", blocks["copper"])

    def test_load_blocks_skips_invalid_lines(self):
        """Test that invalid lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            file1 = tmp_path / "test.txt"
            file1.write_text(
                "minecraft:dirt\n"
                "invalid_line\n"
                "no_colon\n"
                "minecraft:stone\n"
                "\n"  # Empty line
            )
            
            blocks = load_blocks([file1])
            
            # Should only have valid entries
            self.assertIn("dirt", blocks)
            self.assertIn("stone", blocks)
            self.assertEqual(len(blocks), 2)

    def test_filter_duplicates(self):
        """Test filtering to only duplicate blocks."""
        blocks = {
            "dirt": ["minecraft", "modname"],  # Duplicate
            "stone": ["minecraft"],  # Not duplicate
            "copper": ["modname", "othermod", "minecraft"],  # Duplicate
        }
        
        dupes = filter_duplicates(blocks)
        
        # Should only contain blocks with multiple namespaces
        self.assertIn("dirt", dupes)
        self.assertIn("copper", dupes)
        self.assertNotIn("stone", dupes)

    def test_filter_duplicates_same_namespace(self):
        """Test that same namespace multiple times doesn't count as duplicate."""
        blocks = {
            "dirt": ["minecraft", "minecraft"],  # Same namespace twice
        }
        
        dupes = filter_duplicates(blocks)
        
        # Should not be considered duplicate
        self.assertNotIn("dirt", dupes)

    def test_build_matches(self):
        """Test building match mappings."""
        dupes = {
            "dirt": ["minecraft", "modname", "othermod"],
            "stone": ["minecraft", "modname"],
        }
        result_ns = "minecraft"
        
        matches = build_matches(dupes, result_ns)
        
        # Should create matches for all non-result namespaces
        self.assertEqual(len(matches), 3)  # modname:dirt, othermod:dirt, modname:stone
        
        # Check specific matches
        match_dict = {m["matchBlock"]: m["resultBlock"] for m in matches}
        self.assertEqual(match_dict["modname:dirt"], "minecraft:dirt")
        self.assertEqual(match_dict["othermod:dirt"], "minecraft:dirt")
        self.assertEqual(match_dict["modname:stone"], "minecraft:stone")

    def test_build_matches_result_not_in_dupes(self):
        """Test that blocks without result namespace are skipped."""
        dupes = {
            "dirt": ["modname", "othermod"],  # No minecraft
            "stone": ["minecraft", "modname"],
        }
        result_ns = "minecraft"
        
        matches = build_matches(dupes, result_ns)
        
        # Should only include stone (dirt doesn't have minecraft)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["matchBlock"], "modname:stone")
        self.assertEqual(matches[0]["resultBlock"], "minecraft:stone")

    def test_build_matches_empty(self):
        """Test building matches with empty duplicates."""
        dupes = {}
        result_ns = "minecraft"
        
        matches = build_matches(dupes, result_ns)
        
        self.assertEqual(len(matches), 0)


if __name__ == "__main__":
    unittest.main()

