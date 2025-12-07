#!/usr/bin/env python3
"""
Docker Compose Builder for Minecraft Servers
--------------------------------------------

Reads .txt and .md files from /mods directory to extract Modrinth project IDs,
reads CurseForge keys from .env file, and generates a docker-compose.yml file
for running a Minecraft server.

Usage:
    python -m tools.docker_builder [options]
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import log, get_project_root
from src.file_operations import read_text_file, find_files, write_text_file


# ---------------------------------------------------------------------
# Modrinth ID extraction
# ---------------------------------------------------------------------
# Modrinth project IDs are extracted from URLs like:
# https://modrinth.com/mod/jtmvUHXj
# Pattern matches modrinth.com/mod/ followed by the project ID
MODRINTH_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?modrinth\.com/mod/([A-Za-z0-9]{6,10})',
    re.IGNORECASE
)

# CurseForge project IDs are extracted from URLs like:
# https://www.curseforge.com/projects/979809
# Pattern matches curseforge.com/projects/ followed by the project ID
CURSEFORGE_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?curseforge\.com/projects/(\d+)',
    re.IGNORECASE
)


def extract_modrinth_ids_from_file(file_path: Path) -> Set[str]:
    """Extract Modrinth project IDs from a text or markdown file.
    
    Looks for URLs in the format: https://modrinth.com/mod/PROJECT_ID
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Set of Modrinth project IDs found in the file
    """
    modrinth_ids: Set[str] = set()
    
    try:
        content = read_text_file(file_path, errors="ignore")
        # Find all Modrinth URLs and extract the project IDs
        matches = MODRINTH_URL_PATTERN.findall(content)
        for match in matches:
            modrinth_ids.add(match)
    except Exception as e:
        log(f"Error reading {file_path.name}: {e}", "WARN")
    
    return modrinth_ids


def extract_curseforge_ids_from_file(file_path: Path) -> Set[str]:
    """Extract CurseForge project IDs from a text or markdown file.
    
    Looks for URLs in the format: https://www.curseforge.com/projects/PROJECT_ID
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Set of CurseForge project IDs found in the file
    """
    curseforge_ids: Set[str] = set()
    
    try:
        content = read_text_file(file_path, errors="ignore")
        # Find all CurseForge URLs and extract the project IDs
        matches = CURSEFORGE_URL_PATTERN.findall(content)
        for match in matches:
            curseforge_ids.add(match)
    except Exception as e:
        log(f"Error reading {file_path.name}: {e}", "WARN")
    
    return curseforge_ids


def find_mod_files(mods_dir: Path) -> list[Path]:
    """Find all .txt and .md files in the mods directory.
    
    Args:
        mods_dir: Directory to search for mod files
        
    Returns:
        List of paths to .txt and .md files
    """
    mod_files: list[Path] = []
    
    if not mods_dir.exists():
        return mod_files
    
    for ext in ["*.txt", "*.md"]:
        mod_files.extend(find_files(mods_dir, ext, recursive=True))
    
    return sorted(set(mod_files))  # Remove duplicates and sort


def extract_all_modrinth_ids(mods_dir: Path) -> Set[str]:
    """Extract all Modrinth project IDs from .txt and .md files in mods directory.
    
    Args:
        mods_dir: Directory containing mod files
        
    Returns:
        Set of all unique Modrinth project IDs found
    """
    all_ids: Set[str] = set()
    mod_files = find_mod_files(mods_dir)
    
    if not mod_files:
        log(f"No .txt or .md files found in {mods_dir}", "WARN")
        return all_ids
    
    log(f"Scanning {len(mod_files)} mod files for Modrinth IDs...")
    
    for mod_file in mod_files:
        ids = extract_modrinth_ids_from_file(mod_file)
        if ids:
            log(f"Found {len(ids)} Modrinth IDs in {mod_file.name}", "OK")
            all_ids.update(ids)
    
    return all_ids


def extract_all_curseforge_ids(mods_dir: Path) -> Set[str]:
    """Extract all CurseForge project IDs from .txt and .md files in mods directory.
    
    Args:
        mods_dir: Directory containing mod files
        
    Returns:
        Set of all unique CurseForge project IDs found
    """
    all_ids: Set[str] = set()
    mod_files = find_mod_files(mods_dir)
    
    if not mod_files:
        return all_ids
    
    log(f"Scanning {len(mod_files)} mod files for CurseForge IDs...")
    
    for mod_file in mod_files:
        ids = extract_curseforge_ids_from_file(mod_file)
        if ids:
            log(f"Found {len(ids)} CurseForge IDs in {mod_file.name}", "OK")
            all_ids.update(ids)
    
    return all_ids


# ---------------------------------------------------------------------
# CurseForge key extraction from .env
# ---------------------------------------------------------------------
CURSEFORGE_KEY_PATTERN = re.compile(r'\b\d{4,10}\b')  # 4-10 digit numbers


def extract_curseforge_keys_from_env(env_file: Path) -> tuple[Set[str], str | None]:
    """Extract CurseForge file IDs from .env file.
    
    Looks for numeric values that could be CurseForge file IDs.
    Also looks for CF_API_KEY if present.
    
    Args:
        env_file: Path to .env file
        
    Returns:
        Tuple of (set of CurseForge file IDs, CF API key if found)
    """
    curseforge_keys: Set[str] = set()
    cf_api_key: str | None = None
    
    if not env_file.exists():
        log(f".env file not found at {env_file}", "WARN")
        return curseforge_keys, cf_api_key
    
    try:
        content = read_text_file(env_file, errors="ignore")
            
            # Look for CF_API_KEY
            api_key_match = re.search(
                r'(?:CF_API_KEY|CURSEFORGE_API_KEY)\s*=\s*["\']?([^"\'\s]+)["\']?',
                content,
                re.IGNORECASE
            )
            if api_key_match:
                cf_api_key = api_key_match.group(1).strip()
            
            # Look for CurseForge file IDs
            # Pattern 1: CURSEFORGE_FILES or CF_FILES with list of numbers
            files_match = re.search(
                r'(?:CURSEFORGE_FILES|CF_FILES)\s*=\s*["\']?([^"\']+)["\']?',
                content,
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            if files_match:
                files_content = files_match.group(1)
                # Extract all numeric IDs from the content
                matches = CURSEFORGE_KEY_PATTERN.findall(files_content)
                for match in matches:
                    if len(match) >= 4:  # CurseForge file IDs are typically 6+ digits
                        curseforge_keys.add(match)
            
            # Pattern 2: Look for standalone numeric values that could be file IDs
            # This is a fallback if no explicit CURSEFORGE_FILES is found
            if not curseforge_keys:
                # Look for lines that might contain CurseForge IDs
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # If line contains "curseforge" or "cf" and numbers, extract them
                    if re.search(r'curseforge|cf_', line, re.IGNORECASE):
                        matches = CURSEFORGE_KEY_PATTERN.findall(line)
                        for match in matches:
                            if len(match) >= 4:
                                curseforge_keys.add(match)
    except Exception as e:
        log(f"Error reading .env file: {e}", "WARN")
    
    return curseforge_keys, cf_api_key


# ---------------------------------------------------------------------
# Docker Compose YAML generation
# ---------------------------------------------------------------------
def generate_docker_compose(
    modrinth_ids: Set[str],
    curseforge_keys: Set[str],
    cf_api_key: str | None,
    output_path: Path,
    server_type: str = "NEOFORGE",
    memory: str = "8192M",
    difficulty: str = "2",
    seed: str = "test_1",
    level: str = "test_1",
    port: str = "25565"
) -> None:
    """Generate docker-compose.yml file.
    
    Args:
        modrinth_ids: Set of Modrinth project IDs
        curseforge_keys: Set of CurseForge file IDs
        cf_api_key: CurseForge API key (optional)
        output_path: Path where docker-compose.yml should be written
        server_type: Minecraft server type (default: NEOFORGE)
        memory: Memory allocation (default: 8192M)
        difficulty: Server difficulty (default: 2)
        seed: World seed (default: test_1)
        level: World level name (default: test_1)
        port: Server port (default: 25565)
    """
    # Sort IDs for consistent output
    sorted_modrinth = sorted(modrinth_ids)
    sorted_curseforge = sorted(curseforge_keys)
    
    # Build Modrinth projects section
    modrinth_section = ""
    if sorted_modrinth:
        modrinth_section = "      MODRINTH_PROJECTS: |-\n"
        for mod_id in sorted_modrinth:
            modrinth_section += f"        {mod_id}\n"
    
    # Build CurseForge files section
    curseforge_section = ""
    if sorted_curseforge:
        curseforge_section = "      CURSEFORGE_FILES: |-\n"
        for cf_key in sorted_curseforge:
            curseforge_section += f"        {cf_key}\n"
    
    # Build CF_API_KEY section
    api_key_section = ""
    if cf_api_key:
        api_key_section = f'      CF_API_KEY: "{cf_api_key}"\n'
    
    # Generate YAML content
    yaml_content = f"""# Generated

