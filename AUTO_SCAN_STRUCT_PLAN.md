# Auto-Scan Plan: PLC Struct Import med HMI Attributer

## Oversigt
Dette dokument beskriver planen for at implementere automatisk scanning og import af PLC structs (DUT - Data Unit Types) der har HMI attributer. Når en struct findes med en attribut der starter med "HMI", skal hele structen importeres og alle dens medlemmer trækkes ind i HMI projektet.

## Nuværende Tilstand
Applikationen har allerede følgende funktionalitet:
- ✅ TMC fil parsing (læser XML metadata fra TwinCAT)
- ✅ Auto-scan af simple symboler med HMI attributer
- ✅ Symbol kategorisering (Setpoints, Process Values, Switches, Alarms)
- ✅ ADS kommunikation med PLC
- ✅ Automatisk config generering

## Problem Statement
**Mål**: Automatisk scanne PLCen for tags med attributer der starter med "HMI". Når attributen findes, skal hele den struct importeres og hver tag trækkes ind i HMI projektet.

### Eksempel PLC Struktur
```iecst
TYPE ST_AnalogInput :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '2'}
    Value : REAL;
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    Scaled : REAL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Sensor Fejl'}
    Error : BOOL;
    
    // Ikke-HMI medlemmer (skal ikke importeres)
    RawValue : INT;
    Timestamp : TIME;
END_STRUCT
END_TYPE

// Brug af struct
VAR_GLOBAL
    {attribute 'HMI_STRUCT'}  // Marker hele structen til import
    Temperature_Sensor_1 : ST_AnalogInput;
    
    {attribute 'HMI_STRUCT'}
    Pressure_Sensor_1 : ST_AnalogInput;
END_VAR
```

### Forventet Resultat
Når PLCen scannes, skal systemet:
1. Finde `Temperature_Sensor_1` (har `HMI_STRUCT` attribut)
2. Se at det er en struct type `ST_AnalogInput`
3. Scanne alle medlemmer i structen
4. Importere kun medlemmer med HMI attributer:
   - `Temperature_Sensor_1.Value` (HMI_PV, °C, 2 decimaler)
   - `Temperature_Sensor_1.Scaled` (HMI_PV, %)
   - `Temperature_Sensor_1.Error` (HMI_ALARM)
5. Springe over ikke-HMI medlemmer:
   - `Temperature_Sensor_1.RawValue` ❌
   - `Temperature_Sensor_1.Timestamp` ❌

## Implementeringsplan

### Fase 1: Forbedre TMC Parser
**Fil**: `tmc_parser.py`

**Opgaver**:
1. Tilføj metode til at finde alle DataType (struct) definitioner i TMC
2. Parse struct medlemmer med deres attributer
3. Implementer metode til at finde symboler af struct typer
4. Håndter nested structs (struct i struct)

**Ny funktionalitet**:
```python
class TMCParser:
    def get_all_datatypes(self) -> List[Dict[str, Any]]:
        """Find alle DUT/STRUCT definitioner i TMC"""
        
    def get_struct_members(self, struct_name: str) -> List[Dict[str, Any]]:
        """Hent alle medlemmer af en struct med deres attributer"""
        
    def find_struct_symbols(self) -> List[Dict[str, Any]]:
        """Find alle symboler der er struct typer med HMI attributer"""
        
    def expand_struct_symbol(self, symbol: Dict) -> List[Dict[str, Any]]:
        """Ekspander en struct til dens individuelle medlemmer"""
```

### Fase 2: Udvid Symbol Auto Config
**Fil**: `symbol_auto_config.py`

**Opgaver**:
1. Detekter når et symbol er en struct type
2. Hent struct definition fra TMC eller PLC
3. Ekspander struct medlemmer
4. Filter medlemmer baseret på HMI attributer
5. Generer config entries for hvert medlem

