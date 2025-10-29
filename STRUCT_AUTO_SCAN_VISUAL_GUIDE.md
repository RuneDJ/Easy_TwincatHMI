# Visual Guide: Struct Auto-Scan Koncept

## Før og Efter Sammenligning

### ❌ FØR: Manuel Konfiguration

```
PLC Kode:
┌─────────────────────────────────┐
│ VAR_GLOBAL                      │
│   Temperature_1.Value : REAL;   │
│   Temperature_1.Error : BOOL;   │
│   Pressure_1.Value : REAL;      │
│   Pressure_1.Error : BOOL;      │
│ END_VAR                         │
└─────────────────────────────────┘
         │
         │ Manuel config
         ▼
config.json:
┌─────────────────────────────────┐
│ "process_values": [             │
│   {"name": "Temperature_1.Value"│
│    "unit": "°C", ...},          │
│   {"name": "Pressure_1.Value",  │
│    "unit": "bar", ...}          │
│ ],                              │
│ "alarms": [                     │
│   {"name": "Temperature_1.Error"│
│    "text": "...", ...}          │
│ ]                               │
└─────────────────────────────────┘

❌ Problem:
- Data duplication
- Manuel vedligeholdelse
- Fejlrisiko
- Tidskrævende
```

### ✅ EFTER: Struct Auto-Import

```
PLC Kode med Struct:
┌─────────────────────────────────┐
│ TYPE ST_Sensor :                │
│ STRUCT                          │
│   {attribute 'HMI_PV'}          │
│   Value : REAL;                 │
│   {attribute 'HMI_ALARM'}       │
│   Error : BOOL;                 │
│ END_STRUCT                      │
│                                 │
│ VAR_GLOBAL                      │
│   {attribute 'HMI_STRUCT'}      │
│   Temperature_1 : ST_Sensor;    │
│   {attribute 'HMI_STRUCT'}      │
│   Pressure_1 : ST_Sensor;       │
│ END_VAR                         │
└─────────────────────────────────┘
         │
         │ Compile → TMC fil
         │
         │ Auto-scan
         ▼
config.json (auto-genereret):
┌─────────────────────────────────┐
│ "manual_symbols": {             │
│   "symbols": {                  │
│     "Temperature_1.Value": {    │
│       "parent_struct": "...",   │
│       "category": "process_...", │
│       ...                       │
│     },                          │
│     "Temperature_1.Error": {    │
│       "parent_struct": "...",   │
│       ...                       │
│     },                          │
│     "Pressure_1.Value": {...},  │
│     "Pressure_1.Error": {...}   │
│   }                             │
│ }                               │
└─────────────────────────────────┘

✅ Fordele:
- Ingen data duplication
- Automatisk opdatering
- Type-sikker
- Hurtig setup
```

## Workflow Diagram

```
┌──────────────────┐
│  PLC Udvikling   │
│                  │
│ 1. Definer       │
│    ST_Sensor     │
│                  │
│ 2. Tilføj HMI    │
│    attributer    │
│                  │
│ 3. Opret         │
│    instancer med │
│    HMI_STRUCT    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TwinCAT Compile  │
│                  │
│ F7 → Genererer   │
│      PLC.tmc     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  HMI Application │
│                  │
│ 1. Connect       │
│                  │
│ 2. Click         │
│    "Scan PLC"    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Auto-Scanner    │
│                  │
│ 1. Parse TMC     │
│                  │
│ 2. Find structs  │
│    with HMI_     │
│    STRUCT        │
│                  │
│ 3. Ekspander     │
│    medlemmer     │
│                  │
│ 4. Filter HMI    │
│    tags          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Config Generator │
│                  │
│ Generer entries  │
│ for hver medlem  │
│ med full path    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   GUI Builder    │
│                  │
│ Opret grupperede │
│ widgets for      │
│ struct medlemmer │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   HMI Display    │
│                  │
│ ┌──────────────┐ │
│ │ Temperature_1│ │
│ │  └─Value     │ │
│ │  └─Error     │ │
│ └──────────────┘ │
│ ┌──────────────┐ │
│ │ Pressure_1   │ │
│ │  └─Value     │ │
│ │  └─Error     │ │
│ └──────────────┘ │
└──────────────────┘
```