services:
  mc:
    image: itzg/minecraft-server:latest
    pull_policy: daily
    tty: true
    stdin_open: true
    ports:
      - "{port}:25565"
    environment:
      EULA: "TRUE"
      TYPE: "{server_type}"
      MEMORY: "{memory}"
      USE_AIKAR_FLAGS: "true"
      DIFFICULTY: "{difficulty}"
      FORCE_GAMEMODE: "true"
      SEED: "{seed}"
      LEVEL: "{level}"
      SPAWN_PROTECTION: "0"
{curseforge_section}{api_key_section}{modrinth_section}      MODRINTH_DOWNLOAD_DEPENDENCIES: "required"
      MODRINTH_ALLOWED_VERSION_TYPE: "alpha"
      RCON_CMDS_STARTUP: |-
        chunky radius 5000
        chunky continue
        chunky quiet 30 
      RCON_CMDS_ON_DISCONNECT: |-
        chunky pause
      RCON_CMDS_FIRST_CONNECT: |-
        chunky pause
      RCON_CMDS_LAST_DISCONNECT: |-
        chunky continue
      PAUSE_WHEN_EMPTY_SECONDS: "30"
    volumes:
      - "./data:/data"

volumes:
  config: {{}}
"""
    
    # Write to file
    try:
        write_text_file(output_path, yaml_content)
        log(f"Generated docker-compose.yml at {output_path.resolve()}", "OK")
        log(f"  - Modrinth projects: {len(modrinth_ids)}", "INFO")
        log(f"  - CurseForge files: {len(curseforge_keys)}", "INFO")
        if cf_api_key:
            log(f"  - CF API key: {'*' * min(len(cf_api_key), 10)}", "INFO")
    except Exception as e:
        log(f"Error writing docker-compose.yml: {e}", "ERROR")
        sys.exit(1)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for docker builder tool."""
    parser = argparse.ArgumentParser(
        description="Generate docker-compose.yml for Minecraft server from mod files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    from src.config_loader import load_paths_from_config, get_default_paths
    
    project_root = get_project_root()
    
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file for standard paths (JSON format)"
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=project_root / ".env",
        help="Path to .env file containing CurseForge keys (default: .env in project root)"
    )
    parser.add_argument(
        "--server-type",
        type=str,
        default="NEOFORGE",
        help="Minecraft server type (default: NEOFORGE)"
    )
    parser.add_argument(
        "--memory",
        type=str,
        default="8192M",
        help="Memory allocation (default: 8192M)"
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="2",
        help="Server difficulty (default: 2)"
    )
    parser.add_argument(
        "--seed",
        type=str,
        default="test_1",
        help="World seed (default: test_1)"
    )
    parser.add_argument(
        "--level",
        type=str,
        default="test_1",
        help="World level name (default: test_1)"
    )
    parser.add_argument(
        "--port",
        type=str,
        default="25565",
        help="Server port (default: 25565)"
    )
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Use mods directory from config
    mods_dir = paths.mods
    
    # Extract Modrinth IDs from mod files
    log("Extracting Modrinth project IDs from mod files...")
    modrinth_ids = extract_all_modrinth_ids(mods_dir)
    
    # Extract CurseForge project IDs from mod files
    log("Extracting CurseForge project IDs from mod files...")
    curseforge_ids_from_files = extract_all_curseforge_ids(mods_dir)
    
    # Extract CurseForge file IDs from .env
    log("Extracting CurseForge keys from .env file...")
    curseforge_keys_from_env, cf_api_key = extract_curseforge_keys_from_env(args.env_file)
    
    # Combine CurseForge IDs from files and .env
    curseforge_keys = curseforge_ids_from_files | curseforge_keys_from_env
    
    # Generate docker-compose.yml (use output directory from config)
    output_path = paths.output / "docker-compose.yml"
    log("Generating docker-compose.yml...")
    generate_docker_compose(
        modrinth_ids=modrinth_ids,
        curseforge_keys=curseforge_keys,
        cf_api_key=cf_api_key,
        output_path=output_path,
        server_type=args.server_type,
        memory=args.memory,
        difficulty=args.difficulty,
        seed=args.seed,
        level=args.level,
        port=args.port
    )
    
    log("Done!", "OK")


if __name__ == "__main__":
    main()
