"""
Enhanced ADS Connection Test
Detailed diagnostics for symbol discovery debugging
"""

import pyads
import logging
import json
import re
import sys
from typing import Dict, List, Any, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")
        return None

def analyze_symbol_comment(comment: str) -> Dict[str, Any]:
    """Analyze symbol comment for HMI attributes"""
    result = {
        'has_hmi_marker': False,
        'hmi_category': None,
        'extracted_attributes': {},
        'has_attribute_syntax': False,
        'comment_length': len(comment) if comment else 0
    }
    
    if not comment:
        return result
    
    # Check for HMI category markers
    hmi_markers = {
        'HMI_SP': 'SETPOINT',
        'HMI_PV': 'PROCESS_VALUE',
        'HMI_SWITCH': 'SWITCH',
        'HMI_ALARM': 'ALARM'
    }
    
    for marker, category in hmi_markers.items():
        if marker in comment:
            result['has_hmi_marker'] = True
            result['hmi_category'] = category
            break
    
    # Check if comment has attribute syntax
    if '{attribute' in comment.lower():
        result['has_attribute_syntax'] = True
    
    # Try to extract attribute lines (pattern: {attribute 'Name' := 'Value'})
    attribute_pattern = r"\{attribute\s+'([^']+)'\s*:=\s*'([^']+)'\}"
    matches = re.findall(attribute_pattern, comment)
    
    for attr_name, attr_value in matches:
        result['extracted_attributes'][attr_name] = attr_value
    
    return result


