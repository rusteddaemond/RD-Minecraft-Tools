# Codebase Documentation

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
│   ├── scanners/       # Scanner tools
│   │   ├── __init__.py
│   │   ├── block_scanner.py
│   │   ├── items_scanner.py
│   │   ├── fluid_scanner.py
│   │   └── recipe_scanner.py
│   ├── matchers/       # Matcher tools
│   │   ├── __init__.py
│   │   ├── block_matcher.py
│   │   ├── items_matcher.py
│   │   └── fluid_matcher.py
│   ├── interfaces/      # Shared argument interfaces
│   │   ├── __init__.py
│   │   ├── scanner_args.py
│   │   └── matcher_args.py
│   └── docker_builder.py
├── src/                # Core architecture
│   ├── models/         # Data models (dataclasses)
│   │   ├── scanner.py  # NamespaceObject, ScannerResult, ScannerConfig
│   │   ├── matcher.py  # MatchRule, MatcherConfig, DuplicateMatch
│   │   ├── datapack.py # DatapackMetadata, ReplacementRule
│   │   ├── jar.py      # JarEntry, JarMetadata
│   │   └── recipe.py   # RecipeResult
│   ├── interfaces/     # Protocol definitions (contracts)
│   │   ├── scanner.py  # IEntryFilter, IScannerProcessor
│   │   ├── matcher.py  # IMatcherProcessor, IMatcherValidator
│   │   ├── processor.py # IJarProcessor, IFileProcessor
│   │   ├── cleaner.py  # IIdentifierCleaner
│   │   └── datapack.py # IDatapackGenerator
│   ├── processors/    # Business logic implementations
│   │   ├── scanner/    # Scanner processors
│   │   ├── matcher/    # Matcher processors
│   │   ├── jar/        # JAR file processors
│   │   ├── datapack/   # Datapack generation
│   │   ├── cleaner/    # Identifier cleaning
│   │   └── file_io.py  # File I/O operations
│   ├── services/      # High-level orchestration
│   │   ├── scanner_service.py
│   │   └── matcher_service.py
│   ├── utils/          # Pure utilities
│   │   ├── logging.py
│   │   ├── threading.py
│   │   └── config.py
│   ├── utils.py        # Backward compatibility (re-exports)
│   ├── jar_processor.py # Legacy (deprecated)
│   ├── scanner_common.py # Legacy (deprecated)
│   ├── matcher_common.py # Legacy (deprecated)
│   └── arg_parser.py   # Common argument parsing
├── tests/             # Unit tests
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_processors.py
│   ├── test_services.py
│   ├── test_block_matcher.py
│   └── test_recipe_scanner.py
├── config/             # Configuration files
│   ├── paths.json
│   └── README.md
└── docs/              # Documentation
    ├── codebase.md
    └── refactoring/    # Architecture refactoring documentation
