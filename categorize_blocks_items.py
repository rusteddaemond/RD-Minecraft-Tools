#!/usr/bin/env python3
"""
Script to categorize blocks and items from scan output into common categories.
Reads blocks.txt and items.txt and categorizes them based on name patterns.
"""

import re
from pathlib import Path
from collections import defaultdict


# Category patterns - keywords that indicate a category
CATEGORY_PATTERNS = {
    'wood': [
        r'\b(log|plank|wood|fence|gate|door|trapdoor|sign|button|pressure_plate|stairs|slab|stair|'
        r'stripped|sapling|leaves|bark|branch|beam|post|panel|board|timber)\b',
        r'_(log|plank|wood|fence|gate|door|trapdoor|sign|button|pressure_plate|stairs|slab|stair|'
        r'stripped|sapling|leaves|bark|branch|beam|post|panel|board|timber)_',
    ],
    'stone': [
        r'\b(stone|cobble|brick|granite|diorite|andesite|basalt|marble|limestone|sandstone|'
        r'quartz|prismarine|end_stone|netherrack|blackstone|deepslate|tuff|calcite)\b',
        r'_(stone|cobble|brick|granite|diorite|andesite|basalt|marble|limestone|sandstone|'
        r'quartz|prismarine|end_stone|netherrack|blackstone|deepslate|tuff|calcite)_',
    ],
    'ore': [
        r'\b(ore|ingot|nugget|raw_|gem|chunk|dust|powder|shard|fragment|crystal)\b',
        r'_(ore|ingot|nugget|raw_|gem|chunk|dust|powder|shard|fragment|crystal)_',
    ],
    'metal': [
        r'\b(iron|gold|copper|tin|silver|lead|zinc|aluminum|aluminium|nickel|platinum|'
        r'titanium|tungsten|steel|bronze|brass|invar|electrum|constantan|uranium)\b',
    ],
    'gem': [
        r'\b(diamond|emerald|ruby|sapphire|amethyst|topaz|peridot|citrine|jade|opal|'
        r'amber|garnet|tourmaline|zircon|pearl|quartz)\b',
    ],
    'food': [
        r'\b(berry|fruit|vegetable|meat|fish|bread|cake|cookie|pie|soup|stew|juice|'
        r'apple|carrot|potato|beetroot|wheat|rice|corn|tomato|onion|pepper|'
        r'seed|pips|basket|meal|food|snack|treat)\b',
    ],
    'tool': [
        r'\b(pickaxe|axe|shovel|hoe|sword|knife|hammer|wrench|screwdriver|drill|'
        r'saw|shears|fishing_rod|bow|crossbow|shield|tool)\b',
    ],
    'armor': [
        r'\b(helmet|chestplate|leggings|boots|armor|armour|mail|plate)\b',
    ],
    'glass': [
        r'\b(glass|pane|stained_glass|tinted_glass)\b',
    ],
    'wool': [
        r'\b(wool|carpet|bed|banner)\b',
    ],
    'concrete': [
        r'\b(concrete|powder)\b',
    ],
    'terracotta': [
        r'\b(terracotta|glazed_terracotta)\b',
    ],
    'slab': [
        r'\b(slab)\b',
    ],
    'stairs': [
        r'\b(stairs|stair)\b',
    ],
    'wall': [
        r'\b(wall)\b',
    ],
    'fence': [
        r'\b(fence|gate)\b',
    ],
    'door': [
        r'\b(door|trapdoor)\b',
    ],
    'button': [
        r'\b(button|pressure_plate)\b',
    ],
    'sign': [
        r'\b(sign|hanging_sign)\b',
    ],
    'leaves': [
        r'\b(leaves|leaf)\b',
    ],
    'sapling': [
        r'\b(sapling|seedling)\b',
    ],
    'flower': [
        r'\b(flower|bloom|petal|rose|tulip|dandelion|poppy|daisy|lily|orchid)\b',
    ],
    'crop': [
        r'\b(crop|plant|seed|wheat|carrot|potato|beetroot|melon|pumpkin|'
        r'cucumber|tomato|pepper|corn|rice|barley|oats|rye)\b',
    ],
    'mushroom': [
        r'\b(mushroom|fungus|mycelium)\b',
    ],
    'grass': [
        r'\b(grass|fern|moss|lichen|ivy|vine)\b',
    ],
    'sand': [
        r'\b(sand|gravel|dirt|clay|mud|soil)\b',
    ],
    'ice': [
        r'\b(ice|snow|frost|frozen)\b',
    ],
    'lava': [
        r'\b(lava|magma|fire|flame|burning)\b',
    ],
    'water': [
        r'\b(water|aqua|wet|moist|damp)\b',
    ],
    'nether': [
        r'\b(nether|soul|warped|crimson|netherrack|soul_sand|soul_soil)\b',
    ],
    'end': [
        r'\b(end|purpur|chorus|elytra|shulker)\b',
    ],
    'redstone': [
        r'\b(redstone|repeater|comparator|dispenser|dropper|hopper|observer|'
        r'piston|sticky_piston|rail|minecart|lever|redstone_torch)\b',
    ],
    'chest': [
        r'\b(chest|barrel|shulker_box|ender_chest)\b',
    ],
    'furnace': [
        r'\b(furnace|smoker|blast_furnace|campfire|fireplace|kiln|forge)\b',
    ],
    'crafting': [
        r'\b(crafting_table|workbench|anvil|enchanting_table|brewing_stand|'
        r'cauldron|loom|cartography_table|fletching_table|smithing_table|'
        r'grindstone|stonecutter)\b',
    ],
    'ore_block': [
        r'\b(ore)\b',
    ],
    'ingot': [
        r'\b(ingot)\b',
    ],
    'nugget': [
        r'\b(nugget)\b',
    ],
    'dust': [
        r'\b(dust|powder)\b',
    ],
    'gem_block': [
        r'\b(gem|diamond|emerald|ruby|sapphire|amethyst)\b',
    ],
}


