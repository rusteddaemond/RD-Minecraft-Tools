## Ore and Non-Stone Type Exclusion System in StoneZone
This codemap traces StoneZone's comprehensive exclusion system that prevents ores, dust, wood, and other non-stone types from being detected as stone types. Key validation points include dust exclusion [1a], ore exclusion [2a], wood exclusion [3a], blacklist filtering [4b], user-configurable exclusions [5a], and vanilla stone handling [6a].
### 1. Dust Type Exclusion Validation
How StoneZone prevents dust blocks from being detected as stone types
### 1a. Dust exclusion check (`StoneTypeRegistry.java:64`)
Validates that detected stone doesn't have corresponding dust item variant
```text
boolean noDustType = !BuiltInRegistries.ITEM.containsKey(
                        new ResourceLocation(baseRes.getNamespace(), blockPath.replaceAll("(?<name>[a-z]+_)\\w+", "${name}dust"))
                );
```
### 1b. Dust validation in condition (`StoneTypeRegistry.java:77`)
Requires dust exclusion to pass before stone type registration
```text
&& noDustType
```
### 1c. Stone type creation (`StoneTypeRegistry.java:83`)
Only creates StoneType if dust exclusion and all validations pass
```text
if (opt.isPresent()) return Optional.of(new StoneType(baseRes.withPath(stoneName), opt.get()));
```
### 2. Ore Type Exclusion Validation
How StoneZone prevents ore blocks from being detected as stone types
### 2a. Ore exclusion check (`StoneTypeRegistry.java:67`)
Validates that detected stone doesn't have corresponding ore block variant
```text
boolean noOreType = !BuiltInRegistries.BLOCK.containsKey(
                        new ResourceLocation(baseRes.getNamespace(), blockPath.replaceAll("(?<name>[a-z]+_)\\w+", "${name}ore"))
                );
```
### 2b. Ore validation in condition (`StoneTypeRegistry.java:78`)
Requires ore exclusion to pass before stone type registration
```text
&& noOreType
```
### 2c. Combined validation chain (`StoneTypeRegistry.java:76`)
All exclusion checks must pass for stone type to be registered
```text
&& isStoneTypeNotBlacklisted
                        && noDustType
                        && noOreType
                        && noWoodType
```
### 3. Wood Type Exclusion Validation
How StoneZone prevents wood blocks from being detected as stone types
### 3a. Wood exclusion check (`StoneTypeRegistry.java:70`)
Validates that detected stone doesn't have corresponding log block variant
```text
boolean noWoodType = !BuiltInRegistries.BLOCK.containsKey(
                        new ResourceLocation(baseRes.getNamespace(), blockPath.replaceAll("(?<name>[a-z]+_)[a-z]+", "${name}log"))
                );
```
### 3b. Wood validation in condition (`StoneTypeRegistry.java:79`)
Requires wood exclusion to pass before stone type registration
```text
&& noWoodType
```
### 3c. Failed detection fallback (`StoneTypeRegistry.java:109`)
Returns empty when any validation fails, preventing invalid stone registration
```text
return Optional.empty();
```
### 4. Comprehensive Blacklist Filtering System
Hardcoded and configurable blacklists that exclude problematic stone types
### 4a. Mod blacklist check (`StoneTypeRegistry.java:53`)
Filters out entire mods that shouldn't be detected
```text
if (!BLACKLISTED_MODS.contains(baseRes.getNamespace())) {
```
### 4b. Stone type blacklist check (`StoneTypeRegistry.java:62`)
Filters out specific stone types that are invalid
```text
boolean isStoneTypeNotBlacklisted = !(BLACKLISTED_STONETYPES.contains(baseRes.withPath(stoneName).toString()) || BLACKLISTED_STONETYPES.contains(baseRes.withPath(stoneAlt).toString()));
```
### 4c. Hardcoded blacklist definitions (`HardcodedBlockType.java:28`)
Specific stone types excluded due to being terracotta, mud, or other non-stone materials
```text
public static final Set<String> BLACKLISTED_STONETYPES = Set.of(
            //REASON: is a terracotta
            "quark:shingles",

            //REASON: not a stonetype
            "outer_end:himmel", "quark:midori", "twigs:silt", "supplementaries:ash", "blue_skies:brumble",
            "nifty:concrete", "blocksyouneed_luna:bluestone", "blocksyouneed_luna:scorchcobble", "sullysmod:amber",
            "endergetic:eumus", "minecraft:mud", "enlightened_end:chorloam"
```
### 5. User-Configurable Exclusion System
How users can configure additional exclusions through config files
### 5a. User stone type exclusion (`HardcodedBlockType.java:61`)
Excludes stone types based on user-configured regex patterns
```text
if (stoneTypeList.get().stream().anyMatch(stoneIdentify::matches)) return true;
```
### 5b. Config definition (`UnsafeDisablerConfigs.java:53`)
Defines user-configurable blacklist for stone types
```text
stoneTypeList = builder.comment("Exclude StoneType from all of Modules\n"+stoneTypeExample).define("blacklist", List.of());
```
### 5c. Dynamic config access (`UnsafeDisablerConfigs.java:14`)
Provides runtime access to user-configured exclusion lists
```text
public static Supplier<List<String>> stoneTypeList;
```
### 6. Vanilla Stone Exclusion and Special Handling
How vanilla stones are excluded and special cases are handled
### 6a. Vanilla stone exclusion (`HardcodedBlockType.java:67`)
Excludes all vanilla Minecraft stones to prevent conflicts
```text
if (isKnownVanillaStone(stoneType)) return true;
```
### 6b. Vanilla stone definitions (`HardcodedBlockType.java:184`)
Complete list of vanilla stones that are excluded from detection
```text
private static final Set<String> VANILLA_STONES = Set.of(
            "stone", "andesite", "granite", "diorite", "tuff", "calcite", "blackstone", "sandstone",
            "basalt", "deepslate", "prismarine", "nether", "end_stone"
        );
```
### 6c. Special inclusion override (`HardcodedBlockType.java:77`)
Force-includes certain blocks like pillars despite other filtering rules
```text
if (isStoneFrom("quark|create|decorative_blocks", "", "", "pillar")) return false;
```