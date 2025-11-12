# Migration: Fra Attributes til Runtime STRUCTs

## Problem med Nuværende Løsning

**Attributes kan IKKE:**
- ❌ Læses runtime via ADS
- ❌ Skrives til online (kræver recompile)
- ❌ Ændres dynamisk under drift
- ❌ Opdateres fra HMI

**Hvorfor?**
Attributes er compile-time metadata som kun findes i TMC XML filen, ikke i PLC runtime memory.

## Løsning: Runtime STRUCTs

Erstat attributes med STRUCT datatyper hvor alle metadata felter er runtime-tilgængelige via ADS.

---

# KOMPLET IMPLEMENTATION PROMPT

## Del 1: PLC Side - TwinCAT Structured Text Kode

### 1.1 Base Configuration STRUCTs

```iecst
// ============================================================================
// BASE CONFIGURATION TYPES
// Disse STRUCTs indeholder alle metadata som tidligere var attributes
// ============================================================================

TYPE ST_NumericConfig :
STRUCT
    Unit        : STRING(20) := '';      // '°C', 'bar', 'L/min', '%'
    Min         : REAL := 0.0;           // Minimum værdi
    Max         : REAL := 100.0;         // Maximum værdi
    Decimals    : USINT := 2;            // Antal decimaler til visning
    Step        : REAL := 1.0;           // Step størrelse for justering
END_STRUCT
END_TYPE

TYPE ST_AlarmLimits :
STRUCT
    AlarmHighHigh   : REAL := 0.0;       // Kritisk høj alarm
    AlarmHigh       : REAL := 0.0;       // Høj alarm
    AlarmLow        : REAL := 0.0;       // Lav alarm
    AlarmLowLow     : REAL := 0.0;       // Kritisk lav alarm
    AlarmPriority   : USINT := 3;        // 1=Critical, 2=High, 3=Medium, 4=Low
    AlarmActive     : BOOL := FALSE;     // TRUE hvis nogen alarm aktiv
    WarningActive   : BOOL := FALSE;     // TRUE hvis warning (medium/low)
    AlarmText       : STRING(80) := '';  // Alarm besked tekst
    Hysteresis      : REAL := 0.5;       // Hysterese for alarm reset
END_STRUCT
END_TYPE

TYPE ST_SwitchConfig :
STRUCT
    NumPositions    : USINT := 2;        // Antal positioner (2-8)
    Pos0_Label      : STRING(40) := '';  // Label for position 0
    Pos1_Label      : STRING(40) := '';  // Label for position 1
    Pos2_Label      : STRING(40) := '';  // Label for position 2
    Pos3_Label      : STRING(40) := '';  // Label for position 3
    Pos4_Label      : STRING(40) := '';  // Label for position 4
    Pos5_Label      : STRING(40) := '';  // Label for position 5
    Pos6_Label      : STRING(40) := '';  // Label for position 6
    Pos7_Label      : STRING(40) := '';  // Label for position 7
END_STRUCT
END_TYPE

TYPE ST_DisplayConfig :
STRUCT
    DisplayName     : STRING(60) := '';  // Vises i HMI
    Description     : STRING(120) := ''; // Detaljeret beskrivelse
    Visible         : BOOL := TRUE;      // Skjul/vis i HMI
    ReadOnly        : BOOL := FALSE;     // Disable write fra HMI
END_STRUCT
END_TYPE
```

### 1.2 HMI Data Types

