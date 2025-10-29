# AI Prompt: Implement PLC Struct Auto-Scan for TwinCAT HMI

## Objective
Implement automatic scanning and importing of PLC struct (DUT) types with HMI attributes into the TwinCAT HMI application. When a struct instance is marked with `{attribute 'HMI_STRUCT'}`, automatically import all struct members that have HMI attributes.

## Context
This is a Python/PyQt5 HMI application that communicates with TwinCAT 3 PLC via ADS protocol. The application already has:
- TMC (Type Management Component) XML parser for reading PLC metadata
- Auto-scan functionality for simple symbols
- Symbol categorization (Setpoints, Process Values, Switches, Alarms)
- Configuration generation to `config.json`

## Input Example (PLC Code)
```iecst
TYPE ST_AnalogInput :
STRUCT
    {attribute 'HMI_PV'}        // ← HMI tag = IMPORT
    {attribute 'Unit' := '°C'}
    Value : REAL;
    
    {attribute 'HMI_ALARM'}     // ← HMI tag = IMPORT
    Error : BOOL;
    
    RawValue : INT;             // ← No HMI tag = SKIP
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}    // ← Marker: auto-import this struct
    Temperature_Sensor_1 : ST_AnalogInput;
END_VAR
```

## Expected Output
After scanning:
1. Find `Temperature_Sensor_1` (has `HMI_STRUCT` attribute)
2. Detect it's type `ST_AnalogInput` (struct)
3. Expand to members with HMI attributes:
   - ✅ `Temperature_Sensor_1.Value` → Process Value (°C)
   - ✅ `Temperature_Sensor_1.Error` → Alarm
   - ❌ `Temperature_Sensor_1.RawValue` → Skipped (no HMI tag)
4. Generate config entries:
```json
{
  "Temperature_Sensor_1.Value": {
    "category": "process_value",
    "parent_struct": "Temperature_Sensor_1",
    "struct_type": "ST_AnalogInput",
    "unit": "°C",
    ...
  },
  "Temperature_Sensor_1.Error": {
    "category": "alarm",
    "parent_struct": "Temperature_Sensor_1",
    "struct_type": "ST_AnalogInput",
    ...
  }
}
```
5. Create grouped GUI widgets

## Files to Modify

### 1. `tmc_parser.py` - Parse Struct Definitions
Add methods:
```python
def get_all_datatypes(self) -> List[Dict[str, Any]]:
    """Find all DataType (struct) definitions in TMC XML"""
    # Find <DataType> elements
    # Return list of struct definitions

def get_struct_members(self, struct_name: str) -> List[Dict[str, Any]]:
    """Get all members of a struct with their attributes"""
    # Find DataType with matching name
    # Parse all <SubItem> elements (struct members)
    # Extract attributes from <Properties>
    # Return list of member dicts with {name, type, attributes}

def find_struct_symbols(self) -> List[Dict[str, Any]]:
    """Find symbols that are struct types with HMI_STRUCT attribute"""
    # Find <Symbol> elements
    # Filter by HMI_STRUCT in Properties
    # Return list of struct symbols
```

### 2. `symbol_auto_config.py` - Expand Structs
Enhance `_analyze_symbol()`:
```python
def _analyze_symbol(self, symbol) -> Optional[Dict[str, Any]]:
    # Existing code...
    
    # NEW: Check if symbol is a struct type
    if self._is_struct_type(data_type):
        # Check for HMI_STRUCT marker in comment/attributes
        if 'hmi_struct' in comment.lower():
            # Expand struct to members
            return self._expand_struct_members(symbol, data_type)
    
    # Existing simple symbol processing...

def _expand_struct_members(self, symbol, data_type: str) -> List[Dict]:
    """Expand struct into individual members with HMI tags"""
    members = []
    
    # Get struct definition from TMC
    struct_def = self.tmc_parser.get_struct_members(data_type)
    
    for member in struct_def:
        # Check if member has HMI attributes
        has_hmi = any(key.startswith('HMI_') for key in member['attributes'])
        
        if has_hmi:
            # Build full member path: "Parent.Member"
            member_path = f"{symbol.name}.{member['name']}"
            
            # Create config with parent_struct metadata
            member_config = {
                'name': member_path,
                'parent_struct': symbol.name,
                'struct_type': data_type,
                'member_name': member['name'],
                'data_type': member['type'],
                'attributes': member['attributes']
            }
            
            # Categorize member
            category = self._determine_category(...)
            if category:
                member_config['category'] = category
                members.append(member_config)
    
    return members
```

### 3. `ads_symbol_parser.py` - Handle Struct Paths
Update `_get_display_name()` to handle struct member paths:
```python
def _get_display_name(self, symbol_name: str) -> str:
    """Convert symbol name to display-friendly format"""
    # Handle struct member paths: "GVL.Sensor.Value"
    parts = symbol_name.split('.')
    
    if len(parts) >= 3:  # Has struct member
        # Return "Sensor Value" or similar
        struct_name = parts[-2]
        member_name = parts[-1]
        return f"{struct_name} {member_name}"
    
    # Existing logic for simple symbols...
```

