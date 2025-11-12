# Prompt: Implementering af Auto-Scan for PLC Structs med HMI Attributer

## Kort Beskrivelse
Implementer funktionalitet til automatisk at scanne TwinCAT PLCen for struct/DUT typer der har HMI attributer, og importere alle struct medlemmer med HMI tags til HMI applikationen.

## Eksempel Input (PLC Kode)
```iecst
TYPE ST_AnalogInput :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '2'}
    Value : REAL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Sensor Fejl'}
    Error : BOOL;
    
    // Ingen HMI attribut - skal ikke importeres
    RawValue : INT;
END_STRUCT
END_TYPE

VAR_GLOBAL
    {attribute 'HMI_STRUCT'}  // Marker for auto-import
    Temperature_Sensor_1 : ST_AnalogInput;
END_VAR
```

## Forventet Output
Når "Scan PLC" køres, skal systemet:

1. **Finde** symbolet `Temperature_Sensor_1` (har `HMI_STRUCT` attribut)
2. **Identificere** at det er type `ST_AnalogInput` (struct)
3. **Ekspandere** structen til medlemmer:
   - `Temperature_Sensor_1.Value` → Process Value (°C, 2 decimaler)
   - `Temperature_Sensor_1.Error` → Alarm (Sensor Fejl)
4. **Skippe** medlemmer uden HMI attributer:
   - ~~`Temperature_Sensor_1.RawValue`~~ (ingen HMI tag)
5. **Generere** config entries og GUI widgets for hver importeret medlem

## Nøgle Krav

### 1. TMC Parser Enhancement
- Parse `<DataType>` elementer (struct definitioner)
- Udtræk `<SubItem>` (struct medlemmer) med attributer
- Find symboler med `HMI_STRUCT` marker
- Håndter nested structs

### 2. Auto-Config Enhancement
- Detekter struct typer under scanning
- Ekspander struct til individuelle medlemmer
- Filter medlemmer baseret på HMI attributer
- Generer config for hver medlem med fuld path (`Parent.Member`)

### 3. GUI Integration
- Gruppér struct medlemmer visuelt
- Vis struct navn som gruppe header
- Organisér medlemmer hierarkisk
- Support collapse/expand af grupper

### 4. Configuration
Ny config sektion:
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

## Implementation Checklist

### Phase 1: Core Struct Parsing
- [ ] `TMCParser.get_all_datatypes()` - Find alle struct definitioner
- [ ] `TMCParser.get_struct_members(struct_name)` - Hent struct medlemmer
- [ ] `TMCParser.find_struct_symbols()` - Find symboler med HMI_STRUCT
- [ ] Test struct parsing med eksempel TMC fil

### Phase 2: Auto-Config Expansion
- [ ] `SymbolAutoConfig._is_struct_type()` - Check om symbol er struct
- [ ] `SymbolAutoConfig._expand_struct_members()` - Ekspander til medlemmer
- [ ] `SymbolAutoConfig._analyze_struct_member()` - Analyser hvert medlem
- [ ] Integrér struct expansion i scan flow

### Phase 3: Config Generation
- [ ] Generer config entries med full member path
- [ ] Inkluder `parent_struct` og `struct_type` metadata
- [ ] Gruppér relaterede medlemmer i output
- [ ] Test config generering med forskellige struct typer

### Phase 4: GUI Display
- [ ] Opret gruppe widgets for structs
- [ ] Placér medlem widgets under struct gruppe
- [ ] Tilføj visual indent/hierarki
- [ ] Implementer collapse/expand (optional)

### Phase 5: Testing
- [ ] Test med simple struct (enkelt niveau)
- [ ] Test med nested struct (struct i struct)
- [ ] Test med arrays af structs
- [ ] Test med mixed HMI/non-HMI medlemmer

## Eksempel Workflow

### Før (Manuel Config)
```json
{
  "symbols": {
    "process_values": [
      {"name": "GVL.Temperature_Sensor_1.Value", "unit": "°C", ...},
      {"name": "GVL.Temperature_Sensor_1.Scaled", "unit": "%", ...}
    ],
    "alarms": [
      {"name": "GVL.Temperature_Sensor_1.Error", "text": "Sensor Fejl", ...}
    ]
  }
}
```

### Efter (Auto-Genereret)
1. Tilføj `{attribute 'HMI_STRUCT'}` til `Temperature_Sensor_1` i PLC
2. Compile TwinCAT projekt
3. Klik "Scan PLC" i HMI
4. ✅ Alle struct medlemmer automatisk importeret og konfigureret

## Success Criteria
- ✅ Structs med `HMI_STRUCT` attribut findes automatisk
- ✅ Kun medlemmer med HMI attributer importeres
- ✅ Config genereres med korrekt full path
- ✅ GUI viser grupperede medlemmer
- ✅ Alle eksisterende features virker stadig (bagudkompatibilitet)

## Nice-to-Have (Future)
- Nested struct support (struct.member.submember)
- Array handling (Sensors[1..10])
- Custom struct templates
- Struct change detection og re-import

## Relaterede Filer
- `tmc_parser.py` - TMC XML parsing
- `symbol_auto_config.py` - Auto-scan og config generering
- `ads_symbol_parser.py` - Symbol kategorisering
- `gui_panels.py` - GUI widgets
- `config.json` - Konfiguration
- `AUTO_SCAN_STRUCT_PLAN.md` - Detaljeret implementeringsplan (dette dokument)

## Reference Implementation
Se `AUTO_SCAN_STRUCT_PLAN.md` for:
- Detaljeret arkitektur
- Kode eksempler
- TMC XML struktur
- Test cases
- Troubleshooting guide
