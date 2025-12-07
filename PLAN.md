# Minecraft Modding Tools Repository - Implementation Plan

## Current State Analysis

### Existing Tools
The repository currently contains 3 Python scripts in the `to implement/` folder:

1. **`scan_assets_to_txt.py`** - JAR Asset Scanner
   - Scans `.jar` files for block/item assets (models, textures)
   - Extracts assets by namespace
   - Performs triple-pass cleaning (removes extensions, affixes, duplicates)
   - Outputs: `jar_scan_results/blocks/` and `jar_scan_results/items/`

2. **`scan_recipes_to_txt.py`** - Recipe Extractor
   - Scans `.jar` files for recipe JSON files
   - Extracts recipe results (excluding `minecraft:` recipes)
   - Outputs: `jar_scan_results/recipes/`

3. **`match_blocks_to_json.py`** - Block Duplicate Matcher
   - Finds duplicate blocks across different namespaces
   - Generates JSON mapping for block matching
   - Outputs: `matches.json`

### Current Issues
- ❌ No README documentation
- ❌ No requirements.txt for dependencies
- ❌ No .gitignore file
- ❌ Tools are in "to implement" folder (not organized)
- ❌ No proper project structure
- ❌ No usage examples or documentation
- ❌ No license file
- ❌ No contribution guidelines

---

## Proposed Repository Structure

```
RD-Minecraft-Tools/
├── README.md                 # Main documentation
├── LICENSE                   # License file (MIT recommended)
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── setup.py                  # Optional: package setup
│
├── tools/                    # Main tools directory
│   ├── __init__.py
│   ├── asset_scanner.py      # Renamed from scan_assets_to_txt.py
│   ├── recipe_scanner.py     # Renamed from scan_recipes_to_txt.py
│   └── block_matcher.py      # Renamed from match_blocks_to_json.py
│
├── src/                      # Shared utilities (if needed)
│   ├── __init__.py
│   └── utils.py              # Common functions
│
├── examples/                 # Example usage scripts
│   └── example_usage.py
│
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_asset_scanner.py
│   ├── test_recipe_scanner.py
│   └── test_block_matcher.py
│
├── docs/                     # Additional documentation
│   ├── USAGE.md
│   └── ARCHITECTURE.md
│
└── output/                   # Default output directory (gitignored)
    ├── blocks/
    ├── items/
    └── recipes/
```

---

## Implementation Tasks

### Phase 1: Repository Setup & Organization
- [ ] Create `.gitignore` file
  - Ignore Python cache (`__pycache__/`, `*.pyc`)
  - Ignore output directories (`jar_scan_results/`, `output/`)
  - Ignore JAR files (`*.jar`)
  - Ignore IDE files (`.vscode/`, `.idea/`)
  - Ignore virtual environments (`venv/`, `.env`)

- [ ] Create `requirements.txt`
  - Currently no external dependencies (uses stdlib only)
  - Add future-proofing for potential dependencies

- [ ] Reorganize code structure
  - Move scripts from `to implement/` to `tools/`
  - Rename files to follow Python naming conventions
  - Add `__init__.py` files for package structure

- [ ] Create LICENSE file
  - Recommend MIT License for open source tools

### Phase 2: Code Improvements
- [ ] Refactor tools for better modularity
  - Extract common utilities to `src/utils.py`
  - Improve error handling
  - Add command-line argument parsing (argparse)
  - Add logging configuration

- [ ] Standardize output handling
  - Make output directory configurable
  - Add option to specify input JAR directory
  - Improve file path handling (cross-platform)

- [ ] Add type hints throughout
  - Improve code maintainability
  - Better IDE support

- [ ] Improve user experience
  - Add progress bars for long operations
  - Better error messages
  - Add dry-run mode

### Phase 3: Documentation
- [ ] Create comprehensive README.md
  - Project description
  - Installation instructions
  - Usage examples for each tool
  - Screenshots/diagrams if helpful
  - Contributing guidelines

- [ ] Create USAGE.md
  - Detailed usage for each tool
  - Command-line options
  - Input/output formats
  - Troubleshooting

- [ ] Add docstrings to all functions
  - Follow Google or NumPy docstring style
  - Include parameter descriptions
  - Include return value descriptions
  - Include usage examples

- [ ] Create ARCHITECTURE.md
  - Explain how tools work
  - Data flow diagrams
  - File format specifications

### Phase 4: Testing & Quality
- [ ] Add unit tests
  - Test each tool's core functionality
  - Mock JAR file operations
  - Test edge cases

