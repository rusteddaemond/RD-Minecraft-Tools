"""Constants for tag scanning functionality."""

# Common tag patterns to search for
COMMON_TAG_PATTERNS = [
    "c:dusts/{material}",
    "c:gears/{material}",
    "c:gems/{material}",
    "c:ingots/{material}",
    "c:nuggets/{material}",
    "c:ores/{material}",
    "c:plates/{material}",
    "c:raw_materials/{material}",
    "c:rods/{material}",
    "c:storage_blocks/raw_{material}",
    "c:storage_blocks/{material}",
    "c:wires/{material}",
    # Sapling-related patterns
    "minecraft:saplings",
    "forge:saplings",
    "c:saplings",
    "c:saplings/{material}",
    # Armor-related patterns
    "minecraft:armor",
    "forge:armor",
    "c:armor/{material}",
    "minecraft:head_armor",
    "minecraft:chest_armor",
    "minecraft:legs_armor",
    "minecraft:feet_armor",
    # Wearable/equippable patterns
    "minecraft:wearable",
    "forge:wearable",
    "c:wearable/{material}",
    "minecraft:equippable",
    "forge:equippable",
    "c:equippable/{material}",
    "minecraft:equipment",
    "forge:equipment",
    # Slot-specific patterns
    "minecraft:head",
    "minecraft:chest",
    "minecraft:legs",
    "minecraft:feet",
    "forge:head",
    "forge:chest",
    "forge:legs",
    "forge:feet",
]

# All possible equipment slots in Minecraft
ALL_EQUIPMENT_SLOTS = {
    # Armor slots
    "head", "chest", "legs", "feet",
    # Hand slots
    "mainhand", "offhand",
    # Body slot (some mods use this)
    "body",
    # Mod-specific slots (common ones)
    "back", "backpack", "belt", "necklace", "ring", "ring1", "ring2",
    "charm", "curio", "curios", "trinket", "trinkets",
    "shoulder", "shoulders", "cape", "cloak",
    "gloves", "hands", "wrist",
    "ankle", "ankles",
    # Slot aliases
    "helmet", "chestplate", "leggings", "boots",
    "hand", "left_hand", "right_hand"
}

# Equipment-related category names that should be split by slot
EQUIPMENT_KEYWORDS = [
    "armor", "armors", "armour", "armours",
    "wearable", "wearables", "equippable", "equippables",
    "equipment", "equipments",
    "head_armor", "chest_armor", "legs_armor", "feet_armor",
    "head_armour", "chest_armour", "legs_armour", "feet_armour",
    "head", "chest", "legs", "feet",
    "helmet", "helmets", "chestplate", "chestplates",
    "leggings", "boots", "boot",
    "head_slot", "chest_slot", "legs_slot", "feet_slot",
    "mainhand", "offhand", "hand", "hands",
    "backpack", "back", "belt", "ring", "necklace",
    "curio", "curios", "trinket", "trinkets",
    "cape", "cloak", "gloves", "shoulder", "ankle", "body"
]
