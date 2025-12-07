## Non-Wood Type Exclusion System
This codemap traces how non-wood types are excluded in WoodGood through a type-based filtering system. The system applies extensive hardcoded exclusion rules specifically for WoodType and LeavesType instances [1b][1c], while other block types like stone and gems bypass these specialized filters entirely. Only basic generic exclusion rules [5a] apply to all block types. The configuration system is also wood/leaves focused [4a][4b], with separate blacklists for wood and leaves types but no equivalent for other block types. This design treats non-wood types as outside the scope of WoodGood's compatibility system.
### 1. Type-Based Filtering in Registration
How the system distinguishes between wood/leaves types and other block types during registration
### 1a. Registration Filter Entry Point (`SimpleModule.java:218`)
Main method that determines if any block type should be excluded from registration
```text
public boolean isEntryAlreadyRegistered(String entrySetId, String blockId, BlockType blockType, Registry<?> registry) {
```
### 1b. Wood Type Special Handling (`SimpleModule.java:230`)
Applies extensive hardcoded exclusion rules only for WoodType instances
```text
if (blockType instanceof WoodType woodType) {
            Boolean hardcoded = HardcodedBlockType.isWoodBlockAlreadyRegistered(entrySetId, blockName, woodType, modId);
            if (hardcoded != null) return hardcoded;
```
### 1c. Leaves Type Special Handling (`SimpleModule.java:233`)
Applies similar hardcoded exclusion rules for LeavesType instances
```text
} else if (blockType instanceof LeavesType leavesType) {
            Boolean hardcoded = HardcodedBlockType.isLeavesBlockAlreadyRegistered(entrySetId, blockName, leavesType, modId);
            if (hardcoded != null) return hardcoded;
```
### 1d. Generic Exclusion Rules (`SimpleModule.java:238`)
Applies basic exclusion rules that affect all block types including non-wood types
```text
/// ========== EXCLUDE ========== \\
        if (this.getAlreadySupportedMods().contains(woodTypeFrom)) return true;
```
### 2. Hardcoded Wood Type Exclusions
How the system applies specific exclusion rules for wood types while ignoring other block types
### 2a. Wood Type Exclusion Method (`HardcodedBlockType.java:23`)
Specialized method that only handles WoodType exclusions
```text
public static Boolean isWoodBlockAlreadyRegistered(String entrySetId, String blockName, WoodType woodType, String supportedModId) {
```
### 2b. Configuration Blacklist Check (`HardcodedBlockType.java:38`)
Excludes wood types based on user-configured regex patterns
```text
if (WOOD_TYPES_BLACKLIST.get().stream().anyMatch(woodidentify::matches)) return true;
```
### 2c. Vanilla Wood Exclusion (`HardcodedBlockType.java:47`)
Hardcoded exclusion for all known vanilla wood types
```text
if (isKnownVanillaWood(woodType)) return true;
```
### 2d. Problematic Wood Exclusion (`HardcodedBlockType.java:50`)
Hardcoded exclusion for specific problematic wood types with texture issues
```text
if (isWoodFrom("", "", "legendarymonuments:distortion", "")) return true;
```
### 3. Hardcoded Leaves Type Exclusions
Parallel exclusion system for leaves types that non-wood types bypass entirely
### 3a. Leaves Type Exclusion Method (`HardcodedBlockType.java:109`)
Separate method that only handles LeavesType exclusions
```text
public static Boolean isLeavesBlockAlreadyRegistered(String entrySetId, String blockName, LeavesType leavesType, String supportedModId) {
```
### 3b. Leaves Configuration Blacklist (`HardcodedBlockType.java:120`)
Separate blacklist system specifically for leaves types
```text
if (LEAVES_TYPES_BLACKLIST.get().stream().anyMatch(leavesidentify::matches)) return true;
```
### 3c. Vanilla Leaves Exclusion (`HardcodedBlockType.java:129`)
Excludes all vanilla leaves types using built-in method
```text
if (leavesType.isVanilla()) return true;
```
### 3d. Testing Leaves Exclusion (`HardcodedBlockType.java:132`)
Hardcoded exclusion for testing/debug leaves blocks
```text
if (isLeavesFrom("", "", "traversable_leaves:dev_leaves", "")) return true;
```
### 4. Configuration-Based Exclusion System
How users can exclude specific block types through configuration, primarily targeting wood/leaves
### 4a. Wood Type Blacklist Config (`UnsafeDisablerConfigs.java:58`)
Configuration option specifically for excluding wood types using regex patterns
```text
WOOD_TYPES_BLACKLIST = builder.comment("Exclude WoodType from all of Modules\n"+WoodTypeExample).define("blacklist", List.of());
```
### 4b. Leaves Type Blacklist Config (`UnsafeDisablerConfigs.java:62`)
Separate configuration specifically for leaves types
```text
LEAVES_TYPES_BLACKLIST = builder.comment("Exclude LeavesType from all of Modules\n\tThe example is same as WoodType's").define("blacklist", List.of());
```
### 4c. Block Blacklist Config (`UnsafeDisablerConfigs.java:76`)
Configuration for specific blocks, but documentation shows it's wood/leaves focused
```text
BLOCKS_BLACKLIST = builder.comment("Exclude a specific WoodType/LeavesType block\n"+blockExample).define("blacklist", List.of());
```
### 4d. Warning System (`UnsafeDisablerConfigs.java:114`)
Warns users about conditional registration risks, only checks wood/leaves configs
```text
if (!WOOD_TYPES_BLACKLIST.get().isEmpty() || !LEAVES_TYPES_BLACKLIST.get().isEmpty() || !BLOCKS_BLACKLIST.get().isEmpty()) {
```
### 5. Generic Exclusion Rules Applied to All Types
Basic exclusion rules that affect all block types including non-wood types
### 5a. Already Supported Mod Check (`SimpleModule.java:239`)
Excludes blocks from mods that have built-in support, applies to all types
```text
if (this.getAlreadySupportedMods().contains(woodTypeFrom)) return true;
```
### 5b. Self-Mod Exclusion (`SimpleModule.java:243`)
Prevents mods from generating blocks for their own types, applies universally
```text
if (woodTypeFrom.equals(modId)) return true;
```
### 5c. Existing Block Check (`SimpleModule.java:246`)
Excludes blocks that already exist in the target mod's registry
```text
if (registry.containsKey(new ResourceLocation(modId, blockName)) ||
                registry.containsKey(new ResourceLocation(modId, underscoreConvention))) {
```
### 5d. Cross-Mod Compatibility Check (`SimpleModule.java:258`)
Prevents duplicate registrations across different compatibility mods
```text
for (var c : EveryCompat.getCompatMods()) {
            String compatModId = c.modId();
            if (c.woodsFrom().contains(woodTypeFrom) && c.blocksFrom().contains(modId)) {
```