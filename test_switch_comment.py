"""Quick test to see switch comments"""
import pyads

plc = pyads.Connection('5.112.50.143.1.1', 851)
plc.open()

symbols = plc.get_all_symbols()

# Find all switch symbols
switches = ['DriftMode', 'PumpeValg', 'Prioritet']

for switch_name in switches:
    for symbol in symbols:
        if switch_name in symbol.name:
            print(f"\n{'='*80}")
            print(f"Symbol: {symbol.name}")
            print(f"Type: {symbol.plc_type}")
            print(f"Comment length: {len(symbol.comment) if symbol.comment else 0}")
            print(f"\nComment:")
            print(symbol.comment if symbol.comment else "(empty)")
            print('='*80)
            break

plc.close()
