# TwinCAT HMI Project Structure

## ✅ Complete Implementation

Alle komponenter er implementeret og klar til brug!

## 📁 Project Files

### Core Application Files
- ✅ **main.py** - Hovedapplikation med GUI og ADS integration
- ✅ **ads_client.py** - ADS kommunikation med TwinCAT 3
- ✅ **ads_symbol_parser.py** - Parser til symbol attributes og kategorisering
- ✅ **alarm_manager.py** - Alarm detection, tilstande, og håndtering
- ✅ **alarm_logger.py** - CSV logging af alarmer med daily rotation
- ✅ **alarm_banner.py** - GUI widget for alarm banner med blinkning
- ✅ **alarm_history_window.py** - Alarm historik vindue med filter og export
- ✅ **gui_panels.py** - Setpoint, Switch, og Process Value widgets

### Configuration & Documentation
- ✅ **config.json** - Application konfiguration (ADS, alarmer, GUI)
- ✅ **README.md** - Projekt oversigt og feature beskrivelse
- ✅ **INSTALLATION.md** - Detaljeret installations guide
- ✅ **QUICKSTART.md** - Hurtig start guide
- ✅ **requirements.txt** - Python dependencies

### Build & Deployment
- ✅ **build_exe.bat** - Windows build script (PyInstaller)
- ✅ **TwinCAT_HMI.spec** - PyInstaller specification fil

### Testing & Examples
- ✅ **test_hmi.py** - Test application med mock PLC data
- ✅ **example_plc_code.st** - Eksempel TwinCAT PLC kode med attributes

### Other
- ✅ **.gitignore** - Git ignore fil

## 🎯 Features Implemented

### ADS Communication
- ✅ Connect/disconnect til TwinCAT PLC
- ✅ Read/write symboler
- ✅ Symbol discovery med attribute filtering
- ✅ Multiple symbol read for efficiency
- ✅ Connection status monitoring

### Symbol Management
- ✅ Automatic symbol discovery baseret på HMI attributes
- ✅ Kategorisering: Setpoints, Process Values, Switches, Alarms
- ✅ Parse alarm limits fra attributes
- ✅ Display name generation
- ✅ Support for units, min/max, decimals

### Alarm System
- ✅ Analog alarmer (HighHigh, High, Low, LowLow)
- ✅ Digital alarmer (BOOL signals)
- ✅ 4 prioritets niveauer (Critical, High, Medium, Low)
- ✅ Alarm tilstande (ACTIVE, ACKNOWLEDGED, CLEARED)
- ✅ Hysterese/deadband for at undgå flapping
- ✅ Alarm callback system
- ✅ Windows beep alarm lyd

### Alarm Display
- ✅ Farve-kodet alarm banner
- ✅ Blinkende display for ikke-kvitterede alarmer
- ✅ Alarm ikoner (⛔, ⚠️, ⚡, ℹ️)
- ✅ Kvitter knapper (individuel og alle)
- ✅ Scrolling alarm liste
- ✅ Auto-sizing baseret på antal alarmer
- ✅ Farveblind-venlig (ikoner + farver)

### Alarm History
- ✅ Alarm historik vindue
- ✅ Filter på prioritet, status, dato
- ✅ Søgning i symboler og beskeder
- ✅ Sorterbare kolonner
- ✅ Export til CSV
- ✅ Ryd historik funktion

### Alarm Logging
- ✅ CSV logging med daily rotation
- ✅ Timestamp med millisekunder
- ✅ Log alarm tilstands ændringer
- ✅ Export til samlet CSV fil
- ✅ Automatic log folder creation
- ✅ Old log cleanup funktion

### GUI Components
- ✅ Setpoint widgets med spinbox og skriv knap
- ✅ Process value widgets med click-for-trend
- ✅ Switch widgets med dropdown
- ✅ Alarm indikatorer på widgets (rød kant)
- ✅ Information panel med log beskeder
- ✅ Connection panel med status indikator
- ✅ Sound toggle button
- ✅ Help dialog

### Data Update
- ✅ Configurable update interval
- ✅ Timer-baseret opdatering
- ✅ Efficient multiple symbol read
- ✅ Automatic alarm checking
- ✅ UI opdatering

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│              Main Window (main.py)          │
│  ┌────────────┬────────────┬──────────────┐ │
│  │ Connection │ Setpoints  │   Process    │ │
│  │   Panel    │   Panel    │    Values    │ │
│  └────────────┴────────────┴──────────────┘ │
│  ┌──────────────────────────────────────┐   │
│  │      Information Panel               │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │      Alarm Banner (if alarms)        │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
              ↕                    ↕
    ┌─────────────────┐   ┌──────────────────┐
    │   ADS Client    │   │  Alarm Manager   │
    │  (ads_client)   │   │ (alarm_manager)  │
    └─────────────────┘   └──────────────────┘
              ↕                    ↕
    ┌─────────────────┐   ┌──────────────────┐
    │  TwinCAT PLC    │   │  Alarm Logger    │
    │   (via ADS)     │   │ (CSV files)      │
    └─────────────────┘   └──────────────────┘
