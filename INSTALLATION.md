# Installation Guide - TwinCAT HMI Application

## System Requirements

- Windows 10 or later
- Python 3.8 or newer (for development)
- TwinCAT 3 XAE/XAR (for PLC communication)
- 4 GB RAM minimum
- 100 MB disk space

## Installation for Development

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- pyads (TwinCAT ADS communication)
- PyQt5 (GUI framework)
- matplotlib (for future trend visualization)

### 2. Configure TwinCAT Route

For ADS communication to work, you need to set up a route to your TwinCAT PLC:

#### Local PLC (on same machine):
- AMS Net ID: `127.0.0.1.1.1` (or your local TwinCAT ID)
- Port: `851` (default PLC runtime port)
- No additional route configuration needed

#### Remote PLC:
1. Open TwinCAT XAE
2. Go to SYSTEM → TwinCAT Static Routes
3. Add route to remote PLC
4. Note the AMS Net ID of the target PLC

### 3. Configure Application

Edit `config.json`:

```json
{
  "ads": {
    "ams_net_id": "YOUR_PLC_AMS_NET_ID",
    "ams_port": 851,
    "update_interval": 1.0
  }
}
```

### 4. Setup PLC Code

1. Open your TwinCAT project
2. Add the example variables from `example_plc_code.st` to your Global Variable List
3. Make sure to use the TwinCAT attributes as shown
4. Compile and download to PLC
5. Set PLC to RUN mode

### 5. Run Application

For testing with mock data (no PLC needed):
```bash
python test_hmi.py
```

For real PLC connection:
```bash
python main.py
```

## Installation for End Users (EXE)

### 1. Build Executable

Run the build script:
```bash
build_exe.bat
```

This creates a standalone executable in the `dist` folder.

### 2. Deploy

Copy the following to target machine:
- `dist\TwinCAT_HMI.exe`
- `config.json` (with correct PLC settings)

### 3. Setup TwinCAT ADS Route

On the target machine:
1. Install TwinCAT ADS Router (free from Beckhoff)
2. Configure route to your PLC as described above

### 4. Run

Double-click `TwinCAT_HMI.exe`

## Troubleshooting

### "pyads" Import Error
- Make sure TwinCAT ADS DLLs are installed
- Reinstall pyads: `pip uninstall pyads` then `pip install pyads`

### Connection Failed
- Check AMS Net ID is correct
- Verify PLC is in RUN mode
- Check firewall allows ADS communication (port 48898)
- Verify route is configured in TwinCAT

### No Symbols Found
- Check that PLC code uses the correct attribute format
- Verify symbols are compiled and downloaded
- Make sure PLC is in RUN mode

### Alarms Not Working
- Check attribute spelling (case-sensitive)
- Verify numeric alarm limits are valid
- Check AlarmPriority is between 1-4

### Performance Issues
- Increase update_interval in config.json
- Reduce number of monitored symbols
- Check network latency to remote PLC

## File Structure

```
Easy_TwincatHMI/
├── main.py                      # Main application
├── ads_client.py                # ADS communication
├── ads_symbol_parser.py         # Symbol parsing
├── alarm_manager.py             # Alarm logic
├── alarm_logger.py              # CSV logging
├── alarm_banner.py              # Alarm display widget
├── alarm_history_window.py      # History window
├── gui_panels.py                # UI panels
├── config.json                  # Configuration
├── requirements.txt             # Python dependencies
├── build_exe.bat               # Build script
├── test_hmi.py                 # Test with mock data
├── example_plc_code.st         # Example PLC code
└── alarm_logs/                 # Auto-created log folder
```

## Testing Without PLC

Use the test script to run with simulated data:

```bash
python test_hmi.py
```

This creates mock PLC data and simulates alarm conditions after 10 and 20 seconds.

## Configuration Options

### config.json

```json
{
  "ads": {
    "ams_net_id": "127.0.0.1.1.1",    // PLC AMS Net ID
    "ams_port": 851,                   // PLC runtime port
    "update_interval": 1.0             // Update rate in seconds
  },
  "alarms": {
    "enabled": true,                   // Enable alarm system
    "sound_enabled": true,             // Play alarm sounds
    "blink_interval": 500,             // Blink rate in ms
    "auto_acknowledge": false,         // Auto-acknowledge alarms
    "log_to_csv": true,                // Log alarms to CSV
    "hysteresis_percent": 2.0          // Alarm hysteresis %
  },
  "symbol_search": {
    "enabled": true,
    "search_patterns": [               // Attributes to search for
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
    "alarm_banner_max_visible": 5      // Max visible alarms
  }
}
```

## Advanced Configuration

### Custom Alarm Priorities

In your PLC code, set AlarmPriority attribute:
- 1 = Critical (Red, ⛔)
- 2 = High (Orange, ⚠️)
- 3 = Medium (Yellow, ⚡)
- 4 = Low (Blue, ℹ️)

### Custom Alarm Hysteresis

Adjust `hysteresis_percent` in config.json to change the deadband for alarm clearing.

Example: With 2% hysteresis and AlarmHigh = 90:
- Alarm triggers at: 90.0
- Alarm clears at: 88.2 (90 - 2%)

### Multiple Update Rates

For different update rates for different symbol types, you would need to modify the code to support multiple timers.

## Support

For issues or questions:
1. Check this guide
2. Review example_plc_code.st
3. Test with test_hmi.py first
4. Check logs in alarm_logs folder

## License

MIT License - Free to use and modify