```iecst
// ============================================================================
// HMI SETPOINT - Justerbar værdi med alarm grænser
// ============================================================================
TYPE ST_HMI_Setpoint :
STRUCT
    // Runtime værdi
    Value           : REAL := 0.0;       // Aktuel setpoint værdi
    
    // Configuration
    Config          : ST_NumericConfig;   // Unit, Min, Max, Decimals, Step
    AlarmLimits     : ST_AlarmLimits;     // Alarm grænser og tekster
    Display         : ST_DisplayConfig;   // Display navn og beskrivelse
    
    // Runtime status
    ValueChanged    : BOOL := FALSE;     // TRUE når værdi ændret
    LastUpdateTime  : DT;                // Timestamp for sidste ændring
END_STRUCT
END_TYPE

// ============================================================================
// HMI PROCESS VALUE - Readonly måling med alarm overvågning
// ============================================================================
TYPE ST_HMI_ProcessValue :
STRUCT
    // Runtime værdi
    Value           : REAL := 0.0;       // Aktuel process værdi
    
    // Configuration
    Config          : ST_NumericConfig;   // Unit, Decimals (ikke Min/Max)
    AlarmLimits     : ST_AlarmLimits;     // Alarm grænser
    Display         : ST_DisplayConfig;   // Display info
    
    // Runtime status
    Quality         : USINT := 0;        // 0=Good, 1=Uncertain, 2=Bad
    SensorFault     : BOOL := FALSE;     // Sensor fejl detection
    LastUpdateTime  : DT;                // Timestamp
END_STRUCT
END_TYPE

// ============================================================================
// HMI SWITCH - Multi-position selector
// ============================================================================
TYPE ST_HMI_Switch :
STRUCT
    // Runtime værdi
    Position        : INT := 0;          // Aktuel position (0-7)
    
    // Configuration
    Config          : ST_SwitchConfig;   // Position labels
    Display         : ST_DisplayConfig;  // Display info
    
    // Runtime status
    PositionChanged : BOOL := FALSE;     // TRUE når position ændret
    LastUpdateTime  : DT;                // Timestamp
END_STRUCT
END_TYPE

// ============================================================================
// HMI DIGITAL ALARM - Boolean alarm input
// ============================================================================
TYPE ST_HMI_Alarm :
STRUCT
    // Runtime værdi
    Active          : BOOL := FALSE;     // TRUE = Alarm aktiv
    
    // Configuration
    AlarmText       : STRING(80) := '';  // Alarm besked
    AlarmPriority   : USINT := 3;        // 1=Critical, 2=High, 3=Medium, 4=Low
    Display         : ST_DisplayConfig;  // Display info
    
    // Runtime status
    Acknowledged    : BOOL := FALSE;     // HMI acknowledged
    TriggerTime     : DT;                // Timestamp alarm aktiveret
    AckTime         : DT;                // Timestamp acknowledged
    TriggerCount    : UDINT := 0;        // Antal gange aktiveret
END_STRUCT
END_TYPE
```

### 1.3 Container STRUCT for alle HMI Data

```iecst
// ============================================================================
// HMI SYMBOLS CONTAINER
// Alle HMI data samlet i én STRUCT for nem adgang
// ============================================================================
TYPE ST_HMI_Symbols :
STRUCT
    // ========================================
    // SETPOINTS
    // ========================================
    TemperaturSetpunkt  : ST_HMI_Setpoint;
    TrykSetpunkt        : ST_HMI_Setpoint;
    FlowSetpunkt        : ST_HMI_Setpoint;
    
    // ========================================
    // PROCESS VALUES
    // ========================================
    Temperatur_1        : ST_HMI_ProcessValue;
    Temperatur_2        : ST_HMI_ProcessValue;
    Tryk_1              : ST_HMI_ProcessValue;
    Flow_1              : ST_HMI_ProcessValue;
    Niveau_1            : ST_HMI_ProcessValue;
    
    // ========================================
    // SWITCHES
    // ========================================
    DriftMode           : ST_HMI_Switch;
    PumpeValg           : ST_HMI_Switch;
    Prioritet           : ST_HMI_Switch;
    
    // ========================================
    // DIGITAL ALARMS
    // ========================================
    Motor1Fejl          : ST_HMI_Alarm;
    NodStop             : ST_HMI_Alarm;
    LavtOlieTryk        : ST_HMI_Alarm;
    FilterAdvarsel      : ST_HMI_Alarm;
    VedligeholdPaamindelse : ST_HMI_Alarm;
END_STRUCT
END_TYPE
```

### 1.4 Initialisering i MAIN Program

