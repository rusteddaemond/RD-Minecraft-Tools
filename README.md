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

Scan all types (default):

```bash
python scanner.py
```

Scan specific types:

```bash
# Items only
python scanner.py -i
```

```bash
# Blocks only
python scanner.py -b
```

```bash
# Fluids only
python scanner.py -f
```

```bash
# Items and blocks
python scanner.py -i -b
```

Custom directories:

```bash
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

Find pairs for all types (default):

```bash
python finder.py
```

Find pairs for specific types:

```bash
# Items only
python finder.py -i
```

```bash
# Blocks only
python finder.py -b
```

```bash
# Fluids only
python finder.py -f
```

```bash
# Items and blocks
python finder.py -i -b
```

Custom options:

```bash
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

Build items datapack:

```bash
python builder.py -i
```

Build blocks datapack:

```bash
python builder.py -b
```

Build fluids datapack:

```bash
python builder.py -f
```

Specify result namespace:

```bash
python builder.py -i -n create
```

Custom output directory:

```bash
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

## License

MIT License
