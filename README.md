# RD-Minecraft-Tools

A collection of Python tools for analyzing and processing Minecraft mod JAR files. These tools help extract assets, recipes, and identify duplicate blocks across different mod namespaces.

## Tools

### 1. Asset Scanner (`tools/asset_scanner.py`)

Scans JAR files for block and item assets (models and textures) and extracts them by namespace. Performs intelligent cleaning to remove file extensions and common affixes.

**Features:**
- Scans multiple JAR files concurrently
- Extracts blocks and items by namespace
- Triple-pass cleaning to normalize identifiers
- Removes file extensions and orientation/state affixes
- Outputs both raw and cleaned results

**Usage:**
```bash
# Scan JARs in current directory
python -m tools.asset_scanner

# Scan JARs in specific directory
python -m tools.asset_scanner --input-dir ./mods --output-dir ./results

# Filter by namespace
python -m tools.asset_scanner --namespace minecraft

# Custom cleaning passes
python -m tools.asset_scanner --clean-passes 5
```

**Options:**
- `--input-dir`: Directory containing JAR files (default: current directory)
- `--output-dir`: Output directory (default: `jar_scan_results`)
- `--namespace`: Filter by specific namespace (case-insensitive)
- `--clean-passes`: Number of cleaning passes (default: 3)
- `--threads`: Number of worker threads (default: CPU count)
- `--skip-raw`: Delete raw files after cleaning
- `--verbose`: Enable verbose error output

### 2. Recipe Scanner (`tools/recipe_scanner.py`)

Scans JAR files for recipe JSON files and extracts recipe results by namespace. By default excludes vanilla Minecraft recipes.

**Features:**
- Extracts recipe results from JSON files
- Groups results by namespace
- Filters out vanilla Minecraft recipes (configurable)
- Sorts and deduplicates results

**Usage:**
```bash
# Scan JARs (exclude minecraft recipes)
python -m tools.recipe_scanner

# Include minecraft recipes
python -m tools.recipe_scanner --include-minecraft

# Custom input/output
python -m tools.recipe_scanner --input-dir ./mods --output-dir ./results
```

**Options:**
- `--input-dir`: Directory containing JAR files (default: current directory)
- `--output-dir`: Output directory (default: `jar_scan_results`)
- `--include-minecraft`: Include minecraft: recipes (default: exclude)
- `--namespace`: Filter by specific namespace (case-insensitive)
- `--threads`: Number of worker threads (default: CPU count)
- `--skip-raw`: Delete raw files after cleaning
- `--verbose`: Enable verbose error output

### 3. Block Matcher (`tools/block_matcher.py`)

Finds duplicate blocks across different namespaces and generates mapping files for block matching. Useful for mod compatibility and block unification.

**Features:**
- Identifies blocks that exist in multiple namespaces
- Interactive namespace selection
- Multiple output formats (JSON, CSV, TXT)
- Non-interactive mode for automation

**Usage:**
```bash
# Interactive mode (default)
python -m tools.block_matcher

# Non-interactive with pre-selected namespace
python -m tools.block_matcher --namespace minecraft --no-interactive

# Custom input/output
python -m tools.block_matcher --input-dir ./results --output-file ./matches.json

# Export as CSV
python -m tools.block_matcher --format csv --output-file matches.csv
```

**Options:**
- `--input-dir`: Directory containing .txt files (default: current directory)
- `--output-file`: Output file path (default: `matches.json` in input directory)
- `--namespace`: Pre-select namespace (enables non-interactive mode)
- `--no-interactive`: Disable interactive namespace selection
- `--format`: Output format - json, csv, or txt (default: json)

### 4. Items Matcher (`tools/items_matcher.py`)

Generates datapacks for the OneEnough Items (OEI) mod from JSON configuration files. Creates replacement mappings that allow items to be unified across different mods.

**Features:**
- Reads JSON configuration with matchItems and resultItems
- Validates configuration to prevent self-replacement bugs
- Generates complete datapack structure
- Supports item tags (e.g., `#forge:ore`)

**Usage:**
```bash
# Generate datapack from config.json
python -m tools.items_matcher --config config.json

# Specify custom output directory
python -m tools.items_matcher --config config.json --output-dir ./datapacks/oei

# Custom pack format
python -m tools.items_matcher --config config.json --pack-format 15
```

**Options:**
- `--config`: Path to JSON configuration file (required)
- `--output-dir`: Output directory for datapack (default: `oei_datapack`)
- `--pack-format`: Minecraft datapack format version (default: 10)
- `--filename`: Name of the replacements file (default: `replacements.json`)

**Configuration Format:**
```json
[
    {
        "matchItems": [
            "#forge:ore",
            "minecraft:potato",
            "minecraft:carrot"
        ],
        "resultItems": "minecraft:egg"
    }
]
```

**Warning:** Never replace an item with itself – this may cause critical bugs!

## Installation

### Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd RD-Minecraft-Tools
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. No additional packages need to be installed - all tools use Python's standard library.

### Development Setup

For development and testing, optional dependencies are available:

```bash
pip install pytest pytest-cov flake8 black mypy
```

See `requirements.txt` for details.

## Output Structure

### Asset Scanner Output

```
jar_scan_results/
├── blocks/
│   ├── {namespace}_blocks_raw.txt    # Raw extracted blocks
│   └── {namespace}_blocks.txt        # Cleaned blocks
└── items/
    ├── {namespace}_items_raw.txt     # Raw extracted items
    └── {namespace}_items.txt         # Cleaned items
```

### Recipe Scanner Output

```
jar_scan_results/
└── recipes/
    ├── {namespace}_recipes_raw.txt   # Raw extracted recipes
    └── {namespace}_recipes.txt       # Cleaned recipes
```

### Block Matcher Output

- `matches.json` - JSON format with matchBlock and resultBlock mappings
- `matches.csv` - CSV format (if --format csv)
- `matches.txt` - Text format (if --format txt)

## File Formats

### Input Files

- **JAR files**: Standard Minecraft mod JAR files (Forge/Fabric compatible)
- **Text files**: For block matcher, expects files with format `namespace:block_id` (one per line)

### Output Files

- **Text files**: Format `namespace:identifier` (one per line)
- **JSON files**: Array of objects with `matchBlock` and `resultBlock` fields
- **CSV files**: Two columns: `matchBlock` and `resultBlock`

## Examples

### Complete Workflow

1. **Extract assets from mods:**
```bash
python -m tools.asset_scanner --input-dir ./mods --output-dir ./scan_results
```

2. **Extract recipes:**
```bash
python -m tools.recipe_scanner --input-dir ./mods --output-dir ./scan_results
```

3. **Find duplicate blocks:**
```bash
python -m tools.block_matcher --input-dir ./scan_results/blocks --output-file ./matches.json
```

## Project Structure

```
RD-Minecraft-Tools/
├── tools/              # Main tool scripts
│   ├── asset_scanner.py
│   ├── recipe_scanner.py
│   ├── block_matcher.py
│   └── items_matcher.py
├── src/                # Shared utilities
│   └── utils.py
├── LICENSE             # MIT License
├── requirements.txt    # Dependencies (currently none)
└── README.md           # This file
```

## Testing

Run the test suite with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tools --cov=src

# Run specific test file
pytest tests/test_asset_scanner.py
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to new code
- Write unit tests for new features
- Update documentation as needed
- Run tests before submitting: `pytest`
- Check code style: `flake8 tools src tests`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Notes

- All tools are designed to work with Minecraft mod JAR files (Forge/Fabric compatible)
- Tools use multi-threading for concurrent JAR processing
- Output directories are created automatically
- Tools handle errors gracefully and continue processing other files

