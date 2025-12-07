# Unimplemented Refactoring Items

## Overview

The core refactoring is **COMPLETE**. All main tools (7 tools: 4 scanners + 3 matchers) have been successfully migrated to the new architecture. The following items are **optional** and can be done in the future if needed.

## Unimplemented Items

### 1. Legacy Tool Migration (Optional)

These tools still use the old architecture but continue to work:

- **`tools/scanners/tag_scanner.py`**
  - Uses `scanner_common.run_scanner()`
  - Specialized tag scanning functionality
  - Status: Works with old architecture, migration optional

- **`tools/asset_scanner.py`**
  - Uses `scanner_common.clean_results()`
  - Unified asset scanner (legacy tool)
  - Status: Works with old architecture, migration optional

**Note**: These tools are functional and don't need to be migrated unless new features are needed or maintenance becomes difficult.

### 2. Deprecated Code Removal (After Legacy Migration)

Once legacy tools are migrated (if ever), these deprecated modules can be removed:

- **`src/scanner_common.py`**
  - Currently used by: `tag_scanner.py`, `asset_scanner.py`
  - Marked with deprecation notice
  - Can be removed after legacy tool migration

- **`src/matcher_common.py`**
  - Marked with deprecation notice
  - Kept for backward compatibility
  - Can be removed after legacy tool migration

- **`src/matcher_base.py`**
  - Marked with deprecation notice
  - Kept for backward compatibility
  - Can be removed after legacy tool migration

**Note**: These modules are marked deprecated but functional. They can remain until legacy tools are migrated.

### 3. Optional Enhancements

These are nice-to-have improvements, not requirements:

- **More Edge Case Tests**
  - Test empty inputs
  - Test very long identifiers
  - Test special characters

- **Performance Benchmarks**
  - Benchmark processing speed
  - Test with large numbers of files
  - Test concurrent processing

- **End-to-End Integration Tests**
  - Test complete scanner workflows with real JAR files
  - Test complete matcher workflows with real data
  - Test with actual Minecraft mod JARs

## Current Status

✅ **Core Refactoring: COMPLETE**
- All main tools migrated
- New architecture fully functional
- All tests passing
- Documentation complete

⚠️ **Optional Items: PENDING**
- Legacy tools can be migrated if needed
- Deprecated code can be removed after legacy migration
- Enhancements can be added incrementally

## Decision

Since the core refactoring is complete and all main tools work with the new architecture, these unimplemented items are **optional** and can be addressed on an as-needed basis.
