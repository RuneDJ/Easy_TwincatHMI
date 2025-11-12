# 📋 PROMPT: Auto-Scan af HMI STRUCTs via {attribute 'HMI'} Marker

## 🎯 FORMÅL
Implementer automatisk scanning af PLC'en for at finde alle symbols med `{attribute 'HMI'}` marker, og automatisk importere hele STRUCT hierarkiet (Setpoint, ProcessValue, Switch, Alarm osv.) uden manuel konfiguration i config.json.

---

## 📐 NUVÆRENDE SITUATION

**Eksisterende system:**
- ✅ STRUCT-baseret design i PLC: `ST_HMI_Setpoint`, `ST_HMI_ProcessValue`, osv.
- ✅ Manuel konfiguration i `config.json` med liste over symbol navne
- ✅ `struct_reader.py` kan læse STRUCT data via ADS
- ❌ Kræver manuel opdatering af config når nye HMI tags tilføjes i PLC

**Problem:**
Hver gang et nyt HMI tag tilføjes i PLC (f.eks. `Motor[2].HMI`), skal det manuelt tilføjes i `config.json`. Dette er fejlprone og tidskrævende.

---

## 🚀 ØNSKET FUNKTIONALITET

### Auto-Scan Proces:

**1. PLC Struktur:**
```iecst
// I TwinCAT PLC kode:
TYPE ST_Motor :
STRUCT
    Speed : REAL;
    Running : BOOL;
    
    {attribute 'HMI'}  // <-- Dette marker aktiverer auto-scan
    HMI : ST_HMI_Motor;  // Indeholder Setpoint, ProcessValue, Switch, Alarm
END_STRUCT
END_TYPE

VAR_GLOBAL
    Motor : ARRAY[1..10] OF ST_Motor;  // 10 motorer
END_VAR

TYPE ST_HMI_Motor :
STRUCT
    SpeedSetpoint : ST_HMI_Setpoint;     // Motor.HMI.SpeedSetpoint
    CurrentSpeed : ST_HMI_ProcessValue;  // Motor.HMI.CurrentSpeed
    Mode : ST_HMI_Switch;                // Motor.HMI.Mode
    Fault : ST_HMI_Alarm;                // Motor.HMI.Fault
END_STRUCT
END_TYPE
```

**2. Auto-Scan Skal:**
- 🔍 Scanne alle PLC symboler for `{attribute 'HMI'}` i comment/metadata
- 📦 Når fundet, læse hele STRUCT hierarkiet under `.HMI` delen
- 🔎 Automatisk detektere hvor mange sub-symbols der findes (SpeedSetpoint, CurrentSpeed, Mode, Fault osv.)
- 🏷️ Kategorisere hvert sub-symbol baseret på STRUCT type:
  - `ST_HMI_Setpoint` → category: "setpoint"
  - `ST_HMI_ProcessValue` → category: "process_value"
  - `ST_HMI_Switch` → category: "switch"
  - `ST_HMI_Alarm` → category: "alarm"
- 💾 Cache resultaterne i memory (IKKE i config.json)

**3. Eksempel på auto-opdaget struktur:**
```
Motor[1].HMI             <-- {attribute 'HMI'} fundet her
├── SpeedSetpoint        <-- ST_HMI_Setpoint (auto-kategoriseret)
│   ├── Value
│   ├── Config.Unit
│   ├── Config.nMin
│   ├── AlarmLimits.*
│   └── Display.*
├── CurrentSpeed         <-- ST_HMI_ProcessValue
├── Mode                 <-- ST_HMI_Switch
└── Fault                <-- ST_HMI_Alarm

Motor[2].HMI             <-- Samme struktur, auto-opdaget
├── SpeedSetpoint
├── CurrentSpeed
├── Mode
└── Fault
```

---

## 🛠️ TEKNISK IMPLEMENTERING

### Fase 1: Symbol Discovery med Attribute Scanning

**Ny fil: `hmi_attribute_scanner.py`**

