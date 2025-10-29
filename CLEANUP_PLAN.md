# Application Cleanup Report

## Files to Remove (Legacy Code)

### Can be safely deleted:
1. `tmc_config_generator.py` - Legacy TMC parser (not needed with STRUCTs)
2. `symbol_auto_config.py` - Auto-discovery based on attributes (replaced by STRUCT discovery)
3. Old test files if any

### Config.json cleanup:
- Remove `tmc_file` path (not needed)
- Remove `auto_scan_on_start` (not needed)
- Remove legacy `symbols` section (replaced by `struct_symbols`)
- Remove `manual_symbols` section (not needed)

### main.py cleanup needed:
- Remove import of `TMCConfigGenerator`
- Remove import of `SymbolAutoConfig`
- Remove `load_from_tmc()` method
- Remove `scan_plc_symbols()` method
- Remove `load_manual_symbols()` method
- Simplify `discover_symbols()` to only call `discover_symbols_from_structs()`
- Remove legacy fallback logic in `discover_symbols()`

## Recommendation

Keep legacy code for now but disable it in config by ensuring `use_structs: true`.
This allows rollback if needed during testing phase.

After 1-2 weeks of successful operation, delete legacy files permanently.