- [ ] Add integration tests
  - Test with sample JAR files
  - Verify output formats

- [ ] Set up linting
  - Add `.flake8` or `pyproject.toml` for linting config
  - Ensure code follows PEP 8

- [ ] Add pre-commit hooks (optional)
  - Format code with black
  - Run linters
  - Run tests

### Phase 5: Enhanced Features (Future)
- [ ] Add CLI interface
  - Single entry point (`mc-tools`) with subcommands
  - Better argument parsing
  - Configuration file support

- [ ] Add GUI option (optional)
  - Simple tkinter or web-based interface
  - Drag-and-drop JAR files

- [ ] Add more tools
  - Block state analyzer
  - Texture pack generator
  - Mod compatibility checker
  - Namespace conflict detector

- [ ] Add export formats
  - Export to CSV
  - Export to SQLite database
  - Export to JSON with metadata

---

## Tool-Specific Improvements

### Asset Scanner (`scan_assets_to_txt.py`)
**Improvements:**
- [ ] Add command-line arguments:
  - `--input-dir`: Directory containing JAR files
  - `--output-dir`: Output directory (default: `jar_scan_results`)
  - `--namespace`: Filter by specific namespace
  - `--clean-passes`: Number of cleaning passes (default: 3)
  - `--threads`: Number of worker threads

- [ ] Add logging levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Add progress reporting
- [ ] Add option to skip raw files (only output cleaned)
- [ ] Add validation of JAR file structure

### Recipe Scanner (`scan_recipes_to_txt.py`)
**Improvements:**
- [ ] Add command-line arguments (similar to asset scanner)
- [ ] Add option to include `minecraft:` recipes
- [ ] Add recipe type filtering (shaped, shapeless, smelting, etc.)
- [ ] Extract more recipe metadata (ingredients, crafting table type)
- [ ] Add JSON output option with full recipe data

### Block Matcher (`match_blocks_to_json.py`)
**Improvements:**
- [ ] Add command-line arguments:
  - `--input-dir`: Directory containing `.txt` files
  - `--output-file`: Output JSON file path
  - `--interactive`: Interactive namespace selection (default: true)
  - `--namespace`: Pre-select namespace (non-interactive mode)
  - `--format`: Output format (json, csv, txt)

- [ ] Add batch processing mode
- [ ] Add confidence scoring for matches
- [ ] Add option to merge multiple match files
- [ ] Add validation of input files

---

## Dependencies

### Current Dependencies
- Python 3.7+ (uses `pathlib`, `zipfile`, `json`, `threading`, `concurrent.futures`)
- Standard library only - no external packages required

### Recommended Future Dependencies
- `tqdm` - Progress bars
- `click` or `argparse` - Better CLI (argparse is stdlib, click is more powerful)
- `pytest` - Testing framework
- `black` - Code formatting
- `mypy` - Type checking

---

## Best Practices to Implement

1. **Code Quality**
   - Follow PEP 8 style guide
   - Use type hints
   - Write docstrings
   - Handle errors gracefully

2. **User Experience**
   - Clear error messages
   - Progress indicators
   - Helpful usage instructions
   - Sensible defaults

3. **Performance**
   - Already uses threading - good!
   - Consider async/await for I/O operations
   - Add caching for repeated operations

4. **Maintainability**
   - Modular code structure
   - Separation of concerns
   - Unit tests
   - Clear documentation

5. **Cross-Platform**
   - Use `pathlib` (already done ✓)
   - Test on Windows, Linux, macOS
   - Handle path separators correctly

---

## Quick Start Checklist

Once implemented, users should be able to:

1. ✅ Clone the repository
2. ✅ Install dependencies (if any): `pip install -r requirements.txt`
3. ✅ Run tools with clear instructions
4. ✅ Understand output formats
5. ✅ Find help/documentation easily
6. ✅ Contribute improvements

---

## Next Steps

1. **Immediate**: Review and approve this plan
2. **Phase 1**: Set up repository structure and basic files
3. **Phase 2**: Refactor and improve existing code
4. **Phase 3**: Add comprehensive documentation
5. **Phase 4**: Add tests and quality checks
6. **Phase 5**: Enhance with additional features

---

## Notes

- All tools currently work in the script's directory
- Tools are designed for Minecraft mod JAR files (Forge/Fabric)
- Output formats are simple text files for easy processing
- Tools are thread-safe and can process multiple JARs concurrently
- The block matcher requires user interaction for namespace selection

