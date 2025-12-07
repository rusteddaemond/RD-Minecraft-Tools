## Wood Type Detection System
This codemap traces the complete wood type detection system in WoodGood, from automatic discovery patterns through hardcoded compatibility rules to user configuration. The system combines Moonlight Lib's automatic detection with manual overrides, filtering through multiple layers to determine which wood types and blocks should be registered. Key locations include the manual registration API [1a], hardcoded exclusion rules [2c], the main registration filter [3a], configuration blacklist system [4a], and dynamic registry integration [5a].
### 1. Automatic Detection via WoodTypeRegistry
How wood types are automatically discovered by scanning for standard block ID patterns
### 1a. Manual Registration API (`EveryCompatAPI.java:43`)
Shows how wood types can be manually registered with simple finder pattern
```text
WoodTypeRegistry.INSTANCE.addSimpleFinder("mod_id", "cherry");
```
### 1b. Advanced Finder Registration (`EveryCompatAPI.java:53`)
Manual registration with custom block names for non-standard patterns
```text
woodReg.addSimpleFinder("mod_id", "dark_birch")
                .log("log_dark_birch")
                .planks("dark_birch_plank")
                .childBlock(VanillaWoodChildKeys.FENCE, "dark_brich_post_fence");
```
### 1c. Automatic Detection Pattern (`EveryCompatAPI.java:79`)
Documentation showing the standard ID patterns used for automatic detection
```text
/// Simple Finder automatically find the blocktypes via IDs:
 *      log - mod_id:cherry_Log
 *      planks - mod_id:cherry_planks
```
### 2. Hardcoded Compatibility Rules
How specific mod combinations are handled through hardcoded exceptions and rules
### 2a. Configuration Blacklist Check (`HardcodedBlockType.java:38`)
First checks user-configured wood type exclusions
```text
if (WOOD_TYPES_BLACKLIST.get().stream().anyMatch(woodidentify::matches)) return true;
```
### 2b. Vanilla Wood Exclusion (`HardcodedBlockType.java:47`)
Excludes known vanilla wood types to prevent conflicts
```text
if (isKnownVanillaWood(woodType)) return true;
```
### 2c. Problematic Wood Type Exclusion (`HardcodedBlockType.java:50`)
Hardcoded exclusion for Cobblemon's distortion wood due to 32x32 textures
```text
if (isWoodFrom("", "", "legendarymonuments:distortion", "")) return true;
```
### 2d. Forced Inclusion (`HardcodedBlockType.java:70`)
Forces inclusion of Terraqueous cherry to avoid conflicts with vanilla cherry
```text
if (isWoodFrom("", "", "terraqueous:cherry", "")) return false;
```
### 3. Block Registration Filter
How the system determines if a block should be registered during the registration process
### 3a. Registration Check Entry Point (`SimpleModule.java:218`)
Main method that determines if a block entry should be registered
```text
public boolean isEntryAlreadyRegistered(String entrySetId, String blockId, BlockType blockType, Registry<?> registry) {
```
### 3b. Hardcoded Rules Application (`SimpleModule.java:230`)
Applies hardcoded compatibility rules for wood types
```text
if (blockType instanceof WoodType woodType) {
            Boolean hardcoded = HardcodedBlockType.isWoodBlockAlreadyRegistered(entrySetId, blockName, woodType, modId);
            if (hardcoded != null) return hardcoded;
```
### 3c. Already Supported Check (`SimpleModule.java:239`)
Excludes wood types from mods that already have built-in support
```text
if (this.getAlreadySupportedMods().contains(woodTypeFrom)) return true;
```
### 3d. Self-Mod Exclusion (`SimpleModule.java:243`)
Prevents mods from generating blocks for their own wood types
```text
if (woodTypeFrom.equals(modId)) return true;
```
### 4. Configuration-Based Filtering
How users can customize wood type detection through configuration files
### 4a. Wood Type Blacklist Config (`UnsafeDisablerConfigs.java:58`)
Configuration option to exclude specific wood types using regex patterns
```text
WOOD_TYPES_BLACKLIST = builder.comment("Exclude WoodType from all of Modules\n"+WoodTypeExample).define("blacklist", List.of());
```
### 4b. Block Blacklist Config (`UnsafeDisablerConfigs.java:76`)
Configuration to exclude specific block combinations using supportedMod/woodMod/blockName format
```text
BLOCKS_BLACKLIST = builder.comment("Exclude a specific WoodType/LeavesType block\n"+blockExample).define("blacklist", List.of());
```
### 4c. Warning System (`UnsafeDisablerConfigs.java:114`)
Warns users about potential server connection issues with conditional registration
```text
if (!WOOD_TYPES_BLACKLIST.get().isEmpty() || !LEAVES_TYPES_BLACKLIST.get().isEmpty() || !BLOCKS_BLACKLIST.get().isEmpty()) {
```
### 5. Dynamic Registry Integration
How the detection system integrates with Minecraft's dynamic registration system
### 5a. Dynamic Block Registration (`EveryCompat.java:242`)
Registers blocks dynamically for all detected wood types
```text
BlockSetAPI.addDynamicBlockRegistration((r, c) -> {
                if (prevRegSize == 0) prevRegSize = BuiltInRegistries.BLOCK.size();
                LOGGER.info("Registering Compat {} Blocks", t.getSimpleName());
                forAllModules(m -> m.registerBlocks(t, r, c));
```
### 5b. Registry Enumeration (`ModEntriesConfigs.java:35`)
Iterates through all detected wood types to generate configuration options
```text
for (var reg : BlockSetAPI.getRegistries()) {
            builder.push(reg.typeName().replace(" ", "_"));
            for (var w : reg.getValues()) {
```
### 5c. Tag Generation (`ServerDynamicResourcesHandler.java:74`)
Generates tags for all detected wood types and their child blocks
```text
for (var r : BlockSetAPI.getRegistries()) {
            String typeName = r.typeName();
            for (BlockType blockType : r.getValues()) {
```