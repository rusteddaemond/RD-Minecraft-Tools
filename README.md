# RD-Minecraft-Tools

**Version 0.1.0**

A unified dynamic scanner for analyzing Minecraft mod JAR files. Uses tags as the primary truth - everything else is derived from them.

## Installation

### Using Git

```bash
git clone https://github.com/rusteddaemond/RD-Minecraft-Tools.git
cd RD-Minecraft-Tools
```

### Using Wget

```bash
wget https://github.com/rusteddaemond/RD-Minecraft-Tools/archive/refs/heads/main.zip
unzip main.zip
cd RD-Minecraft-Tools-main
```

### Using Curl

```bash
curl -L https://github.com/rusteddaemond/RD-Minecraft-Tools/archive/refs/heads/main.zip -o RD-Minecraft-Tools.zip
unzip RD-Minecraft-Tools.zip
cd RD-Minecraft-Tools-main
```

## Quick Start

1. Place your mod JAR files in the `mods/` directory
2. Run the scanner:
   ```bash
   python scanner.py
   ```
3. Find mod pairs:
   ```bash
   python finder.py
   ```
4. Build datapacks:
   ```bash
   python builder.py -i
   ```

## Commands

### Scanner

Scans mod JAR files and extracts tags, recipes, and items.

```bash
# Scan all types (default)
python scanner.py

# Scan specific types
python scanner.py -i          # Items only
python scanner.py -b          # Blocks only
python scanner.py -f          # Fluids only
python scanner.py -i -b       # Items and blocks

# Custom directories
python scanner.py -m ./my_mods -o ./my_output
```

**Flags:**
- `-m, --mods-dir` - Directory containing mod JAR files (default: `mods/`)
- `-o, --output-dir` - Directory to save scan results (default: `scan_output/`)
- `-i, --items` - Process items
- `-b, --blocks` - Process blocks
- `-f, --fluids` - Process fluids

### Finder

Finds mod pairs with overlapping base names for datapack generation.

```bash
# Find pairs for all types (default)
python finder.py

# Find pairs for specific types
python finder.py -i          # Items only
python finder.py -b           # Blocks only
python finder.py -f           # Fluids only
python finder.py -i -b        # Items and blocks

# Custom options
python finder.py -m 5 -o ./my_find_output
```

**Flags:**
- `-m, --min-matches` - Minimum matches required (default: 1)
- `-o, --output` - Output directory (default: `find_output/`)
- `-i, --items` - Process items
- `-b, --blocks` - Process blocks
- `-f, --fluids` - Process fluids

### Builder

Builds datapack files from scanned mod data.

```bash
# Build items datapack
python builder.py -i

# Build blocks datapack
python builder.py -b

# Build fluids datapack
python builder.py -f

# Specify result namespace
python builder.py -i -n create

# Custom output directory
python builder.py -i -o ./my_datapack
```

**Flags:**
- `-i, --items` - Build items datapack
- `-b, --blocks` - Build blocks datapack
- `-f, --fluids` - Build fluids datapack
- `-n, --result-namespace` - Result namespace (default: prompts for selection)
- `-o, --output-dir` - Output directory (default: `build_output/`)

**Note:** Builder searches for `.txt` files in the project root directory. Place your mod files there before running.

## Output Structure

```
scan_output/          # Scanner output
├── tags/             # Tag groups by type
├── tag_to_items/     # Tag → items (installed/not_installed)
├── item_to_tags/     # Item → tags (installed/not_installed)
├── recipes/          # Recipe data (by_mod, by_type, item_inputs, item_outputs)
├── items/            # Items by namespace (installed/not_installed)
├── blocks/           # Blocks by namespace (installed/not_installed)
├── fluids/           # Fluids by namespace (installed/not_installed)
├── mods/             # Mod information (installed/not_installed)
└── summary.txt       # Summary

find_output/          # Finder output
├── items/            # Items pairs and summaries
├── blocks/           # Blocks pairs and summaries
├── fluids/           # Fluids pairs and summaries
└── *_summary.txt     # Type-specific summaries

build_output/         # Builder output
└── [datapack files]
```

## Requirements

- Python 3.7+
- No external dependencies (uses only Python standard library)

## License

MIT License