**Ny funktionalitet**:
```python
class SymbolAutoConfig:
    def _is_struct_symbol(self, symbol) -> bool:
        """Check om symbol er en struct type"""
        
    def _expand_struct_members(self, symbol, data_type: str) -> List[Dict]:
        """Ekspander struct til individuelle medlemmer med HMI tags"""
        
    def _get_struct_definition(self, type_name: str) -> Dict:
        """Hent struct definition fra TMC eller PLC"""
        
    def _analyze_struct_member(self, parent_name: str, member: Dict) -> Optional[Dict]:
        """Analyser et struct medlem og generer config"""
```

### Fase 3: Opdater ADS Client
**Fil**: `ads_client.py`

**Opgaver**:
1. Tilføj support til at læse struct type information
2. Implementer metode til at læse struct medlemmer individuelt
3. Håndter nested struct member access (dot notation)

**Ny funktionalitet**:
```python
class ADSClient:
    def get_symbol_type_info(self, symbol_name: str) -> Dict:
        """Hent type information for et symbol"""
        
    def is_struct_type(self, type_name: str) -> bool:
        """Check om en type er en struct"""
        
    def read_struct_member(self, struct_name: str, member_name: str) -> Any:
        """Læs en specifik struct medlem"""
```

### Fase 4: Udvid Symbol Parser
**Fil**: `ads_symbol_parser.py`

**Opgaver**:
1. Håndter struct member paths (f.eks. "GVL.Sensor1.Value")
2. Parse hierarchiske symbol navne
3. Generer display names for struct medlemmer

**Ny funktionalitet**:
```python
class SymbolParser:
    def _parse_struct_member_path(self, symbol_name: str) -> tuple:
        """Split struct.member.submember paths"""
        
    def _get_struct_display_name(self, symbol_name: str) -> str:
        """Generer display navn for struct medlem"""
```

### Fase 5: Opdater Konfiguration
**Fil**: `config.json`

**Nye konfigurationsmuligheder**:
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

### Fase 6: GUI Visning
**Fil**: `gui_panels.py`

**Opgaver**:
1. Gruppér struct medlemmer visuelt
2. Vis struct navn som gruppe header
3. Indent medlemmer under struct
4. Tilføj collapse/expand funktionalitet

**Eksempel GUI Layout**:
```
┌─ Temperature_Sensor_1 ────────────┐
│  └─ Value:        23.45 °C        │
│  └─ Scaled:       45.2 %          │
│  └─ Error:        ⚠️ Sensor Fejl  │
└───────────────────────────────────┘
```

## Detaljeret Workflow

### Step-by-Step Proces
1. **Start Scan**
   - Bruger klikker "Scan PLC" eller auto-scan ved opstart
   
2. **Symbol Discovery**
   - ADS Client henter alle symboler fra PLC
   - Filter symboler med HMI relaterede attributer
   
3. **Type Detection**
   - For hvert symbol, check data typen
   - Hvis type er STRUCT/DUT → gå til struct expansion
   - Hvis type er simpel (REAL, INT, BOOL) → normal processing
   
4. **Struct Expansion** (NY FEATURE)
   ```
   Symbol: GVL.Temperature_Sensor_1
   Type: ST_AnalogInput
   Attributes: {HMI_STRUCT}
   
   ↓ Ekspander
   
   Members:
   - GVL.Temperature_Sensor_1.Value (REAL, HMI_PV, Unit='°C')
   - GVL.Temperature_Sensor_1.Scaled (REAL, HMI_PV, Unit='%')
   - GVL.Temperature_Sensor_1.Error (BOOL, HMI_ALARM)
   ```
   
5. **Member Analysis**
   - For hvert struct medlem:
     - Check for HMI attributer
     - Hvis HMI attribut findes → analyser og kategoriser
     - Hvis ingen HMI attribut → skip
   
6. **Config Generation**
   - Generer config entries for hvert HMI medlem
   - Gruppér efter parent struct for organisering
   - Gem i `config.json` under `manual_symbols`
   
7. **GUI Creation**
   - Opret widgets for hvert medlem
   - Gruppér medlemmer under struct navn
   - Tilføj visual hierarchy

## TMC XML Struktur for Structs

