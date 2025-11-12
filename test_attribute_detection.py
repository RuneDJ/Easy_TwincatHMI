"""
Debug script to test pyads attribute detection
Tests different methods to find {attribute 'HMI'} markers in PLC
"""

import pyads
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_attribute_detection():
    """Test different methods to detect attributes in PLC"""
    
    AMS_NET_ID = "5.112.50.143.1.1"
    AMS_PORT = 851
    
    print("=" * 80)
    print("PYADS ATTRIBUTE DETECTION TEST")
    print("=" * 80)
    
    try:
        # Connect
        print(f"\nConnecting to {AMS_NET_ID}:{AMS_PORT}...")
        plc = pyads.Connection(AMS_NET_ID, AMS_PORT)
        plc.open()
        print("✓ Connected\n")
        
        # Method 1: Get all symbols and inspect properties
        print("=" * 80)
        print("METHOD 1: Inspecting all symbol properties")
        print("=" * 80)
        
        symbols = plc.get_all_symbols()
        print(f"Found {len(symbols)} total symbols in PLC\n")
        
        # Inspect first 10 symbols in detail
        print("Inspecting first 10 symbols:")
        for i, symbol in enumerate(symbols[:10]):
            print(f"\n{i+1}. Symbol: {symbol.name}")
            print(f"   Type: {symbol.plc_type if hasattr(symbol, 'plc_type') else 'N/A'}")
            print(f"   Size: {symbol.size if hasattr(symbol, 'size') else 'N/A'}")
            
            # Check for comment
            if hasattr(symbol, 'comment'):
                print(f"   Comment: '{symbol.comment}'")
                if '{attribute' in symbol.comment.lower():
                    print(f"   >>> FOUND ATTRIBUTE IN COMMENT! <<<")
            else:
                print(f"   Comment: Not available")
            
            # Check for attributes property
            if hasattr(symbol, 'attributes'):
                print(f"   Attributes: {symbol.attributes}")
            else:
                print(f"   Attributes: Not available")
            
            # Check other properties
            print(f"   All properties: {dir(symbol)}")
        
        # Method 2: Search for symbols with 'HMI' in name
        print("\n" + "=" * 80)
        print("METHOD 2: Searching for 'HMI' in symbol names")
        print("=" * 80)
        
        hmi_symbols = [s for s in symbols if 'HMI' in s.name.upper()]
        print(f"Found {len(hmi_symbols)} symbols with 'HMI' in name:\n")
        
        for symbol in hmi_symbols[:20]:  # Show first 20
            print(f"  - {symbol.name}")
            if hasattr(symbol, 'plc_type'):
                print(f"    Type: {symbol.plc_type}")
            if hasattr(symbol, 'comment'):
                print(f"    Comment: {symbol.comment}")
        
        # Method 3: Try to read symbol information from specific paths and explore recursively
        print("\n" + "=" * 80)
        print("METHOD 3: Testing specific known paths and exploring structure")
        print("=" * 80)
        
        def explore_symbol(path, indent=0, max_depth=10, found_hmi_symbols=None):
            """Recursively explore symbol structure - searches EVERYTHING including deep arrays"""
            if found_hmi_symbols is None:
                found_hmi_symbols = []
            
            if indent > max_depth:
                print(f"{'  ' * indent}... (max depth {max_depth} reached)")
                return found_hmi_symbols
            
            prefix = "  " * indent
            try:
                symbol = plc.get_symbol(path)
                
                # Show basic info
                type_str = str(symbol.plc_type) if hasattr(symbol, 'plc_type') else 'Unknown'
                size = symbol.size if hasattr(symbol, 'size') else 0
                
                # Check if this is an HMI symbol
                is_hmi_type = 'ST_HMI' in type_str.upper()
                has_hmi_in_name = 'HMI' in path.upper()
                has_attribute = False
                
                comment = ''
                if hasattr(symbol, 'comment') and symbol.comment:
                    comment = symbol.comment
                    if '{attribute' in comment.lower() and 'hmi' in comment.lower():
                        has_attribute = True
                
                # Print info
                print(f"{prefix}✓ {path}")
                print(f"{prefix}  Type: {type_str}, Size: {size}")
                
                if comment:
                    print(f"{prefix}  Comment: '{comment}'")
                
                # Highlight if HMI-related
                if is_hmi_type:
                    print(f"{prefix}  >>> ST_HMI_* TYPE FOUND! <<<")
                    found_hmi_symbols.append({
                        'path': path,
                        'type': type_str,
                        'reason': 'ST_HMI type'
                    })
                
                if has_attribute:
                    print(f"{prefix}  >>> {{attribute 'HMI'}} FOUND! <<<")
                    found_hmi_symbols.append({
                        'path': path,
                        'type': type_str,
                        'reason': 'attribute marker'
                    })
                
                # Check if it's an array type
                is_array = 'ARRAY' in type_str.upper() or '[' in type_str
                
                # Explore sub-items
                sub_items = None
                if hasattr(symbol, 'sub_items') and symbol.sub_items:
                    sub_items = symbol.sub_items
                elif hasattr(symbol, 'subitems') and symbol.subitems:
                    sub_items = symbol.subitems
                
                if sub_items and len(sub_items) > 0:
                    print(f"{prefix}  Sub-items: {len(sub_items)}")
                    
                    # If it's an array, show sample of items
                    if is_array and len(sub_items) > 5:
                        print(f"{prefix}  (Array detected - showing first 3 and last 1)")
                        items_to_explore = list(sub_items[:3]) + [sub_items[-1]]
                    else:
                        items_to_explore = sub_items
                    
                    for sub in items_to_explore:
                        sub_path = f"{path}.{sub.name}"
                        explore_symbol(sub_path, indent + 1, max_depth, found_hmi_symbols)
                
                return found_hmi_symbols
                
            except Exception as e:
                print(f"{prefix}✗ {path}: {str(e)[:100]}")
                return found_hmi_symbols
        
        # Test common root paths
        test_roots = [
            "MAIN",
            "GVL",
        ]
        
        print("\n🔍 DEEP RECURSIVE SEARCH - Searching up to 10 levels deep")
        print("This will find HMI symbols even in deep array structures")
        print("=" * 80)
        
        all_found_hmi_symbols = []
        
        for root in test_roots:
            print(f"\n--- Exploring: {root} (recursively) ---")
            found = explore_symbol(root, indent=0, max_depth=10, found_hmi_symbols=[])
            all_found_hmi_symbols.extend(found)
        
        # Summary of found HMI symbols
        if all_found_hmi_symbols:
            print("\n" + "=" * 80)
            print(f"🎯 FOUND {len(all_found_hmi_symbols)} HMI SYMBOLS:")
            print("=" * 80)
            for item in all_found_hmi_symbols:
                print(f"\n  Path: {item['path']}")
                print(f"  Type: {item['type']}")
                print(f"  Reason: {item['reason']}")
        else:
            print("\n⚠️ No HMI symbols found in deep recursive search")
        
        # Additionally, search top-level symbols with 'HMI' in name
        print("\n" + "=" * 80)
        print("METHOD 3B: Quick check of top-level symbols with 'HMI'")
        print("=" * 80)
        
        for symbol in symbols[:50]:  # Check first 50 symbols
            if 'HMI' in symbol.name.upper():
                print(f"\n--- Top-level HMI symbol: {symbol.name} ---")
                explore_symbol(symbol.name, indent=0, max_depth=3, found_hmi_symbols=all_found_hmi_symbols)
        
        # Method 4: Check symbol info structure
        print("\n" + "=" * 80)
        print("METHOD 4: Detailed symbol info structure")
        print("=" * 80)
        
        if len(symbols) > 0:
            test_symbol = symbols[0]
            print(f"\nDetailed inspection of: {test_symbol.name}")
            print("\nAll attributes and methods:")
            for attr in dir(test_symbol):
                if not attr.startswith('_'):
                    try:
                        value = getattr(test_symbol, attr)
                        if not callable(value):
                            print(f"  {attr}: {value}")
                    except:
                        print(f"  {attr}: <not accessible>")
        
        # Method 5: Try to access symbol via TMC file
        print("\n" + "=" * 80)
        print("METHOD 5: Checking for TMC file access")
        print("=" * 80)
        
        try:
            # Check if we can get symbol upload info
            info = plc.read_state()
            print(f"PLC State: {info}")
        except Exception as e:
            print(f"Could not read PLC state: {e}")
        
        # Method 6: Search for specific STRUCT types
        print("\n" + "=" * 80)
        print("METHOD 6: Searching for ST_HMI_* types")
        print("=" * 80)
        
        hmi_struct_symbols = []
        for symbol in symbols:
            if hasattr(symbol, 'plc_type'):
                type_name = symbol.plc_type
                if 'ST_HMI' in str(type_name).upper():
                    hmi_struct_symbols.append(symbol)
                    print(f"  Found: {symbol.name}")
                    print(f"    Type: {type_name}")
                    if hasattr(symbol, 'comment'):
                        print(f"    Comment: {symbol.comment}")
        
        print(f"\nFound {len(hmi_struct_symbols)} symbols with ST_HMI_* types")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total symbols scanned: {len(symbols)}")
        print(f"Symbols with 'HMI' in name: {len(hmi_symbols)}")
        print(f"Symbols with ST_HMI_* type: {len(hmi_struct_symbols)}")
        print(f"HMI symbols found in deep search: {len(all_found_hmi_symbols)}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        
        if len(all_found_hmi_symbols) > 0:
            print("✅ HMI symbols found in deep recursive search!")
            print("\nPaths to use in auto-scan:")
            unique_paths = list(set([item['path'] for item in all_found_hmi_symbols]))
            for path in unique_paths:
                print(f"  - {path}")
        elif len(hmi_struct_symbols) > 0:
            print("✓ ST_HMI_* types found at top level!")
            print("  Scanner should look for plc_type containing 'ST_HMI'")
        elif len(hmi_symbols) > 0:
            print("⚠ Symbols with 'HMI' in name found, but no ST_HMI_* types")
            print("  Check if PLC uses different naming convention")
        else:
            print("✗ No HMI symbols found")
            print("  Options:")
            print("  1. Check if PLC has HMI symbols at all")
            print("  2. Verify {attribute 'HMI'} is added in PLC code")
            print("  3. Try scanning with different root paths")
            print("  4. Check TMC file for attribute information")
        
        # Close connection
        plc.close()
        print("\n✓ Disconnected")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")


if __name__ == "__main__":
    test_attribute_detection()
