# 📚 Struct Auto-Scan Feature Documentation

## Oversigt

Dette er dokumentationen for den nye **Struct Auto-Scan** feature i TwinCAT HMI applikationen. Featuren gør det muligt automatisk at importere PLC struct (DUT) typer med deres medlemmer til HMI'en, baseret på HMI attributer.

## 📄 Dokumenter

### 1. 🎯 STRUCT_AUTO_SCAN_PROMPT.md
**Hvad**: Kort prompt/summary med implementeringskrav  
**Til hvem**: Udviklere der skal implementere featuren  
**Indhold**:
- Kort beskrivelse af feature
- Eksempel PLC kode og forventet resultat
- Implementation checklist
- Success criteria

👉 **Start her** hvis du skal implementere featuren!

---

### 2. 📋 AUTO_SCAN_STRUCT_PLAN.md
**Hvad**: Komplet detaljeret implementeringsplan  
**Til hvem**: Alle involverede i projektet  
**Indhold**:
- Nuværende tilstand analyse
- Fase-for-fase implementeringsplan
- Detaljerede kode eksempler
- TMC XML struktur dokumentation
- Test cases
- Troubleshooting guide
- Tekniske detaljer

👉 **Brug denne** for dybdegående forståelse og som reference under udvikling!

---

### 3. 📊 STRUCT_AUTO_SCAN_VISUAL_GUIDE.md
**Hvad**: Visual guide med diagrammer og eksempler  
**Til hvem**: Alle - nem forståelse af konceptet  
**Indhold**:
- Før/efter sammenligning
- Workflow diagrammer
- Struct expansion eksempler
- GUI layout koncepter
- Nested structs og arrays
- Use cases og tidsbesparelser

👉 **Perfekt til** at forstå konceptet visuelt og præsentere til andre!

---

### 4. 💻 example_struct_plc_code.st
**Hvad**: Komplet PLC kode eksempler  
**Til hvem**: PLC udviklere og test  
**Indhold**:
- Struct definitioner (ST_AnalogInput, ST_Motor, etc.)
- Nested structs (ST_TempController med PID)
- Array af structs
- Forventet HMI import resultat
- Best practices og instruktioner

👉 **Brug dette** til at teste featuren med realistiske eksempler!

---

## 🚀 Quick Start Guide

### For PLC Udviklere

1. **Opret struct** med HMI attributer:
```iecst
TYPE ST_Sensor :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    Value : REAL;
    
    {attribute 'HMI_ALARM'}
    Error : BOOL;
END_STRUCT
END_TYPE
```

2. **Brug struct** med HMI_STRUCT marker:
```iecst
VAR_GLOBAL
    {attribute 'HMI_STRUCT'}
    Temperature_Sensor_1 : ST_Sensor;
END_VAR
```

3. **Compile** TwinCAT projekt (F7)

4. **Klar!** HMI kan nu auto-importere sensoren

### For HMI Udviklere

1. **Læs** `STRUCT_AUTO_SCAN_PROMPT.md` for requirements

2. **Følg** `AUTO_SCAN_STRUCT_PLAN.md` for implementation

3. **Implementer** fase-for-fase:
   - Phase 1: TMC Parser enhancement
   - Phase 2: Auto-Config expansion
   - Phase 3: Config generation
   - Phase 4: GUI display

4. **Test** med `example_struct_plc_code.st`

### For Projekt Ledere / Stakeholders

1. **Læs** `STRUCT_AUTO_SCAN_VISUAL_GUIDE.md` for overblik

2. **Review** use cases og tidsbesparelser

3. **Prioriter** features til første iteration

## 📖 Læseguide

### Scenario 1: "Jeg skal implementere featuren"
```
1. STRUCT_AUTO_SCAN_PROMPT.md ───► Forstå krav
2. AUTO_SCAN_STRUCT_PLAN.md ─────► Detaljeret guide
3. example_struct_plc_code.st ───► Test eksempler
4. STRUCT_AUTO_SCAN_VISUAL_GUIDE.md ► Referere til koncepter
```

### Scenario 2: "Jeg skal forstå konceptet"
```
1. STRUCT_AUTO_SCAN_VISUAL_GUIDE.md ► Visual forståelse
2. example_struct_plc_code.st ──────► Se konkrete eksempler
3. AUTO_SCAN_STRUCT_PLAN.md ────────► Dybere detaljer
```

### Scenario 3: "Jeg skal præsentere til team"
```
1. STRUCT_AUTO_SCAN_VISUAL_GUIDE.md ► Use cases og fordele
2. example_struct_plc_code.st ──────► Live demo eksempler
3. STRUCT_AUTO_SCAN_PROMPT.md ─────► Implementation oversigt
```