```python
"""
HMI Attribute Scanner
Scans TwinCAT PLC for symbols with {attribute 'HMI'} and builds
automatic symbol catalog.
"""

import pyads
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SymbolInfo:
    """Information about a discovered HMI symbol"""
    full_path: str
    category: str  # 'setpoint', 'process_value', 'switch', 'alarm'
    struct_type: str
    display_name: str
    parent_path: str


class HMIAttributeScanner:
    """
    Scanner PLC for symbols med {attribute 'HMI'} og bygger
    automatisk symbol katalog
    """
    
    # Mapping fra STRUCT type til HMI category
    STRUCT_TYPE_MAP = {
        'ST_HMI_Setpoint': 'setpoint',
        'ST_HMI_ProcessValue': 'process_value',
        'ST_HMI_Switch': 'switch',
        'ST_HMI_Alarm': 'alarm',
    }
    
    def __init__(self, plc_connection: pyads.Connection):
        """
        Initialize scanner with PLC connection
        
        Args:
            plc_connection: Active pyads Connection object
        """
        self.plc = plc_connection
        self.discovered_symbols = {}
        
    def scan_for_hmi_attributes(self) -> List[str]:
        """
        Scan alle PLC symboler for {attribute 'HMI'}
        
        Returns:
            Liste af base paths, f.eks. ['Motor[1].HMI', 'Motor[2].HMI', 'Pump.HMI']
        """
        logger.info("Starting scan for {attribute 'HMI'} markers...")
        hmi_paths = []
        
        try:
            # Få alle symboler fra PLC
            symbols = self.plc.get_all_symbols()
            
            for symbol in symbols:
                # Tjek om symbol har 'HMI' attribute i comment
                if self._has_hmi_attribute(symbol):
                    hmi_paths.append(symbol.name)
                    logger.debug(f"Found HMI attribute on: {symbol.name}")
                    
                # Tjek også sub-members for nested HMI structs
                if hasattr(symbol, 'sub_items'):
                    for sub in symbol.sub_items:
                        if self._has_hmi_attribute(sub):
                            full_path = f"{symbol.name}.{sub.name}"
                            hmi_paths.append(full_path)
                            logger.debug(f"Found HMI attribute on: {full_path}")
            
            logger.info(f"Scan complete. Found {len(hmi_paths)} HMI structures")
            return hmi_paths
            
        except Exception as e:
            logger.error(f"Error during HMI attribute scan: {e}")
            raise
    
    def _has_hmi_attribute(self, symbol) -> bool:
        """
        Tjek om symbol har {attribute 'HMI'} marker
        
        Args:
            symbol: pyads symbol object
            
        Returns:
            True hvis {attribute 'HMI'} findes
        """
        # Tjek comment field for attribute marker
        if hasattr(symbol, 'comment'):
            comment = symbol.comment.lower()
            if '{attribute' in comment and "'hmi'" in comment:
                return True
                
        # Alternative: Tjek symbol attributes hvis tilgængelig
        if hasattr(symbol, 'attributes'):
            for attr in symbol.attributes:
                if 'HMI' in attr:
                    return True
                    
        return False
    
    def analyze_hmi_struct(self, base_path: str) -> Dict[str, SymbolInfo]:
        """
        Analyser STRUCT hierarkiet under en HMI base path
        
        Args:
            base_path: f.eks. "Motor[1].HMI"
            
        Returns:
            Dictionary med alle sub-symbols:
            {
                'Motor[1].HMI.SpeedSetpoint': SymbolInfo(...),
                'Motor[1].HMI.CurrentSpeed': SymbolInfo(...),
                ...
            }
        """
        logger.info(f"Analyzing HMI struct at: {base_path}")
        symbols = {}
        
        try:
            # Få symbol info fra PLC
            base_symbol = self.plc.get_symbol(base_path)
            
            # Læs alle sub-members af denne STRUCT
            members = self._introspect_struct_members(base_symbol)
            
            for member in members:
                # Bestem category baseret på STRUCT type
                category = self.determine_symbol_category(member['type'])
                
                if category:  # Kun hvis det er en kendt HMI type
                    symbol_info = SymbolInfo(
                        full_path=member['full_path'],
                        category=category,
                        struct_type=member['type'],
                        display_name=member['name'],
                        parent_path=base_path
                    )
                    
                    symbols[member['full_path']] = symbol_info
                    logger.debug(f"  Found {category}: {member['name']}")
            
            logger.info(f"  Analyzed {len(symbols)} HMI symbols under {base_path}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error analyzing HMI struct {base_path}: {e}")
            return {}
    
    def _introspect_struct_members(self, symbol) -> List[Dict]:
        """
        Brug pyads til at få alle members af en STRUCT
        
        Args:
            symbol: pyads symbol object for STRUCT
            
        Returns:
            List af member info dictionaries
        """
        members = []
        
        try:
            # pyads har forskellige måder at få sub-items
            if hasattr(symbol, 'sub_items'):
                for sub in symbol.sub_items:
                    members.append({
                        'name': sub.name,
                        'type': sub.plc_type if hasattr(sub, 'plc_type') else 'UNKNOWN',
                        'full_path': f"{symbol.name}.{sub.name}"
                    })
                    
            elif hasattr(symbol, 'subitems'):  # Alternative property navn
                for sub in symbol.subitems:
                    members.append({
                        'name': sub.name,
                        'type': sub.plc_type if hasattr(sub, 'plc_type') else 'UNKNOWN',
                        'full_path': f"{symbol.name}.{sub.name}"
                    })
        
        except Exception as e:
            logger.warning(f"Could not introspect members of {symbol.name}: {e}")
            
        return members
    
    def determine_symbol_category(self, struct_type: str) -> Optional[str]:
        """
        Map STRUCT type til HMI category
        
        Args:
            struct_type: f.eks. 'ST_HMI_Setpoint'
            
        Returns:
            Category string eller None hvis ikke en HMI type
            
        Examples:
            ST_HMI_Setpoint -> 'setpoint'
            ST_HMI_ProcessValue -> 'process_value'
            ST_HMI_Switch -> 'switch'
            ST_HMI_Alarm -> 'alarm'
        """
        # Direct mapping
        if struct_type in self.STRUCT_TYPE_MAP:
            return self.STRUCT_TYPE_MAP[struct_type]
        
        # Fuzzy matching for variations
        struct_lower = struct_type.lower()
        if 'setpoint' in struct_lower:
            return 'setpoint'
        elif 'processvalue' in struct_lower or 'process_value' in struct_lower:
            return 'process_value'
        elif 'switch' in struct_lower:
            return 'switch'
        elif 'alarm' in struct_lower:
            return 'alarm'
            
        return None
    
    def get_all_discovered_symbols(self) -> Dict[str, List[SymbolInfo]]:
        """
        Få alle opdagede symboler kategoriseret
        
        Returns:
            Dictionary med symboler grupperet efter category:
            {
                'setpoints': [SymbolInfo, ...],
                'process_values': [SymbolInfo, ...],
                'switches': [SymbolInfo, ...],
                'alarms': [SymbolInfo, ...]
            }
        """
        categorized = {
            'setpoints': [],
            'process_values': [],
            'switches': [],
            'alarms': []
        }
        
        for symbol_info in self.discovered_symbols.values():
            if symbol_info.category == 'setpoint':
                categorized['setpoints'].append(symbol_info)
            elif symbol_info.category == 'process_value':
                categorized['process_values'].append(symbol_info)
            elif symbol_info.category == 'switch':
                categorized['switches'].append(symbol_info)
            elif symbol_info.category == 'alarm':
                categorized['alarms'].append(symbol_info)
                
        return categorized
```