```iecst
PROGRAM MAIN
VAR
    // Global HMI data instance
    HMI : ST_HMI_Symbols;
    
    // Initialization flag
    bInitialized : BOOL := FALSE;
END_VAR

// ============================================================================
// INITIALIZATION - Kaldes én gang ved opstart
// ============================================================================
IF NOT bInitialized THEN
    bInitialized := TRUE;
    
    // ========================================
    // TEMPERATUR SETPUNKT
    // ========================================
    HMI.TemperaturSetpunkt.Value := 25.0;
    HMI.TemperaturSetpunkt.Config.Unit := '°C';
    HMI.TemperaturSetpunkt.Config.Min := 0.0;
    HMI.TemperaturSetpunkt.Config.Max := 100.0;
    HMI.TemperaturSetpunkt.Config.Decimals := 1;
    HMI.TemperaturSetpunkt.Config.Step := 0.5;
    HMI.TemperaturSetpunkt.Display.DisplayName := 'Temperatur Setpunkt';
    HMI.TemperaturSetpunkt.Display.Description := 'Ønsket temperatur for processen';
    
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmHighHigh := 95.0;
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmHigh := 85.0;
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmLow := 10.0;
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmLowLow := 5.0;
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmPriority := 1;
    HMI.TemperaturSetpunkt.AlarmLimits.Hysteresis := 1.0;
    HMI.TemperaturSetpunkt.AlarmLimits.AlarmText := 'Temperatur setpunkt uden for grænser';
    
    // ========================================
    // TRYK SETPUNKT
    // ========================================
    HMI.TrykSetpunkt.Value := 5.0;
    HMI.TrykSetpunkt.Config.Unit := 'bar';
    HMI.TrykSetpunkt.Config.Min := 0.0;
    HMI.TrykSetpunkt.Config.Max := 10.0;
    HMI.TrykSetpunkt.Config.Decimals := 2;
    HMI.TrykSetpunkt.Config.Step := 0.1;
    HMI.TrykSetpunkt.Display.DisplayName := 'Tryk Setpunkt';
    
    HMI.TrykSetpunkt.AlarmLimits.AlarmHigh := 9.5;
    HMI.TrykSetpunkt.AlarmLimits.AlarmPriority := 3;
    HMI.TrykSetpunkt.AlarmLimits.AlarmText := 'Tryk setpunkt for højt';
    
    // ========================================
    // FLOW SETPUNKT
    // ========================================
    HMI.FlowSetpunkt.Value := 100.0;
    HMI.FlowSetpunkt.Config.Unit := 'L/min';
    HMI.FlowSetpunkt.Config.Min := 0.0;
    HMI.FlowSetpunkt.Config.Max := 200.0;
    HMI.FlowSetpunkt.Config.Decimals := 1;
    HMI.FlowSetpunkt.Config.Step := 5.0;
    HMI.FlowSetpunkt.Display.DisplayName := 'Flow Setpunkt';
    
    // ========================================
    // TEMPERATUR MÅLING 1
    // ========================================
    HMI.Temperatur_1.Value := 23.5;
    HMI.Temperatur_1.Config.Unit := '°C';
    HMI.Temperatur_1.Config.Decimals := 2;
    HMI.Temperatur_1.Display.DisplayName := 'Temperatur 1';
    HMI.Temperatur_1.Display.Description := 'Indløbs temperatur måling';
    
    HMI.Temperatur_1.AlarmLimits.AlarmHighHigh := 98.0;
    HMI.Temperatur_1.AlarmLimits.AlarmHigh := 90.0;
    HMI.Temperatur_1.AlarmLimits.AlarmLow := 5.0;
    HMI.Temperatur_1.AlarmLimits.AlarmLowLow := 2.0;
    HMI.Temperatur_1.AlarmLimits.AlarmPriority := 1;
    HMI.Temperatur_1.AlarmLimits.Hysteresis := 2.0;
    HMI.Temperatur_1.AlarmLimits.AlarmText := 'Temperatur 1 alarm';
    
    // ========================================
    // TEMPERATUR MÅLING 2
    // ========================================
    HMI.Temperatur_2.Value := 24.0;
    HMI.Temperatur_2.Config.Unit := '°C';
    HMI.Temperatur_2.Config.Decimals := 2;
    HMI.Temperatur_2.Display.DisplayName := 'Temperatur 2';
    
    HMI.Temperatur_2.AlarmLimits.AlarmHighHigh := 95.0;
    HMI.Temperatur_2.AlarmLimits.AlarmHigh := 85.0;
    HMI.Temperatur_2.AlarmLimits.AlarmPriority := 3;
    
    // ========================================
    // TRYK MÅLING
    // ========================================
    HMI.Tryk_1.Value := 5.0;
    HMI.Tryk_1.Config.Unit := 'bar';
    HMI.Tryk_1.Config.Decimals := 2;
    HMI.Tryk_1.Display.DisplayName := 'Tryk 1';
    
    HMI.Tryk_1.AlarmLimits.AlarmHigh := 9.5;
    HMI.Tryk_1.AlarmLimits.AlarmPriority := 2;
    
    // ========================================
    // FLOW MÅLING
    // ========================================
    HMI.Flow_1.Value := 100.0;
    HMI.Flow_1.Config.Unit := 'L/min';
    HMI.Flow_1.Config.Decimals := 1;
    HMI.Flow_1.Display.DisplayName := 'Flow 1';
    
    HMI.Flow_1.AlarmLimits.AlarmHigh := 180.0;
    HMI.Flow_1.AlarmLimits.AlarmLow := 20.0;
    HMI.Flow_1.AlarmLimits.AlarmPriority := 3;
    
    // ========================================
    // NIVEAU MÅLING
    // ========================================
    HMI.Niveau_1.Value := 50.0;
    HMI.Niveau_1.Config.Unit := '%';
    HMI.Niveau_1.Config.Decimals := 1;
    HMI.Niveau_1.Display.DisplayName := 'Niveau 1';
    
    // ========================================
    // DRIFT MODE SWITCH
    // ========================================
    HMI.DriftMode.Position := 1;
    HMI.DriftMode.Config.NumPositions := 3;
    HMI.DriftMode.Config.Pos0_Label := 'Stop';
    HMI.DriftMode.Config.Pos1_Label := 'Auto';
    HMI.DriftMode.Config.Pos2_Label := 'Manuel';
    HMI.DriftMode.Display.DisplayName := 'Drift Mode';
    HMI.DriftMode.Display.Description := 'Vælg drifts tilstand';
    
    // ========================================
    // PUMPE VALG SWITCH
    // ========================================
    HMI.PumpeValg.Position := 0;
    HMI.PumpeValg.Config.NumPositions := 4;
    HMI.PumpeValg.Config.Pos0_Label := 'Fra';
    HMI.PumpeValg.Config.Pos1_Label := 'Pumpe 1';
    HMI.PumpeValg.Config.Pos2_Label := 'Pumpe 2';
    HMI.PumpeValg.Config.Pos3_Label := 'Begge';
    HMI.PumpeValg.Display.DisplayName := 'Pumpe Valg';
    
    // ========================================
    // PRIORITET SWITCH
    // ========================================
    HMI.Prioritet.Position := 0;
    HMI.Prioritet.Config.NumPositions := 3;
    HMI.Prioritet.Config.Pos0_Label := 'Normal';
    HMI.Prioritet.Config.Pos1_Label := 'Høj';
    HMI.Prioritet.Config.Pos2_Label := 'Kritisk';
    HMI.Prioritet.Display.DisplayName := 'Prioritet';
    
    // ========================================
    // MOTOR 1 FEJL ALARM
    // ========================================
    HMI.Motor1Fejl.Active := FALSE;
    HMI.Motor1Fejl.AlarmText := 'Motor 1 Fejl';
    HMI.Motor1Fejl.AlarmPriority := 1;
    HMI.Motor1Fejl.Display.DisplayName := 'Motor 1 Fejl';
    
    // ========================================
    // NØDSTOP ALARM
    // ========================================
    HMI.NodStop.Active := FALSE;
    HMI.NodStop.AlarmText := 'Nødstop Aktiveret';
    HMI.NodStop.AlarmPriority := 1;
    HMI.NodStop.Display.DisplayName := 'Nødstop';
    
    // ========================================
    // LAVT OLIETRYK ALARM
    // ========================================
    HMI.LavtOlieTryk.Active := FALSE;
    HMI.LavtOlieTryk.AlarmText := 'Lavt Olietryk';
    HMI.LavtOlieTryk.AlarmPriority := 2;
    HMI.LavtOlieTryk.Display.DisplayName := 'Olie Tryk';
    
    // ========================================
    // FILTER ADVARSEL
    // ========================================
    HMI.FilterAdvarsel.Active := FALSE;
    HMI.FilterAdvarsel.AlarmText := 'Filter Skal Skiftes';
    HMI.FilterAdvarsel.AlarmPriority := 3;
    HMI.FilterAdvarsel.Display.DisplayName := 'Filter Status';
    
    // ========================================
    // VEDLIGEHOLD PÅMINDELSE
    // ========================================
    HMI.VedligeholdPaamindelse.Active := FALSE;
    HMI.VedligeholdPaamindelse.AlarmText := 'Vedligehold Nødvendigt';
    HMI.VedligeholdPaamindelse.AlarmPriority := 4;
    HMI.VedligeholdPaamindelse.Display.DisplayName := 'Vedligehold';
END_IF

// ============================================================================
// RUNTIME LOGIC
// Her kan du tilføje din process logic
// ============================================================================

// Simuler sensor værdier (erstat med rigtige inputs)
HMI.Temperatur_1.Value := HMI.Temperatur_1.Value + 0.1;
IF HMI.Temperatur_1.Value > 30.0 THEN
    HMI.Temperatur_1.Value := 20.0;
END_IF

// Opdater timestamps
HMI.Temperatur_1.LastUpdateTime := DT#2025-01-01-12:00:00;  // Brug rigtig systemtid

// Simuler alarm condition
IF HMI.Temperatur_1.Value > HMI.Temperatur_1.AlarmLimits.AlarmHigh THEN
    HMI.Temperatur_1.AlarmLimits.AlarmActive := TRUE;
ELSE
    HMI.Temperatur_1.AlarmLimits.AlarmActive := FALSE;
END_IF
```

