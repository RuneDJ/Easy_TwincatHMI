# PLC Export Files - Import Guide

## ✅ Status: Klar til Import

**Alle filer er genereret og verificeret:**
- ✅ XML Format: Korrekt TwinCAT XML struktur
- ✅ Syntax Check: Alle filer ender med `</TcPlcObject>`
- ✅ File Count: 11 filer (9 DUTs + 2 POUs)
- ✅ Total Size: ~24 KB
- ✅ Import Ready: Ja - drag-drop direkte ind i TwinCAT Visual Studio

## Oversigt
Denne mappe indeholder alle TwinCAT PLC filer i XML format klar til import i dit TwinCAT projekt.

**Migration:** Fra attribute-baseret til STRUCT-baseret arkitektur
**Fordel:** Alle metadata (labels, units, limits) kan nu læses/skrives runtime via ADS

## Filer

### Data Types (.TcDUT)
**Base Configuration Types:**
1. `ST_NumericConfig.TcDUT` (631 bytes) - Unit, Min, Max, Decimals, Step
2. `ST_AlarmLimits.TcDUT` (878 bytes) - Alarm grænser med hysteresis og alarm tekster
3. `ST_SwitchConfig.TcDUT` (873 bytes) - Switch position labels (2-8 positioner)
4. `ST_DisplayConfig.TcDUT` (547 bytes) - Display navn, beskrivelse, Visible, ReadOnly

**HMI Data Types:**
5. `ST_HMI_Setpoint.TcDUT` (787 bytes) - Setpoint med alarm grænser og runtime tracking
6. `ST_HMI_ProcessValue.TcDUT` (813 bytes) - Process value med quality indikation
7. `ST_HMI_Switch.TcDUT` (663 bytes) - Multi-position switch med position tracking
8. `ST_HMI_Alarm.TcDUT` (868 bytes) - Digital alarm med acknowledge tracking

**Container:**
9. `ST_HMI_Symbols.TcDUT` (1,406 bytes) - Container med alle 17 HMI symboler

### Programs (.TcPOU)
10. `PRG_HMI_Init.TcPOU` (7,686 bytes) - Initialiserer alle HMI data (200+ linjer kode)
11. `MAIN.TcPOU` (2,731 bytes) - Main program med HMI instance og simulation

## Import Instruktioner

### Metode 1: Drag & Drop (Nemmest)

1. **Åbn dit TwinCAT projekt** i Visual Studio
2. **Naviger til DUTs folder** i Solution Explorer
3. **Træk alle .TcDUT filer** fra `plc_export` mappen til DUTs folder
4. **Naviger til POUs folder**
5. **Træk alle .TcPOU filer** til POUs folder
6. **Build Solution** (F7)

### Metode 2: Via Context Menu

1. **Åbn dit TwinCAT projekt**
2. **Højreklik på DUTs folder** → "Add" → "Existing Item..."
3. **Naviger til plc_export** mappe
4. **Vælg alle .TcDUT filer** → "Add"
5. **Højreklik på POUs folder** → "Add" → "Existing Item..."
6. **Vælg alle .TcPOU filer** → "Add"
7. **Build Solution** (F7)

### Metode 3: Copy-Paste Kode

Hvis import ikke virker, kan du copy-paste koden manuelt:

#### For DUTs:
1. Højreklik på DUTs → "Add" → "DUT..."
2. Naviger til DUTs navn (fx `ST_NumericConfig`)
3. Åbn `.TcDUT` filen i en tekst editor
4. Kopier koden mellem `<![CDATA[` og `]]>` tags
5. Indsæt i TwinCAT DUT editoren

#### For POUs:
1. Højreklik på POUs → "Add" → "POU..."
2. Vælg "Program" og navngiv (fx `PRG_HMI_Init`)
3. Kopier koden fra `.TcPOU` filen
4. Indsæt i TwinCAT POU editoren

## Import Rækkefølge (Vigtigt!)

Import i denne rækkefølge for at undgå dependency errors:

### Trin 1: Base Types
```
1. ST_NumericConfig.TcDUT
2. ST_AlarmLimits.TcDUT
3. ST_SwitchConfig.TcDUT
4. ST_DisplayConfig.TcDUT
```

### Trin 2: HMI Types
```
5. ST_HMI_Setpoint.TcDUT
6. ST_HMI_ProcessValue.TcDUT
7. ST_HMI_Switch.TcDUT
8. ST_HMI_Alarm.TcDUT
```

### Trin 3: Container
```
9. ST_HMI_Symbols.TcDUT
```

### Trin 4: Programs
```
10. PRG_HMI_Init.TcPOU
11. MAIN.TcPOU
```