### Fase 2: Integration i Main Application

**Opdater `main.py`:**

```python
from hmi_attribute_scanner import HMIAttributeScanner, SymbolInfo

class TwinCATHMI(QMainWindow):
    def __init__(self):
        # ... existing code ...
        
        self.hmi_scanner = None
        self.auto_scan_enabled = self.config.get('auto_scan', {}).get('enabled', False)
        self.discovered_symbols_cache = {}
        
    def connect_to_plc(self):
        """Connect to PLC and auto-scan if enabled"""
        try:
            # ... existing connection code ...
            
            if self.auto_scan_enabled:
                logger.info("Auto-scan enabled, discovering HMI symbols...")
                self.discover_symbols_auto_scan()
            else:
                # Use manual config
                self.discover_symbols_from_structs()
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            
    def discover_symbols_auto_scan(self):
        """
        Automatisk scan mode - finder alle HMI tags via attributes
        """
        try:
            # 1. Opret scanner
            self.hmi_scanner = HMIAttributeScanner(self.ads_client)
            
            # 2. Scan for {attribute 'HMI'} markers
            hmi_base_paths = self.hmi_scanner.scan_for_hmi_attributes()
            logger.info(f"Found {len(hmi_base_paths)} HMI structures with {{attribute 'HMI'}}")
            
            # 3. For hver HMI base path, analyser STRUCT hierarkiet
            all_symbols = {}
            for base_path in hmi_base_paths:
                symbols = self.hmi_scanner.analyze_hmi_struct(base_path)
                all_symbols.update(symbols)
                
                # Gem i scanner's cache
                self.hmi_scanner.discovered_symbols.update(symbols)
            
            logger.info(f"Auto-discovered {len(all_symbols)} HMI symbols total")
            
            # 4. Konverter SymbolInfo til GUI format
            gui_symbols = self.convert_scanner_symbols_to_gui(all_symbols)
            
            # 5. Opret GUI widgets
            self.create_symbol_widgets(gui_symbols)
            
            # 6. Gem til runtime cache
            self.discovered_symbols_cache = all_symbols
            
            # 7. Start update timer
            self.start_update_timer()
            
        except Exception as e:
            logger.error(f"Auto-scan failed: {e}")
            QMessageBox.critical(self, "Auto-Scan Error", 
                               f"Failed to auto-scan PLC for HMI symbols:\n{e}")
    
    def convert_scanner_symbols_to_gui(self, scanner_symbols: Dict[str, SymbolInfo]) -> Dict:
        """
        Konverter SymbolInfo objekter til GUI-format
        
        Args:
            scanner_symbols: Dictionary af SymbolInfo fra scanner
            
        Returns:
            Dictionary i samme format som discover_symbols_from_structs()
        """
        gui_symbols = {
            'setpoints': {},
            'process_values': {},
            'switches': {},
            'alarms': {}
        }
        
        for path, symbol_info in scanner_symbols.items():
            # Læs faktisk data fra PLC via struct_reader
            try:
                if symbol_info.category == 'setpoint':
                    data = self.struct_reader.read_setpoint(path)
                    gui_symbols['setpoints'][path] = data
                    
                elif symbol_info.category == 'process_value':
                    data = self.struct_reader.read_process_value(path)
                    gui_symbols['process_values'][path] = data
                    
                elif symbol_info.category == 'switch':
                    data = self.struct_reader.read_switch(path)
                    gui_symbols['switches'][path] = data
                    
                elif symbol_info.category == 'alarm':
                    data = self.struct_reader.read_alarm(path)
                    gui_symbols['alarms'][path] = data
                    
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")
                continue
        
        return gui_symbols
    
    def refresh_symbols(self):
        """
        Refresh knap handler - re-scan PLC for nye/ændrede symboler
        """
        if self.auto_scan_enabled:
            logger.info("Refreshing auto-scanned symbols...")
            self.discover_symbols_auto_scan()
        else:
            logger.info("Refreshing manual symbols...")
            self.discover_symbols_from_structs()
```

