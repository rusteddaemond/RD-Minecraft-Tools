# Detailed Usage Guide

This document provides comprehensive usage instructions for all tools in RD-Minecraft-Tools.

## Table of Contents

- [Asset Scanner](#asset-scanner)
- [Recipe Scanner](#recipe-scanner)
- [Block Matcher](#block-matcher)
- [Items Matcher](#items-matcher)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Asset Scanner

### Overview

The Asset Scanner extracts block and item identifiers from Minecraft mod JAR files. It scans for:
- Block models: `assets/{namespace}/models/block/*`
- Block textures: `assets/{namespace}/textures/block/*`
- Item models: `assets/{namespace}/models/item/*`
- Item textures: `assets/{namespace}/textures/item/*`

### Basic Usage

```bash
# Scan JARs in current directory
python -m tools.asset_scanner
```

This will:
1. Find all `.jar` files in the current directory
2. Extract assets to `jar_scan_results/blocks/` and `jar_scan_results/items/`
3. Create both raw and cleaned output files

### Advanced Options

#### Specify Input/Output Directories

```bash
# Scan JARs from mods folder, output to results folder
python -m tools.asset_scanner --input-dir ./mods --output-dir ./results
```

#### Filter by Namespace

```bash
# Only extract assets from 'minecraft' namespace
python -m tools.asset_scanner --namespace minecraft
```

#### Custom Cleaning Passes

The cleaning process removes file extensions and affixes. More passes = more aggressive cleaning:

```bash
# Use 5 cleaning passes instead of default 3
python -m tools.asset_scanner --clean-passes 5
```

#### Thread Control

```bash
# Use 8 worker threads (default: CPU count)
python -m tools.asset_scanner --threads 8
```

#### Clean Up Raw Files

```bash
# Delete raw files after cleaning (keeps only cleaned output)
python -m tools.asset_scanner --skip-raw
```

#### Verbose Output

```bash
# Show detailed error messages
python -m tools.asset_scanner --verbose
```

### Output Format

**Raw Files** (`*_blocks_raw.txt`, `*_items_raw.txt`):
```
minecraft:dirt
minecraft:dirt_side
minecraft:dirt_top
minecraft:stone
```

**Cleaned Files** (`*_blocks.txt`, `*_items.txt`):
```
minecraft:dirt
minecraft:stone
```

The cleaned files have:
- File extensions removed (`.png`, `.jpg`, etc.)
- Orientation affixes removed (`_top`, `_side`, `_bottom`, etc.)
- State affixes removed (`_open`, `_closed`, `_on`, `_off`, etc.)
- Duplicates removed
- Sorted alphabetically

### Example Output Structure

```
jar_scan_results/
├── blocks/
│   ├── minecraft_blocks_raw.txt
│   ├── minecraft_blocks.txt
│   ├── modname_blocks_raw.txt
│   └── modname_blocks.txt
└── items/
    ├── minecraft_items_raw.txt
    ├── minecraft_items.txt
    ├── modname_items_raw.txt
    └── modname_items.txt
```

---

## Recipe Scanner

### Overview

The Recipe Scanner extracts recipe results from Minecraft mod JAR files. It scans for recipe JSON files under:
- `data/{namespace}/recipes/*.json`
- `data/{namespace}/recipe/*.json` (alternative path)

### Basic Usage

```bash
# Scan JARs in current directory (excludes minecraft recipes)
python -m tools.recipe_scanner
```

### Advanced Options

#### Include Minecraft Recipes

By default, vanilla Minecraft recipes are excluded. To include them:

```bash
python -m tools.recipe_scanner --include-minecraft
```

#### Specify Directories

```bash
python -m tools.recipe_scanner --input-dir ./mods --output-dir ./results
```

#### Filter by Namespace

```bash
# Only extract recipes from 'modname' namespace
python -m tools.recipe_scanner --namespace modname
```

#### Other Options

```bash
# Use 8 threads, skip raw files, verbose output
python -m tools.recipe_scanner --threads 8 --skip-raw --verbose
```

### Output Format

**Raw Files** (`*_recipes_raw.txt`):
```
modname:iron_ingot
modname:gold_ingot
modname:copper_ingot
```

**Cleaned Files** (`*_recipes.txt`):
```
modname:copper_ingot
modname:gold_ingot
modname:iron_ingot
```

Cleaned files are:
- Deduplicated
- Sorted alphabetically

### Recipe JSON Format Support

The scanner supports multiple recipe formats:
- Single result: `{"result": "modname:item"}`
- Result object: `{"result": {"id": "modname:item"}}`
- Multiple results: `{"results": [{"id": "modname:item1"}, {"id": "modname:item2"}]}`

---

## Block Matcher

### Overview

The Block Matcher finds duplicate blocks across different namespaces. This is useful for:
- Mod compatibility checking
- Block unification projects
- Identifying conflicting block IDs

### Basic Usage (Interactive)

```bash
# Interactive mode - prompts for namespace selection
python -m tools.block_matcher
```

The tool will:
1. Scan all `.txt` files in the current directory
2. Find blocks that appear in multiple namespaces
3. Display duplicates and prompt you to choose a target namespace
4. Generate a mapping file

### Non-Interactive Mode

```bash
# Pre-select namespace (no prompts)
python -m tools.block_matcher --namespace minecraft --no-interactive
```

### Specify Input Directory

```bash
# Scan blocks from asset scanner output
python -m tools.block_matcher --input-dir ./jar_scan_results/blocks
```

### Custom Output File

```bash
# Specify output file path
python -m tools.block_matcher --output-file ./my_matches.json
```

### Output Formats

#### JSON Format (Default)

```json
[
  {
    "matchBlock": "modname:dirt",
    "resultBlock": "minecraft:dirt"
  },
  {
    "matchBlock": "othermod:dirt",
    "resultBlock": "minecraft:dirt"
  }
]
```

#### CSV Format

```bash
python -m tools.block_matcher --format csv --output-file matches.csv
```

Output:
```csv
matchBlock,resultBlock
modname:dirt,minecraft:dirt
othermod:dirt,minecraft:dirt
```

#### Text Format

```bash
python -m tools.block_matcher --format txt --output-file matches.txt
```

Output:
```
modname:dirt -> minecraft:dirt
othermod:dirt -> minecraft:dirt
```

### Input File Format

The Block Matcher expects text files with format:
```
namespace:block_id
```

One entry per line. Example:
```
minecraft:dirt
minecraft:stone
modname:dirt
modname:copper_ore
```

---

## Items Matcher

### Overview

The Items Matcher generates datapacks for the OneEnough Items (OEI) mod. OEI is datapack-driven and supports hot reloading. This tool reads a JSON configuration file and creates the proper datapack structure with replacement mappings.

### Basic Usage

```bash
# Generate datapack from config.json
python -m tools.items_matcher --config config.json
```

This will:
1. Load and validate the configuration file
2. Create the datapack structure at `data/oei/replacements`
3. Generate the replacements JSON file
4. Create `pack.mcmeta` for the datapack

### Configuration Format

Create a JSON file with the following structure:

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

**Fields:**
- `matchItems`: Array of item IDs or tags (tags start with `#`) to be replaced
- `resultItems`: Single item ID that will replace all items in `matchItems`

**Important:** Never replace an item with itself – this may cause critical bugs!

### Advanced Options

#### Specify Output Directory

```bash
# Output to custom directory
python -m tools.items_matcher --config config.json --output-dir ./datapacks/oei
```

#### Custom Pack Format

```bash
# Use Minecraft 1.20.2+ pack format (15)
python -m tools.items_matcher --config config.json --pack-format 15
```

#### Custom Filename

```bash
# Use custom filename for replacements file
python -m tools.items_matcher --config config.json --filename custom_replacements.json
```

### Output Structure

The tool generates a complete datapack structure:

```
oei_datapack/
├── pack.mcmeta
└── data/
    └── oei/
        └── replacements/
            └── replacements.json
```

### Installation

To use the generated datapack:

1. Copy the entire output directory to your Minecraft world's datapacks folder:
   ```
   .minecraft/saves/<world>/datapacks/oei_datapack/
   ```

2. The datapack will be automatically loaded when you reload datapacks in-game (`/reload` command)

### Example Configuration

**Example 1: Unify Ores**
```json
[
    {
        "matchItems": [
            "#forge:ore",
            "minecraft:iron_ore",
            "minecraft:gold_ore"
        ],
        "resultItems": "minecraft:iron_ore"
    }
]
```

**Example 2: Multiple Replacement Rules**
```json
[
    {
        "matchItems": ["minecraft:potato", "minecraft:carrot"],
        "resultItems": "minecraft:egg"
    },
    {
        "matchItems": ["#forge:ingots/iron"],
        "resultItems": "minecraft:iron_ingot"
    }
]
```

### Validation

The tool automatically validates:
- Configuration is valid JSON
- All required fields are present
- `matchItems` is a non-empty array
- `resultItems` is a string
- **Items are not replaced with themselves** (prevents critical bugs)

### Error Messages

**Configuration file not found:**
```
[ERROR] Configuration file not found: config.json
```
Solution: Verify the path to your configuration file is correct.

**Invalid JSON:**
```
[ERROR] Invalid JSON in configuration file: ...
```
Solution: Check your JSON syntax using a JSON validator.

**Self-replacement detected:**
```
[ERROR] Configuration validation failed: Entry 0: Cannot replace item with itself. 'minecraft:egg' is in both matchItems and resultItems
```
Solution: Remove the item from `matchItems` if it matches `resultItems`.

---

## Common Workflows

### Workflow 1: Complete Mod Analysis

Analyze all mods in a directory:

```bash
# Step 1: Extract assets
python -m tools.asset_scanner --input-dir ./mods --output-dir ./analysis

# Step 2: Extract recipes
python -m tools.recipe_scanner --input-dir ./mods --output-dir ./analysis

# Step 3: Find duplicate blocks
python -m tools.block_matcher --input-dir ./analysis/blocks --output-file ./analysis/block_matches.json
```

### Workflow 2: Single Mod Analysis

Analyze a specific mod:

```bash
# Extract assets from single mod
python -m tools.asset_scanner --input-dir ./single_mod --namespace modname --output-dir ./modname_analysis
```

### Workflow 3: Automated Block Matching

For CI/CD or automation:

```bash
# Non-interactive block matching
python -m tools.block_matcher \
  --input-dir ./results/blocks \
  --namespace minecraft \
  --no-interactive \
  --format json \
  --output-file ./matches.json
```

### Workflow 4: Clean Output Only

If you only want cleaned output (no raw files):

```bash
python -m tools.asset_scanner --skip-raw
python -m tools.recipe_scanner --skip-raw
```

---

## Troubleshooting

### No JAR Files Found

**Error:** `No .jar files found in {directory}`

**Solutions:**
- Verify the directory path is correct
- Check that files have `.jar` extension (case-sensitive on Linux/Mac)
- Ensure you have read permissions for the directory

### Permission Denied

**Error:** `Access denied to '{directory}'`

**Solutions:**
- Check file/directory permissions
- Run with appropriate permissions (admin/sudo if needed)
- The tool will automatically use a temp directory as fallback

### Bad Zip File

**Warning:** `Bad zip file: {filename}`

**Solutions:**
- The JAR file may be corrupted
- Try re-downloading the mod
- The tool will skip corrupted files and continue

### No Duplicates Found

**Message:** `No cross-namespace duplicates found`

**Solutions:**
- This is normal if blocks don't overlap across namespaces
- Verify input files contain blocks in format `namespace:block_id`
- Check that multiple namespaces are present in the files

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solutions:**
- Run from the repository root directory
- Use `python -m tools.asset_scanner` (not `python tools/asset_scanner.py`)
- Ensure you're using Python 3.7+

### Empty Output Files

**Issue:** Output files are created but empty

**Solutions:**
- Check that JAR files contain assets/recipes in expected paths
- Verify namespace filtering isn't excluding everything
- Use `--verbose` flag to see detailed processing information

### Thread Errors

**Error:** `Thread error: {error}`

**Solutions:**
- Reduce thread count with `--threads 1`
- Check system resources (memory, file handles)
- Use `--verbose` for detailed error information

---

## Performance Tips

1. **Use appropriate thread count**: Default (CPU count) is usually optimal, but reduce if you encounter resource issues

2. **Skip raw files**: Use `--skip-raw` to save disk space if you only need cleaned output

3. **Namespace filtering**: Filter by namespace early to reduce processing time

4. **Batch processing**: Process mods in batches if you have many JAR files

5. **Output directory**: Use fast storage (SSD) for output directory if processing many files

---

## Command Reference

### Asset Scanner

```bash
python -m tools.asset_scanner [OPTIONS]

Options:
  --input-dir PATH      Directory containing JAR files (default: current dir)
  --output-dir PATH     Output directory (default: jar_scan_results)
  --namespace NAME      Filter by namespace (case-insensitive)
  --clean-passes N      Number of cleaning passes (default: 3)
  --threads N           Worker threads (default: CPU count)
  --skip-raw            Delete raw files after cleaning
  --verbose, -v         Enable verbose error output
  --help, -h            Show help message
```

### Recipe Scanner

```bash
python -m tools.recipe_scanner [OPTIONS]

Options:
  --input-dir PATH      Directory containing JAR files (default: current dir)
  --output-dir PATH     Output directory (default: jar_scan_results)
  --include-minecraft   Include minecraft: recipes (default: exclude)
  --namespace NAME      Filter by namespace (case-insensitive)
  --threads N           Worker threads (default: CPU count)
  --skip-raw            Delete raw files after cleaning
  --verbose, -v         Enable verbose error output
  --help, -h            Show help message
```

### Block Matcher

```bash
python -m tools.block_matcher [OPTIONS]

Options:
  --input-dir PATH      Directory containing .txt files (default: current dir)
  --output-file PATH    Output file path (default: matches.json)
  --namespace NAME      Pre-select namespace (non-interactive)
  --no-interactive      Disable interactive prompts
  --format FORMAT       Output format: json, csv, or txt (default: json)
  --help, -h            Show help message
```

### Items Matcher

```bash
python -m tools.items_matcher [OPTIONS]

Options:
  --config PATH         Path to JSON configuration file (required)
  --output-dir PATH Output directory for datapack (default: oei_datapack)
  --pack-format N       Minecraft datapack format version (default: 10)
  --filename NAME       Name of replacements file (default: replacements.json)
  --help, -h            Show help message
```

