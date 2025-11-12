"""
Test script to check if pyads.get_all_symbols() can access HMI attributes

This tests whether we can use the built-in get_all_symbols() method
to directly access all PLC symbols and their attributes.
"""

import pyads
import json
from typing import Dict, Any


def inspect_symbol_properties(symbol) -> Dict[str, Any]:
    """Extract all available properties from a symbol"""
    properties = {}
    
    # Standard properties
    properties['name'] = getattr(symbol, 'name', None)
    properties['symbol_type'] = getattr(symbol, 'symbol_type', None)
    properties['index_group'] = getattr(symbol, 'index_group', None)
    properties['index_offset'] = getattr(symbol, 'index_offset', None)
    properties['size'] = getattr(symbol, 'size', None)
    properties['plc_type'] = getattr(symbol, 'plc_type', None)
    properties['comment'] = getattr(symbol, 'comment', None)
    
    # Check for attributes
    if hasattr(symbol, 'attributes'):
        properties['attributes'] = symbol.attributes
    
    # Check for all possible attribute-related properties
    for attr_name in dir(symbol):
        if 'attr' in attr_name.lower() or 'hmi' in attr_name.lower():
            try:
                value = getattr(symbol, attr_name)
                if not callable(value):
                    properties[attr_name] = value
            except:
                pass
    
    return properties