## Struct Expansion Eksempel

### Input: PLC Symbol med Struct Type

```
Symbol Information:
┌────────────────────────────────┐
│ Name: GVL.Temperature_Sensor_1 │
│ Type: ST_AnalogInput           │
│ Attributes: [HMI_STRUCT]       │
└────────────────────────────────┘
```

### Struct Definition (fra TMC)

```
ST_AnalogInput:
┌─────────────────────────────────┐
│ Members:                        │
│ ┌─────────────────────────────┐ │
│ │ Value : REAL                │ │
│ │   HMI_PV ✅                 │ │
│ │   Unit = '°C'               │ │
│ │   Decimals = 2              │ │
│ │   AlarmHigh = 90            │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Scaled : REAL               │ │
│ │   HMI_PV ✅                 │ │
│ │   Unit = '%'                │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Error : BOOL                │ │
│ │   HMI_ALARM ✅              │ │
│ │   AlarmText = 'Sensor Fejl' │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ RawValue : INT              │ │
│ │   (ingen HMI attribut) ❌   │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### Output: Ekspanderede Medlemmer

```
Auto-Scan Resultat:
┌───────────────────────────────────────────────┐
│ ✅ Temperature_Sensor_1.Value                 │
│    Path: GVL.Temperature_Sensor_1.Value       │
│    Category: process_value                    │
│    Unit: °C                                   │
│    Decimals: 2                                │
│    Alarm High: 90                             │
│    Parent: GVL.Temperature_Sensor_1           │
│    Struct Type: ST_AnalogInput                │
├───────────────────────────────────────────────┤
│ ✅ Temperature_Sensor_1.Scaled                │
│    Path: GVL.Temperature_Sensor_1.Scaled      │
│    Category: process_value                    │
│    Unit: %                                    │
│    Decimals: 1                                │
│    Parent: GVL.Temperature_Sensor_1           │
│    Struct Type: ST_AnalogInput                │
├───────────────────────────────────────────────┤
│ ✅ Temperature_Sensor_1.Error                 │
│    Path: GVL.Temperature_Sensor_1.Error       │
│    Category: alarm                            │
│    Alarm Text: Sensor Fejl                    │
│    Priority: 2                                │
│    Parent: GVL.Temperature_Sensor_1           │
│    Struct Type: ST_AnalogInput                │
├───────────────────────────────────────────────┤
│ ❌ Temperature_Sensor_1.RawValue (skipped)    │
│    Reason: Ingen HMI attribut                 │
└───────────────────────────────────────────────┘
```

## GUI Layout Koncept

### Før: Flad Liste

```
┌─────────────────────────────────┐
│ Process Values                  │
├─────────────────────────────────┤
│ Temperature_Sensor_1.Value: 23°C│
│ Temperature_Sensor_1.Scaled: 46%│
│ Pressure_Sensor_1.Value: 5.2 bar│
│ Pressure_Sensor_1.Scaled: 52%   │
│ Flow_Sensor_1.Value: 100 L/min  │
│ Flow_Sensor_1.Scaled: 50%       │
└─────────────────────────────────┘

❌ Problem: Svært at se sammenhæng
```

### Efter: Grupperet Hierarki

```
┌─────────────────────────────────┐
│ Process Values                  │
├─────────────────────────────────┤
│ ▼ Temperature_Sensor_1          │
│   ├─ Value:   23.45 °C          │
│   └─ Scaled:  46.9 %            │
│                                 │
│ ▼ Pressure_Sensor_1             │
│   ├─ Value:   5.23 bar          │
│   └─ Scaled:  52.3 %            │
│                                 │
│ ▼ Flow_Sensor_1                 │
│   ├─ Value:   100.2 L/min       │
│   └─ Scaled:  50.1 %            │
└─────────────────────────────────┘

