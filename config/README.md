# Configuration Files

## Paths Configuration

Standard path configuration file: `paths.json`

### Format

```json
{
  "input": "./input",
  "output": "./output",
  "logs": "./logs",
  "mods": "./mods"
}
```

### Path Descriptions

- **`input`**: Directory containing scanner output files (.txt files with `namespace:object` lines, one per line). Used by matchers as input.
- **`output`**: Directory for cleaned/processed output files. Scanners write cleaned results here: `output/{category}/`. Matchers write datapacks here.
- **`logs`**: Directory for raw/log files. Scanners write raw results here: `logs/{category}/`.
- **`mods`**: Directory containing JAR files for scanning. Used by scanners to find mod JAR files.

### Path Resolution

- All paths are resolved relative to project root unless absolute (starting with `/`)
- If `/input` exists as an absolute path (for Docker/container usage), it is used by default
- Use `--config config/paths.json` to specify a custom paths configuration

### Example Usage

```bash
# Use default paths
python -m tools.scanners.block_scanner

# Use custom paths config
python -m tools.scanners.block_scanner --config config/paths.json
```

## Other Configuration Files

- `pytest.ini` / `pytest.yaml` - Pytest configuration
- `mypy.yaml` - MyPy type checking configuration
- `flake8.yaml` - Flake8 linting configuration
- `black.yaml` - Black code formatting configuration
