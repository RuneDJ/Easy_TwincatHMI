"""
Quick test to see which symbols exist in PLC
"""
import pyads
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

ams_net_id = config['plc']['ams_net_id']
ams_port = config['plc']['port']

print("Checking available symbols in PLC...")
print(f"Connecting to {ams_net_id}:{ams_port}")

plc = pyads.Connection(ams_net_id, ams_port)
plc.open()

test_symbols = [
    "MAIN.HMI",
    "MAIN.HMI.TemperaturSetpunkt",
    "MAIN.HMI.TemperaturSetpunkt.Value",
    "MAIN.HMI.TemperaturSetpunkt.Config",
    "MAIN.HMI.TemperaturSetpunkt.Config.Unit",
    "MAIN.HMI.TemperaturSetpunkt.Config.Min",
    "MAIN.HMI.TemperaturSetpunkt.AlarmLimits",
    "MAIN.HMI.TemperaturSetpunkt.AlarmLimits.AlarmHigh",
    "MAIN.HMI.TemperaturSetpunkt.Display",
    "MAIN.HMI.TemperaturSetpunkt.Display.DisplayName",
    "MAIN.HMI.Temperatur_1",
    "MAIN.HMI.Temperatur_1.Value",
    "MAIN.HMI.Temperatur_1.Config",
    "MAIN.HMI.Temperatur_1.Config.Unit",
    "MAIN.HMI.DriftMode",
    "MAIN.HMI.DriftMode.Position",
    "MAIN.HMI.DriftMode.Config",
    "MAIN.HMI.DriftMode.Config.Pos0_Label",
    "MAIN.HMI.Motor1Fejl",
    "MAIN.HMI.Motor1Fejl.Active",
]

print("\nSymbol Check:")
print("-" * 60)
for sym in test_symbols:
    try:
        # Try to get handle (this checks if symbol exists)
        handle = plc.get_handle(sym)
        plc.release_handle(handle)
        print(f"✓ {sym}")
    except Exception as e:
        print(f"✗ {sym} - {e}")

plc.close()