✅ Fordel: Klar struktur og sammenhæng
```

## Nested Struct Eksempel

### PLC Definition

```
TYPE ST_PID :
STRUCT
    {attribute 'HMI_SP'}
    Kp : REAL;
    {attribute 'HMI_SP'}
    Ki : REAL;
    {attribute 'HMI_SP'}
    Kd : REAL;
END_STRUCT

TYPE ST_Controller :
STRUCT
    {attribute 'HMI_SP'}
    Setpoint : REAL;
    {attribute 'HMI_PV'}
    ProcessValue : REAL;
    PID : ST_PID;  ← Nested struct
END_STRUCT

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}
    TempController : ST_Controller;
END_VAR
```

### Expansion Result

```
┌───────────────────────────────────┐
│ TempController                    │
│                                   │
│ Level 1 (ST_Controller):          │
│   ✅ TempController.Setpoint      │
│   ✅ TempController.ProcessValue  │
│                                   │
│ Level 2 (ST_PID nested):          │
│   ✅ TempController.PID.Kp        │
│   ✅ TempController.PID.Ki        │
│   ✅ TempController.PID.Kd        │
└───────────────────────────────────┘
```

### GUI Display (Nested)

```
┌─────────────────────────────────┐
│ Setpoints                       │
├─────────────────────────────────┤
│ ▼ TempController                │
│   ├─ Setpoint:    25.0 °C       │
│   └─ PID                        │
│      ├─ Kp:       1.50          │
│      ├─ Ki:       0.10          │
│      └─ Kd:       0.05          │
└─────────────────────────────────┘
```

## Array of Structs Eksempel

### PLC Definition

```
VAR_GLOBAL
    {attribute 'HMI_STRUCT_ARRAY'}
    Tanks : ARRAY[1..3] OF ST_Tank;
END_VAR
```

### Expansion Result

```
┌──────────────────────────────┐
│ Auto-expanded:               │
│                              │
│ ✅ Tanks[1].Level            │
│ ✅ Tanks[1].OverflowAlarm    │
│                              │
│ ✅ Tanks[2].Level            │
│ ✅ Tanks[2].OverflowAlarm    │
│                              │
│ ✅ Tanks[3].Level            │
│ ✅ Tanks[3].OverflowAlarm    │
└──────────────────────────────┘
```

### GUI Display (Array)

```
┌─────────────────────────────────┐
│ Process Values                  │
├─────────────────────────────────┤
│ ▼ Tank 1                        │
│   ├─ Level:         45.2 %      │
│   └─ OverflowAlarm: ⚠️ Active   │
│                                 │
│ ▼ Tank 2                        │
│   ├─ Level:         78.5 %      │
│   └─ OverflowAlarm: ✓ OK        │
│                                 │
│ ▼ Tank 3                        │
│   ├─ Level:         23.1 %      │
│   └─ OverflowAlarm: ✓ OK        │
└─────────────────────────────────┘
```

## Implementation Stack

```
┌─────────────────────────────────┐
│       GUI Display Layer         │
│  (gui_panels.py)                │
│  - Grouped widgets              │
│  - Visual hierarchy             │
│  - Collapse/expand              │
└───────────┬─────────────────────┘
            │
┌───────────▼─────────────────────┐
│    Symbol Parser Layer          │
│  (ads_symbol_parser.py)         │
│  - Parse member paths           │
│  - Categorize members           │
│  - Generate display names       │
└───────────┬─────────────────────┘
            │
┌───────────▼─────────────────────┐
│   Config Generator Layer        │
│  (symbol_auto_config.py)        │
│  - Expand structs               │
│  - Filter HMI members           │
│  - Generate config entries      │
└───────────┬─────────────────────┘
            │
