"""
Test if PLC exports attributes after update
"""
import pyads
import re
import sys
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_attribute_export():
    """Test if attributes are now available in symbol comments"""
    
    print("="*80)
    print("TESTING ATTRIBUTE EXPORT FROM PLC")
    print("="*80)
    print()
    
    # Connect
    plc = pyads.Connection('5.112.50.143.1.1', 851)
    plc.open()
    print("✓ Connected to PLC")
    print()
    
    # Get all symbols
    symbols = plc.get_all_symbols()
    print(f"Found {len(symbols)} total symbols")
    print()
    
    # Test specific symbols that should have attributes
    test_cases = {
        'GVL.TemperaturSetpunkt': {
            'expected_attrs': ['Unit', 'Min', 'Max', 'Decimals', 'AlarmHighHigh', 'AlarmHigh'],
            'expected_unit': '°C',
            'expected_category': 'HMI_SP'
        },
        'GVL.Temperatur_1': {
            'expected_attrs': ['Unit', 'Decimals', 'AlarmHighHigh', 'AlarmHigh', 'AlarmLow'],
            'expected_unit': '°C',
            'expected_category': 'HMI_PV'
        },
        'GVL.DriftMode': {
            'expected_attrs': ['Pos0', 'Pos1', 'Pos2'],
            'expected_category': 'HMI_SWITCH'
        },
        'GVL.Motor1Fejl': {
            'expected_attrs': ['AlarmText', 'AlarmPriority'],
            'expected_category': 'HMI_ALARM'
        }
    }
    
    print("="*80)
    print("DETAILED SYMBOL ANALYSIS")
    print("="*80)
    
    results = {}
    
    for symbol in symbols:
        if symbol.name in test_cases:
            expected = test_cases[symbol.name]
            
            print(f"\n{symbol.name}")
            print("-"*80)
            print(f"Type: {symbol.plc_type}")
            print(f"Comment length: {len(symbol.comment) if symbol.comment else 0} chars")
            
            # Check for category marker
            has_category = expected['expected_category'] in (symbol.comment or '')
            print(f"Category marker ({expected['expected_category']}): {'✓ FOUND' if has_category else '✗ NOT FOUND'}")
            
            # Check for each attribute
            found_attrs = []
            missing_attrs = []
            
            for attr in expected['expected_attrs']:
                # Look for attribute in comment
                pattern = rf"\{{attribute\s+'{attr}'[^}}]*\}}"
                match = re.search(pattern, symbol.comment or '', re.IGNORECASE)
                
                if match:
                    found_attrs.append(attr)
                    print(f"  ✓ {attr}: {match.group(0)[:60]}...")
                else:
                    # Try simpler pattern
                    if attr.lower() in (symbol.comment or '').lower():
                        found_attrs.append(attr)
                        print(f"  ⚠ {attr}: mentioned but not in attribute format")
                    else:
                        missing_attrs.append(attr)
                        print(f"  ✗ {attr}: NOT FOUND")
            
            # Show comment excerpt
            if symbol.comment:
                print(f"\nComment excerpt (first 300 chars):")
                print(symbol.comment[:300])
                if len(symbol.comment) > 300:
                    print(f"... ({len(symbol.comment) - 300} more chars)")
            else:
                print("\nComment: EMPTY")
            
            # Store results
            results[symbol.name] = {
                'has_category': has_category,
                'found_attrs': found_attrs,
                'missing_attrs': missing_attrs,
                'comment_length': len(symbol.comment) if symbol.comment else 0
            }
    
    plc.close()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    total_symbols = len(test_cases)
    symbols_with_category = sum(1 for r in results.values() if r['has_category'])
    total_expected_attrs = sum(len(tc['expected_attrs']) for tc in test_cases.values())
    total_found_attrs = sum(len(r['found_attrs']) for r in results.values())
    
    print(f"Tested symbols: {total_symbols}")
    print(f"With category markers: {symbols_with_category}/{total_symbols}")
    print(f"Expected attributes: {total_expected_attrs}")
    print(f"Found attributes: {total_found_attrs}/{total_expected_attrs}")
    print()
    
    if total_found_attrs == 0:
        print("❌ NO ATTRIBUTES FOUND")
        print("\nThis means TwinCAT still does NOT export {attribute ...} lines")
        print("to symbol comments, even after PLC update.")
        print()
        print("SOLUTION: Continue using intelligent auto-scanner with name-based detection")
    elif total_found_attrs < total_expected_attrs:
        print("⚠️ PARTIAL ATTRIBUTE EXPORT")
        print("\nSome attributes found but not all. TwinCAT may export")
        print("attributes partially or in a different format.")
    else:
        print("✅ ALL ATTRIBUTES FOUND!")
        print("\nTwinCAT now exports attributes! The auto-scanner can be")
        print("enhanced to parse these directly.")
    
    return results

if __name__ == '__main__':
    test_attribute_export()
    input("\nPress Enter to exit...")
