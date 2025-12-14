#!/usr/bin/env python3
"""
Mod & Namespace Discovery
Discovers all mods and namespaces from JAR files.
"""

import os
import json
import re
import logging
from pathlib import Path
from core.utils.jar import open_jar_safe, extract_namespaces_from_jar
from core.utils.json import load_json_from_jar

logger = logging.getLogger(__name__)


def extract_mod_id_from_jar(jar_path):
    """Extract mod ID from a JAR file by reading mods.toml, fabric.mod.json, or META-INF."""
    mod_id = None
    mod_name = os.path.basename(jar_path)
    
    with open_jar_safe(jar_path) as jar:
        file_list = jar.namelist()
        
        # Try NeoForge/Forge: META-INF/neoforge.mods.toml or META-INF/mods.toml
        for toml_path in ['META-INF/neoforge.mods.toml', 'META-INF/mods.toml']:
            if toml_path in file_list:
                try:
                    with jar.open(toml_path) as f:
                        content = f.read().decode('utf-8')
                        # Simple TOML parsing for modid field
                        match = re.search(r'modId\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            mod_id = match.group(1)
                            break
                except (UnicodeDecodeError, KeyError) as e:
                    logger.debug(f"Failed to parse TOML {toml_path} from {jar_path}: {e}")
        
        # Try Fabric: fabric.mod.json
        if not mod_id and 'fabric.mod.json' in file_list:
            data = load_json_from_jar(jar, 'fabric.mod.json')
            if data and 'id' in data:
                mod_id = data['id']
        
        # Fallback: derive from JAR name or first namespace found in data/
        if not mod_id:
            # Try to find first namespace in data/ directory
            for file_path in file_list:
                if file_path.startswith('data/') and '/' in file_path[5:]:
                    parts = file_path.split('/')
                    if len(parts) >= 2:
                        potential_namespace = parts[1]
                        # Skip common non-mod namespaces
                        if potential_namespace not in ['minecraft', 'forge', 'c']:
                            mod_id = potential_namespace
                            break
            
            # Last resort: use filename without extension
            if not mod_id:
                mod_id = os.path.splitext(mod_name)[0]
    
    return mod_id or mod_name


def discover_mods_and_namespaces(mods_dir='mods'):
    """Phase 1: Discover all mods and namespaces."""
    mods_path = Path(mods_dir)
    
    from core.utils.logging import log_error
    if not mods_path.exists():
        log_error(f"Directory '{mods_dir}' does not exist!")
        return {}, set(), {}
    
    jar_files = list(mods_path.glob('*.jar'))
    
    if not jar_files:
        print(f"No JAR files found in '{mods_dir}' directory!")
        return {}, set(), {}
    
    mods = {}  # mod_id -> jar_path
    namespaces = set()
    namespace_to_mod = {}  # namespace -> mod_id (maps namespaces to their mods)
    
    from core.utils.format import print_separator, print_subseparator
    print(f"PHASE 1: Mod & Namespace Discovery")
    print_separator()
    print(f"Found {len(jar_files)} JAR file(s) to scan...")
    print_subseparator()
    
    for jar_file in jar_files:
        mod_id = extract_mod_id_from_jar(jar_file)
        mods[mod_id] = jar_file
        
        # Discover namespaces from data/ directory and map them to this mod
        mod_namespaces = extract_namespaces_from_jar(jar_file)
        namespaces.update(mod_namespaces)
        
        # Map namespaces to mod_id (primary namespace is usually mod_id)
        for namespace in mod_namespaces:
            if namespace not in namespace_to_mod:
                namespace_to_mod[namespace] = mod_id
        # Also map mod_id itself as a namespace (common case)
        if mod_id not in namespace_to_mod:
            namespace_to_mod[mod_id] = mod_id
        
        print(f"  {mod_id:40s}: {jar_file.name}")
    
    print_subseparator()
    print(f"Total mods discovered: {len(mods)}")
    print(f"Total namespaces discovered: {len(namespaces)}")
    
    return mods, namespaces, namespace_to_mod

