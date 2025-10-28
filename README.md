# TwinCAT HMI Application

Windows HMI application for TwinCAT 3 PLC communication via ADS protocol with integrated alarm system.

## Features

- ✅ ADS communication with TwinCAT 3
- ✅ Automatic symbol discovery via attributes
- ✅ Setpoints, Process Values, and Switches
- ✅ Comprehensive alarm system
  - Analog alarms (High/Low/HighHigh/LowLow)
  - Digital alarms (BOOL signals)
  - 4 priority levels (Critical, High, Medium, Low)
  - Alarm acknowledgment
  - Alarm history
  - CSV logging
- ✅ Color-coded alarm banner
- ✅ Trend visualization
- ✅ Information panel

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json` to match your TwinCAT setup:
- AMS Net ID
- AMS Port (default 851)
- Update interval
- Alarm settings

## TwinCAT Setup

Use attributes in your PLC code to define HMI elements:

```iecst
{attribute 'HMI_SP'}
{attribute 'Unit' := '°C'}
{attribute 'Min' := '0'}
{attribute 'Max' := '100'}
{attribute 'AlarmHighHigh' := '95'}
{attribute 'AlarmHigh' := '85'}
TemperaturSetpunkt : REAL := 25.0;
```

## Usage

```bash
python main.py
```

## Build EXE

```bash
build_exe.bat
```

## Alarm System

### Alarm Types
- **HighHigh (HH)**: Critical high alarm
- **High (H)**: Warning high
- **Low (L)**: Warning low
- **LowLow (LL)**: Critical low alarm
- **Digital**: BOOL-based alarms

### Alarm Priorities
- Priority 1: CRITICAL (Red, ⛔)
- Priority 2: HIGH (Orange, ⚠️)
- Priority 3: MEDIUM (Yellow, ⚡)
- Priority 4: LOW (Blue, ℹ️)

### Alarm States
- **ACTIVE**: Alarm is currently active
- **ACKNOWLEDGED**: Alarm acknowledged but still active
- **CLEARED**: Alarm condition resolved (history)

## License

MIT License


## UI PIC
![alt text](UI001-1.png)