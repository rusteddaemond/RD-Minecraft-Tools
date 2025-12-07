# RD-Minecraft-Tools

A collection of Python tools for analyzing and processing Minecraft mod JAR files.

## Tools

**Scanners:**
- **[Block Scanner](docs/codebase.md#block-scanner)** - Extract block assets from JAR files
- **[Items Scanner](docs/codebase.md#items-scanner)** - Extract item assets from JAR files
- **[Fluid Scanner](docs/codebase.md#fluid-scanner)** - Extract fluid assets from JAR files
- **[Recipe Scanner](docs/codebase.md#recipe-scanner)** - Extract recipe results from JAR files

**Matchers:**
- **[Block Matcher](docs/codebase.md#block-matcher)** - Find duplicate blocks across namespaces
- **[Items Matcher](docs/codebase.md#items-matcher)** - Generate OEI datapacks from JSON config
- **[Fluid Matcher](docs/codebase.md#fluid-matcher)** - Generate OEF datapacks from JSON config

## Quick Start

```bash
# Install (no dependencies required - uses Python standard library)
git clone <repository-url>
cd RD-Minecraft-Tools

# Run a scanner (uses default paths or config/paths.json)
python -m tools.scanners.block_scanner
python -m tools.scanners.items_scanner
python -m tools.scanners.fluid_scanner
python -m tools.scanners.recipe_scanner

# Run a matcher
python -m tools.matchers.block_matcher
python -m tools.matchers.items_matcher
python -m tools.matchers.fluid_matcher
```

## Documentation

- **[Codebase Documentation](docs/codebase.md)** - Architecture, design decisions, and internal structure
- **[Path Configuration](config/README.md)** - Standard paths configuration
- **[Architecture Overview](docs/refactoring/architecture_overview.md)** - New architecture with separation of interfaces, models, and processors

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)

## License

MIT License - see [LICENSE](LICENSE) file for details.