### Fase 3: PyADS STRUCT Introspection

**Udfordring:** PyADS skal kunne:
1. Læse alle symboler og deres comments (for `{attribute 'HMI'}`)
2. Læse STRUCT definition fra PLC (sub-members)
3. Detektere STRUCT type navn (`ST_HMI_Setpoint` osv.)

**Løsning - Udvidet scanner metode:**

```python
def get_symbol_with_metadata(self, symbol_path: str) -> Dict:
    """
    Få symbol med fuld metadata (type, comment, attributes)
    
    Returns:
        {
            'name': 'Motor[1].HMI',
            'type': 'ST_HMI_Motor',
            'comment': '{attribute 'HMI'} Motor HMI interface',
            'size': 256,
            'sub_items': [...]
        }
    """
    try:
        symbol = self.plc.get_symbol(symbol_path)
        
        metadata = {
            'name': symbol.name,
            'type': symbol.plc_type if hasattr(symbol, 'plc_type') else 'UNKNOWN',
            'comment': symbol.comment if hasattr(symbol, 'comment') else '',
            'size': symbol.size if hasattr(symbol, 'size') else 0,
            'sub_items': []
        }
        
        # Få sub-items hvis det er en STRUCT
        if hasattr(symbol, 'sub_items') or hasattr(symbol, 'subitems'):
            items = symbol.sub_items if hasattr(symbol, 'sub_items') else symbol.subitems
            for sub in items:
                metadata['sub_items'].append({
                    'name': sub.name,
                    'type': sub.plc_type if hasattr(sub, 'plc_type') else 'UNKNOWN'
                })
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to get metadata for {symbol_path}: {e}")
        return None
```