### 4. `gui_panels.py` - Grouped Display
Add struct grouping to widget creation:
```python
def add_struct_group(self, struct_name: str, members: List[Dict]):
    """Create grouped display for struct members"""
    # Create QGroupBox for struct
    group = QGroupBox(struct_name)
    layout = QVBoxLayout()
    
    # Add widgets for each member
    for member in members:
        widget = self._create_member_widget(member)
        layout.addWidget(widget)
    
    group.setLayout(layout)
    self.main_layout.addWidget(group)
```

### 5. `config.json` - Add Configuration
```json
{
  "struct_import": {
    "enabled": true,
    "auto_expand": true,
    "exclude_members_without_hmi": true,
    "max_depth": 3
  }
}
```

## Implementation Steps

1. **Parse Structs** (tmc_parser.py)
   - Implement `get_all_datatypes()` to find `<DataType>` in TMC XML
   - Implement `get_struct_members()` to parse `<SubItem>` elements
   - Implement `find_struct_symbols()` to find symbols with `HMI_STRUCT`

2. **Expand Structs** (symbol_auto_config.py)
   - In `_analyze_symbol()`, detect struct types
   - Implement `_expand_struct_members()` to iterate members
   - Filter members by HMI attributes
   - Generate config with full paths and parent metadata

3. **Update Parser** (ads_symbol_parser.py)
   - Handle struct member paths (dot notation)
   - Generate appropriate display names

4. **Update GUI** (gui_panels.py)
   - Group struct members visually
   - Show struct name as header
   - Indent members under struct

5. **Test**
   - Use `example_struct_plc_code.st` for testing
   - Verify simple structs work
   - Verify nested structs work
   - Verify arrays work

## TMC XML Structure Reference

### Struct Definition
```xml
<DataType>
  <Name>ST_AnalogInput</Name>
  <SubItem>
    <Name>Value</Name>
    <Type>REAL</Type>
    <Properties>
      <Property><Name>HMI_PV</Name></Property>
      <Property><Name>Unit</Name><Value>°C</Value></Property>
    </Properties>
  </SubItem>
  <SubItem>
    <Name>Error</Name>
    <Type>BOOL</Type>
    <Properties>
      <Property><Name>HMI_ALARM</Name></Property>
    </Properties>
  </SubItem>
  <SubItem>
    <Name>RawValue</Name>
    <Type>INT</Type>
    <!-- No Properties = no HMI tags -->
  </SubItem>
</DataType>
```

### Symbol Instance
```xml
<Symbol>
  <Name>GVL.Temperature_Sensor_1</Name>
  <BaseType>ST_AnalogInput</BaseType>
  <Properties>
    <Property><Name>HMI_STRUCT</Name></Property>
  </Properties>
</Symbol>
```

## Edge Cases to Handle

1. **Nested Structs**: Struct containing another struct
   - Solution: Recursive expansion with max depth limit
   - Path: `Controller.PID.Kp`

2. **Arrays**: `ARRAY[1..10] OF ST_Sensor`
   - Solution: Expand each index: `Sensors[1].Value`, `Sensors[2].Value`

3. **No HMI Members**: Struct with no HMI attributes
   - Solution: Skip entirely, log warning

4. **Mixed Symbols**: Project has both simple and struct symbols
   - Solution: Both work simultaneously

5. **Member Name Conflicts**: Same member name in different structs
   - Solution: Full path ensures uniqueness

## Success Criteria

- ✅ Structs with `HMI_STRUCT` are auto-detected
- ✅ Only members with HMI attributes imported
- ✅ Config generated with full paths
- ✅ GUI shows grouped members
- ✅ Backward compatible (existing features work)
- ✅ Performance acceptable (< 2s scan time)

## Available Resources

- `AUTO_SCAN_STRUCT_PLAN.md` - Detailed implementation plan (19KB)
- `STRUCT_AUTO_SCAN_VISUAL_GUIDE.md` - Visual guide with diagrams (21KB)
- `example_struct_plc_code.st` - Complete PLC examples (11KB)
- Existing code: `tmc_parser.py`, `symbol_auto_config.py`, etc.

## Key Implementation Notes

1. **TMC is Primary Source**: Use TMC XML for struct definitions (most reliable)
2. **Filter by HMI Attributes**: Only import members with HMI_SP/HMI_PV/HMI_SWITCH/HMI_ALARM
3. **Full Path Access**: Members accessed as `Parent.Member` for uniqueness
4. **Preserve Metadata**: Keep parent_struct and struct_type in config for grouping
5. **Visual Grouping**: GUI should show clear struct hierarchy

## Testing Checklist

- [ ] Simple struct (ST_AnalogInput) expands correctly
- [ ] Nested struct (ST_Controller with PID) expands with full paths
- [ ] Array of structs expands all indices
- [ ] Members without HMI tags are skipped
- [ ] Config.json generated correctly
- [ ] GUI displays grouped widgets
- [ ] Existing simple symbols still work
- [ ] Performance is acceptable

## Example Test Code

Use the provided `example_struct_plc_code.st` which includes:
- ST_AnalogInput (simple struct)
- ST_Motor (multiple member types)
- ST_TempController (nested with PID)
- ST_Tank (simple for arrays)
- Multiple instances of each

---

**Note**: This is a documentation-complete, implementation-pending feature. All planning is done, ready for development.