### Scenario 4: "Jeg skal teste featuren"
```
1. example_struct_plc_code.st ──────► Copy til TwinCAT
2. AUTO_SCAN_STRUCT_PLAN.md ───────► Test cases sektion
3. STRUCT_AUTO_SCAN_PROMPT.md ─────► Success criteria
```

## 🎯 Nøgle Koncepter

### Struct Auto-Import
Automatisk import af alle medlemmer i en PLC struct når structen er markeret med `{attribute 'HMI_STRUCT'}`:

```
Input:  {attribute 'HMI_STRUCT'} Sensor1 : ST_Sensor;
          ↓
Output: Sensor1.Value      (Process Value)
        Sensor1.Error      (Alarm)
        Sensor1.Offset     (Setpoint)
```

### HMI Attribut Filtering
Kun struct medlemmer med HMI attributer importeres:

```
✅ {attribute 'HMI_PV'} Value : REAL;     → Importeres
✅ {attribute 'HMI_ALARM'} Error : BOOL;  → Importeres
❌ RawValue : INT;                        → Springes over
❌ Timestamp : TIME;                      → Springes over
```

### Full Path Notation
Struct medlemmer tilgås med full path:

```
Struct: Temperature_Sensor_1 : ST_AnalogInput
  └─ Medlem: Value

Full path: GVL.Temperature_Sensor_1.Value
           └──┘ └────────────────────┘ └───┘
          Prefix    Parent struct    Member
```

### Grouped GUI Display
Medlemmer grupperes visuelt under parent struct:

```
┌─ Temperature_Sensor_1 ─────┐
│  └─ Value:   23.45 °C      │
│  └─ Scaled:  46.9 %        │
│  └─ Error:   ✓ OK          │
└────────────────────────────┘
```

## 🔧 Implementeringsstadie

### ✅ Færdigt
- [x] Komplet dokumentation
- [x] Implementation plan
- [x] Visual guide
- [x] PLC eksempler
- [x] Test cases

### ⏳ Næste Skridt (Pending)
- [ ] TMC parser enhancement
- [ ] Auto-config expansion
- [ ] Config generation
- [ ] GUI display implementation
- [ ] Testing og validation

## 📊 Forventet Impact

### Tidsbesparelse
```
Manuel config:     30 minutter per sensor
Auto-import:       2 minutter per sensor
──────────────────────────────────────────
Besparelse:        28 minutter (93% ↓)
```

### Skalerbarhed
```
1 sensor:          Samme tid (2 min)
10 sensorer:       Samme tid (2 min)
100 sensorer:      Samme tid (2 min)
```

### Fejlreduktion
```
Manuel config:     Høj risiko for fejl
Auto-import:       Minimal (PLC compiler validated)
```

## 🤝 Bidrag

### Workflow for Opdateringer
1. Læs relevant dokumentation
2. Foretag ændringer
3. Opdater andre relaterede dokumenter
4. Test med eksempel kode
5. Commit med beskrivende besked

### Dokumentationsstruktur
```
STRUCT_AUTO_SCAN_README.md (denne fil)
├─ STRUCT_AUTO_SCAN_PROMPT.md
│  └─ Kort, konkret, actionable
├─ AUTO_SCAN_STRUCT_PLAN.md
│  └─ Detaljeret, teknisk, komplet
├─ STRUCT_AUTO_SCAN_VISUAL_GUIDE.md
│  └─ Visual, forståelig, eksempler
└─ example_struct_plc_code.st
   └─ Praktisk, testbar, kommenteret
```

## 📞 Support

### Spørgsmål?
1. Check **FAQ** i `AUTO_SCAN_STRUCT_PLAN.md`
2. Se **Troubleshooting** sektion
3. Review **Test Cases** for eksempler
4. Kontakt development team

### Problemer?
1. Verificer TMC fil findes og er opdateret
2. Check at HMI attributer er korrekt sat
3. Test med simple eksempler først
4. Se debug logs i HMI applikation

## 🔗 Relaterede Dokumenter

I hovedrepository:
- `README.md` - HMI application overview
- `TMC_METADATA.md` - TMC integration guide
- `PROJECT_OVERVIEW.md` - Project structure
- `example_plc_code.st` - Basic HMI examples (non-struct)

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial documentation created |
| | | - Implementation plan |
| | | - Visual guide |
| | | - Example code |
| | | - Prompt document |

## 📝 Licens

Samme licens som hovedprojektet - se main `README.md`

---

**Senest opdateret**: 2025-10-29  
**Forfatter**: Development Team  
**Status**: Documentation Complete ✅ | Implementation Pending ⏳