---

## Del 2: Python HMI Side

### 2.1 STRUCT Parser for pyads

```python
"""
struct_reader.py - Læser TwinCAT STRUCTs via ADS
"""
import pyads
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class StructReader:
    """Read TwinCAT STRUCT data via ADS"""
    
    def __init__(self, plc):
        """
        Initialize STRUCT reader
        
        Args:
            plc: pyads.Connection object
        """
        self.plc = plc
    
    def read_setpoint(self, symbol_path: str) -> Dict[str, Any]:
        """
        Read ST_HMI_Setpoint STRUCT
        
        Args:
            symbol_path: Full symbol path (e.g., "HMI.TemperaturSetpunkt")
            
        Returns:
            Dict with value and all config fields
        """
        try:
            # Læs hele STRUCT som bytes og parse
            # Alternative: Læs individuelle felter
            
            result = {
                'value': self.plc.read_by_name(f"{symbol_path}.Value", pyads.PLCTYPE_REAL),
                'config': {
                    'unit': self.plc.read_by_name(f"{symbol_path}.Config.Unit", pyads.PLCTYPE_STRING),
                    'min': self.plc.read_by_name(f"{symbol_path}.Config.Min", pyads.PLCTYPE_REAL),
                    'max': self.plc.read_by_name(f"{symbol_path}.Config.Max", pyads.PLCTYPE_REAL),
                    'decimals': self.plc.read_by_name(f"{symbol_path}.Config.Decimals", pyads.PLCTYPE_USINT),
                    'step': self.plc.read_by_name(f"{symbol_path}.Config.Step", pyads.PLCTYPE_REAL),
                },
                'alarm_limits': {
                    'high_high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL),
                    'high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL),
                    'low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL),
                    'low_low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL),
                    'priority': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmPriority", pyads.PLCTYPE_USINT),
                    'active': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmActive", pyads.PLCTYPE_BOOL),
                    'warning': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.WarningActive", pyads.PLCTYPE_BOOL),
                    'text': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmText", pyads.PLCTYPE_STRING),
                },
                'display': {
                    'name': self.plc.read_by_name(f"{symbol_path}.Display.DisplayName", pyads.PLCTYPE_STRING),
                    'description': self.plc.read_by_name(f"{symbol_path}.Display.Description", pyads.PLCTYPE_STRING),
                    'visible': self.plc.read_by_name(f"{symbol_path}.Display.Visible", pyads.PLCTYPE_BOOL),
                    'readonly': self.plc.read_by_name(f"{symbol_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL),
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading setpoint {symbol_path}: {e}")
            return None
    
    def read_process_value(self, symbol_path: str) -> Dict[str, Any]:
        """Read ST_HMI_ProcessValue STRUCT"""
        try:
            result = {
                'value': self.plc.read_by_name(f"{symbol_path}.Value", pyads.PLCTYPE_REAL),
                'config': {
                    'unit': self.plc.read_by_name(f"{symbol_path}.Config.Unit", pyads.PLCTYPE_STRING),
                    'decimals': self.plc.read_by_name(f"{symbol_path}.Config.Decimals", pyads.PLCTYPE_USINT),
                },
                'alarm_limits': {
                    'high_high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL),
                    'high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL),
                    'low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL),
                    'low_low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL),
                    'priority': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmPriority", pyads.PLCTYPE_USINT),
                    'active': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmActive", pyads.PLCTYPE_BOOL),
                },
                'display': {
                    'name': self.plc.read_by_name(f"{symbol_path}.Display.DisplayName", pyads.PLCTYPE_STRING),
                },
                'quality': self.plc.read_by_name(f"{symbol_path}.Quality", pyads.PLCTYPE_USINT),
                'sensor_fault': self.plc.read_by_name(f"{symbol_path}.SensorFault", pyads.PLCTYPE_BOOL),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading process value {symbol_path}: {e}")
            return None
    
    def read_switch(self, symbol_path: str) -> Dict[str, Any]:
        """Read ST_HMI_Switch STRUCT"""
        try:
            num_pos = self.plc.read_by_name(f"{symbol_path}.Config.NumPositions", pyads.PLCTYPE_USINT)
            
            # Læs labels for alle positioner
            labels = []
            for i in range(num_pos):
                label = self.plc.read_by_name(f"{symbol_path}.Config.Pos{i}_Label", pyads.PLCTYPE_STRING)
                labels.append(label)
            
            result = {
                'position': self.plc.read_by_name(f"{symbol_path}.Position", pyads.PLCTYPE_INT),
                'config': {
                    'num_positions': num_pos,
                    'labels': labels,
                },
                'display': {
                    'name': self.plc.read_by_name(f"{symbol_path}.Display.DisplayName", pyads.PLCTYPE_STRING),
                },
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading switch {symbol_path}: {e}")
            return None
    
    def read_alarm(self, symbol_path: str) -> Dict[str, Any]:
        """Read ST_HMI_Alarm STRUCT"""
        try:
            result = {
                'active': self.plc.read_by_name(f"{symbol_path}.Active", pyads.PLCTYPE_BOOL),
                'text': self.plc.read_by_name(f"{symbol_path}.AlarmText", pyads.PLCTYPE_STRING),
                'priority': self.plc.read_by_name(f"{symbol_path}.AlarmPriority", pyads.PLCTYPE_USINT),
                'acknowledged': self.plc.read_by_name(f"{symbol_path}.Acknowledged", pyads.PLCTYPE_BOOL),
                'trigger_count': self.plc.read_by_name(f"{symbol_path}.TriggerCount", pyads.PLCTYPE_UDINT),
                'display': {
                    'name': self.plc.read_by_name(f"{symbol_path}.Display.DisplayName", pyads.PLCTYPE_STRING),
                },
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading alarm {symbol_path}: {e}")
            return None
    
    def write_setpoint_value(self, symbol_path: str, value: float) -> bool:
        """Write setpoint value"""
        try:
            self.plc.write_by_name(f"{symbol_path}.Value", value, pyads.PLCTYPE_REAL)
            return True
        except Exception as e:
            logger.error(f"Error writing setpoint {symbol_path}: {e}")
            return False
    
    def write_switch_position(self, symbol_path: str, position: int) -> bool:
        """Write switch position"""
        try:
            self.plc.write_by_name(f"{symbol_path}.Position", position, pyads.PLCTYPE_INT)
            return True
        except Exception as e:
            logger.error(f"Error writing switch {symbol_path}: {e}")
            return False
    
    def acknowledge_alarm(self, symbol_path: str) -> bool:
        """Acknowledge alarm"""
        try:
            self.plc.write_by_name(f"{symbol_path}.Acknowledged", True, pyads.PLCTYPE_BOOL)
            return True
        except Exception as e:
            logger.error(f"Error acknowledging alarm {symbol_path}: {e}")
            return False
```

