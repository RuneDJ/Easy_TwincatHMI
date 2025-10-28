# Quick Start Guide

## For Testing (No PLC Required)

```bash
# Install dependencies
pip install -r requirements.txt

# Run test with simulated data
python test_hmi.py
```

The test application will:
1. Start with mock PLC data
2. Show all HMI features
3. Trigger test alarms after 10 and 20 seconds
4. Allow you to test acknowledgment, history, etc.

## For Real PLC Connection

### 1. Setup PLC

Add to your TwinCAT Global Variable List:

```iecst
{attribute 'HMI_SP'}
{attribute 'Unit' := '°C'}
{attribute 'Min' := '0'}
{attribute 'Max' := '100'}
{attribute 'AlarmHighHigh' := '95'}
{attribute 'AlarmHigh' := '85'}
TemperaturSetpunkt : REAL := 25.0;

{attribute 'HMI_PV'}
{attribute 'Unit' := '°C'}
{attribute 'AlarmHighHigh' := '98'}
{attribute 'AlarmHigh' := '90'}
Temperatur_1 : REAL := 23.5;
```

See `example_plc_code.st` for complete examples.

### 2. Configure Connection

Edit `config.json`:
```json
{
  "ads": {
    "ams_net_id": "127.0.0.1.1.1",
    "ams_port": 851
  }
}
```

### 3. Run Application

```bash
python main.py
```

### 4. Connect

1. Click "Forbind" button
2. Application discovers symbols automatically
3. Monitors for alarms continuously

## Features Overview

### Setpoints (HMI_SP)
- Edit values and click "Skriv" to send to PLC
- Red border indicates active alarm
- Supports Min/Max ranges

### Process Values (HMI_PV)
- Real-time display from PLC
- Click for trend (future feature)
- Shows alarm limits below value

### Switches (HMI_SWITCH)
- Dropdown selection
- Changes immediately sent to PLC
- Supports multiple positions

### Alarm System

**Analog Alarms:**
- HighHigh: Critical high (red)
- High: Warning high (orange)
- Low: Warning low (orange)
- LowLow: Critical low (red)

**Digital Alarms:**
- BOOL signals (motor faults, etc.)
- Priority 1-4 (Critical to Low)

**Alarm Actions:**
- Kvitter: Acknowledge single alarm
- Kvitter Alle: Acknowledge all alarms
- Historik: View alarm log

**Alarm Display:**
- Color-coded by priority
- Blinking for unacknowledged
- Click alarm to view trend
- Auto-scrolling list

### Alarm History

- Filter by priority, state, date
- Search by symbol or message
- Export to CSV
- Sortable columns

## Keyboard Shortcuts

- None currently (future feature)

## Tips

1. **Test First**: Always use `test_hmi.py` before connecting to real PLC
2. **Symbol Names**: Use clear, descriptive names in PLC
3. **Units**: Always specify units in attributes
4. **Alarm Limits**: Set realistic limits with some margin
5. **Priorities**: Reserve Priority 1 (Critical) for serious issues

## Troubleshooting Quick Fixes

**Can't Connect:**
- Check PLC is running
- Verify AMS Net ID in config.json
- Test route: `ping <plc_ip>`

**No Symbols:**
- Check attribute spelling
- Recompile and download PLC code
- Verify PLC is in RUN mode

**Alarms Not Triggering:**
- Check alarm limits in attributes
- Verify AlarmPriority is set
- Test values exceed limits

## Build Standalone EXE

```bash
build_exe.bat
```

Executable will be in `dist\TwinCAT_HMI.exe`

## Next Steps

1. ✅ Test with `test_hmi.py`
2. ✅ Configure `config.json` for your PLC
3. ✅ Add HMI attributes to your PLC code
4. ✅ Connect and test
5. ✅ Configure alarm limits
6. ✅ Build EXE for deployment

## Example Session

```
1. Start application
   python test_hmi.py

2. Application opens, click "Forbind"
   → Discovers 5 test symbols
   → Shows setpoints, PV, switches

3. After 10 seconds
   → High temperature alarm (orange)
   → Alarm banner appears
   → Sound plays

4. After 20 seconds
   → Critical temperature alarm (red)
   → Blinking display

5. Click "Kvitter" on alarm
   → Alarm acknowledged
   → Stops blinking
   → Still visible until cleared

6. Click "Historik"
   → View all alarms
   → Filter and export
```

## Documentation Files

- `README.md` - Overview and features
- `INSTALLATION.md` - Detailed installation
- `QUICKSTART.md` - This file
- `example_plc_code.st` - PLC code examples

Enjoy! 🚀