### Fase 4: Config.json Simplificering

**Opdater `config.json`:**

```json
{
  "ads": {
    "ams_net_id": "5.112.50.143.1.1",
    "ams_port": 851,
    "update_interval": 1.0
  },
  
  "auto_scan": {
    "enabled": true,
    "scan_on_startup": true,
    "attribute_marker": "HMI",
    "cache_discovered_symbols": true,
    "rescan_interval_seconds": 0
  },
  
  "gui": {
    "window_title": "TwinCAT HMI - Auto Scan",
    "show_symbol_count": true,
    "group_by_parent": true
  },
  
  "_legacy": {
    "_comment": "Legacy manual config - ikke brugt når auto_scan.enabled = true",
    "use_structs": true,
    "hmi_struct_path": "MAIN.HMI",
    "struct_symbols": {}
  }
}
```

### Fase 5: GUI Updates

**Tilføj Refresh knap i connection panel:**

```python
def init_connection_panel(self):
    """Initialize connection control panel"""
    # ... existing code ...
    
    # Tilføj Refresh knap
    self.refresh_btn = QPushButton("Refresh Symbols")
    self.refresh_btn.setEnabled(False)
    self.refresh_btn.clicked.connect(self.refresh_symbols)
    
    # Status label for auto-scan
    self.scan_status_label = QLabel("Symboler: -")
    
    # Layout
    button_layout.addWidget(self.connect_btn)
    button_layout.addWidget(self.refresh_btn)
    button_layout.addWidget(self.scan_status_label)
    
def update_scan_status(self, symbol_count: int):
    """Opdater status label med antal opdagede symboler"""
    self.scan_status_label.setText(f"Symboler: {symbol_count}")
    
    if self.auto_scan_enabled:
        self.scan_status_label.setStyleSheet("color: green;")
```

---

## 📝 IMPLEMENTATION CHECKLIST

### ✅ Krav til Løsningen:

**1. Auto-Detection:**
- [ ] Scan alle PLC symboler for `{attribute 'HMI'}`
- [ ] Introspekt STRUCT hierarkiet under hver HMI base path
- [ ] Detekter STRUCT type (ST_HMI_Setpoint, ST_HMI_ProcessValue osv.)
- [ ] Håndter arrays: `Motor[1].HMI`, `Motor[2].HMI` osv.
- [ ] Håndter nested paths: `System.Subsystem.HMI`