### Struct Definition i TMC
```xml
<DataType>
  <Name>ST_AnalogInput</Name>
  <BitSize>192</BitSize>
  <SubItem>
    <Name>Value</Name>
    <Type>REAL</Type>
    <BitSize>32</BitSize>
    <BitOffs>0</BitOffs>
    <Properties>
      <Property><Name>HMI_PV</Name></Property>
      <Property><Name>Unit</Name><Value>°C</Value></Property>
      <Property><Name>Decimals</Name><Value>2</Value></Property>
    </Properties>
  </SubItem>
  <SubItem>
    <Name>Scaled</Name>
    <Type>REAL</Type>
    <BitSize>32</BitSize>
    <BitOffs>32</BitOffs>
    <Properties>
      <Property><Name>HMI_PV</Name></Property>
      <Property><Name>Unit</Name><Value>%</Value></Property>
    </Properties>
  </SubItem>
  <SubItem>
    <Name>Error</Name>
    <Type>BOOL</Type>
    <BitSize>8</BitSize>
    <BitOffs>64</BitOffs>
    <Properties>
      <Property><Name>HMI_ALARM</Name></Property>
      <Property><Name>AlarmText</Name><Value>Sensor Fejl</Value></Property>
    </Properties>
  </SubItem>
  <SubItem>
    <Name>RawValue</Name>
    <Type>INT</Type>
    <BitSize>16</BitSize>
    <BitOffs>96</BitOffs>
    <!-- Ingen HMI Properties -->
  </SubItem>
</DataType>

<Symbol>
  <Name>GVL.Temperature_Sensor_1</Name>
  <BaseType>ST_AnalogInput</BaseType>
  <BitSize>192</BitSize>
  <Properties>
    <Property><Name>HMI_STRUCT</Name></Property>
  </Properties>
</Symbol>
```

## Kode Eksempler

### Eksempel 1: TMC Parser Enhancement
```python
# tmc_parser.py
def get_struct_members(self, struct_name: str) -> List[Dict[str, Any]]:
    """
    Get all members of a struct with their attributes
    
    Args:
        struct_name: Name of struct type (e.g., 'ST_AnalogInput')
        
    Returns:
        List of member dictionaries with attributes
    """
    # Find DataType element
    for datatype in self.root.findall(".//DataType"):
        name_elem = datatype.find("Name")
        if name_elem is not None and name_elem.text == struct_name:
            members = []
            
            # Parse all SubItems
            for subitem in datatype.findall(".//SubItem"):
                member = self._parse_subitem(subitem)
                if member:
                    members.append(member)
            
            return members
    
    return []

def find_struct_symbols(self) -> List[Dict[str, Any]]:
    """Find all symbols that are struct types with HMI attributes"""
    struct_symbols = []
    
    for symbol_elem in self.root.findall(".//Symbol"):
        symbol = self._parse_symbol(symbol_elem)
        if not symbol:
            continue
        
        # Check if symbol has HMI_STRUCT marker
        if 'HMI_STRUCT' in symbol.get('attributes', {}):
            struct_symbols.append(symbol)
    
    return struct_symbols
```

