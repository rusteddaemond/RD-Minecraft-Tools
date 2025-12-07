## DustType Detection System
This codemap traces the complete DustType detection system in GemsRealm, from automated pattern matching [1b] through manual registration [2c] to blacklist filtering [4a]. The system uses a multi-layered approach combining regex pattern matching, item validation, exclusion checks, and priority-based registry ordering to accurately identify dust-type blocks across different mods.
### 1. Automated Detection Process
Core pattern matching and validation logic for detecting DustTypes from block names
### 1a. Entry Point (`DustTypeRegistry.java:31`)
Main detection method called by registry system
```text
public Optional<DustType> detectTypeFromBlock(Block baseBlock, ResourceLocation baseRes)
```
### 1b. Pattern Matching (`DustTypeRegistry.java:35`)
Checks for standard naming convention (e.g., 'redstone_block')
```text
if (blockPath.matches("\\w+_block")) {
```
### 1c. Dust Item Validation (`DustTypeRegistry.java:40`)
Ensures corresponding dust item exists
```text
boolean hasDust = BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "dust")))
```
### 1d. Comprehensive Validation (`DustTypeRegistry.java:54`)
Final validation against duplicates, exclusions, and blacklists
```text
if (!valuesReg.containsKey(idBlockType) && hasDust && noWoodType && noMetalType && noGemType && !BLACKLISTED_DUSTTYPES.contains(idBlockType.toString()) && !BLACKLISTED_MODS.contains(baseRes.getNamespace()) && !BLACKLISTED_DUST_MODS.contains(baseRes.getNamespace()))
```
### 1e. Type Creation (`DustTypeRegistry.java:65`)
Creates and returns new DustType instance
```text
return Optional.of(new DustType(idBlockType, opt.get()))
```
### 2. Manual Registration System
Fallback mechanism for DustTypes that don't follow standard naming conventions
### 2a. Registry Registration (`GemsRealm.java:38`)
Registers DustType system with the BlockSet API
```text
BlockSetAPI.registerBlockSetDefinition(DustTypeRegistry.INSTANCE)
```
### 2b. Manual Registration (`GemsRealm.java:39`)
Initializes manual DustType registrations
```text
CompatDustType.init()
```
### 2c. Custom Finder (`CompatDustType.java:37`)
Example of manual registration for non-standard naming
```text
dustReg.addSimpleFinder("atlantis:aquatic_power").dustBlockSuffix("_stone")
```
### 2d. Finder Configuration (`DustType.java:77`)
Sets up dust block finder for manual registration
```text
this.dustBlock(() -> findDustBlock(id))
```
### 3. Child Discovery and Validation
How DustType discovers related items and validates against other material types
### 3a. Dust Child Discovery (`DustType.java:39`)
Automatically discovers dust item for this type
```text
this.addChild("dust", findRelatedItem("", "dust"))
```
### 3b. Wood Type Exclusion (`DustTypeRegistry.java:43`)
Ensures block isn't actually a wood type
```text
boolean noWoodType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "log")))
```
### 3c. Metal Type Exclusion (`DustTypeRegistry.java:46`)
Ensures block isn't actually a metal type
```text
boolean noMetalType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "ingot")))
```
### 3d. Vanilla Validation (`HardcodedBlockType.java:129`)
Checks if DustType is from vanilla Minecraft
```text
return VANILLA_DUST.contains(id.getPath())
```
### 4. Blacklist and Priority System
Filtering mechanisms and registry priority for DustType detection
### 4a. Mod Blacklist (`HardcodedBlockType.java:24`)
Mods whose blocks should not be detected as DustTypes
```text
public static final Set<String> BLACKLISTED_DUST_MODS = Set.of("gtceu")
```
### 4b. Type Blacklist (`HardcodedBlockType.java:60`)
Specific block types to exclude from detection
```text
public static final Set<String> BLACKLISTED_DUSTTYPES = Set.of("betterend:ender")
```
### 4c. Registry Priority (`DustTypeRegistry.java:90`)
Sets detection priority order in the system
```text
public int priority() { return 110; }
```
### 4d. Vanilla Registration (`VanillaDustTypes.java:8`)
Manual registration of vanilla redstone DustType
```text
public static final DustType REDSTONE = DustTypeRegistry.INSTANCE.register(new DustType(new ResourceLocation("redstone"), Blocks.REDSTONE_BLOCK))
```