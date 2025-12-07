# Architecture Documentation

This document explains the internal architecture and design decisions of RD-Minecraft-Tools.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Tool Architecture](#tool-architecture)
- [Data Flow](#data-flow)
- [Threading Model](#threading-model)
- [File Formats](#file-formats)
- [Design Decisions](#design-decisions)

---

## Overview

RD-Minecraft-Tools is a collection of Python tools for analyzing Minecraft mod JAR files. The tools are designed to be:
- **Modular**: Each tool is independent but shares common utilities
- **Thread-safe**: Concurrent processing of multiple JAR files
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Extensible**: Easy to add new tools or features

---

## Project Structure

```
RD-Minecraft-Tools/
├── tools/              # Main tool modules
│   ├── __init__.py
│   ├── asset_scanner.py
│   ├── recipe_scanner.py
│   └── block_matcher.py
├── src/                # Shared utilities
│   ├── __init__.py
│   └── utils.py       # Common functions (logging, thread-safe I/O)
├── tests/             # Unit tests
│   ├── __init__.py
│   ├── test_asset_scanner.py
│   ├── test_recipe_scanner.py
│   └── test_block_matcher.py
└── docs/              # Documentation
    ├── USAGE.md
    └── ARCHITECTURE.md
```

### Module Organization

- **tools/**: Contains the main tool scripts, each as an independent module
- **src/**: Shared code used by multiple tools (DRY principle)
  - `utils.py`: Core utilities (logging, thread-safe I/O, directory management)
  - `jar_processor.py`: JAR file discovery, validation, and output directory creation
  - `arg_parser.py`: Common command-line argument definitions
  - `thread_pool.py`: Standardized concurrent execution patterns
- **tests/**: Unit tests mirroring the tool structure
- **docs/**: User and developer documentation

---

## Tool Architecture

### Asset Scanner

**Purpose**: Extract block/item identifiers from JAR files

**Process Flow**:
1. **Discovery Phase**: Find all `.jar` files in input directory
2. **Scanning Phase**: Concurrently process each JAR file
   - Open JAR as ZIP archive
   - Iterate through entries
   - Filter by path pattern (`assets/{namespace}/models|textures/{block|item}/*`)
   - Extract namespace and identifier
   - Buffer entries by namespace
3. **Writing Phase**: Thread-safely write raw entries to files
4. **Cleaning Phase**: Process raw files
   - Remove file extensions
   - Remove affixes (orientation, state, etc.)
   - Deduplicate
   - Sort alphabetically

**Key Components**:
- `AFFIX_GROUPS`: Dictionary of affix categories for cleaning
- `clean_identifier()`: Recursive cleaning function
- `process_jar()`: Per-JAR processing function
- `clean_results()`: Post-processing cleaning function

### Recipe Scanner

**Purpose**: Extract recipe results from JAR files

**Process Flow**:
1. **Discovery Phase**: Find all `.jar` files
2. **Scanning Phase**: Concurrently process each JAR
   - Open JAR as ZIP archive
   - Find recipe JSON files (`data/{namespace}/recipe*/*.json`)
   - Parse JSON and extract result IDs
   - Filter out `minecraft:` recipes (unless included)
   - Buffer by namespace
3. **Writing Phase**: Thread-safely write raw entries
4. **Cleaning Phase**: Deduplicate and sort

**Key Components**:
- `extract_results_from_json()`: JSON parsing with multiple format support
- `process_jar()`: Per-JAR processing
- `clean_results()`: Deduplication and sorting

### Block Matcher

**Purpose**: Find duplicate blocks across namespaces

**Process Flow**:
1. **Discovery Phase**: Find all `.txt` files in input directory
2. **Loading Phase**: Parse text files
   - Read each line as `namespace:block_id`
   - Build map: `block_id -> [namespaces]`
3. **Filtering Phase**: Find duplicates
   - Filter blocks appearing in multiple namespaces
4. **Selection Phase**: Choose target namespace
   - Interactive: Prompt user
   - Non-interactive: Use provided namespace
5. **Generation Phase**: Build match mappings
   - Create `matchBlock -> resultBlock` pairs
6. **Output Phase**: Write in selected format (JSON/CSV/TXT)

**Key Components**:
- `load_blocks()`: Parse text files into data structure
- `filter_duplicates()`: Find cross-namespace duplicates
- `choose_result_namespace()`: User interaction or auto-selection
- `build_matches()`: Generate mapping pairs

---

## Data Flow

### Asset Scanner Data Flow

```
JAR Files
    ↓
[Concurrent Processing]
    ↓
Raw Entries (namespace:identifier)
    ↓
[Thread-safe Writing]
    ↓
*_raw.txt files
    ↓
[Cleaning Process]
    ↓
Cleaned Entries (normalized)
    ↓
*.txt files (final output)
```

### Recipe Scanner Data Flow

```
JAR Files
    ↓
[Concurrent Processing]
    ↓
Recipe JSON Files
    ↓
[JSON Parsing]
    ↓
Result IDs
    ↓
[Filtering (exclude minecraft:)]
    ↓
*_recipes_raw.txt files
    ↓
[Deduplication & Sorting]
    ↓
*_recipes.txt files (final output)
```

### Block Matcher Data Flow

```
*.txt files (from asset scanner)
    ↓
[Parsing]
    ↓
block_id -> [namespaces] map
    ↓
[Duplicate Detection]
    ↓
Duplicate blocks
    ↓
[Namespace Selection]
    ↓
Match mappings
    ↓
[Format Conversion]
    ↓
matches.json/csv/txt
```

---

## Threading Model

### Concurrent Processing

Both Asset Scanner and Recipe Scanner use the shared `execute_concurrent()` function from `src.thread_pool` for concurrent JAR processing:

```python
from src.thread_pool import execute_concurrent

def process_jar_wrapper(jar_path: Path) -> None:
    process_jar(jar_path, ...)

execute_concurrent(jars, process_jar_wrapper, max_workers=max_workers, verbose=args.verbose)
```

This provides standardized error handling and thread management across all tools.

**Benefits**:
- I/O-bound operations (reading JAR files) benefit from threading
- Multiple JARs processed simultaneously
- Scales with CPU count

### Thread-Safe File Writing

Since multiple threads write to the same output files, we use locks:

```python
_write_locks: Dict[Path, threading.Lock] = {}
_write_locks_lock = threading.Lock()

def get_lock(path: Path) -> threading.Lock:
    with _write_locks_lock:
        if path not in _write_locks:
            _write_locks[path] = threading.Lock()
        return _write_locks[path]

def write_entry(out_file: Path, lines: List[str]):
    lock = get_lock(out_file)
    with lock:
        with out_file.open("a", encoding="utf-8") as f:
            f.writelines(lines)
```

**Design**:
- One lock per output file
- Lock creation is thread-safe
- Append mode for concurrent writes

---

## File Formats

### Input Formats

#### JAR Files
- Standard ZIP archives
- Structure: `assets/{namespace}/...` or `data/{namespace}/...`
- Must be readable as ZIP files

#### Text Files (Block Matcher)
- Format: `namespace:block_id` (one per line)
- Encoding: UTF-8
- Example:
  ```
  minecraft:dirt
  minecraft:stone
  modname:copper_ore
  ```

### Output Formats

#### Text Files
- Format: `namespace:identifier` (one per line)
- Encoding: UTF-8
- Sorted alphabetically
- Deduplicated

#### JSON Files
```json
[
  {
    "matchBlock": "namespace:block_id",
    "resultBlock": "namespace:block_id"
  }
]
```

#### CSV Files
```csv
matchBlock,resultBlock
namespace:block_id,namespace:block_id
```

---

## Design Decisions

### Why Threading Instead of Multiprocessing?

- **I/O-bound operations**: Reading JAR files is I/O-bound, not CPU-bound
- **Shared state**: Need to write to same files (easier with threads)
- **Lower overhead**: Threads have less overhead than processes
- **GIL impact**: GIL doesn't significantly impact I/O operations

### Why Separate Raw and Cleaned Files?

- **Transparency**: Users can see what was extracted before cleaning
- **Debugging**: Easier to debug cleaning issues
- **Flexibility**: Users can re-run cleaning with different parameters
- **Audit trail**: Raw files serve as a record of extraction

### Why Triple-Pass Cleaning?

- **Nested affixes**: Some identifiers have multiple affixes (e.g., `dirt_top_side`)
- **Recursive removal**: Each pass removes one layer of affixes
- **Balance**: Too few passes miss nested affixes, too many might over-clean
- **Configurable**: Users can adjust with `--clean-passes`

### Why Exclude Minecraft Recipes by Default?

- **Focus on mods**: Most use cases care about mod recipes, not vanilla
- **Reduce noise**: Vanilla recipes are well-documented
- **Optional inclusion**: Can be enabled with `--include-minecraft`
- **Performance**: Slightly faster by skipping vanilla recipes

### Why Interactive Namespace Selection?

- **User control**: Users know which namespace should be the "canonical" one
- **Context-aware**: Different projects may have different preferences
- **Non-interactive option**: Can be automated with `--namespace` and `--no-interactive`

### Why Multiple Output Formats?

- **Flexibility**: Different tools/scripts may need different formats
- **Human-readable**: TXT format for manual inspection
- **Machine-readable**: JSON/CSV for automated processing
- **Easy conversion**: Can convert between formats if needed

---

## Extension Points

### Adding a New Tool

1. Create new file in `tools/` directory
2. Import shared utilities:
   ```python
   from src.utils import log, write_entry
   from src.jar_processor import validate_input_directory, find_jar_files, create_output_dirs
   from src.arg_parser import add_common_jar_args, get_thread_count
   from src.thread_pool import execute_concurrent
   ```
3. Follow existing patterns:
   - Use `argparse` for CLI with `add_common_jar_args()` for standard options
   - Use `log()` for all output (replaces print statements)
   - Use `write_entry()` for thread-safe file writing
   - Use `execute_concurrent()` for parallel processing
   - Add type hints
   - Add docstrings

### Adding New Affixes

Edit `AFFIX_GROUPS` in `tools/asset_scanner.py`:
```python
AFFIX_GROUPS = {
    "new_category": [
        "_new_affix1",
        "_new_affix2"
    ],
    # ... existing groups
}
```

### Adding New Output Formats

In `tools/block_matcher.py`, add new format function:
```python
def write_new_format(matches: List[Dict[str, str]], out_file: Path):
    # Implementation
```

Then add to `--format` choices and main() function.

---

## Performance Considerations

### Memory Usage

- **Buffering**: Each JAR is processed in memory (buffers entries before writing)
- **Large JARs**: May use significant memory for very large mods
- **Mitigation**: Process entries immediately if memory is a concern

### Disk I/O

- **Append mode**: Raw files use append mode for thread-safe writing
- **Sequential writes**: Cleaned files are written sequentially
- **SSD recommended**: For large-scale processing, use fast storage

### CPU Usage

- **Thread count**: Defaults to CPU count (optimal for I/O-bound work)
- **Cleaning**: Single-threaded (CPU-bound, but fast)
- **Parsing**: JSON parsing is fast for typical recipe files

---

## Future Improvements

### Potential Enhancements

1. **Progress bars**: Add `tqdm` for visual progress indication
2. **Caching**: Cache JAR file metadata to skip unchanged files
3. **Incremental updates**: Only process new/changed JARs
4. **Database output**: Export to SQLite for querying
5. **Parallel cleaning**: Use multiprocessing for cleaning phase
6. **Streaming**: Process very large JARs without full memory load

### Architecture Improvements

1. **Plugin system**: Allow external tools to extend functionality
2. **Configuration files**: YAML/JSON config for default settings
3. **Logging framework**: Replace print statements with proper logging
4. **Error recovery**: Better handling of corrupted JARs
5. **Validation**: Validate JAR structure before processing