```

## 🔧 Configuration

### config.json Structure
```json
{
  "ads": {
    "ams_net_id": "127.0.0.1.1.1",
    "ams_port": 851,
    "update_interval": 1.0
  },
  "alarms": {
    "enabled": true,
    "sound_enabled": true,
    "blink_interval": 500,
    "auto_acknowledge": false,
    "log_to_csv": true,
    "hysteresis_percent": 2.0
  },
  "symbol_search": {
    "enabled": true,
    "search_patterns": [
      "HMI_SP",
      "HMI_PV", 
      "HMI_SWITCH",
      "HMI_ALARM"
    ]
  },
  "gui": {
    "window_title": "TwinCAT HMI",
    "window_width": 1200,
    "window_height": 800,
    "alarm_banner_max_visible": 5
  }
}
```

## 🚀 Usage

### Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Test with mock data (no PLC needed)
python test_hmi.py

# Run with real PLC
python main.py
```

### Production Mode
```bash
# Build standalone EXE
build_exe.bat

# Run
dist\TwinCAT_HMI.exe
```

## 📝 TwinCAT PLC Integration

### Required Attributes

**Setpoint:**
```iecst
{attribute 'HMI_SP'}
{attribute 'Unit' := '°C'}
{attribute 'Min' := '0'}
{attribute 'Max' := '100'}
{attribute 'AlarmHighHigh' := '95'}
{attribute 'AlarmHigh' := '85'}
TemperaturSetpunkt : REAL := 25.0;
```

**Process Value:**
```iecst
{attribute 'HMI_PV'}
{attribute 'Unit' := '°C'}
{attribute 'AlarmHighHigh' := '98'}
{attribute 'AlarmHigh' := '90'}
{attribute 'AlarmLow' := '5'}
{attribute 'AlarmLowLow' := '2'}
Temperatur_1 : REAL := 23.5;
```

**Switch:**
```iecst
{attribute 'HMI_SWITCH'}
{attribute 'Pos0' := 'Stop'}
{attribute 'Pos1' := 'Auto'}
{attribute 'Pos2' := 'Manuel'}
DriftMode : INT := 1;
```

**Digital Alarm:**
```iecst
{attribute 'HMI_ALARM'}
{attribute 'AlarmText' := 'Motor 1 Fejl'}
{attribute 'AlarmPriority' := '1'}
Motor1Fejl : BOOL := FALSE;
```

## 🎨 Alarm Color Scheme

| Priority | Color  | Icon | Background | Use Case              |
|----------|--------|------|------------|-----------------------|
| 1        | Red    | ⛔   | #DC143C    | Critical, Emergency   |
| 2        | Orange | ⚠️   | #FF8C00    | High, Warning         |
| 3        | Yellow | ⚡   | #FFD700    | Medium, Attention     |
| 4        | Blue   | ℹ️   | #4169E1    | Low, Information      |

## 📦 Dependencies

- **pyads** (≥3.3.0) - TwinCAT ADS communication
- **PyQt5** (≥5.15.0) - GUI framework
- **matplotlib** (≥3.5.0) - Future trend visualization
- **Python** (≥3.8) - Required interpreter

## ✨ Key Features Summary

✅ **Automatic Symbol Discovery** - Finder symboler baseret på HMI attributes  
✅ **Real-time Monitoring** - Kontinuerlig opdatering fra PLC  
✅ **Comprehensive Alarm System** - Analog og digital alarmer med 4 prioriteter  
✅ **Visual Alarm Display** - Farve-kodet, blinkende alarm banner  
✅ **Alarm History** - Full historik med filter og export  
✅ **CSV Logging** - Automatisk logging af alle alarmer  
✅ **Hysteresis** - Undgår alarm flapping med deadband  
✅ **Sound Alerts** - Windows beep for alarmer  
✅ **User-friendly GUI** - Intuitivt interface med PyQt5  
✅ **Standalone EXE** - PyInstaller build til deployment  
✅ **Test Mode** - Mock PLC data for test uden hardware  

## 🔮 Future Enhancements (Not Implemented)

- Trend visualization (matplotlib plots)
- Alarm acknowledgment med user authentication
- Database storage (SQLite) for historik
- Custom alarm sound files (WAV)
- Network alarm notifications (email/SMS)
- Multi-language support
- Custom themes/skins
- Recipe management
- Data logging og export

## 📄 License

MIT License - Free to use and modify

## 🏁 Status

**PROJECT COMPLETE** ✅

All core features implemented and tested!

---

**Created:** October 28, 2025  
**Language:** Python 3.8+  
**Framework:** PyQt5  
**Protocol:** TwinCAT ADS  
**Platform:** Windows