### 2.2 Config Format (config.json)

```json
{
  "plc": {
    "ams_net_id": "5.112.50.143.1.1",
    "port": 851
  },
  "ads": {
    "ams_net_id": "5.112.50.143.1.1",
    "ams_port": 851,
    "update_interval": 1.0
  },
  "hmi_struct_path": "HMI",
  "symbols": {
    "setpoints": [
      "TemperaturSetpunkt",
      "TrykSetpunkt",
      "FlowSetpunkt"
    ],
    "process_values": [
      "Temperatur_1",
      "Temperatur_2",
      "Tryk_1",
      "Flow_1",
      "Niveau_1"
    ],
    "switches": [
      "DriftMode",
      "PumpeValg",
      "Prioritet"
    ],
    "alarms": [
      "Motor1Fejl",
      "NodStop",
      "LavtOlieTryk",
      "FilterAdvarsel",
      "VedligeholdPaamindelse"
    ]
  }
}
```

### 2.3 Main Application Update

```python
"""
main.py - Opdateret til at bruge STRUCT baseret data
"""

def discover_symbols(self):
    """Discover symbols from config and read STRUCT metadata"""
    try:
        struct_path = self.config.get('hmi_struct_path', 'HMI')
        symbols_config = self.config.get('symbols', {})
        
        # Initialize STRUCT reader
        struct_reader = StructReader(self.ads_client.plc)
        
        # Build symbol dictionary
        symbols = {}
        
        # Read setpoints
        for sp_name in symbols_config.get('setpoints', []):
            full_path = f"{struct_path}.{sp_name}"
            sp_data = struct_reader.read_setpoint(full_path)
            if sp_data:
                symbols[full_path] = {
                    'name': full_path,
                    'type': 'setpoint',
                    'data': sp_data
                }
        
        # Read process values
        for pv_name in symbols_config.get('process_values', []):
            full_path = f"{struct_path}.{pv_name}"
            pv_data = struct_reader.read_process_value(full_path)
            if pv_data:
                symbols[full_path] = {
                    'name': full_path,
                    'type': 'process_value',
                    'data': pv_data
                }
        
        # Read switches
        for sw_name in symbols_config.get('switches', []):
            full_path = f"{struct_path}.{sw_name}"
            sw_data = struct_reader.read_switch(full_path)
            if sw_data:
                symbols[full_path] = {
                    'name': full_path,
                    'type': 'switch',
                    'data': sw_data
                }
        
        # Read alarms
        for al_name in symbols_config.get('alarms', []):
            full_path = f"{struct_path}.{al_name}"
            al_data = struct_reader.read_alarm(full_path)
            if al_data:
                symbols[full_path] = {
                    'name': full_path,
                    'type': 'alarm',
                    'data': al_data
                }
        
        # Create GUI with discovered symbols
        self.create_gui_from_structs(symbols)
        
    except Exception as e:
        logger.error(f"Error discovering symbols: {e}")
```