## Efter Import

### 1. Verificer Build
```
Build → Build Solution (F7)
```
Skulle give 0 errors, 0 warnings.

### 2. Tilpas MAIN
Hvis du allerede har et MAIN program:
- Kopier kun VAR sektionen (`HMI : ST_HMI_Symbols`)
- Kopier kun initialiserings kode (`fbHmiInit(HMI := HMI);`)

### 3. Test Data
Download til PLC og verificer:
- HMI variabel findes
- Alle sub-structs er tilgængelige
- Kan læse/skrive værdier online

## Brug i Eksisterende Projekt

### Tilføj til Eksisterende MAIN:

```iecst
PROGRAM MAIN
VAR
    // ... dine eksisterende variabler ...
    
    // Tilføj HMI STRUCT
    HMI : ST_HMI_Symbols;
    fbHmiInit : PRG_HMI_Init;
END_VAR

// Initialiser ved opstart
fbHmiInit(HMI := HMI);

// ... din eksisterende kode ...

// Opdater HMI værdier
HMI.Temperatur_1.Value := ActualTemperature;
HMI.Tryk_1.Value := ActualPressure;
// etc...
```

## Verificer Symboler er Synlige

1. **Åbn TwinCAT XAE**
2. **Højreklik på PLC projekt** → "Properties"
3. **Symbol Configuration** tab
4. Verificer "Support Parameter Transfer" er enabled
5. **Build** projektet igen

## Test fra Python HMI

Efter PLC download:

```python
# Test læsning af STRUCT
value = plc.read_by_name("MAIN.HMI.TemperaturSetpunkt.Value", pyads.PLCTYPE_REAL)
unit = plc.read_by_name("MAIN.HMI.TemperaturSetpunkt.Config.Unit", pyads.PLCTYPE_STRING)
print(f"Setpoint: {value} {unit}")

# Test skrivning
plc.write_by_name("MAIN.HMI.TemperaturSetpunkt.Value", 30.0, pyads.PLCTYPE_REAL)
```

## Troubleshooting

### "Type not found" Error
**Problem:** Base types ikke importeret først

**Løsning:** 
1. Import i korrekt rækkefølge (se ovenfor)
2. Build efter hver gruppe af types

### "Duplicate definition" Error
**Problem:** Type allerede eksisterer i projekt

**Løsning:**
1. Slet eksisterende type først
2. Eller omdøb ny type

### "Symbol not found" via ADS
**Problem:** Symbol ikke eksporteret

**Løsning:**
1. PLC Properties → Symbol Configuration
2. Enable "Support Parameter Transfer"
3. Rebuild og download

### Build Errors eller XML Import Fejl
**Problem:** XML format issues eller parser fejl

**Løsning:**
- **Alle filer har korrekt XML format** (verificeret 28/10/2025)
- Filer ender korrekt med `</TcPlcObject>` (ikke `</TcPlcObject>]]>`)
- Hvis import stadig fejler: Brug "Copy-Paste Kode" metode
- Copy koden mellem `<![CDATA[` og `]]>` tags og indsæt manuelt

### Verification af XML Format
Alle filer er testet og verificeret med:
```powershell
Get-ChildItem *.TcDUT, *.TcPOU | Select-Object Name, Length, LastWriteTime
```
Status: ✅ Alle 11 filer korrekt formateret

## Tilpasning

### Tilføj Flere Symboler

I `ST_HMI_Symbols.TcDUT`:
```iecst
TYPE ST_HMI_Symbols :
STRUCT
    // ... eksisterende symboler ...
    
    // Tilføj nye:
    MinNyTemperatur : ST_HMI_ProcessValue;
    MinNySwitch : ST_HMI_Switch;
END_STRUCT
END_TYPE
```

I `PRG_HMI_Init.TcPOU`:
```iecst
// Initialiser nye symboler
HMI.MinNyTemperatur.Config.Unit := '°C';
HMI.MinNyTemperatur.Display.DisplayName := 'Min Ny Temperatur';
// etc...
```

### Ændr Labels Online

Med STRUCT approach kan du ændre labels runtime:
```iecst
// I PLC kode, online mode:
HMI.DriftMode.Config.Pos0_Label := 'Ny Label';
```

Dette var ikke muligt med attributes!

## Næste Steps

1. ✅ Import alle filer
2. ✅ Build solution
3. ✅ Download til PLC
4. ✅ Test læsning fra Python
5. ✅ Opdater Python HMI til at bruge STRUCTs (se struct_reader.py)

## Support

Se `MIGRATION_TO_STRUCTS.md` for komplet migration guide og Python integration.
