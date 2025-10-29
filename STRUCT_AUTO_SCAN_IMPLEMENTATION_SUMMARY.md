# Implementation Summary: PLC Struct Auto-Scan Feature

## Executive Summary

This document provides a comprehensive plan for implementing automatic scanning and importing of PLC struct (DUT - Data Unit Type) definitions with HMI attributes into the TwinCAT HMI application.

## Problem Statement

**Current Challenge**: When creating HMI interfaces for multiple similar sensors/devices in TwinCAT PLC, developers must manually configure each instance in `config.json`, leading to:
- Time-consuming manual configuration
- High risk of errors and inconsistencies
- Difficult maintenance when structures change
- Poor scalability with many similar devices

**Proposed Solution**: Automatically scan the PLC for struct types marked with `HMI_STRUCT` attribute, expand them to their individual members, and import only members with HMI attributes (HMI_SP, HMI_PV, HMI_SWITCH, HMI_ALARM).

## Example Use Case

### PLC Code
```iecst
TYPE ST_AnalogInput :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    Value : REAL;
    
    {attribute 'HMI_ALARM'}
    Error : BOOL;
    
    RawValue : INT;  // No HMI attribute - not imported
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}  // Marker for auto-import
    Temperature_Sensor_1 : ST_AnalogInput;
END_VAR
```

### Expected Result
When scanning the PLC, the system should:
1. Find `Temperature_Sensor_1` (has `HMI_STRUCT` attribute)
2. Identify it as type `ST_AnalogInput` (struct)
3. Expand the struct to members:
   - `Temperature_Sensor_1.Value` → Process Value (°C)
   - `Temperature_Sensor_1.Error` → Alarm
4. Skip non-HMI members:
   - ~~`Temperature_Sensor_1.RawValue`~~ (no HMI attribute)
5. Auto-generate config entries and GUI widgets

## Documentation Structure

### 1. **STRUCT_AUTO_SCAN_README.md** (This File)
- Master index of all documentation
- Quick start guides
- Reading guide for different scenarios
- Current status

### 2. **AUTO_SCAN_STRUCT_PLAN.md** (19KB, Danish)
**Purpose**: Complete technical implementation plan  
**Contents**:
- Current state analysis
- Phase-by-phase implementation guide
- Detailed code examples for each component
- TMC XML structure documentation
- Test cases and scenarios
- Troubleshooting guide
- Performance considerations

**Target Audience**: Developers implementing the feature

### 3. **STRUCT_AUTO_SCAN_PROMPT.md** (5KB, Danish)
**Purpose**: Concise implementation prompt/summary  
**Contents**:
- Brief feature description
- Example PLC code and expected results
- Implementation checklist
- Success criteria

**Target Audience**: Developers needing quick reference

### 4. **STRUCT_AUTO_SCAN_VISUAL_GUIDE.md** (21KB, Danish)
**Purpose**: Visual understanding with diagrams  
**Contents**:
- Before/after comparisons
- Workflow diagrams
- Struct expansion examples
- GUI layout concepts
- Nested structs and arrays
- Use cases with time savings

**Target Audience**: All stakeholders, presentations

### 5. **example_struct_plc_code.st** (11KB)
**Purpose**: Complete PLC code examples  
**Contents**:
- Struct definitions (ST_AnalogInput, ST_Motor, ST_Tank, etc.)
- Nested struct example (ST_TempController with PID)
- Array of structs example
- Comprehensive comments and usage instructions

**Target Audience**: PLC developers, testing

## Implementation Phases

### Phase 1: TMC Parser Enhancement
**File**: `tmc_parser.py`

**Tasks**:
- Add method to find all DataType (struct) definitions in TMC
- Parse struct members with their attributes
- Implement method to find symbols of struct types
- Handle nested structs (struct in struct)

**New Methods**:
```python
def get_all_datatypes(self) -> List[Dict[str, Any]]
def get_struct_members(self, struct_name: str) -> List[Dict[str, Any]]
def find_struct_symbols(self) -> List[Dict[str, Any]]
def expand_struct_symbol(self, symbol: Dict) -> List[Dict[str, Any]]
```

### Phase 2: Auto-Config Enhancement
**File**: `symbol_auto_config.py`

**Tasks**:
- Detect when a symbol is a struct type
- Get struct definition from TMC or PLC
- Expand struct members
- Filter members based on HMI attributes
- Generate config entries for each member

**New Methods**:
```python
def _is_struct_symbol(self, symbol) -> bool
def _expand_struct_members(self, symbol, data_type: str) -> List[Dict]
def _get_struct_definition(self, type_name: str) -> Dict
def _analyze_struct_member(self, parent_name: str, member: Dict) -> Optional[Dict]
```

### Phase 3: Symbol Parser Update
**File**: `ads_symbol_parser.py`

**Tasks**:
- Handle struct member paths (e.g., "GVL.Sensor1.Value")
- Parse hierarchical symbol names
- Generate display names for struct members

### Phase 4: GUI Display
**File**: `gui_panels.py`

**Tasks**:
- Group struct members visually
- Display struct name as group header
- Indent members under struct
- Add collapse/expand functionality (optional)

### Phase 5: Configuration
**File**: `config.json`

**New Section**:
```json
{
  "struct_import": {
    "enabled": true,
    "auto_expand": true,
    "include_markers": ["HMI_STRUCT", "HMI_DUT"],
    "exclude_members_without_hmi": true,
    "max_depth": 3,
    "flatten_nested": false
  }
}
```

## Key Benefits

