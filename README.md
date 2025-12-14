# RD-Minecraft-Tools

**Version 0.1.0**

A collection of standalone Python scripts for scanning and analyzing Minecraft mod JAR files. Each script is independent and uses only Python standard library - no external dependencies required.

## Overview

These tools scan Minecraft mod JAR files to extract and categorize:
- Blocks and items
- Recipes and recipe types
- Tags and tag groups
- Item categories and properties

All scripts are standalone and can be run independently without any configuration or setup.

## Tools

### 🔍 Block and Item Scanner

**Script:** `scan_mods_blocks_items.py`

Scans all mod JAR files in the `/mods` directory and extracts blocks and items.

**Features:**
- Discovers blocks and items from multiple sources (data files, assets, blockstates, models)
- Outputs complete catalogues: `blocks.txt` and `items.txt`
- Organizes by namespace: `blocks/{namespace}.txt` and `items/{namespace}.txt`
- Format: `namespace:item` (one per line)

**Usage:**
```bash
python scan_mods_blocks_items.py
# Or specify custom mods directory:
python scan_mods_blocks_items.py /path/to/mods
```

**Output:**
- `scan_output/blocks.txt` - All blocks (complete catalogue)
- `scan_output/items.txt` - All items (complete catalogue)
- `scan_output/blocks/{namespace}.txt` - Blocks per namespace
- `scan_output/items/{namespace}.txt` - Items per namespace

---

### 📊 Block and Item Categorizer

**Script:** `categorize_blocks_items.py`

Categorizes blocks and items from scan output into common categories (wood, stone, ore, metal, etc.).

**Features:**
- Reads `blocks.txt` and `items.txt` from scan output
- Categorizes by name patterns (wood, stone, ore, metal, gem, food, tool, armor, etc.)
- Outputs categorized files for easy searching

**Usage:**
```bash
python categorize_blocks_items.py
# Or specify custom output directory:
python categorize_blocks_items.py scan_output
```

**Output:**
- `scan_output/categories/blocks/{category}.txt` - Blocks by category
- `scan_output/categories/items/{category}.txt` - Items by category
- `scan_output/categories/summary.txt` - Summary with counts

**Categories:**
- Wood (logs, planks, fences, doors, etc.)
- Stone (stone, cobblestone, bricks, etc.)
- Ore (ores, ingots, nuggets, gems, etc.)
- Metal (iron, gold, copper, steel, etc.)
- Gem (diamond, emerald, ruby, etc.)
- Food (berries, fruits, vegetables, etc.)
- Tool (pickaxes, axes, swords, etc.)
- Armor (helmets, chestplates, etc.)
- And many more...

---

### 🔬 Dynamic Recipe and Tag Scanner

**Script:** `scan_mods_recipes_dynamic.py`

Dynamically discovers ALL recipe types and tag groups from mods, including custom mod recipe types.

**Features:**
- **Two-pass scanning:**
  - Pass 1: Collects ALL tags from all mods
  - Pass 2: Scans recipes and categorizes using collected tags
- Discovers all recipe types dynamically (not just predefined ones)
- Discovers all tag types dynamically (blocks, items, fluids, entity_types, worldgen, etc.)
- Categorizes items by recipe properties (smeltable, craftable, pickaxeable, wearable, etc.)
- Creates reverse lookups (item → tags)

**Usage:**
```bash
python scan_mods_recipes_dynamic.py
# Or specify custom mods directory:
python scan_mods_recipes_dynamic.py /path/to/mods
```

**Output:**
- `scan_output/dynamic/recipe_types/` - All discovered recipe types
  - `all_recipe_types.txt` - Summary of all types
  - `recipes/{recipe_type}.txt` - Recipes per type
- `scan_output/dynamic/tags/` - All discovered tag groups
  - `all_tags_summary.txt` - Summary with common c: tags check
  - `{tag_type}/{tag_name}.txt` - Items in each tag
- `scan_output/dynamic/categories/` - Categorized items
  - `recipe_inputs/{recipe_type}.txt` - Items used as inputs
  - `recipe_outputs/{recipe_type}.txt` - Items produced
  - `items_by_tag/{tag_type}/{tag_name}.txt` - Items categorized by tags
  - `item_to_tags/all_items_with_tags.txt` - Reverse lookup
- `scan_output/dynamic/summary.txt` - Comprehensive summary

**Recipe Types Discovered:**
- All standard Minecraft recipe types (crafting, smelting, blasting, etc.)
- Custom mod recipe types (woodcutting, sawmill, etc.)
- Any recipe type introduced by mods

**Tag Types Discovered:**
- Blocks, Items, Fluids, Entity Types
- Worldgen tags
- Any custom tag types from mods

---

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd RD-Minecraft-Tools
   ```

2. **Place your mod JAR files in the `mods/` directory**

3. **Run the scanners:**
   ```bash
   # Scan blocks and items
   python scan_mods_blocks_items.py
   
   # Categorize blocks and items
   python categorize_blocks_items.py
   
   # Scan recipes and tags
   python scan_mods_recipes_dynamic.py
   ```

4. **Check the output in `scan_output/` directory**

## Requirements

- **Python 3.7 or higher**
- **No external dependencies** - uses only Python standard library:
  - `zipfile` - For reading JAR files
  - `json` - For parsing JSON files
  - `pathlib` - For file operations
  - `collections` - For data structures
  - `re` - For pattern matching

## Directory Structure

```
RD-Minecraft-Tools/
├── scan_mods_blocks_items.py      # Block/item scanner
├── categorize_blocks_items.py      # Block/item categorizer
├── scan_mods_recipes_dynamic.py    # Recipe/tag scanner
├── mods/                           # Your mod JAR files (place here)
├── example_mods/                   # Example mod files
├── scan_output/                    # Output from scanners
└── README.md                       # This file
```

## Output Format

All output files use the format `namespace:item` (one per line), for example:
```
minecraft:oak_log
minecraft:oak_planks
aether:skyroot_log
create:copper_ore
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Version History

### 0.1.0 (Current)
- Initial release with standalone scanners
- Block and item scanner
- Block and item categorizer
- Dynamic recipe and tag scanner