**2. Symbol Kategorisering:**
- [ ] Map STRUCT type → HMI category
- [ ] Læs alle STRUCT fields (Value, Config, AlarmLimits, Display)
- [ ] Byg komplet symbol metadata runtime
- [ ] Konverter til GUI-kompatibelt format

**3. Performance:**
- [ ] Cache scannede symboler i memory
- [ ] Kun re-scan ved "Refresh" knap eller genstart
- [ ] Batch læsning af STRUCT data
- [ ] Scan skal tage <5 sekunder for 100 symboler

**4. Compatibility:**
- [ ] Virker med eksisterende `struct_reader.py`
- [ ] Fallback til manuel config hvis auto-scan fejler
- [ ] Håndter symboler der forsvinder fra PLC
- [ ] Bevar eksisterende GUI funktionalitet

**5. UI Features:**
- [ ] "Refresh Symbols" knap i forbindelsespanel
- [ ] Vis antal auto-opdagede symboler
- [ ] Indikator for auto-scan status (enabled/disabled)
- [ ] Fejlbesked hvis scan fejler

**6. Configuration:**
- [ ] `auto_scan.enabled` toggle i config
- [ ] `auto_scan.attribute_marker` for custom marker navn
- [ ] Backward compatibility med manuel config
- [ ] Dokumentation af nye config options

---

## 🧪 TEST CASES

### Test 1: Single HMI STRUCT
**PLC Kode:**
```iecst
VAR_GLOBAL
    {attribute 'HMI'}
    Pump : ST_HMI_Pump;
END_VAR

TYPE ST_HMI_Pump :
STRUCT
    FlowSetpoint : ST_HMI_Setpoint;
    CurrentFlow : ST_HMI_ProcessValue;
    Mode : ST_HMI_Switch;
    Fault : ST_HMI_Alarm;
END_STRUCT
END_TYPE
```

**Forventet Resultat:**
- Scanner finder `Pump` med {attribute 'HMI'}
- Analyzer finder 4 sub-symbols:
  - `Pump.FlowSetpoint` (category: setpoint)
  - `Pump.CurrentFlow` (category: process_value)
  - `Pump.Mode` (category: switch)
  - `Pump.Fault` (category: alarm)
- GUI viser alle 4 widgets korrekt

### Test 2: Array af HMI STRUCTs
**PLC Kode:**
```iecst
VAR_GLOBAL
    {attribute 'HMI'}
    Motor : ARRAY[1..5] OF ST_Motor;
END_VAR

TYPE ST_Motor :
STRUCT
    HMI : ST_HMI_Motor;
    // ... other fields
END_STRUCT

TYPE ST_HMI_Motor :
STRUCT
    SpeedSetpoint : ST_HMI_Setpoint;
    CurrentSpeed : ST_HMI_ProcessValue;
    Mode : ST_HMI_Switch;
    OverloadAlarm : ST_HMI_Alarm;
END_STRUCT
END_TYPE
```

**Forventet Resultat:**
- Scanner finder `Motor[1]` til `Motor[5]` med HMI sub-struct
- Analyzer finder 5 × 4 = 20 symbols total
- GUI grupperer per motor eller viser alle i kategorier

### Test 3: Nested STRUCTs
**PLC Kode:**
```iecst
VAR_GLOBAL
    {attribute 'HMI'}
    System : ST_System;
END_VAR

TYPE ST_System :
STRUCT
    Temperature : ST_SubSystem;
    Pressure : ST_SubSystem;
END_STRUCT

TYPE ST_SubSystem :
STRUCT
    HMI : ST_HMI_SubSystem;
END_STRUCT

TYPE ST_HMI_SubSystem :
STRUCT
    Setpoint : ST_HMI_Setpoint;
    Measurement : ST_HMI_ProcessValue;
END_STRUCT
END_TYPE
```

**Forventet Resultat:**
- Scanner finder `System` med {attribute 'HMI'}
- Analyzer traverser nested structure
- Finder:
  - `System.Temperature.HMI.Setpoint`
  - `System.Temperature.HMI.Measurement`
  - `System.Pressure.HMI.Setpoint`
  - `System.Pressure.HMI.Measurement`