def test_get_all_symbols():
    """Test pyads.get_all_symbols() method"""
    
    print("=" * 80)
    print("TESTING: pyads.Connection.get_all_symbols()")
    print("=" * 80)
    
    try:
        # Connect to PLC
        plc = pyads.Connection('5.112.50.143.1.1', pyads.PORT_TC3PLC1)
        plc.open()
        print("✓ Connected to PLC")
        
        # Get all symbols
        print("\nRetrieving all symbols from PLC...")
        all_symbols = plc.get_all_symbols()
        print(f"✓ Found {len(all_symbols)} symbols")
        
        # Analyze symbols
        print("\n" + "=" * 80)
        print("ANALYZING SYMBOLS")
        print("=" * 80)
        
        hmi_sp_symbols = []
        hmi_pv_symbols = []
        hmi_switch_symbols = []
        hmi_alarm_symbols = []
        symbols_with_comment = []
        symbols_with_attributes = []
        
        for i, symbol in enumerate(all_symbols[:50]):  # First 50 for quick overview
            props = inspect_symbol_properties(symbol)
            
            # Check for HMI-related content
            name = props.get('name', '')
            comment = props.get('comment', '')
            
            # Check if comment contains attribute markers
            if comment:
                symbols_with_comment.append((name, comment))
                
                if 'HMI_SP' in comment:
                    hmi_sp_symbols.append(name)
                if 'HMI_PV' in comment:
                    hmi_pv_symbols.append(name)
                if 'HMI_SWITCH' in comment:
                    hmi_switch_symbols.append(name)
                if 'HMI_ALARM' in comment:
                    hmi_alarm_symbols.append(name)
            
            # Check for attributes property
            if props.get('attributes'):
                symbols_with_attributes.append((name, props['attributes']))
            
            # Print first few symbols in detail
            if i < 10:
                print(f"\n--- Symbol {i+1}: {name} ---")
                for key, value in props.items():
                    if value is not None:
                        print(f"  {key}: {value}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY OF FIRST 50 SYMBOLS")
        print("=" * 80)
        print(f"Total symbols: {len(all_symbols)}")
        print(f"Symbols with comments: {len(symbols_with_comment)}")
        print(f"Symbols with attributes property: {len(symbols_with_attributes)}")
        print(f"\nHMI_SP symbols found: {len(hmi_sp_symbols)}")
        print(f"HMI_PV symbols found: {len(hmi_pv_symbols)}")
        print(f"HMI_SWITCH symbols found: {len(hmi_switch_symbols)}")
        print(f"HMI_ALARM symbols found: {len(hmi_alarm_symbols)}")
        
        # Show examples
        if symbols_with_comment:
            print("\n" + "=" * 80)
            print("SYMBOLS WITH COMMENTS (Examples)")
            print("=" * 80)
            for name, comment in symbols_with_comment[:5]:
                print(f"\n{name}:")
                print(f"  {comment}")
        
        if symbols_with_attributes:
            print("\n" + "=" * 80)
            print("SYMBOLS WITH ATTRIBUTES PROPERTY")
            print("=" * 80)
            for name, attributes in symbols_with_attributes[:5]:
                print(f"\n{name}:")
                print(f"  {attributes}")
        
        # Deep search through ALL symbols for HMI markers
        print("\n" + "=" * 80)
        print("DEEP SEARCH: ALL SYMBOLS FOR HMI MARKERS")
        print("=" * 80)
        
        all_hmi_symbols = {
            'HMI_SP': [],
            'HMI_PV': [],
            'HMI_SWITCH': [],
            'HMI_ALARM': []
        }
        
        for symbol in all_symbols:
            props = inspect_symbol_properties(symbol)
            name = props.get('name', '')
            comment = props.get('comment', '') or ''
            
            # Check comment for HMI markers
            if 'HMI_SP' in comment:
                all_hmi_symbols['HMI_SP'].append(name)
            if 'HMI_PV' in comment:
                all_hmi_symbols['HMI_PV'].append(name)
            if 'HMI_SWITCH' in comment:
                all_hmi_symbols['HMI_SWITCH'].append(name)
            if 'HMI_ALARM' in comment:
                all_hmi_symbols['HMI_ALARM'].append(name)
        
        print(f"\nTotal HMI_SP symbols: {len(all_hmi_symbols['HMI_SP'])}")
        if all_hmi_symbols['HMI_SP']:
            print("  Examples:")
            for sym in all_hmi_symbols['HMI_SP'][:5]:
                print(f"    - {sym}")
        
        print(f"\nTotal HMI_PV symbols: {len(all_hmi_symbols['HMI_PV'])}")
        if all_hmi_symbols['HMI_PV']:
            print("  Examples:")
            for sym in all_hmi_symbols['HMI_PV'][:5]:
                print(f"    - {sym}")
        
        print(f"\nTotal HMI_SWITCH symbols: {len(all_hmi_symbols['HMI_SWITCH'])}")
        if all_hmi_symbols['HMI_SWITCH']:
            print("  Examples:")
            for sym in all_hmi_symbols['HMI_SWITCH'][:5]:
                print(f"    - {sym}")
        
        print(f"\nTotal HMI_ALARM symbols: {len(all_hmi_symbols['HMI_ALARM'])}")
        if all_hmi_symbols['HMI_ALARM']:
            print("  Examples:")
            for sym in all_hmi_symbols['HMI_ALARM'][:5]:
                print(f"    - {sym}")
        
        # Detailed analysis of one HMI symbol if found
        if any(len(v) > 0 for v in all_hmi_symbols.values()):
            print("\n" + "=" * 80)
            print("DETAILED ANALYSIS OF HMI SYMBOL")
            print("=" * 80)
            
            # Find first HMI symbol
            for category, symbols in all_hmi_symbols.items():
                if symbols:
                    test_symbol_name = symbols[0]
                    # Get the symbol object
                    test_symbol = next((s for s in all_symbols if s.name == test_symbol_name), None)
                    if test_symbol:
                        print(f"\nSymbol: {test_symbol_name}")
                        print(f"Category: {category}")
                        props = inspect_symbol_properties(test_symbol)
                        print("\nAll properties:")
                        for key, value in props.items():
                            if value is not None:
                                print(f"  {key}: {value}")
                        
                        # Try to extract individual attributes from comment
                        comment = props.get('comment', '')
                        if comment:
                            print("\nParsing comment for attributes:")
                            lines = comment.split('\n')
                            for line in lines:
                                if 'attribute' in line.lower():
                                    print(f"  {line.strip()}")
                    break
        
        # Recommendations
        print("\n" + "=" * 80)
        print("CONCLUSIONS & RECOMMENDATIONS")
        print("=" * 80)
        
        total_hmi = sum(len(v) for v in all_hmi_symbols.values())
        
        if total_hmi > 0:
            print(f"✅ SUCCESS! Found {total_hmi} HMI symbols using get_all_symbols()")
            print("\nget_all_symbols() CAN access HMI attributes in comments!")
            print("\nNext steps:")
            print("1. Update hmi_attribute_scanner.py to use get_all_symbols()")
            print("2. Parse comment field to extract attribute markers")
            print("3. Extract additional attributes (Unit, Min, Max, etc.) from comment")
        else:
            print("⚠ No HMI symbols found in comments")
            print("\nPossible reasons:")
            print("1. PLC not running or not compiled with example code")
            print("2. Attributes not accessible via ADS comment field")
            print("3. Need to use TMC file parsing instead")
        
        plc.close()
        print("\n✓ Disconnected from PLC")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_get_all_symbols()