def test_ads_connection():
    """Test ADS connection and symbol discovery with detailed diagnostics"""
    
    # Load configuration
    config = load_config()
    if config:
        AMS_NET_ID = config['ads']['ams_net_id']
        AMS_PORT = config['ads']['ams_port']
    else:
        # Fallback to defaults
        AMS_NET_ID = "5.112.50.143.1.1"
        AMS_PORT = 851
    
    print("=" * 80)
    print("ENHANCED ADS CONNECTION TEST - SYMBOL DISCOVERY DIAGNOSTICS")
    print("=" * 80)
    print(f"Target: {AMS_NET_ID}:{AMS_PORT}")
    print()
    
    try:
        # Create and open connection
        plc = pyads.Connection(AMS_NET_ID, AMS_PORT)
        plc.open()
        print("✓ Connection opened successfully")
        
        # Read device info
        try:
            device_info = plc.read_device_info()
            print(f"✓ Device: {device_info.name}")
            print(f"✓ Version: {device_info.version}")
        except Exception as e:
            print(f"⚠ Device info unavailable: {e}")
        
        print()
        print("=" * 80)
        print("DISCOVERING SYMBOLS")
        print("=" * 80)
        
        # Get all symbols
        symbols = plc.get_all_symbols()
        print(f"✓ Found {len(symbols)} total symbols")
        print()
        
        # Analyze all symbols
        hmi_categories = {
            'HMI_SP': [],
            'HMI_PV': [],
            'HMI_SWITCH': [],
            'HMI_ALARM': []
        }
        
        symbols_with_comments = 0
        symbols_with_hmi_markers = 0
        symbols_with_attribute_syntax = 0
        symbols_with_extracted_attrs = 0
        
        all_analyzed = []
        
        for symbol in symbols:
            comment = symbol.comment if hasattr(symbol, 'comment') else ''
            analysis = analyze_symbol_comment(comment)
            
            if comment:
                symbols_with_comments += 1
            
            if analysis['has_hmi_marker']:
                symbols_with_hmi_markers += 1
                # Categorize
                for marker, category in [('HMI_SP', 'HMI_SP'), ('HMI_PV', 'HMI_PV'), 
                                        ('HMI_SWITCH', 'HMI_SWITCH'), ('HMI_ALARM', 'HMI_ALARM')]:
                    if marker in comment:
                        hmi_categories[marker].append((symbol, analysis))
                        break
            
            if analysis['has_attribute_syntax']:
                symbols_with_attribute_syntax += 1
            
            if analysis['extracted_attributes']:
                symbols_with_extracted_attrs += 1
            
            all_analyzed.append((symbol, analysis))
        
        # Statistics
        print("STATISTICS:")
        print(f"  Total symbols: {len(symbols)}")
        print(f"  With comments: {symbols_with_comments}")
        print(f"  With HMI markers: {symbols_with_hmi_markers}")
        print(f"  With {{attribute}} syntax: {symbols_with_attribute_syntax}")
        print(f"  With extracted attributes: {symbols_with_extracted_attrs}")
        print()
        
        print("HMI CATEGORY BREAKDOWN:")
        for category, items in hmi_categories.items():
            print(f"  {category}: {len(items)} symbols")
        print()
        
        # Expected symbols from example_plc_code.st
        expected_symbols = {
            'SETPOINTS (HMI_SP)': [
                'GVL.TemperaturSetpunkt',
                'GVL.TrykSetpunkt',
                'GVL.FlowSetpunkt'
            ],
            'PROCESS VALUES (HMI_PV)': [
                'GVL.Temperatur_1',
                'GVL.Temperatur_2',
                'GVL.Tryk_1',
                'GVL.Flow_1',
                'GVL.Niveau_1'
            ],
            'SWITCHES (HMI_SWITCH)': [
                'GVL.DriftMode',
                'GVL.PumpeValg',
                'GVL.Prioritet'
            ],
            'ALARMS (HMI_ALARM)': [
                'GVL.Motor1Fejl',
                'GVL.NodStop',
                'GVL.LavtOlieTryk',
                'GVL.FilterAdvarsel',
                'GVL.VedligeholdPaamindelse'
            ]
        }
        
        print("=" * 80)
        print("CHECKING EXPECTED SYMBOLS FROM example_plc_code.st")
        print("=" * 80)
        print()
        
        found_by_name = {s.name: (s, analyze_symbol_comment(s.comment if hasattr(s, 'comment') else '')) 
                        for s in symbols}
        
        total_expected = 0
        total_found = 0
        total_with_hmi = 0
        total_with_attrs = 0
        
        for category_name, symbol_names in expected_symbols.items():
            print(f"{category_name}:")
            print("-" * 80)
            
            for symbol_name in symbol_names:
                total_expected += 1
                
                if symbol_name in found_by_name:
                    total_found += 1
                    symbol, analysis = found_by_name[symbol_name]
                    
                    # Status indicators
                    found_marker = "✓" if analysis['has_hmi_marker'] else "⚠"
                    
                    print(f"\n  {found_marker} {symbol_name}")
                    print(f"      Type: {symbol.plc_type}")
                    
                    # Try to read value
                    try:
                        value = plc.read_by_name(symbol_name)
                        print(f"      Value: {value}")
                    except Exception as e:
                        print(f"      Value: Error ({e})")
                    
                    # Analysis details
                    if analysis['has_hmi_marker']:
                        total_with_hmi += 1
                        print(f"      HMI Category: {analysis['hmi_category']}")
                    else:
                        print(f"      HMI Marker: NOT FOUND")
                    
                    if analysis['extracted_attributes']:
                        total_with_attrs += 1
                        print(f"      Extracted Attributes: {list(analysis['extracted_attributes'].keys())}")
                    else:
                        print(f"      Extracted Attributes: None")
                    
                    # Show comment
                    if analysis['comment_length'] > 0:
                        print(f"      Comment Length: {analysis['comment_length']} chars")
                        
                        # Show first 200 chars of comment
                        comment = symbol.comment[:200] if hasattr(symbol, 'comment') else ''
                        if comment:
                            print(f"      Comment Preview: {comment}...")
                    else:
                        print(f"      Comment: EMPTY")
                else:
                    print(f"\n  ✗ {symbol_name}: NOT FOUND IN PLC")
            
            print()
        
        # Show ALL HMI-tagged symbols found
        print("=" * 80)
        print("ALL SYMBOLS WITH HMI MARKERS (detailed)")
        print("=" * 80)
        print()
        
        for category, items in hmi_categories.items():
            if items:
                print(f"\n{category} ({len(items)} symbols):")
                print("-" * 80)
                
                for symbol, analysis in items:
                    print(f"\n  Symbol: {symbol.name}")
                    print(f"  Type: {symbol.plc_type}")
                    
                    # Try read
                    try:
                        value = plc.read_by_name(symbol.name)
                        print(f"  Current Value: {value}")
                    except Exception as e:
                        print(f"  Read Error: {e}")
                    
                    # Attributes
                    if analysis['extracted_attributes']:
                        print(f"  Extracted Attributes:")
                        for attr_name, attr_value in analysis['extracted_attributes'].items():
                            print(f"    - {attr_name}: {attr_value}")
                    else:
                        print(f"  Extracted Attributes: None")
                    
                    # Comment
                    if analysis['comment_length'] > 0:
                        print(f"  Comment ({analysis['comment_length']} chars):")
                        
                        comment = symbol.comment if hasattr(symbol, 'comment') else ''
                        # Show more of the comment for detailed analysis
                        lines = comment.split('\n')[:10]  # First 10 lines
                        for line in lines:
                            print(f"    {line}")
                        
                        if len(comment.split('\n')) > 10:
                            print(f"    ... ({len(comment.split('\n')) - 10} more lines)")
        
        # Final diagnosis
        print("\n" + "=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print()
        print(f"Expected symbols: {total_expected}")
        print(f"Found in PLC: {total_found}")
        print(f"With HMI markers: {total_with_hmi}")
        print(f"With extracted attributes: {total_with_attrs}")
        print()
        
        if total_found < total_expected:
            print("❌ ISSUE 1: Not all expected symbols found")
            print("   → Check if PLC code from example_plc_code.st is compiled and downloaded")
            print()
        
        if total_with_hmi < total_found:
            print("❌ ISSUE 2: Symbols found but HMI markers missing from comments")
            print("   → TwinCAT may not be exporting {attribute 'HMI_XX'} in comments")
            print("   → Check PLC code has {attribute 'HMI_SP'} etc. above variables")
            print()
        
        if total_with_attrs < total_with_hmi:
            print("⚠️  ISSUE 3: HMI markers found but detailed attributes not extracted")
            print("   → TwinCAT exports attribute markers but not full {attribute 'Unit' := '°C'} syntax")
            print("   → This is EXPECTED behavior - attributes are compile-time metadata")
            print("   → Solution: Use symbol_auto_config.py to parse from comment text")
            print()
        
        if total_found == total_expected and total_with_hmi == total_found:
            print("✅ All expected symbols found with HMI markers!")
            if total_with_attrs > 0:
                print(f"✅ Bonus: {total_with_attrs} symbols have extractable attributes!")
            else:
                print("ℹ️  Note: Attributes not extracted (expected) - use auto-scan feature")
        
        plc.close()
        print("\n✓ Diagnostic test completed")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify AMS Net ID is correct")
        print("  2. Check PLC is in RUN mode")
        print("  3. Confirm TwinCAT route is configured")
        print("  4. Check firewall allows ADS (port 48898)")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    test_ads_connection()
    input("\nPress Enter to exit...")