---

## Del 3: Migration Checklist

### Phase 1: PLC Side
- [ ] Opret alle STRUCT types i TwinCAT projekt
- [ ] Opret `ST_HMI_Symbols` container STRUCT
- [ ] Instantier `HMI : ST_HMI_Symbols` i MAIN
- [ ] Implementer initialisering af alle felter
- [ ] Fjern gamle `{attribute}` definitioner
- [ ] Compile og test i TwinCAT

### Phase 2: Python Side
- [ ] Opret `struct_reader.py`
- [ ] Opdater `config.json` med symbol liste
- [ ] Opdater `main.py` til at bruge StructReader
- [ ] Test læsning af alle STRUCT felter
- [ ] Test skrivning af værdier
- [ ] Verificer alarm funktionalitet

### Phase 3: Test & Validering
- [ ] Test setpoint ændring fra HMI → PLC
- [ ] Test process value visning med enheder
- [ ] Test switch labels vises korrekt
- [ ] Test alarm tekster og prioriteter
- [ ] Test at metadata kan ændres runtime i PLC
- [ ] Performance test (update rate)

---

## Fordele ved STRUCT Løsning

✅ **Runtime Read/Write**
- Alle felter tilgængelige via ADS
- Ændr labels, grænser, enheder online
- Ingen recompile nødvendig