```

### Module Organization

- **tools/**: Contains the main tool scripts, each as a thin wrapper around services
- **src/models/**: Explicit data structures using dataclasses (immutable where possible)
- **src/interfaces/**: Protocol definitions that define contracts for components
- **src/processors/**: Business logic implementations that adhere to interfaces
- **src/services/**: High-level orchestration that composes processors
- **src/utils/**: Pure utility functions without business logic
- **tests/**: Unit tests for models, processors, and services
- **config/**: Configuration files
- **docs/**: Developer documentation

### Architecture Principles

The codebase follows a layered architecture with clear separation of concerns:

1. **Models Layer**: Explicit, type-safe data structures
2. **Interfaces Layer**: Well-defined contracts using `typing.Protocol`
3. **Processors Layer**: Business logic implementations
4. **Services Layer**: High-level orchestration
5. **Utilities Layer**: Pure helper functions

See [Architecture Overview](refactoring/architecture_overview.md) for detailed information.

---

## Tool Architecture

### New Architecture (Current)

The codebase uses a layered architecture with clear separation of concerns:

- **Models**: Data structures (`NamespaceObject`, `ScannerResult`, `MatchRule`, etc.)
- **Interfaces**: Protocol definitions (`IScannerProcessor`, `IMatcherProcessor`, etc.)
- **Processors**: Business logic implementations (`AssetScannerProcessor`, `DuplicateMatcherProcessor`, etc.)
- **Services**: High-level orchestration (`ScannerService`, `MatcherService`)

Tools are thin wrappers that use services to orchestrate workflows.

### Asset Scanners (Block, Items, Fluid)

**Purpose**: Extract asset identifiers from JAR files

**Architecture**: Uses `ScannerService` with `AssetScannerProcessor` and entry filters

**Shared Process Flow**:
1. **Discovery Phase**: Find all `.jar` files in input directory
2. **Scanning Phase**: Concurrently process each JAR file
   - Open JAR as ZIP archive
   - Iterate through entries
   - Filter by path pattern (varies by scanner type)
   - Extract namespace and identifier
   - Buffer entries by namespace
3. **Writing Phase**: Thread-safely write raw entries to files
4. **Cleaning Phase**: Process raw files with convergence-based cleaning
   - Remove file extensions (including .json for fluids)
   - Remove affixes (orientation, state, etc.) until convergence
   - Deduplicate
   - Sort alphabetically

**Scanner-Specific Path Patterns**:
- **Block Scanner**: `assets/{namespace}/models|textures/block/*`
- **Items Scanner**: `assets/{namespace}/models|textures/item/*`
- **Fluid Scanner**: `assets/{namespace}/fluid/*` or `assets/{namespace}/fluid_types/*`

**Key Components**:
- `src/services/scanner_service.py`: Orchestrates scanner workflows
- `src/processors/scanner/asset.py`: `AssetScannerProcessor` implementation
- `src/processors/scanner/filters.py`: Entry filters (`BlockEntryFilter`, `ItemsEntryFilter`, `FluidEntryFilter`)
- `src/processors/cleaner/identifier.py`: Identifier cleaning (`IdentifierCleaner`, `FluidIdentifierCleaner`)
- `src/models/scanner.py`: Data models (`ScannerResult`, `ScannerConfig`, `NamespaceObject`)

### Recipe Scanner

**Purpose**: Extract recipe results from JAR files

**Architecture**: Uses `ScannerService` with `RecipeScannerProcessor`

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
- `src/services/scanner_service.py`: Orchestrates scanner workflows
- `src/processors/scanner/recipe.py`: `RecipeScannerProcessor` implementation
- `src/models/scanner.py`: Data models

### Block Matcher

**Purpose**: Find duplicate blocks across namespaces

**Architecture**: Uses `MatcherService` with `DuplicateMatcherProcessor`

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
6. **Output Phase**: Generate datapack with match rules

**Key Components**:
- `src/services/matcher_service.py`: Orchestrates matcher workflows
- `src/processors/matcher/duplicate.py`: `DuplicateMatcherProcessor` implementation
- `src/processors/file_io.py`: File I/O operations
- `src/models/matcher.py`: Data models (`MatchRule`, `MatcherConfig`)

### Matchers (Block, Items, Fluid)

**Purpose**: Find duplicate objects across namespaces and generate datapacks (OEB/OEI/OEF)

**Architecture**: All matchers use `MatcherService` with `DuplicateMatcherProcessor`

**Shared Process Flow**:
1. **Discovery Phase**: Find all `.txt` files in input directory (from scanners)
2. **Loading Phase**: Parse text files
   - Read each line as `namespace:object_id`
   - Build map: `object_id -> [namespaces]`
3. **Filtering Phase**: Find duplicates
   - Filter objects appearing in multiple namespaces
4. **Selection Phase**: Choose target namespace
   - Interactive: Prompt user
   - Non-interactive: Use provided namespace
5. **Generation Phase**: Build match rules
   - Create match mappings (matchField -> resultField)
6. **Datapack Generation Phase**: Create datapack structure
   - Create directory: `data/{datapack_path}/replacements/`
   - Generate `replacements.json` with match rules
   - Create `pack.mcmeta` with datapack metadata
7. **Output Phase**: Write datapack to output directory

**Matcher-Specific Details**:
- **Block Matcher (OEB)**:
  - Fields: `matchBlock` and `resultBlock`
  - Datapack path: `data/oeb/replacements/`
  - Output file: Named after target namespace (e.g., `farm_and_charm.json`)
- **Items Matcher (OEI)**:
  - Fields: `matchItems` and `resultItems`
  - Datapack path: `data/oei/replacements/`
  - Output file: Named after target namespace (e.g., `minecraft.json`)
- **Fluid Matcher (OEF)**:
  - Fields: `matchFluid` and `resultFluid`
  - Datapack path: `data/oef/replacements/`
  - Output file: Named after target namespace (e.g., `minecraft.json`)
  - OEF is an add-on for OEI that extends fluid-replacement functionality
  - Enables fluid replacement for blocks, items, and recipes

**Output File Naming**:
- Input files are named by source namespace: `namespace1.txt`, `namespace2.txt`
- Output file is named after the target namespace (the namespace replacements are made TO)
- Example: If `minecraft:egg` is replaced with `farm_and_charm:haybale`, output is `farm_and_charm.json`

**Key Components**:
- `src/services/matcher_service.py`: Orchestrates matcher workflows
- `src/processors/matcher/duplicate.py`: `DuplicateMatcherProcessor` implementation
- `src/processors/file_io.py`: File I/O operations for reading `.txt` files
- `src/processors/datapack/generator.py`: `DatapackGenerator` implementation
- `src/models/matcher.py`: Data models (`MatchRule`, `MatcherConfig`)
- `src/models/datapack.py`: Data models (`DatapackMetadata`, `ReplacementRule`)

---

## Data Flow

### Asset Scanner Data Flow (Block/Items/Fluid)

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
[Convergence-based Cleaning]
    ↓
Cleaned Entries (normalized)
    ↓
*.txt files (final output)
```

**Note**: All asset scanners follow the same data flow pattern, differing only in path patterns (see Scanner-Specific Path Patterns above).

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
*.txt files (from block scanner: namespace:block_id)
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
Match rules (matchBlock -> resultBlock)
    ↓
[Datapack Generation]
    ↓
data/oeb/replacements/{target_namespace}.json
    ↓
[Metadata Creation]
    ↓
pack.mcmeta
    ↓
OEB datapack (ready to install)
```

### Matcher Data Flow (Block/Items/Fluid)

All matchers follow the same data flow pattern - they differ only in the type of objects they match:

```
*.txt files (from scanners: namespace:object_id)
    ↓
[Parsing]
    ↓
object_id -> [namespaces] map
    ↓
[Duplicate Detection]
    ↓
Duplicate objects (appearing in multiple namespaces)
    ↓
[Namespace Selection]
    ↓
Match rules (matchField -> resultField)
    ↓
[Datapack Generation]
    ↓
data/{datapack_path}/replacements/{target_namespace}.json
    ↓
[Metadata Creation]
    ↓
pack.mcmeta
    ↓
OEI/OEF/OEB datapack (ready to install)
```

**Matcher-Specific Details**:
- **Block Matcher (OEB)**: Uses `matchBlock` and `resultBlock` fields
- **Items Matcher (OEI)**: Uses `matchItems` and `resultItems` fields
- **Fluid Matcher (OEF)**: Uses `matchFluid` and `resultFluid` fields

**File Naming**:
- Input files: Named by source namespace (e.g., `minecraft.txt`, `farm_and_charm.txt`)
- Output file: Named after target namespace (e.g., `farm_and_charm.json` if replacements target that namespace)

All matchers read from `.txt` files and output JSON datapacks.

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

#### Matcher Input Files (Text Format)

Input files are named by namespace (e.g., `minecraft.txt`, `farm_and_charm.txt`):

**minecraft.txt**:
```
minecraft:dirt
minecraft:stone
minecraft:egg
```

**farm_and_charm.txt**:
```
farm_and_charm:haybale
farm_and_charm:copper_block
```

Format: `namespace:object_id` (one per line), UTF-8 encoding, sorted alphabetically, deduplicated.

These `.txt` files are generated by the scanner tools (block_scanner, items_scanner, fluid_scanner).

#### Matcher Output Files (Datapack JSON Format)

All matchers generate JSON datapacks with the same structure, differing only in field names:

**OEB (Block Matcher)**:
```json
[
  {
    "matchBlock": [
      "modname:copper_block",
      "othermod:copper_block"
    ],
    "resultBlock": "minecraft:copper_block"
  }
]
```

**OEI (Items Matcher)**:
```json
[
  {
    "matchItems": [
      "minecraft:potato",
      "minecraft:carrot"
    ],
    "resultItems": "minecraft:egg"
  }
]
```

**OEF (Fluid Matcher)**:
```json
[
  {
    "matchFluid": [
      "minecraft:water",
      "minecraft:lava"
    ],
    "resultFluid": "minecraft:water"
  }
]
```

All matchers read from `.txt` files (output from scanners) and generate JSON datapacks.

**Output File Naming**: The output JSON file is named after the target namespace (the namespace that replacements are made TO). For example, if `minecraft:egg` is replaced with `farm_and_charm:haybale`, the output file will be `farm_and_charm.json`.

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

### Why Convergence-Based Cleaning?

- **Nested affixes**: Some identifiers have multiple affixes (e.g., `dirt_top_side_stage0`)
- **Thorough removal**: Continues cleaning until no more changes occur
- **No pass limit**: Handles deeply nested affixes automatically
- **Automatic**: No configuration needed - cleans until convergence

### Why Exclude Minecraft Recipes by Default?

- **Focus on mods**: Most use cases care about mod recipes, not vanilla
- **Reduce noise**: Vanilla recipes are well-documented
- **Optional inclusion**: Can be enabled with `--include-minecraft`
- **Performance**: Slightly faster by skipping vanilla recipes

### Why Interactive Namespace Selection?

- **User control**: Users know which namespace should be the "canonical" one
- **Context-aware**: Different projects may have different preferences
- **Non-interactive option**: Can be automated with `--namespace` and `--no-interactive`

### Why Datapack Output Format?

- **Standardized**: All matchers output Minecraft datapacks in the same format
- **Ready to use**: Datapacks can be directly installed in Minecraft worlds
- **Consistent structure**: Same format across OEB, OEI, and OEF datapacks
- **Field-based**: Only difference between matchers is field names (matchBlock/matchItems/matchFluid)

---

## Extension Points

### Adding a New Scanner Tool

1. Create new file in `tools/scanners/` directory
2. Use the new architecture:
   ```python
   from src.services.scanner_service import ScannerService
   from src.processors.scanner import AssetScannerProcessor, BlockEntryFilter
   from src.processors.cleaner import IdentifierCleaner
   from src.processors.file_io import FileIOProcessor
   from src.models.scanner import ScannerConfig
   
   # Create components
   entry_filter = BlockEntryFilter()  # Or create custom filter
   cleaner = IdentifierCleaner()
   processor = AssetScannerProcessor(entry_filter, cleaner)
   file_io = FileIOProcessor()
   service = ScannerService(processor, file_io, cleaner)
   
   # Create config and run
   config = ScannerConfig(...)
   service.run_scan(config)
   ```

### Adding a New Matcher Tool

1. Create new file in `tools/matchers/` directory
2. Use the new architecture:
   ```python
   from src.services.matcher_service import MatcherService
   from src.processors.matcher import DuplicateMatcherProcessor
   from src.processors.file_io import FileIOProcessor
   from src.models.matcher import MatcherConfig
   
   # Create components
   file_io = FileIOProcessor()
   processor = DuplicateMatcherProcessor(file_io)
   service = MatcherService(processor, file_io)
   
   # Create config and run
   config = MatcherConfig(...)
   service.run_duplicate_matcher(config, result_ns="minecraft")
   ```

### Creating a Custom Entry Filter

Implement `IEntryFilter` interface:
```python
from src.interfaces.scanner import IEntryFilter
from src.models.scanner import NamespaceObject

class CustomEntryFilter(IEntryFilter):
    def should_include(self, entry_path: str) -> bool:
        # Your filtering logic
        return entry_path.endswith(".json")
    
    def extract_object(self, entry_path: str) -> NamespaceObject | None:
        # Extract namespace and object_id from path
        # Return None if extraction fails
        pass
```

### Creating a Custom Processor

Implement the appropriate interface:
```python
from src.interfaces.scanner import IScannerProcessor
from src.models.scanner import ScannerConfig, ScannerResult

class CustomScannerProcessor(IScannerProcessor):
    def process_jar(self, jar_path: Path, config: ScannerConfig) -> List[ScannerResult]:
        # Your processing logic
        pass
```

### Adding New Affixes

Edit `AFFIX_GROUPS` in `src/processors/cleaner/identifier.py`:
```python
AFFIX_GROUPS = {
    "new_category": [
        "_new_affix1",
        "_new_affix2"
    ],
    # ... existing groups
}
```

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

1. **Migrate legacy tools**: Migrate `tag_scanner.py` and `asset_scanner.py` to new architecture
2. **Remove deprecated code**: After legacy migration, remove `scanner_common.py`, `matcher_common.py`, `matcher_base.py`
3. **Plugin system**: Allow external tools to extend functionality via interfaces
4. **Enhanced testing**: Add more integration and end-to-end tests
5. **Performance optimization**: Profile hot paths and optimize
