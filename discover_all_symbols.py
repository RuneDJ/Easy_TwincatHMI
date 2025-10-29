"""
Complete PLC symbol discovery - check what actually exists
"""
import pyads
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

ams_net_id = config['plc']['ams_net_id']
ams_port = config['plc']['port']

print("=" * 70)
print("COMPLETE PLC SYMBOL DISCOVERY")
print("=" * 70)
print(f"Connecting to {ams_net_id}:{ams_port}\n")

plc = pyads.Connection(ams_net_id, ams_port)
plc.open()

# Test MAIN.HMI structure
print("Checking MAIN.HMI structure:")
print("-" * 70)

base_symbols = [
    "MAIN.HMI",
]

# Expected symbols from config
expected = {
    'setpoints': ["TemperaturSetpunkt", "TrykSetpunkt", "FlowSetpunkt"],
    'process_values': ["Temperatur_1", "Temperatur_2", "Tryk_1", "Flow_1", "Niveau_1"],
    'switches': ["DriftMode", "PumpeValg", "Prioritet"],
    'alarms': ["Motor1Fejl", "NodStop", "LavtOlieTryk", "FilterAdvarsel", "VedligeholdPaamindelse"]
}

found = {
    'setpoints': [],
    'process_values': [],
    'switches': [],
    'alarms': []
}

# Check each category
for category, symbols in expected.items():
    print(f"\n{category.upper()}:")
    for sym_name in symbols:
        full_path = f"MAIN.HMI.{sym_name}"
        try:
            handle = plc.get_handle(full_path)
            plc.release_handle(handle)
            
            # Try to read .Value or .Position or .Active
            if category in ['setpoints', 'process_values']:
                test_field = f"{full_path}.Value"
            elif category == 'switches':
                test_field = f"{full_path}.Position"
            else:  # alarms
                test_field = f"{full_path}.Active"
            
            try:
                h2 = plc.get_handle(test_field)
                plc.release_handle(h2)
                print(f"  ✓ {sym_name} (complete STRUCT)")
                found[category].append(sym_name)
            except:
                print(f"  ⚠ {sym_name} (exists but incomplete)")
                
        except Exception as e:
            print(f"  ✗ {sym_name} - NOT FOUND")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
for category, symbols in found.items():
    expected_count = len(expected[category])
    found_count = len(symbols)
    status = "✓" if found_count == expected_count else "✗"
    print(f"{status} {category}: {found_count}/{expected_count}")

print("\n" + "=" * 70)
print("RECOMMENDED CONFIG")
print("=" * 70)
print('"struct_symbols": {')
for category, symbols in found.items():
    if symbols:
        print(f'  "{category}": [')
        for sym in symbols:
            print(f'    "{sym}",')
        print(f'  ],')
print('}')

plc.close()