### Eksempel 2: Auto Config Enhancement
```python
# symbol_auto_config.py
def _analyze_symbol(self, symbol) -> Optional[Dict[str, Any]]:
    """Analyze a single symbol and determine its configuration"""
    try:
        symbol_name = symbol.name
        data_type = str(symbol.plc_type) if hasattr(symbol, 'plc_type') else ''
        comment = symbol.comment if hasattr(symbol, 'comment') and symbol.comment else ''
        
        # Check if this is a struct type
        if self._is_struct_type(data_type):
            logger.info(f"Found struct symbol: {symbol_name} (type: {data_type})")
            
            # Check if it has HMI_STRUCT marker
            if 'hmi_struct' in comment.lower() or 'hmi_dut' in comment.lower():
                # Expand struct members
                return self._expand_struct_members(symbol, data_type)
        
        # Normal symbol processing
        config = {}
        category = self._determine_category(symbol_name, comment, data_type)
        # ... rest of processing
        
    except Exception as e:
        logger.warning(f"Error analyzing symbol {symbol.name}: {e}")
        return None

def _expand_struct_members(self, symbol, data_type: str) -> List[Dict[str, Any]]:
    """
    Expand struct into individual members with HMI tags
    
    Args:
        symbol: pyads symbol object
        data_type: Struct type name
        
    Returns:
        List of member configurations
    """
    members = []
    
    # Get struct definition from TMC
    if hasattr(self, 'tmc_parser') and self.tmc_parser:
        struct_def = self.tmc_parser.get_struct_members(data_type)
        
        for member in struct_def:
            # Check if member has HMI attributes
            member_attrs = member.get('attributes', {})
            has_hmi = any(key.startswith('HMI_') for key in member_attrs.keys())
            
            if has_hmi:
                # Build full member path
                member_path = f"{symbol.name}.{member['name']}"
                
                # Create config for this member
                member_config = {
                    'name': member_path,
                    'parent_struct': symbol.name,
                    'struct_type': data_type,
                    'member_name': member['name'],
                    'data_type': member['type'],
                    'attributes': member_attrs
                }
                
                # Categorize member
                category = self._determine_category(
                    member['name'], 
                    member.get('comment', ''),
                    member['type']
                )
                
                if category:
                    member_config['category'] = category
                    members.append(member_config)
                    logger.info(f"  Added member: {member_path} ({category})")
    
    return members
```

### Eksempel 3: Config.json Output
```json
{
  "manual_symbols": {
    "enabled": true,
    "auto_discovered": true,
    "last_scan": "2025-10-29 08:30:00",
    "symbols": {
      "GVL.Temperature_Sensor_1.Value": {
        "category": "process_value",
        "parent_struct": "GVL.Temperature_Sensor_1",
        "struct_type": "ST_AnalogInput",
        "member_name": "Value",
        "unit": "°C",
        "decimals": 2,
        "alarm_limits": {
          "high_high": 100,
          "high": 90
        }
      },
      "GVL.Temperature_Sensor_1.Scaled": {
        "category": "process_value",
        "parent_struct": "GVL.Temperature_Sensor_1",
        "struct_type": "ST_AnalogInput",
        "member_name": "Scaled",
        "unit": "%",
        "decimals": 1
      },
      "GVL.Temperature_Sensor_1.Error": {
        "category": "alarm",
        "parent_struct": "GVL.Temperature_Sensor_1",
        "struct_type": "ST_AnalogInput",
        "member_name": "Error",
        "alarm_text": "Sensor Fejl",
        "alarm_priority": 2
      }
    }
  }
}
```

## Test Cases

### Test Case 1: Simple Struct
```iecst
TYPE ST_Motor :
STRUCT
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'RPM'}
    SpeedSetpoint : REAL;
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'RPM'}
    ActualSpeed : REAL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Motor Fejl'}
    Fault : BOOL;
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}
    Motor1 : ST_Motor;
END_VAR
```

**Forventet Resultat**:
- `Motor1.SpeedSetpoint` → Setpoint widget (RPM)
- `Motor1.ActualSpeed` → Process Value widget (RPM)
- `Motor1.Fault` → Alarm (Motor Fejl)

### Test Case 2: Nested Struct
```iecst
TYPE ST_PID :
STRUCT
    {attribute 'HMI_SP'}
    Kp : REAL;
    
    {attribute 'HMI_SP'}
    Ki : REAL;
    
    {attribute 'HMI_SP'}
    Kd : REAL;
END_STRUCT
END_TYPE

TYPE ST_Controller :
STRUCT
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '°C'}
    Setpoint : REAL;
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    ProcessValue : REAL;
    
    PID : ST_PID;  // Nested struct
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}
    TempController : ST_Controller;
END_VAR
```

**Forventet Resultat**:
- `TempController.Setpoint` → Setpoint (°C)
- `TempController.ProcessValue` → Process Value (°C)
- `TempController.PID.Kp` → Setpoint
- `TempController.PID.Ki` → Setpoint
- `TempController.PID.Kd` → Setpoint