✅ **Type Safety**
- STRUCT definitions sikrer korrekt datatype
- Compiler validering i TwinCAT
- IntelliSense i TwinCAT

✅ **Struktureret Data**
- Alt relateret data samlet
- Nem at udvide med nye felter
- Overskueligt i PLC kode

✅ **Performance**
- Kan læse hele STRUCT i én operation
- Mindre ADS traffic
- Batch updates muligt

✅ **Vedligeholdelse**
- Ændringer i én STRUCT definition
- Genbrug af STRUCTs
- Clear separation of concerns

---

## Implementation Tidslinje

**Dag 1: PLC Setup**
- Opret alle STRUCT types
- Implementer initialisering
- Test i TwinCAT

**Dag 2: Python Integration**
- Opret StructReader
- Opdater main.py
- Test læsning

**Dag 3: Full Integration**
- Test skrivning
- Alarm integration
- GUI opdateringer

**Dag 4: Test & Polish**
- End-to-end test
- Performance optimization
- Documentation

---

## Næste Steps

1. **Start med én symbol type** (fx Setpoints)
2. **Verificer det virker** before continuing
3. **Expand til andre typer** (Process Values, Switches, Alarms)
4. **Full migration** når alle typer virker

**Start command:**
Kopier PLC kode fra dette dokument til TwinCAT og compile!