### Test 4: No HMI Attributes
**PLC Kode:**
```iecst
VAR_GLOBAL
    Motor : ST_Motor;  // INGEN {attribute 'HMI'}
END_VAR
```

**Forventet Resultat:**
- Scanner finder INGEN HMI symbols
- GUI viser "No HMI symbols found" besked
- Ingen fejl eller crash

### Test 5: Mixed Manual + Auto
**Config:**
```json
{
  "auto_scan": {
    "enabled": true
  },
  "struct_symbols": {
    "setpoints": ["ManualSetpoint"]
  }
}
```

**Forventet Resultat:**
- Auto-scan finder HMI symbols fra PLC
- Manuel config tilføjer `ManualSetpoint`
- Begge vises i GUI uden konflikter

---

## 🚦 PRIORITET

**HØJI PRIORITET (Må implementeres):**
- ✅ `hmi_attribute_scanner.py` med scan og analyze metoder
- ✅ Integration i `main.py` med `discover_symbols_auto_scan()`
- ✅ Config.json opdatering med `auto_scan` sektion
- ✅ STRUCT type mapping (ST_HMI_Setpoint → 'setpoint')
- ✅ GUI widget generation fra scannede symboler

**MEDIUM PRIORITET (Bør implementeres):**
- ⚡ Cache mekanisme for hurtigere opstart
- ⚡ "Refresh Symbols" knap i GUI
- ⚡ Status indikator (antal symboler, scan tid)
- ⚡ Fejlhåndtering ved manglende/fjernede symboler
- ⚡ Logging af scan proces

**LAV PRIORITET (Nice to have):**
- 💡 Gem scan resultat til JSON fil
- 💡 Incremental scan (kun ændringer siden sidst)
- 💡 Filter/søgning i auto-opdagede symboler
- 💡 Gruppering efter parent path eller array index
- 💡 Export af opdagede symboler til dokumentation

---

## 📚 DEPENDENCIES

**Eksisterende Filer:**
- `pyads` - ADS kommunikation med TwinCAT
- `struct_reader.py` - Læsning af STRUCT data
- `main.py` - Hoved GUI og symbol management
- `gui_panels.py` - Widget panels for HMI controls
- `config.json` - Konfiguration

**Nye Filer:**
- `hmi_attribute_scanner.py` - **NY** - Auto-scan logik
- `config.json` - **OPDATER** - Tilføj auto_scan sektion
- `main.py` - **OPDATER** - Integration af scanner

**PyADS Funktioner Benyttet:**
```python
# Kritiske pyads metoder for scanning:
plc.get_all_symbols()          # Få alle PLC symboler
plc.get_symbol(path)           # Få specifik symbol
symbol.name                     # Symbol navn
symbol.plc_type                 # STRUCT type navn
symbol.comment                  # Comment med {attribute}
symbol.sub_items / subitems     # Sub-members af STRUCT
```

---

## ✅ SUCCESS CRITERIA

Implementeringen er succesfuld når:

### Funktionel Success:
1. ✅ PLC kode kan tilføjes/fjernes med `{attribute 'HMI'}` uden at røre Python kode
2. ✅ HMI opdager automatisk alle HMI STRUCTs ved opstart
3. ✅ Alle STRUCT fields læses korrekt (Value, Config, Alarms, Display)
4. ✅ GUI viser alle auto-opdagede symboler i korrekte kategorier
5. ✅ Symboler kan refreshes uden genstart af HMI
6. ✅ Både auto-scan og manuel config kan bruges samtidig

### Performance Success:
7. ✅ Initial scan tager <5 sekunder for 100+ symboler
8. ✅ Refresh scan tager <3 sekunder
9. ✅ Ingen lag i GUI under normal drift
10. ✅ Memory forbrug stiger ikke over tid

