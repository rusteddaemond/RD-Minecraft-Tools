# RD-Minecraft-Tools

A collection of Python tools for analyzing and processing Minecraft mod JAR files.

## Tools

- **[Asset Scanner](docs/codebase.md#asset-scanner)** - Extract block/item assets from JAR files
- **[Recipe Scanner](docs/codebase.md#recipe-scanner)** - Extract recipe results from JAR files
- **[Block Matcher](docs/codebase.md#block-matcher)** - Find duplicate blocks across namespaces
- **[Items Matcher](docs/codebase.md#items-matcher)** - Generate OEI datapacks from JSON config
- **[Fluid Matcher](docs/codebase.md#fluid-matcher)** - Generate OEF datapacks from JSON config

## Quick Start

```bash
# Install (no dependencies required - uses Python standard library)
git clone <repository-url>
cd RD-Minecraft-Tools

# Run a tool
python -m tools.asset_scanner --input-dir ./mods
```

## Documentation

- **[Codebase Documentation](docs/codebase.md)** - Architecture, design decisions, and internal structure

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)

## License

MIT License - see [LICENSE](LICENSE) file for details.