### Test Case 3: Array af Structs
```iecst
TYPE ST_Tank :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    Level : REAL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Tank Overfyldt'}
    OverflowAlarm : BOOL;
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT_ARRAY'}
    Tanks : ARRAY[1..3] OF ST_Tank;
END_VAR
```

**Forventet Resultat**:
- `Tanks[1].Level` → Process Value (%)
- `Tanks[1].OverflowAlarm` → Alarm
- `Tanks[2].Level` → Process Value (%)
- `Tanks[2].OverflowAlarm` → Alarm
- `Tanks[3].Level` → Process Value (%)
- `Tanks[3].OverflowAlarm` → Alarm

## Fordele ved Struct Import

### 1. Genbrug af Datatyper
```iecst
// Definer én gang
TYPE ST_AnalogInput : STRUCT
    {attribute 'HMI_PV'} Value : REAL;
    {attribute 'HMI_ALARM'} Error : BOOL;
END_STRUCT

// Brug mange gange
VAR_GLOBAL
    {attribute 'HMI_STRUCT'} Temp1 : ST_AnalogInput;
    {attribute 'HMI_STRUCT'} Temp2 : ST_AnalogInput;
    {attribute 'HMI_STRUCT'} Pressure1 : ST_AnalogInput;
END_VAR
```

### 2. Organiseret Kode
- Grupperer relaterede data sammen
- Lettere at vedligeholde
- Bedre oversigt i GUI

### 3. Type Sikkerhed
- PLC compiler sikrer konsistens
- Ingen risiko for fejl i manuel config
- Automatisk opdatering ved type ændringer

### 4. Skalerbarhed
- Nemt at tilføje nye sensorer
- Ingen manuel config nødvendig
- Automatisk GUI opdatering

## Potentielle Udfordringer

### 1. Performance
**Problem**: Scanning af mange structs kan tage tid
**Løsning**: 
- Cache struct definitioner
- Parallel processing af symboler
- Progress bar under scan

### 2. Deep Nesting
**Problem**: Structs i structs i structs
**Løsning**:
- Konfigurebar max dybde (`max_depth: 3`)
- Flat path notation (`Sensor.PID.Kp`)
- Visual hierarki i GUI

### 3. Arrays
**Problem**: Array af structs (e.g., `Tanks[1..10]`)
**Løsning**:
- Iterér gennem array indices
- Generer unique paths (`Tanks[1].Level`, `Tanks[2].Level`)
- Gruppér i GUI under array navn

### 4. TMC vs Runtime
**Problem**: Struct info måske ikke komplet i ADS runtime
**Løsning**:
- Primært brug TMC fil (mest komplet)
- Fallback til ADS hvis TMC ikke tilgængelig
- Advarsler hvis info mangler

## Implementeringsrækkefølge

### Iteration 1: Basic Struct Support
1. ✅ TMC parser for struct definitions
2. ✅ Struct member expansion
3. ✅ Config generation for members
4. ✅ Basic GUI visning

### Iteration 2: Enhanced Features
1. ⬜ Nested struct support
2. ⬜ Array handling
3. ⬜ Grupperet GUI layout
4. ⬜ Collapse/expand widgets

### Iteration 3: Advanced Features
1. ⬜ Custom struct templates
2. ⬜ Conditional member import
3. ⬜ Dynamic struct discovery
4. ⬜ Struct change detection

## Konklusion

Dette dokument beskriver en komplet plan for at implementere automatisk import af PLC structs med HMI attributer. Implementeringen bygger videre på eksisterende funktionalitet og følger samme arkitektur mønstre.

**Nøgle takeaways**:
- Brug TMC fil som primær kilde til struct definitioner
- Ekspander structs rekursivt til individuelle medlemmer
- Filter medlemmer baseret på HMI attributer
- Gruppér relaterede medlemmer visuelt i GUI
- Vedligehold samme konfigurationsformat

**Næste skridt**:
1. Review denne plan med team
2. Prioriter features til første iteration
3. Implementer fase-for-fase
4. Test med reelle PLC projekter
5. Dokumentér best practices