┌───────────▼─────────────────────┐
│      TMC Parser Layer           │
│  (tmc_parser.py)                │
│  - Parse struct definitions     │
│  - Extract member attributes    │
│  - Find HMI_STRUCT symbols      │
└───────────┬─────────────────────┘
            │
┌───────────▼─────────────────────┐
│        ADS Layer                │
│  (ads_client.py)                │
│  - Read PLC symbols             │
│  - Access struct members        │
│  - Type information             │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│       TwinCAT PLC               │
│  - Struct definitions (DUT)     │
│  - Symbol instances             │
│  - TMC metadata file            │
└─────────────────────────────────┘
```

## Success Metrics

### Målbare Forbedringer

```
┌────────────────────┬──────────┬──────────┐
│ Metric             │ Før      │ Efter    │
├────────────────────┼──────────┼──────────┤
│ Config tid         │ 30 min   │ 2 min    │
│ (20 sensorer)      │          │          │
├────────────────────┼──────────┼──────────┤
│ Fejlrisiko         │ Høj      │ Minimal  │
│                    │          │          │
├────────────────────┼──────────┼──────────┤
│ Vedligeholdelse    │ Manuel   │ Auto     │
│                    │          │          │
├────────────────────┼──────────┼──────────┤
│ Skalerbarhed       │ Lineær   │ Constant │
│ (tid per sensor)   │          │          │
├────────────────────┼──────────┼──────────┤
│ Type sikkerhed     │ Ingen    │ PLC      │
│                    │          │ compiler │
└────────────────────┴──────────┴──────────┘
```

## Use Cases

### Use Case 1: Ny Sensor
```
UDEN struct auto-import:
1. Tilføj sensor i PLC ────────► 5 min
2. Compile PLC ────────────────► 1 min
3. Manuel config.json update ─► 10 min
4. Test i HMI ─────────────────► 5 min
                    Total: 21 min ⏱️

MED struct auto-import:
1. Tilføj sensor i PLC ────────► 5 min
   {attribute 'HMI_STRUCT'}
   NewSensor : ST_AnalogInput;
2. Compile PLC ────────────────► 1 min
3. Scan PLC i HMI ─────────────► 10 sek
4. Test i HMI ─────────────────► 2 min
                    Total: 8 min ⏱️

💾 Spar: 13 minutter per sensor!
```

### Use Case 2: Struct Update
```
UDEN struct auto-import:
1. Tilføj nyt medlem i PLC ───► 2 min
2. Compile ───────────────────► 1 min
3. Find alle instancer ───────► 5 min
4. Update config for hver ────► 15 min
   (10 instancer × 1.5 min)
                    Total: 23 min ⏱️

MED struct auto-import:
1. Tilføj nyt medlem i PLC ───► 2 min
   Med HMI attribut
2. Compile ───────────────────► 1 min
3. Scan PLC i HMI ────────────► 10 sek
                    Total: 3 min ⏱️

💾 Spar: 20 minutter ved struct update!
```

## Konklusion

### Nøgle Fordele
```
✅ Automatisering
   └─ Manuel config → Auto-generering

✅ Type Sikkerhed
   └─ PLC compiler validation

✅ Skalerbarhed
   └─ 1 struct → Mange instancer

✅ Vedligeholdelse
   └─ Ændring ét sted → Alle opdateret

✅ Organisering
   └─ Grupperet visning i GUI

✅ Tidsbesparelse
   └─ 13-20 min per sensor/update
```

### Hvornår Bruges Det?

```
✅ BRUG struct auto-import når:
   - Mange ens sensorer/enheder
   - Standardiserede datastrukturer
   - Gentagne mønstre
   - Team udvikling (konsistens)

⚠️ UNDGÅ hvis:
   - Unikke, ikke-gentagende symboler
   - Legacy system uden TMC
   - Meget simple projekter (< 5 symboler)
```
