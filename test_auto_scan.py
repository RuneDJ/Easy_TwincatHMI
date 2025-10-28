"""
Test automatic symbol scanning
"""

import sys
import json
from ads_client import ADSClient
from symbol_auto_config import SymbolAutoConfig

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def load_config():
    """Load config"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def test_auto_scan():
    """Test automatic scanning"""
    print("="*80)
    print("TESTING AUTOMATIC SYMBOL SCANNER")
    print("="*80)
    print()
    
    # Load config
    config = load_config()
    
    # Create ADS client
    print("Connecting to PLC...")
    ads_client = ADSClient(
        config['ads']['ams_net_id'],
        config['ads']['ams_port']
    )
    
    if not ads_client.connect():
        print("❌ Failed to connect")
        return False
    
    print("✓ Connected")
    print()
    
    # Create auto-config scanner
    print("Creating scanner...")
    scanner = SymbolAutoConfig(ads_client)
    
    # Run scan
    print("Scanning PLC symbols...")
    print("-"*80)
    success = scanner.scan_and_generate_config('config_auto_test.json')
    print("-"*80)
    print()
    
    if success:
        print("✓ Scan completed successfully!")
        print()
        
        # Load and display results
        with open('config_auto_test.json', 'r', encoding='utf-8') as f:
            auto_config = json.load(f)
        
        manual_symbols = auto_config.get('manual_symbols', {})
        symbols_dict = manual_symbols.get('symbols', {})
        
        # Convert dict to list with name included
        symbols = [{'name': k, **v} for k, v in symbols_dict.items()]
        
        print("="*80)
        print(f"DISCOVERED {len(symbols)} SYMBOLS")
        print("="*80)
        print()
        
        # Group by category
        by_category = {}
        for sym in symbols:
            cat = sym.get('category', 'unknown')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(sym)
        
        # Display by category
        for category in ['setpoint', 'process_value', 'switch', 'alarm']:
            if category in by_category:
                items = by_category[category]
                print(f"\n{category.upper()} ({len(items)} symbols):")
                print("-"*80)
                
                for sym in items:
                    print(f"\n  {sym['name']}")
                    if 'unit' in sym:
                        print(f"    Unit: {sym['unit']}")
                    if 'min' in sym and 'max' in sym:
                        print(f"    Range: {sym['min']} - {sym['max']}")
                    if 'positions' in sym:
                        print(f"    Positions: {sym['positions']}")
                    if 'alarm_limits' in sym:
                        limits = sym['alarm_limits']
                        if any(limits.values()):
                            print(f"    Alarm Limits: {limits}")
                    if 'priority' in sym:
                        print(f"    Priority: {sym['priority']}")
        
        print()
        print("="*80)
        print("COMPARISON WITH EXPECTED SYMBOLS")
        print("="*80)
        
        expected = {
            'setpoint': ['GVL.TemperaturSetpunkt', 'GVL.TrykSetpunkt', 'GVL.FlowSetpunkt'],
            'process_value': ['GVL.Temperatur_1', 'GVL.Temperatur_2', 'GVL.Tryk_1', 
                             'GVL.Flow_1', 'GVL.Niveau_1'],
            'switch': ['GVL.DriftMode', 'GVL.PumpeValg', 'GVL.Prioritet'],
            'alarm': ['GVL.Motor1Fejl', 'GVL.NodStop', 'GVL.LavtOlieTryk', 
                     'GVL.FilterAdvarsel', 'GVL.VedligeholdPaamindelse']
        }
        
        found_names = {sym['name'] for sym in symbols}
        
        for category, expected_names in expected.items():
            print(f"\n{category.upper()}:")
            for name in expected_names:
                if name in found_names:
                    # Check if correct category
                    sym = next(s for s in symbols if s['name'] == name)
                    if sym['category'] == category:
                        print(f"  ✓ {name} (correct category)")
                    else:
                        print(f"  ⚠ {name} (found as {sym['category']})")
                else:
                    print(f"  ✗ {name} (NOT FOUND)")
        
        # Summary
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        total_expected = sum(len(v) for v in expected.values())
        total_found = len([n for names in expected.values() for n in names if n in found_names])
        correct_category = len([n for cat, names in expected.items() 
                               for n in names if n in found_names 
                               and next(s for s in symbols if s['name'] == n)['category'] == cat])
        
        print(f"Expected: {total_expected}")
        print(f"Found: {total_found}")
        print(f"Correct category: {correct_category}")
        print()
        
        if correct_category == total_expected:
            print("✅ ALL SYMBOLS DETECTED CORRECTLY!")
        elif total_found == total_expected:
            print("⚠️ All symbols found but some categories incorrect")
        else:
            print("❌ Some symbols not detected - algorithm needs improvement")
    else:
        print("❌ Scan failed")
        return False
    
    ads_client.disconnect()
    print()
    print("Test completed")
    return True

if __name__ == '__main__':
    test_auto_scan()
    input("\nPress Enter to exit...")
