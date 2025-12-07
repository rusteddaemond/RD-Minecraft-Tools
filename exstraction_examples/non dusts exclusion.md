## Non-Dust Block Exclusion System
This codemap traces the comprehensive exclusion system that prevents non-dust blocks from being incorrectly classified as DustTypes in GemsRealm. The system uses cross-validation logic [1b-1d] to exclude wood, metal, and gem materials, reciprocal exclusion across all material type registries [2a-2e], hardcoded blacklists for problematic mods and blocks [3a-3c], and priority-based registry execution [4a-4d] to maintain clean type separation across the diverse Minecraft mod ecosystem.
### 1. DustType Cross-Validation Logic
Core validation checks that prevent wood, metal, and gem blocks from being detected as DustTypes
### 1a. Dust Item Requirement (`DustTypeRegistry.java:40`)
Ensures corresponding dust item exists for positive identification
```text
boolean hasDust = BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "dust")))
```
### 1b. Wood Type Exclusion (`DustTypeRegistry.java:43`)
Rejects blocks that have corresponding log items (wood materials)
```text
boolean noWoodType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "log")))
```
### 1c. Metal Type Exclusion (`DustTypeRegistry.java:46`)
Rejects blocks that have corresponding ingot items (metal materials)
```text
boolean noMetalType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "ingot")))
```
### 1d. Gem Type Exclusion (`DustTypeRegistry.java:49`)
Rejects blocks that have items with same name (gem materials)
```text
boolean noGemType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("_block", "")))
```
### 1e. Comprehensive Validation (`DustTypeRegistry.java:54`)
Final gate requiring all validation checks to pass before DustType creation
```text
if (!valuesReg.containsKey(idBlockType) && hasDust && noWoodType && noMetalType && noGemType && !BLACKLISTED_DUSTTYPES.contains(idBlockType.toString()) && !BLACKLISTED_MODS.contains(baseRes.getNamespace()) && !BLACKLISTED_DUST_MODS.contains(baseRes.getNamespace()))
```
### 2. Cross-Type Registry Exclusion
How other material type registries exclude dust blocks to maintain type separation
### 2a. Gem Registry Dust Exclusion (`GemTypeRegistry.java:57`)
GemType registry excludes blocks with dust items to avoid conflicts
```text
boolean noDustType = !BuiltInRegistries.ITEM.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "dust")))
```
### 2b. Gem Multi-Type Validation (`GemTypeRegistry.java:71`)
GemType requires exclusion of crystal, dust, and metal indicators
```text
&& noCrystalType && noDustType && noMetalType
```
### 2c. Metal Registry Wood Exclusion (`MetalTypeRegistry.java:94`)
MetalType registry excludes blocks with log items
```text
boolean noWoodType = !BuiltInRegistries.BLOCK.containsKey(new ResourceLocation(baseRes.getNamespace(), blockPath.replace("block", "log")))
```
### 2d. Metal Multi-Type Validation (`MetalTypeRegistry.java:102`)
MetalType requires ingot presence and exclusion of wood/gem indicators
```text
&& hasIngot && noWoodType && noGemType
```
### 2e. Crystal Multi-Type Validation (`CrystalTypeRegistry.java:61`)
CrystalType excludes wood, metal, and gem indicators
```text
&& noWoodType && noMetalType && noGemType
```
### 3. Blacklist Filtering System
Hardcoded exclusions for problematic mods and specific block types
### 3a. Dust Mod Blacklist (`HardcodedBlockType.java:24`)
Entire mods excluded from DustType detection
```text
public static final Set<String> BLACKLISTED_DUST_MODS = Set.of("gtceu")
```
### 3b. Specific Dust Type Blacklist (`HardcodedBlockType.java:60`)
Individual blocks excluded from DustType detection
```text
public static final Set<String> BLACKLISTED_DUSTTYPES = Set.of("betterend:ender")
```
### 3c. Metal Type Blacklist (`HardcodedBlockType.java:28`)
Specific blocks excluded from MetalType detection
```text
public static final Set<String> BLACKLISTED_METALTYPES = Set.of("ms:blaze", "atlantis:raw_ancient_metal", "advancednetherite:netherite_diamond")
```
### 3d. Gem Type Blacklist (`HardcodedBlockType.java:36`)
Vanilla and mod blocks excluded from GemType detection
```text
public static final Set<String> BLACKLISTED_GEMTYPES = Set.of("minecraft:redstone", "minecraft:coal")
```
### 3e. Blacklist Application (`DustTypeRegistry.java:59`)
Final blacklist checks applied before DustType registration
```text
&& !BLACKLISTED_DUSTTYPES.contains(idBlockType.toString()) && !BLACKLISTED_MODS.contains(baseRes.getNamespace()) && !BLACKLISTED_DUST_MODS.contains(baseRes.getNamespace())
```
### 4. Priority-Based Registry Execution
How registry priority order prevents conflicts between material type detection
### 4a. DustType Priority (`DustTypeRegistry.java:90`)
DustType detection runs at priority 110
```text
public int priority() { return 110; }
```
### 4b. GemType Priority (`GemTypeRegistry.java:104`)
GemType detection also runs at priority 110
```text
public int priority() { return 110; }
```
### 4c. MetalType Priority (`MetalTypeRegistry.java:134`)
MetalType detection runs at priority 110
```text
public int priority() { return 110; }
```
### 4d. CrystalType Priority (`CrystalTypeRegistry.java:92`)
CrystalType detection runs at priority 110
```text
public int priority() { return 110; }
```