def load_entries(file_path):
    """Load entries from a text file."""
    if not file_path.exists():
        return []
    
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(line)
    return entries


def categorize_entry(entry, patterns):
    """Categorize a single entry based on patterns."""
    # Extract the name part (after namespace:)
    if ':' in entry:
        name = entry.split(':', 1)[1].lower()
    else:
        name = entry.lower()
    
    categories = []
    
    for category, category_patterns in patterns.items():
        for pattern in category_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                categories.append(category)
                break  # Only add category once per entry
    
    return categories if categories else ['uncategorized']


def categorize_blocks_and_items(output_dir='scan_output'):
    """Categorize blocks and items from scan output."""
    output_path = Path(output_dir)
    
    # Load entries
    blocks_file = output_path / 'blocks.txt'
    items_file = output_path / 'items.txt'
    
    blocks = load_entries(blocks_file)
    items = load_entries(items_file)
    
    if not blocks and not items:
        print(f"Error: No blocks or items found in '{output_dir}' directory!")
        print(f"Looking for: {blocks_file} and {items_file}")
        return
    
    print(f"Loaded {len(blocks)} blocks and {len(items)} items")
    print("Categorizing...")
    
    # Categorize blocks
    blocks_by_category = defaultdict(list)
    for block in blocks:
        categories = categorize_entry(block, CATEGORY_PATTERNS)
        for category in categories:
            blocks_by_category[category].append(block)
    
    # Categorize items
    items_by_category = defaultdict(list)
    for item in items:
        categories = categorize_entry(item, CATEGORY_PATTERNS)
        for category in categories:
            items_by_category[category].append(item)
    
    # Create output directory
    categories_dir = output_path / 'categories'
    categories_dir.mkdir(exist_ok=True)
    
    blocks_cat_dir = categories_dir / 'blocks'
    items_cat_dir = categories_dir / 'items'
    blocks_cat_dir.mkdir(exist_ok=True)
    items_cat_dir.mkdir(exist_ok=True)
    
    # Save categorized blocks
    for category in sorted(blocks_by_category.keys()):
        category_file = blocks_cat_dir / f"{category}.txt"
        with open(category_file, 'w', encoding='utf-8') as f:
            for block in sorted(blocks_by_category[category]):
                f.write(f"{block}\n")
    
    # Save categorized items
    for category in sorted(items_by_category.keys()):
        category_file = items_cat_dir / f"{category}.txt"
        with open(category_file, 'w', encoding='utf-8') as f:
            for item in sorted(items_by_category[category]):
                f.write(f"{item}\n")
    
    # Print summary
    print("\n" + "=" * 60)
    print("CATEGORIZATION SUMMARY")
    print("=" * 60)
    
    print("\nBLOCKS BY CATEGORY:")
    for category in sorted(blocks_by_category.keys(), key=lambda x: len(blocks_by_category[x]), reverse=True):
        count = len(blocks_by_category[category])
        print(f"  {category:20s}: {count:5d} blocks")
    
    print("\nITEMS BY CATEGORY:")
    for category in sorted(items_by_category.keys(), key=lambda x: len(items_by_category[x]), reverse=True):
        count = len(items_by_category[category])
        print(f"  {category:20s}: {count:5d} items")
    
    print(f"\nResults saved to '{categories_dir}/' directory:")
    print(f"  - blocks/ (categories for blocks)")
    print(f"  - items/ (categories for items)")
    
    # Save summary file
    summary_file = categories_dir / 'summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Categorization Summary\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("BLOCKS BY CATEGORY:\n")
        for category in sorted(blocks_by_category.keys(), key=lambda x: len(blocks_by_category[x]), reverse=True):
            count = len(blocks_by_category[category])
            f.write(f"  {category:20s}: {count:5d} blocks\n")
        
        f.write("\nITEMS BY CATEGORY:\n")
        for category in sorted(items_by_category.keys(), key=lambda x: len(items_by_category[x]), reverse=True):
            count = len(items_by_category[category])
            f.write(f"  {category:20s}: {count:5d} items\n")


if __name__ == '__main__':
    import sys
    
    output_dir = 'scan_output'
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    categorize_blocks_and_items(output_dir)

