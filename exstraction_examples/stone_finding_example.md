## Stone Detection System in StoneZone
This codemap traces the complete stone detection system in StoneZone, from initialization through automatic pattern matching, manual registration, and filtering. Key locations include the main registry setup [1a], TFC special handling [2b], standard bricks detection [3a], polished stone detection [4a], manual registration examples [5a], and the filtering system [6c].
### 1. Initialization and Registration Flow
Main entry point where stone detection begins and registries are set up
### 1a. Registry Registration (`StoneZone.java:31`)
Stone type registry is registered with the BlockSetAPI system
```text
BlockSetAPI.registerBlockSetDefinition(StoneTypeRegistry.INSTANCE);
```
### 1b. Manual Registration Init (`StoneZone.java:33`)
Manual stone type registration is triggered for non-standard cases
```text
CompatStoneType.init();
```
### 1c. Detection Method Entry (`StoneTypeRegistry.java:36`)
Core detection logic that analyzes each block for stone type potential
```text
public Optional<StoneType> detectTypeFromBlock(Block baseblock, ResourceLocation baseRes) {
```
### 2. TFC/AFC Special Detection Path
Special handling for TerraFirmaCraft and ArborFirmaCraft stone detection
### 2a. TFC/AC check (`StoneTypeRegistry.java:39`)
Checks if block belongs to TFC or AFC mods
```text
if (baseRes.getNamespace().matches("tfc|afc")) {
```
### 2b. TFC pattern validation (`StoneTypeRegistry.java:40`)
Validates TFC rock/bricks pattern and BASEDRUM instrument type
```text
if (blockPath.matches("rock/bricks/\\w+") && baseblock.defaultBlockState().instrument() == NoteBlockInstrument.BASEDRUM ) {
```
### 2c. TFC stone creation (`StoneTypeRegistry.java:47`)
Creates StoneType object for detected TFC stone
```text
return Optional.of(new StoneType(baseRes.withPath(stoneName), opt.get()));
```
### 3. Standard Bricks Detection Pattern
Automatic detection of stone types ending with _bricks or _stone_bricks
### 3a. Bricks pattern match (`StoneTypeRegistry.java:55`)
Detects blocks following standard _bricks naming convention
```text
if (blockPath.matches("[a-z]+_(?:stone_)?bricks?")) {
```
### 3b. Dust exclusion check (`StoneTypeRegistry.java:64`)
Ensures detected stone is not actually a dust type
```text
boolean noDustType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replaceAll("(?<name>[a-z]+_)\\w+", "${name}dust")));
```
### 3c. Ore exclusion check (`StoneTypeRegistry.java:67`)
Ensures detected stone is not actually an ore type
```text
boolean noOreType = !BuiltInRegistries.BLOCK.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replaceAll("(?<name>[a-z]+_)\\w+", "${name}ore")));
```
### 3d. Stone type creation (`StoneTypeRegistry.java:83`)
Creates StoneType object for validated bricks pattern
```text
return Optional.of(new StoneType(baseRes.withPath(stoneName), opt.get()));
```
### 4. Polished Stone Detection Pattern
Automatic detection of polished stone variants
### 4a. Polished pattern match (`StoneTypeRegistry.java:89`)
Detects blocks starting with polished_ prefix
```text
else if (blockPath.matches("polished_[a-z]+(?:_stone)?")) {
```
### 4b. Stone name extraction (`StoneTypeRegistry.java:90`)
Extracts base stone name from polished variant
```text
String stoneName = blockPath.replace("polished_", "");
```
### 4c. Polished stone creation (`StoneTypeRegistry.java:104`)
Creates StoneType object for polished variants
```text
return Optional.of(new StoneType(baseRes.withPath(stoneName), opt.get()));
```
### 5. Manual Registration System
Handling of non-standard stone types through manual registration
### 5a. Two-word name handling (`CompatStoneType.java:56`)
Example of manual registration for stone with two-word name
```text
stoneReg.addSimpleFinder("pokecube_legends", "ultra_darkstone")
```
### 5b. ID affix handling (`CompatStoneType.java:64`)
Example of stone with _block suffix in actual block ID
```text
.stone("meteorite_block");
```
### 5c. Non-standard brick handling (`CompatStoneType.java:79`)
Example of bricks with non-standard suffix
```text
.childBlockSuffix(BRICKS, "_bricks_ornate")
```
### 6. Filtering and Blacklist System
Comprehensive filtering to exclude invalid stone types
### 6a. Mod blacklist check (`StoneTypeRegistry.java:53`)
Filters out entire mods that shouldn't be detected
```text
if (!BLACKLISTED_MODS.contains(baseRes.getNamespace())) {
```
### 6b. Stone type blacklist check (`StoneTypeRegistry.java:62`)
Filters out specific stone types that are invalid
```text
boolean isStoneTypeNotBlacklisted = !(BLACKLISTED_STONETYPES.contains(baseRes.withPath(stoneName).toString()) || BLACKLISTED_STONETYPES.contains(baseRes.withPath(stoneAlt).toString()));
```
### 6c. Vanilla exclusion (`HardcodedBlockType.java:67`)
Excludes all vanilla Minecraft stones from detection
```text
if (isKnownVanillaStone(stoneType)) return true;
```
### 6d. Special inclusions (`HardcodedBlockType.java:77`)
Force-includes certain blocks despite conflicts
```text
if (isStoneFrom("quark|create|decorative_blocks", "", "", "pillar")) return false;
```