### Time Savings
```
Manual Configuration:  30 minutes per sensor
Auto-Import:           2 minutes per sensor
─────────────────────────────────────────
Savings:              28 minutes (93% reduction)
```

### Scalability
```
1 sensor:    2 minutes
10 sensors:  2 minutes  
100 sensors: 2 minutes  (Same time!)
```

### Error Reduction
```
Manual Config:  High risk of typos, missing attributes
Auto-Import:    Minimal risk (PLC compiler validated)
```

### Maintainability
```
Manual:  Update each instance separately
Auto:    Update struct once, all instances updated
```

## Technical Architecture

### Data Flow
```
PLC Code (Structs with HMI attributes)
    ↓
TwinCAT Compile → TMC File
    ↓
TMC Parser → Extract struct definitions
    ↓
Auto Scanner → Find HMI_STRUCT symbols
    ↓
Struct Expander → Extract members with HMI tags
    ↓
Config Generator → Create config entries
    ↓
Symbol Parser → Categorize members
    ↓
GUI Builder → Create grouped widgets
    ↓
HMI Display
```

### Component Stack
```
┌─────────────────────────┐
│   GUI Display Layer     │  gui_panels.py
├─────────────────────────┤
│   Symbol Parser Layer   │  ads_symbol_parser.py
├─────────────────────────┤
│   Config Generator      │  symbol_auto_config.py
├─────────────────────────┤
│   TMC Parser Layer      │  tmc_parser.py
├─────────────────────────┤
│   ADS Layer             │  ads_client.py
├─────────────────────────┤
│   TwinCAT PLC + TMC     │  (External)
└─────────────────────────┘
```

## Test Cases

### Test Case 1: Simple Struct
**Input**: Struct with 3 members (2 with HMI, 1 without)  
**Expected**: 2 members imported, 1 skipped

### Test Case 2: Nested Struct
**Input**: Struct containing another struct  
**Expected**: All HMI members from both levels imported with full path

### Test Case 3: Array of Structs
**Input**: `ARRAY[1..3] OF ST_Tank`  
**Expected**: All 3 instances expanded with indexed paths

### Test Case 4: Mixed Symbols
**Input**: Some simple symbols, some struct symbols  
**Expected**: Simple symbols work as before, struct symbols expanded

## Success Criteria

- ✅ Structs with `HMI_STRUCT` attribute are found automatically
- ✅ Only members with HMI attributes are imported
- ✅ Config is generated with correct full paths
- ✅ GUI displays grouped members
- ✅ All existing features work (backward compatibility)
- ✅ Performance is acceptable (< 2 seconds for typical project)
- ✅ Nested structs work up to configured depth
- ✅ Arrays of structs are handled correctly

## Current Status

### Completed ✅
- [x] Complete documentation package created
- [x] Implementation plan documented
- [x] Visual guide with diagrams
- [x] Example PLC code for testing
- [x] Architecture design
- [x] Test cases defined

### Pending ⏳
- [ ] TMC parser enhancement implementation
- [ ] Auto-config expansion implementation
- [ ] Config generation implementation
- [ ] GUI display implementation
- [ ] Testing and validation
- [ ] Integration with main application
- [ ] Documentation in main README

## Getting Started

### For PLC Developers
1. Review `example_struct_plc_code.st` for struct patterns
2. Add `{attribute 'HMI_STRUCT'}` to your struct instances
3. Ensure struct members have HMI attributes
4. Compile project and verify TMC file

### For HMI Developers
1. Read `STRUCT_AUTO_SCAN_PROMPT.md` for requirements
2. Follow `AUTO_SCAN_STRUCT_PLAN.md` for implementation
3. Implement phase-by-phase
4. Test with example code
5. Refer to `STRUCT_AUTO_SCAN_VISUAL_GUIDE.md` for concepts

### For Project Managers
1. Review `STRUCT_AUTO_SCAN_VISUAL_GUIDE.md` for overview
2. Assess time savings and benefits
3. Prioritize implementation phases
4. Allocate resources

## Resources

### Documentation Files
- `STRUCT_AUTO_SCAN_README.md` - This file
- `AUTO_SCAN_STRUCT_PLAN.md` - Detailed plan (Danish)
- `STRUCT_AUTO_SCAN_PROMPT.md` - Quick reference (Danish)
- `STRUCT_AUTO_SCAN_VISUAL_GUIDE.md` - Visual guide (Danish)
- `example_struct_plc_code.st` - PLC examples

### Related Files in Repository
- `tmc_parser.py` - TMC XML parsing
- `symbol_auto_config.py` - Auto-scan functionality
- `ads_symbol_parser.py` - Symbol categorization
- `gui_panels.py` - GUI widgets
- `config.json` - Configuration
- `TMC_METADATA.md` - TMC integration guide

## Questions & Support

### Common Questions

**Q: Do I need to change existing code?**  
A: No, existing functionality will work as before. This is purely additive.

**Q: What if I don't use structs?**  
A: Continue using the current auto-scan or manual configuration.

**Q: Can I mix struct and non-struct symbols?**  
A: Yes, both will work simultaneously.

**Q: What about nested structs?**  
A: Supported up to configurable max depth (default: 3 levels).

**Q: How do arrays work?**  
A: Each array element is expanded: `Tanks[1].Level`, `Tanks[2].Level`, etc.

### Troubleshooting
See `AUTO_SCAN_STRUCT_PLAN.md` for detailed troubleshooting guide.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial documentation package |

## License

Same as main project - see main `README.md`

---

**Last Updated**: 2025-10-29  
**Status**: Documentation Complete ✅ | Implementation Pending ⏳  
**Contact**: Development Team