### Robusthed Success:
11. ✅ Håndterer PLC disconnect/reconnect med re-scan
12. ✅ Håndterer symboler der fjernes fra PLC
13. ✅ Fallback til manuel config hvis auto-scan fejler
14. ✅ Ingen crashes ved manglende/ugyldig STRUCT data

### Usability Success:
15. ✅ "Refresh Symbols" knap virker intuitiv
16. ✅ Status viser antal opdagede symboler
17. ✅ Fejlbeskeder er klare og hjælpsomme
18. ✅ Dokumentation forklarer hvordan man tilføjer {attribute 'HMI'}

---

## 🎯 SLUTRESULTAT

### Før (Manuel Config):
```
1. Udvikler tilføjer ST_Motor.HMI i PLC
2. Compile PLC
3. Åbn config.json
4. Tilføj "Motor[1].HMI.SpeedSetpoint" til struct_symbols
5. Tilføj "Motor[1].HMI.CurrentSpeed" til struct_symbols
6. ... (gentag for alle felter)
7. Gem config.json
8. Genstart HMI applikation
```

### Efter (Auto Scan):
```
1. Udvikler tilføjer ST_Motor.HMI med {attribute 'HMI'} i PLC
2. Compile PLC
3. HMI opdager automatisk alle Motor[X].HMI.* symboler
4. GUI opdateres automatisk
```

**Tidbesparelse: Fra 8 trin til 2 trin! 🚀**

---

## 🔧 TROUBLESHOOTING GUIDE

### Problem: Ingen symboler findes
**Symptom:** Auto-scan finder 0 symboler
**Løsninger:**
1. Tjek at {attribute 'HMI'} er skrevet korrekt i PLC
2. Tjek at PLC er compiled og online
3. Verificer ADS connection er aktiv
4. Check logs for scanning errors

### Problem: Nogle symboler mangler
**Symptom:** Kun nogle HMI symboler vises
**Løsninger:**
1. Tjek at alle HMI STRUCTs har {attribute 'HMI'}
2. Verificer STRUCT type navne matcher ST_HMI_Setpoint osv.
3. Tjek nested STRUCT levels (max depth?)
4. Prøv "Refresh Symbols" knap

### Problem: Scan tager lang tid
**Symptom:** Opstart >10 sekunder
**Løsninger:**
1. Reducer antal symboler i PLC
2. Implementer caching til disk
3. Scan kun ændrede symboler (incremental)
4. Overvej parallel scanning

### Problem: Forkerte kategorier
**Symptom:** Setpoint vises som ProcessValue
**Løsninger:**
1. Verificer STRUCT type navne i PLC
2. Tjek STRUCT_TYPE_MAP i scanner
3. Tilføj custom type mappings i config
4. Check logs for type detection

---

## 📖 DOKUMENTATION FOR BRUGERE

### Sådan Tilføjer Du Auto-Scannede HMI Tags:

**Trin 1: Opret HMI STRUCT i TwinCAT**
```iecst
TYPE ST_MyDevice :
STRUCT
    {attribute 'HMI'}  // <-- VIGTIGT: Dette aktiverer auto-scan
    HMI : ST_HMI_MyDevice;
END_STRUCT
END_TYPE

TYPE ST_HMI_MyDevice :
STRUCT
    Temperature : ST_HMI_Setpoint;
    Pressure : ST_HMI_ProcessValue;
    Mode : ST_HMI_Switch;
    Alarm : ST_HMI_Alarm;
END_STRUCT
END_TYPE
```

**Trin 2: Compile og Download PLC**
- Build → Compile
- Download til PLC
- Aktiver

**Trin 3: Refresh HMI**
- Klik "Refresh Symbols" i HMI
- ELLER genstart HMI applikation
- Nye symboler vises automatisk!

**Trin 4: Fjernelse af HMI Tags**
- Fjern {attribute 'HMI'} fra PLC
- Compile og download
- Refresh HMI
- Symboler forsvinder automatisk

---

**🎉 KOMPLET AUTO-SCAN LØSNING KLAR TIL IMPLEMENTERING! 🎉**
